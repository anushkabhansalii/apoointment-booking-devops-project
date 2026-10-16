#!/usr/bin/env bash
# Local rehearsal of the Kubernetes deployment on minikube with locally built images.
#   scripts/deploy-minikube.sh            then add "$(minikube ip) slotsync.local" to /etc/hosts
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

minikube status >/dev/null 2>&1 || minikube start --cpus 4 --memory 8192 --addons ingress,metrics-server

echo "==> Building images inside minikube's Docker daemon"
eval "$(minikube docker-env)"
docker build -t slotsync-backend:local "$ROOT/backend"
docker build -t slotsync-frontend:local "$ROOT/frontend"

kubectl apply -f "$ROOT/k8s/namespace.yaml"
EXTRA=()
kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1 || \
  EXTRA=(--set serviceMonitor.enabled=false --set prometheusRule.enabled=false)

helm upgrade --install slotsync "$ROOT/helm/slotsync" -n slotsync \
  -f "$ROOT/helm/slotsync/values-dev.yaml" "${EXTRA[@]}" --wait --timeout 6m
helm test slotsync -n slotsync --logs
kubectl get pods,svc,ingress,hpa -n slotsync
