# Evidence — mapped to the grading rubric

Every screenshot below was captured from this project running for real: locally with Docker Compose, in GitHub
Actions, and on the AWS EKS cluster built by `terraform/` in **ap-south-1** (account IDs are masked).
Terminal screenshots are rendered from the exact command output.

Pipeline run used for the live demo: [Actions run #5](https://github.com/anushkabhansalii/apoointment-booking-devops-project/actions/runs/38901245916)
(push `eb90e7c` → all jobs green → bot commit `be5839a` → Argo CD rolled it out on EKS).

---

## M1 — Application (Frontend + Backend + Database)

| Criterion | Evidence |
|---|---|
| FastAPI starts, `/health` responds | [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) (`GET /health 200`), [m8-helm-list-test.png](screenshots/m8-helm-list-test.png) |
| ≥4 REST endpoints (GET/POST/PUT/DELETE) | [m1-swagger.png](screenshots/m1-swagger.png) · `backend/app/routers/appointments.py` |
| PostgreSQL + Alembic | `backend/alembic/versions/0001_create_providers_and_appointments.py`; migration logs in [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) |
| React frontend making API calls | [m1-dashboard.png](screenshots/m1-dashboard.png), [m1-schedule.png](screenshots/m1-schedule.png), [m1-appointments.png](screenshots/m1-appointments.png), [m1-double-booking-409.png](screenshots/m1-double-booking-409.png) |
| Responsive UI | [m1-mobile.png](screenshots/m1-mobile.png) (390 px phone layout) |

## M2 — Testing

| Criterion | Evidence |
|---|---|
| `pytest -v` passes | [m2-pytest-passing.png](screenshots/m2-pytest-passing.png) (32 passed; 33 after the `/api/version` feature) |
| ≥5 tests over ≥3 endpoints | `backend/tests/` — CRUD, status, stats, providers, services, health, ready, metrics |
| Test DB, not production | `backend/tests/conftest.py` (in-memory SQLite + `get_db` override) |
| `pytest.ini` / `conftest.py` | `backend/pytest.ini`, `backend/tests/conftest.py` |

## M3 — Git and GitHub

| Criterion | Evidence |
|---|---|
| Public repo | https://github.com/anushkabhansalii/apoointment-booking-devops-project |
| Meaningful commits (≥10) | [m3-commit-history.png](screenshots/m3-commit-history.png) · `git log` (40+ commits) |
| `.gitignore` | `.gitignore` — `.env`, `__pycache__`, `node_modules`, `.venv`, Terraform state, `*.tfvars` |

## M4 — Docker

| Criterion | Evidence |
|---|---|
| Backend Dockerfile builds | `backend/Dockerfile`; build steps in [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) |
| Frontend multi-stage (Node → Nginx) | `frontend/Dockerfile` (`node:20-alpine` → `nginx-unprivileged`) |
| Non-root | backend `USER 10001`, frontend UID 101; enforced in K8s by Pod Security *restricted* |
| `docker compose up --build` starts 3 services | [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) |
| App at `localhost:3000` | [m1-dashboard.png](screenshots/m1-dashboard.png) |

## M5 — CI/CD

| Criterion | Evidence |
|---|---|
| Workflow file, triggers on push to `main` | `.github/workflows/ci-cd.yml` |
| pytest job fails the build on failure | `backend-tests` job (images `needs:` it) |
| Frontend built | `frontend-build` job |
| Images for both, pushed to GHCR | [m5-actions-run.png](screenshots/m5-actions-run.png) |
| SHA tags, not `latest` | [m5-ghcr-backend.png](screenshots/m5-ghcr-backend.png), [m5-ghcr-frontend.png](screenshots/m5-ghcr-frontend.png) |

## M6 — DevSecOps (Trivy)

| Criterion | Evidence |
|---|---|
| Trivy on both images in CI | [m6-trivy-ci-clean.png](screenshots/m6-trivy-ci-clean.png) |
| Fails on HIGH/CRITICAL | `exit-code: "1"`, `severity: HIGH,CRITICAL`; the gate failing on the pre-fix image: [m6-trivy-before-fix-7-high.png](screenshots/m6-trivy-before-fix-7-high.png) |
| Explanation | README §8 — *Trivy found 7 HIGH CVEs (e.g. CVE-2025-62727, a Starlette Range-header DoS); upgrading FastAPI/Starlette and removing pip from the runtime image fixed them. Trivy compares OS and Python package versions inside the image against vulnerability feeds; a clean result means no known, fixable HIGH/CRITICAL CVE in what we ship today.* |

## M7 — Terraform (AWS)

| Criterion | Evidence |
|---|---|
| Valid HCL, `init` | `terraform/*.tf`; `terraform validate` runs in CI |
| `plan` (non-empty, no errors) | [m7-terraform-plan.png](screenshots/m7-terraform-plan.png) — 61 to add |
| VPC with 2 public subnets; EKS + node group | [m7-terraform-apply.png](screenshots/m7-terraform-apply.png) (outputs, `aws eks describe-cluster` ACTIVE, 2 nodes in 2 AZs) |
| AWS Console | [m7-aws-vpc-console.png](screenshots/m7-aws-vpc-console.png), [m7-aws-eks-console.png](screenshots/m7-aws-eks-console.png) |
| `destroy` | [m7-terraform-destroy.png](screenshots/m7-terraform-destroy.png) |
| `terraform.tfvars.example`, no credentials | `terraform/terraform.tfvars.example`; Gitleaks gate in CI |

## M8 — Kubernetes + Helm

| Criterion | Evidence |
|---|---|
| `k8s/namespace.yaml` | `k8s/namespace.yaml` (applied: [m8-kubectl-pods-svc.png](screenshots/m8-kubectl-pods-svc.png)) |
| Helm chart (`Chart.yaml`, `values.yaml`, templates) | `helm/slotsync/` |
| `helm upgrade --install` works | [m8-helm-list-test.png](screenshots/m8-helm-list-test.png) (release `slotsync` in `slotsync-helm`, `helm test` Succeeded); also the `Deploy · Helm on kind` CI job |
| ≥2 replicas each, ClusterIP Services, Ingress `/` + `/api` | [m8-kubectl-pods-svc.png](screenshots/m8-kubectl-pods-svc.png) · `helm/slotsync/templates/ingress.yaml` |
| All pods Running | [m8-kubectl-pods-svc.png](screenshots/m8-kubectl-pods-svc.png) |
| App through the Ingress | [m8-app-via-ingress.png](screenshots/m8-app-via-ingress.png), [m8-swagger-via-ingress.png](screenshots/m8-swagger-via-ingress.png) |
| GitOps (Argo CD) | [m8-argocd-app.png](screenshots/m8-argocd-app.png), [m8-gitops-rollout.png](screenshots/m8-gitops-rollout.png) |
| HPA | [m8-hpa-scaling.png](screenshots/m8-hpa-scaling.png) — 2 → 8 pods under load |

The `slotsync` namespace is owned by Argo CD, which renders the chart itself (so it is not a Helm *release*).
To show the Helm CLI workflow on the same cluster, the identical chart was also installed directly as release
`slotsync` in namespace `slotsync-helm`.

**Load balancer note:** ingress-nginx is configured for an internet-facing AWS NLB
(`monitoring/ingress-nginx-values.yaml`), but the brand-new AWS account used for the demo returned
`OperationNotPermitted: This AWS account currently does not support creating load balancers`. The controller was
therefore run as a ClusterIP Service and reached with `kubectl port-forward`; requests still pass through the real
Ingress rules (`http://slotsync.localhost:8080` → ingress-nginx → `/` frontend, `/api` backend).

## M9 — Observability

| Criterion | Evidence |
|---|---|
| `/metrics` in Prometheus format | [m9-metrics-endpoint.png](screenshots/m9-metrics-endpoint.png) |
| Prometheus scraping the app | [m9-prometheus-targets.png](screenshots/m9-prometheus-targets.png), [m9-prometheus-all-targets.png](screenshots/m9-prometheus-all-targets.png) |
| Grafana accessible + live panel | [m9-grafana-dashboard.png](screenshots/m9-grafana-dashboard.png) |
| Values files | `monitoring/kube-prometheus-stack-values.yaml` |

## M10 — Presentation + documentation

| Item | Where |
|---|---|
| README | [`README.md`](../README.md) |
| Video | [`demo/presentation.mp4`](../demo/presentation.mp4) |
| Slides | [`demo/SlotSync-DevOps-Capstone.pptx`](../demo/SlotSync-DevOps-Capstone.pptx) and [`demo/SlotSync-DevOps-Capstone.pdf`](../demo/SlotSync-DevOps-Capstone.pdf) |
