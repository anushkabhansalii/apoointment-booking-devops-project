# Presentation video — script and shot list

`demo/presentation.mp4` follows the order required by `SUBMISSION.md`: slides first, then the live walkthrough.
Every screen in the video is a real capture of this project (the running app, the GitHub Actions run, the EKS
cluster, Argo CD, Prometheus and Grafana). This script is also a ready guide for re-recording it in your own voice.

| # | Segment | On screen | Narration (summary) |
|---|---------|-----------|---------------------|
| 1 | Title | Slide 1 | Who I am, what SlotSync is |
| 2 | What and why | Slide 2 | The studio's problem; app + delivery platform; ground rules |
| 3 | Tech stack | Slide 3 | One line per layer |
| 4 | Architecture | Slide 4 | GitHub side (gates → images → promote) and AWS side (VPC, EKS, Argo CD, ingress, Prometheus/Grafana) |
| 5 | Pipeline + security | Slides 7–8 | Five stages, SHA tags, Trivy caught 7 HIGH CVEs and how they were fixed |
| 6 | Infra + K8s + GitOps + observability | Slides 9–12 | Terraform VPC/EKS, Helm chart, Argo CD loop, metrics and dashboards |
| 7 | **Live: the app** | Browser on the EKS load balancer | Dashboard, schedule, booking, double-booking rejected (409) |
| 8 | **Live: codebase** | Repo tree + key files | backend/app, tests, Dockerfiles, helm/slotsync, terraform, workflow |
| 9 | **Live: CI/CD** | Commit + push → GitHub Actions run | Every job going green, then the bot's promote commit |
| 10 | **Live: Terraform** | `terraform plan` / apply output, AWS Console VPC + EKS | 61 resources, two public + two private subnets, node group |
| 11 | **Live: Argo CD** | Argo CD UI | App Synced/Healthy at the new SHA, resource tree |
| 12 | **Live: Kubernetes** | `kubectl get pods,svc,ingress,hpa` and `helm list` | Everything Running, 2+ replicas, ingress address |
| 13 | **Live: Prometheus** | Targets page | slotsync-backend targets UP |
| 14 | **Live: Grafana** | SlotSync / API overview | Live request rate, latency, errors, bookings, HPA replicas |
| 15 | Learnings + close | Slides 13–14 | What I learned, next steps |

## Re-recording it yourself

1. Bring the stack up (`terraform apply`, `scripts/install-platform.sh eks`, `scripts/bootstrap-gitops.sh`).
2. Open the slides (`demo/SlotSync-DevOps-Capstone.pptx`) and press QuickTime → File → New Screen Recording.
3. Talk through slides 1–4, 7–12, then switch to the browser and terminal for segments 7–14 using the commands in
   the README, and finish on slides 13–14.
4. Run `scripts/teardown-eks.sh` afterwards.
