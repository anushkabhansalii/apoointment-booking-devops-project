# SlotSync — Appointment Booking, from laptop to monitored Kubernetes

[![CI/CD](https://github.com/anushkabhansalii/apoointment-booking-devops-project/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/anushkabhansalii/apoointment-booking-devops-project/actions/workflows/ci-cd.yml)

**SlotSync** is the front-desk booking system for *Bloom Wellness Studio*, a studio with four practitioners
(yoga, physiotherapy, massage and nutrition). Receptionists book, reschedule, confirm and cancel sessions;
the system refuses double-bookings and bookings outside opening hours, and shows the day's schedule,
revenue and completion rate at a glance.

The application is the vehicle. The project is the **delivery platform around it**: every push to `main`
is tested, scanned for secrets and CVEs, packaged as SHA-tagged images, published to GHCR, promoted
through Git, and rolled out by Argo CD to an EKS cluster that Terraform built — with Prometheus and
Grafana watching it.

> **Demo:** [`demo/presentation.mp4`](demo/presentation.mp4) (slides + live walkthrough on EKS) · [`demo/SlotSync-DevOps-Capstone.pptx`](demo/SlotSync-DevOps-Capstone.pptx) / [`.pdf`](demo/SlotSync-DevOps-Capstone.pdf) (slides) · [`docs/EVIDENCE.md`](docs/EVIDENCE.md) (screenshots for every rubric item)

---

## Contents

1. [Architecture](#1-architecture)
2. [Tech stack](#2-tech-stack)
3. [Repository layout](#3-repository-layout)
4. [The application](#4-the-application)
5. [Run it locally (Docker Compose)](#5-run-it-locally-docker-compose)
6. [Testing](#6-testing)
7. [CI/CD pipeline](#7-cicd-pipeline)
8. [DevSecOps: Trivy, Gitleaks, hardening](#8-devsecops)
9. [Terraform: AWS VPC + EKS](#9-terraform-aws-vpc--eks)
10. [Kubernetes + Helm](#10-kubernetes--helm)
11. [GitOps with Argo CD](#11-gitops-with-argo-cd)
12. [Observability: Prometheus + Grafana](#12-observability-prometheus--grafana)
13. [Autoscaling (HPA)](#13-autoscaling-hpa)
14. [Troubleshooting labs](#14-troubleshooting-labs)
15. [Tear-down and cost](#15-tear-down-and-cost)
16. [Known issues and limitations](#16-known-issues-and-limitations)

---

## 1. Architecture

![SlotSync architecture](docs/architecture.png)

<details><summary>Same diagram as Mermaid (renders on GitHub)</summary>

```mermaid
flowchart LR
    dev([Developer]) -->|git push| gh[(GitHub<br/>main)]

    subgraph CI["GitHub Actions"]
      direction TB
      t1[Gitleaks<br/>secret scan] & t2[Ruff + pytest<br/>33 tests] & t3[Alembic on<br/>real Postgres] & t4[React build<br/>+ ESLint] & t5[helm lint<br/>terraform validate]
      t1 & t2 & t3 & t4 & t5 --> b[docker build<br/>backend + frontend]
      b --> s{Trivy<br/>HIGH/CRITICAL?}
      s -- clean --> p[push to GHCR<br/>tag = commit SHA]
      t2 & t4 --> k[kind cluster<br/>helm install + helm test]
      p & k --> pr[promote:<br/>commit SHA to<br/>values-gitops.yaml]
    end

    gh --> CI
    pr -->|git commit| gh
    p --> ghcr[(GHCR<br/>images)]

    subgraph AWS["AWS ap-south-1 (Terraform)"]
      subgraph VPC["VPC 10.20.0.0/16 — 2 public + 2 private subnets, NAT"]
        nlb[Network Load Balancer] --> ing
        subgraph EKS["EKS cluster · managed node group"]
          argo[Argo CD] -->|sync| app
          ing[ingress-nginx] -->|/| fe[frontend x2<br/>React + Nginx]
          ing -->|/api| be[backend x2..8<br/>FastAPI · HPA]
          fe -->|/api proxy| be
          be --> pg[(PostgreSQL<br/>StatefulSet · gp3 EBS)]
          prom[Prometheus] -->|scrape /metrics| be
          graf[Grafana] --> prom
          app((slotsync<br/>namespace))
        end
      end
    end

    argo -->|watch| gh
    EKS -->|pull images| ghcr
    user([Studio staff]) --> nlb
```

</details>

**Request path:** browser → AWS NLB → ingress-nginx → `/` frontend Service (Nginx serving the React build) or
`/api` backend Service (FastAPI) → PostgreSQL. The browser only ever calls relative `/api/...` URLs, so the same
build works behind Vite (dev), Nginx (Compose) and the Ingress (Kubernetes).

**Delivery path:** `git push` → pipeline gates → image `ghcr.io/anushkabhansalii/slotsync-backend:<git-sha>` →
the pipeline commits that SHA into `helm/slotsync/values-gitops.yaml` → Argo CD sees the commit and rolls the
cluster forward. The pipeline never holds cluster credentials.

## 2. Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 6, plain CSS (responsive, container queries), served by Nginx (unprivileged) |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.1, Uvicorn |
| Database | PostgreSQL 16, Alembic migrations |
| Testing / quality | pytest (+ coverage gate 85%), Ruff lint + format, ESLint, `alembic check` |
| Containers | Docker multi-stage builds, Docker Compose, non-root users, read-only root FS in K8s |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR), multi-arch images (amd64 + arm64) |
| Security | Trivy (image CVEs, SARIF to GitHub Security), Gitleaks (secrets), SBOM + provenance attestations, Pod Security "restricted", NetworkPolicy |
| Infrastructure as Code | Terraform 1.6+, AWS provider 6, `terraform-aws-modules/vpc` and `/eks` |
| Cloud | AWS VPC, NAT gateway, EKS 1.35, managed node group (2× m7i-flex.large), EBS CSI (gp3), EKS Pod Identity, NLB |
| Kubernetes | Helm 3/4 chart, Ingress (ingress-nginx), HPA, PDB, NetworkPolicy, StatefulSet + PVC, `helm test` |
| GitOps | Argo CD (automated sync, prune, self-heal) |
| Observability | Prometheus + Grafana (kube-prometheus-stack), ServiceMonitor, PrometheusRule alerts, dashboard-as-code |

## 3. Repository layout

```text
.
├── backend/                     FastAPI service
│   ├── app/                     main.py · models.py · schemas.py · routers/ · metrics.py · database.py · config.py
│   ├── alembic/versions/        0001_create_providers_and_appointments.py
│   ├── tests/                   conftest.py (isolated SQLite DB) · test_appointments.py · test_catalog.py · test_meta.py
│   ├── Dockerfile               multi-stage, UID 10001, migrations in entrypoint
│   └── pytest.ini · ruff.toml · requirements*.txt
├── frontend/                    React + Vite dashboard
│   ├── src/                     App.jsx · components/ · api.js · time.js · styles.css
│   ├── Dockerfile               Node build stage → nginx-unprivileged runtime
│   └── nginx.conf.template      SPA routing + /api reverse proxy + security headers
├── docker-compose.yml           postgres + backend + frontend, health-gated
├── .github/workflows/ci-cd.yml  the whole pipeline
├── terraform/                   VPC + EKS (vpc.tf, eks.tf, variables.tf, outputs.tf, terraform.tfvars.example)
├── k8s/                         namespace (Pod Security restricted), monitoring namespace, gp3 StorageClass
├── helm/slotsync/               the application chart (templates, values-{dev,eks,gitops}.yaml, dashboard JSON)
├── gitops/                      Argo CD Application + Argo CD Helm values
├── monitoring/                  kube-prometheus-stack + ingress-nginx values, dashboard generator
├── scripts/                     install-platform · bootstrap-gitops · deploy-minikube · teardown-eks · seed data · load generator
├── troubleshooting/             three deliberately broken manifests + guide
├── docs/                        EVIDENCE.md and screenshots
└── demo/                        presentation video + slide deck
```

## 4. The application

### Domain rules (enforced by the API, covered by tests)

* A booking must fit inside opening hours (07:00–21:00 studio time, `Asia/Kolkata`).
* A practitioner cannot be double-booked: an overlapping booking returns **409 Conflict** with a readable message
  (`Diya Sharma is already booked from 10:00 to 10:45`). Cancelled bookings free their slot.
* Duration defaults from the service menu (e.g. Physiotherapy = 45 min) and can be overridden (15–240 min).
* Times sent without an offset are interpreted as studio time; everything is stored in UTC (`timestamptz`).

### REST API

Swagger UI: `/docs` · OpenAPI: `/openapi.json`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness — process is up (never touches the DB) |
| GET | `/ready` | Readiness — `SELECT 1` against PostgreSQL, 503 if unreachable |
| GET | `/metrics` | Prometheus metrics (HTTP + business counters) |
| GET | `/api/appointments` | List; filters `status`, `provider_id`, `day=YYYY-MM-DD`, `search` |
| GET | `/api/appointments/{id}` | One appointment |
| POST | `/api/appointments` | Book (validates hours, provider, conflicts) |
| PUT | `/api/appointments/{id}` | Update / reschedule (re-checks conflicts) |
| PATCH | `/api/appointments/{id}/status` | Confirm, complete, cancel, no-show |
| DELETE | `/api/appointments/{id}` | Delete |
| GET | `/api/appointments/stats` | KPIs: today, upcoming, by status/service/provider, completion & cancellation rate, revenue, next booking |
| GET | `/api/providers` | Active practitioners |
| GET | `/api/services` | Service menu with duration and price |
| GET | `/api/version` | Git SHA the API image was built from (shown in the UI sidebar next to the UI's own SHA) |

### Database

Two tables, created by Alembic revision `0001` (which also seeds the four practitioners):

```text
providers(id, name UNIQUE, specialty, color, active)
appointments(id, customer_name, customer_email, customer_phone, service, provider_id → providers.id,
             start_time timestamptz, duration_minutes CHECK 15..240, status appointment_status ENUM,
             notes, created_at, updated_at)   indexes: provider_id, start_time, status
```

Every backend container runs `alembic upgrade head` on start. A PostgreSQL **advisory lock** in `alembic/env.py`
makes concurrently starting replicas take turns, and `app/wait_for_db.py` waits for the database first so pods
don't crash-loop while PostgreSQL initialises.

### Frontend

A SaaS-style dashboard (dark sidebar, light workspace):

* **Front desk** – KPI cards (today's bookings, upcoming, completion rate, booked revenue), today's agenda with a
  "next up" card, service-mix and practitioner-load bars.
* **Schedule** – day timeline with one column per practitioner; bookings are positioned by time, a red line marks
  "now", double-click an empty slot to book it.
* **Appointments** – searchable, filterable table (status chips with counts, practitioner filter) with one-click
  status transitions, edit and delete. It collapses into cards on narrow screens.
* Booking modal with service-driven defaults and inline API errors; toasts; loading skeletons; a "backend
  unavailable" banner; a sidebar card showing API health and the build SHA baked in by CI.

## 5. Run it locally (Docker Compose)

Requirements: Docker Desktop (or Docker Engine + Compose v2).

```bash
docker compose up --build
python3 scripts/seed_demo_data.py        # optional: a realistic fortnight of bookings
```

| URL | What |
|---|---|
| http://localhost:3000 | SlotSync UI |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health · /ready · /metrics | probes and metrics |

```bash
docker compose down        # stop
docker compose down -v     # stop and delete the database volume
```

Compose starts PostgreSQL first, waits for `pg_isready`, then the backend (which migrates and waits until its own
`/health` passes), then the frontend. Both app images run as non-root users.

### Without Docker

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://slotsync:slotsync@localhost:5432/slotsync'
alembic upgrade head
uvicorn app.main:app --reload --port 8000

cd ../frontend && npm ci && npm run dev    # http://localhost:5173, proxies /api to :8000
```

## 6. Testing

```bash
cd backend
pytest -v
```

* **33 tests** across every endpoint: CRUD, validation (parametrised bad payloads), opening hours,
  double-booking and back-to-back rules, cancelled-slot reuse, filters, stats maths, `/health`, `/ready`,
  `/metrics` content, OpenAPI routes and the wait-for-DB helper.
* **Isolation:** `tests/conftest.py` sets `DATABASE_URL` to SQLite in-memory *before* the app is imported and
  overrides FastAPI's `get_db` dependency, so each test gets a brand-new database. The real PostgreSQL is never
  touched.
* `pytest.ini` turns warnings into errors; CI also enforces **≥85% coverage** (currently ~97%).
* Migrations are tested separately in CI against a real PostgreSQL 16 service container:
  `upgrade head → downgrade base → upgrade head`, then `alembic check` proves the models and migrations agree.

## 7. CI/CD pipeline

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push to `main` (and on pull requests,
without publishing).

```text
 TEST (parallel)                         BUILD + SCAN + PUSH (matrix)           DEPLOY
 ─────────────────────────────           ───────────────────────────            ───────────────────────────
 Gitleaks secret scan          ┐         docker build (cached)                  promote: write the SHA into
 Ruff + pytest + coverage      │         Trivy report (all severities)          helm/slotsync/values-gitops.yaml,
 Alembic on real Postgres      ├──────▶  Trivy SARIF → Security tab   ───────▶  commit "[skip ci]"
 ESLint + Vite build           │         Trivy GATE (HIGH/CRITICAL)                       │
 helm lint + template          │         push to GHCR  :<git-sha>                         ▼
 terraform fmt + validate      ┘         (amd64 + arm64, SBOM, provenance)      Argo CD syncs EKS
                                 └────▶  kind cluster: helm upgrade --install + helm test
```

| Requirement | Where |
|---|---|
| Triggers on push to `main` | `on.push.branches: [main]` |
| pytest fails the build | `backend-tests` job; `build-scan-push` `needs:` it |
| Frontend built | `frontend-build` job (`npm run build`, artifact `frontend-dist`) |
| Images for both services | `build-scan-push` matrix `[backend, frontend]` |
| Pushed to GHCR | `docker/login-action` with `GITHUB_TOKEN` (`packages: write`) |
| Tags = commit SHA, not `latest` | `docker/metadata-action` `type=sha,format=long`, `flavor: latest=false` |
| Deploy | `helm-smoke-test` (real `helm upgrade --install` on kind) and `promote` (GitOps to EKS via Argo CD) |

Images: `ghcr.io/anushkabhansalii/slotsync-backend:<sha>` and `ghcr.io/anushkabhansalii/slotsync-frontend:<sha>`.
Commit A → image A: any running pod can be traced back to the exact source commit (the SHA is also shown in the
UI sidebar and in the `/` API response).

Design choices:

* **Fail fast, publish late.** Nothing is pushed until tests, migrations, lint, Helm, Terraform and Trivy all pass.
* **Scan the exact bytes you ship.** The image is built once with `load: true`, scanned, then pushed from the same
  build cache.
* **Third-party actions are pinned to commit SHAs** (a moved tag cannot inject code — the 2025
  `tj-actions/changed-files` compromise worked exactly by re-pointing tags).
* **Least privilege.** Workflow default `contents: read`; only the jobs that need it get `packages: write`,
  `security-events: write` or `contents: write`.

## 8. DevSecOps

### Trivy container scanning

Each image is scanned three ways: a full report (artifact), SARIF uploaded to **GitHub → Security → Code scanning**,
and a **gate** that fails the pipeline on any `HIGH` or `CRITICAL` vulnerability that has a fix available
(`ignore-unfixed: true`, `exit-code: 1`).

**What Trivy found, and what we did.** The first local scan of the backend image failed the gate with 7 HIGH findings:

| Package | CVE | Problem | Fix |
|---|---|---|---|
| starlette 0.46.2 | CVE-2025-62727 | DoS: a crafted `Range` header makes `FileResponse` merge ranges in quadratic time, pinning a CPU | FastAPI 0.143 / Starlette 1.8 |
| starlette 0.46.2 | CVE-2026-48818, CVE-2026-54283 | SSRF via UNC paths; `request.form()` size limits ignored | same upgrade |
| urllib3 2.7.0, msgpack 1.1.2, setuptools 70.3 | CVE-2026-97687/97689, GHSA-6v7p-g79w-8964, CVE-2025-47273 | vendored *inside pip* in the virtualenv | pip/setuptools/wheel removed from the runtime image — the app never installs packages at runtime |

After the fix both images scan clean (0 fixable HIGH/CRITICAL). In plain words: Trivy reads the OS package
database (Debian / Alpine) and the Python package metadata inside the image, matches every version against
vulnerability feeds, and reports which ones have known CVEs. A clean result means *no known, fixable* HIGH or
CRITICAL CVE in what we ship today — not that the image is "secure" forever, which is why it runs on every build.

### Other controls

* **Gitleaks** scans the full Git history on every run; the build fails if any credential is committed.
* **No secrets in Git.** Database and Grafana passwords are generated inside the cluster by the scripts;
  Terraform uses the standard AWS credential chain; `*.tfvars`, state files and `.env` are git-ignored.
* **Containers:** non-root (UID 10001 / 101 / 70), `readOnlyRootFilesystem`, all Linux capabilities dropped,
  `allowPrivilegeEscalation: false`, seccomp `RuntimeDefault` — the `slotsync` namespace enforces Pod Security
  **restricted**, so a pod that breaks these rules is rejected.
* **Network:** a NetworkPolicy lets only pods labelled `slotsync/db-access=true` (the backend) reach PostgreSQL;
  enforcement is enabled in the VPC CNI by Terraform.
* **Supply chain:** images carry an SBOM and SLSA provenance attestation; base images are upgraded at build time.

## 9. Terraform: AWS VPC + EKS

```text
AWS ap-south-1
└── VPC 10.20.0.0/16
    ├── public  subnets 10.20.0.0/20, 10.20.16.0/20   (2 AZs)  → NLB, NAT gateway   tag kubernetes.io/role/elb
    ├── private subnets 10.20.64.0/18, 10.20.128.0/18 (2 AZs)  → nodes, pods        tag kubernetes.io/role/internal-elb
    ├── Internet gateway + 1 NAT gateway (single_nat_gateway = true to save cost)
    └── EKS "slotsync-demo" (Kubernetes 1.35, API logs to CloudWatch, secrets encrypted with KMS)
        ├── managed node group "general": 2× m7i-flex.large (2 vCPU / 8 GiB), AL2023, encrypted gp3 root volumes
        ├── add-ons: vpc-cni (NetworkPolicy on), coredns, kube-proxy, eks-pod-identity-agent,
        │            aws-ebs-csi-driver (IAM via Pod Identity — no static keys), metrics-server
        └── access entries: the creator is cluster-admin; public API endpoint limited to the operator's IP
```

Files: `versions.tf` (pins), `providers.tf`, `variables.tf` (validated inputs), `vpc.tf`, `eks.tf`, `outputs.tf`,
`terraform.tfvars.example`. Uses the community modules `terraform-aws-modules/vpc` (~> 6.7) and `/eks` (~> 21).

```bash
aws configure                                   # your own credentials; never committed
cd terraform
cp terraform.tfvars.example terraform.tfvars    # optional overrides (git-ignored)
terraform init
terraform plan -out tfplan
terraform apply tfplan                          # ~15 minutes, 61 resources
$(terraform output -raw configure_kubectl)      # aws eks update-kubeconfig ...
kubectl get nodes
```

State is local and git-ignored for this single-operator project; `versions.tf` shows the S3 backend (with native
lock file) a team would use.

## 10. Kubernetes + Helm

### Bootstrap the platform (once per cluster)

```bash
scripts/install-platform.sh eks
#   kube-prometheus-stack (Prometheus, Grafana, Alertmanager) in "monitoring"
#   ingress-nginx behind an internet-facing AWS NLB
#   gp3 StorageClass (default)
#   Argo CD in "argocd"
```

> **New AWS accounts:** if `kubectl -n ingress-nginx describe svc ingress-nginx-controller` shows
> `OperationNotPermitted: This AWS account currently does not support creating load balancers`, run the controller
> as ClusterIP and reach it through a port-forward (traffic still goes through the Ingress rules):
>
> ```bash
> helm upgrade ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx \
>   -f monitoring/ingress-nginx-values.yaml --set controller.service.type=ClusterIP
> kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80   # http://slotsync.localhost:8080
> ```

### Deploy with Helm directly

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install slotsync ./helm/slotsync -n slotsync \
  -f helm/slotsync/values-eks.yaml --set global.imageTag=<git-sha>
helm test slotsync -n slotsync
kubectl get pods,svc,ingress,hpa -n slotsync
helm list -n slotsync
```

### What the chart (`helm/slotsync`) creates

| Object | Notes |
|---|---|
| Deployment `slotsync-backend` | ≥2 replicas (HPA 2–8), startup/liveness on `/health`, readiness on `/ready`, rolling update with `maxUnavailable: 0`, spread across nodes |
| Deployment `slotsync-frontend` | 2 replicas, probes on `/healthz`, Nginx proxies `/api` to the backend Service |
| StatefulSet `slotsync-postgres` | PostgreSQL 16 with a 2 Gi gp3 PVC (`volumeClaimTemplates`) |
| Services | ClusterIP `slotsync-backend:8000`, `slotsync-frontend:80`, `slotsync-postgres:5432` |
| Ingress `slotsync` | class `nginx`; `/api`, `/docs`, `/openapi.json` → backend, `/` → frontend |
| HPA, PDB ×2, NetworkPolicy | autoscaling on CPU; at least one pod of each tier survives node drains; DB isolation |
| Secret / ConfigMap | random DB password kept across upgrades (`lookup`), or an existing Secret (GitOps) |
| ServiceMonitor, PrometheusRule, dashboard ConfigMap | scraping, alerts, Grafana dashboard |
| `helm test` pod | checks `/ready`, the frontend, and the frontend → backend proxy path |

In the live EKS demo the `slotsync` namespace is managed by Argo CD (which renders the chart itself), and the same
chart was additionally installed with `helm upgrade --install` as release `slotsync` in namespace `slotsync-helm`
to show the Helm CLI workflow (`helm list`, `helm test`).

Values files: `values.yaml` (defaults) · `values-dev.yaml` (minikube, local images, host `slotsync.local`) ·
`values-eks.yaml` (gp3, monitoring on) · `values-gitops.yaml` (image SHA, written by CI).

### Local Kubernetes rehearsal

```bash
MINIKUBE_PROFILE=slotsync scripts/install-platform.sh minikube
scripts/deploy-minikube.sh
```

## 11. GitOps with Argo CD

```bash
scripts/bootstrap-gitops.sh
#   1. k8s/namespace.yaml (Pod Security restricted)
#   2. Secret slotsync/slotsync-db with a random password (generated in-cluster)
#   3. gitops/argocd-application.yaml
kubectl -n argocd port-forward svc/argocd-server 8080:80     # http://localhost:8080
```

The Application tracks `helm/slotsync` on `main` with `values.yaml + values-eks.yaml + values-gitops.yaml`,
automated sync with **prune** (delete what was removed from Git) and **self-heal** (revert manual `kubectl edit`
drift), retries with back-off, and a custom health check so a brand-new HPA shows *Progressing* rather than
*Degraded*.

The loop: `git push` → green pipeline → bot commit `chore(gitops): promote slotsync <sha>` → Argo CD polls Git
(60 s) → rolling update to the new SHA. Rolling back is `git revert` of the promote commit.

## 12. Observability: Prometheus + Grafana

* The backend exposes `/metrics` via `prometheus-fastapi-instrumentator` (request count by method/handler/status,
  latency histograms) plus business counters:
  `slotsync_appointments_created_total{service}`, `slotsync_appointment_status_changes_total{status}`,
  `slotsync_booking_conflicts_total`.
* `kube-prometheus-stack` ([values](monitoring/kube-prometheus-stack-values.yaml)) installs the Prometheus
  Operator, Prometheus, Alertmanager, Grafana, node-exporter and kube-state-metrics. Control-plane scrapers that
  EKS doesn't expose are disabled so the Targets page has no permanent DOWN entries.
* The chart's **ServiceMonitor** makes Prometheus scrape every backend pod every 15 s.
* **PrometheusRule** alerts: backend down (2 m), 5xx ratio > 5 % (5 m), p95 latency > 500 ms (10 m).
* **Grafana dashboard "SlotSync / API overview"** (19 panels, generated by
  [`monitoring/build_dashboard.py`](monitoring/build_dashboard.py) and shipped by the chart): request rate, p95
  latency, 5xx ratio, pods up, bookings in 24 h; requests by endpoint; p50/p95/p99; responses by status code;
  bookings by service; status changes; rejected double-bookings; CPU / memory per pod; HPA current / desired / max.

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090   # Status → Targets
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80         # home = SlotSync dashboard
```

Grafana and Argo CD allow **read-only anonymous viewing** because they are only reachable through
`kubectl port-forward`; changing anything still needs the admin passwords stored in Kubernetes Secrets.

## 13. Autoscaling (HPA)

The backend HPA targets 60 % CPU of its 100 m request, scaling 2 → 8 pods (scale up by 2 pods / 30 s, scale down
by 1 pod / 60 s after a 2-minute window). Metrics come from the `metrics-server` EKS add-on.

```bash
kubectl apply -f scripts/load-generator.yaml        # 4 busybox pods hammering the API
kubectl get hpa -n slotsync -w                      # cpu: 222%/60% → REPLICAS 2 → 6 → 8
kubectl delete -f scripts/load-generator.yaml
```

## 14. Troubleshooting labs

[`troubleshooting/`](troubleshooting/README.md) has three broken manifests in an isolated namespace:
`ImagePullBackOff` (bad tag), a Service with no endpoints (label/selector mismatch) and a pod that is `Running`
but never `Ready` (database unreachable, `/ready` → 503), each with the commands that reveal the cause and the fix.

## 15. Tear-down and cost

```bash
scripts/teardown-eks.sh
```

The order matters: the script deletes the Argo CD app, the workloads, ingress-nginx (which owns the **NLB**) and
the PVCs (which own **EBS volumes**) *before* `terraform destroy`. Otherwise those AWS resources keep ENIs in the VPC
and the destroy hangs. While running, the demo costs roughly **US$0.35/hour** (EKS control plane $0.10, 2× m7i-flex.large,
NAT gateway, NLB) — a few dollars for a full demo session.

## 16. Known issues and limitations

* **PostgreSQL runs in the cluster** (StatefulSet, single replica) to keep the demo self-contained. Production
  should use Amazon RDS (Multi-AZ, automated backups, PITR) — the chart supports `postgres.enabled=false` +
  `database.externalUrl`.
* **No public load balancer in the demo.** The EKS demo ran on a brand-new AWS account that AWS does not yet allow
  to create load balancers, so the app was reached through `kubectl port-forward` to ingress-nginx instead of the NLB
  hostname. The NLB configuration is in `monitoring/ingress-nginx-values.yaml` and works on an established account.
* **No TLS / DNS.** The app is served over plain HTTP on the NLB hostname. Production would add a Route 53 record,
  cert-manager or ACM, and HTTPS redirects.
* **No authentication** on the booking UI/API; it assumes a trusted front-desk network. Adding OIDC (e.g. Cognito)
  is the next step.
* **Single NAT gateway** (one AZ) to save cost; set `single_nat_gateway = false` for HA egress.
* **Local Terraform state.** Fine for one operator; teams should enable the S3 backend shown in `versions.tf`.
* **Studio timezone is global** (`STUDIO_TZ`), so a multi-branch, multi-timezone business would need a per-location
  setting.
* Metrics and HPA react to CPU only; request-rate–based autoscaling (KEDA / Prometheus adapter) would track load
  more directly.

---

*The demo video's narration is synthesized (macOS text-to-speech) over real recordings of this project running;
[`demo/VIDEO-SCRIPT.md`](demo/VIDEO-SCRIPT.md) has the script and shot list for re-recording it live.*
