#!/usr/bin/env bash
# Local rehearsal of the Kubernetes deployment on minikube with locally built images.
#   scripts/deploy-minikube.sh     then: minikube -p slotsync tunnel, and add "127.0.0.1 slotsync.local" to /etc/hosts
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${MINIKUBE_PROFILE:-slotsync}"

minikube -p "$PROFILE" status >/dev/null 2>&1 || \
  minikube start -p "$PROFILE" --driver=docker --container-runtime=docker --cpus 4 --memory 5500 --addons ingress,metrics-server

echo "==> Building images inside minikube's Docker daemon"
eval "$(minikube -p "$PROFILE" docker-env)"
docker build -t slotsync-backend:local "$ROOT/backend"
docker build -t slotsync-frontend:local "$ROOT/frontend"

kubectl apply -f "$ROOT/k8s/namespace.yaml"
EXTRA=()
kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1 || \
  EXTRA=(--set serviceMonitor.enabled=false --set prometheusRule.enabled=false)

helm upgrade --install slotsync "$ROOT/helm/slotsync" -n slotsync \
  -f "$ROOT/helm/slotsync/values-dev.yaml" ${EXTRA[@]+"${EXTRA[@]}"} --wait --timeout 6m
helm test slotsync -n slotsync --logs
kubectl get pods,svc,ingress,hpa -n slotsync
