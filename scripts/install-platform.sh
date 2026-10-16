#!/usr/bin/env bash
# Install the cluster add-ons SlotSync relies on:
#   ingress-nginx (AWS NLB) · kube-prometheus-stack (Prometheus + Grafana) · Argo CD
# Usage: scripts/install-platform.sh [eks|minikube]     (default: eks)
set -euo pipefail
TARGET="${1:-eks}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Helm repositories"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null
helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update >/dev/null

echo "==> Monitoring: kube-prometheus-stack"
kubectl apply -f "$ROOT/k8s/monitoring-namespace.yaml"
if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  # Random admin password, generated in-cluster and never committed.
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin \
    --from-literal=admin-password="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)"
fi
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring -f "$ROOT/monitoring/kube-prometheus-stack-values.yaml" --wait --timeout 10m

echo "==> Ingress controller"
if [ "$TARGET" = "minikube" ]; then
  minikube -p "${MINIKUBE_PROFILE:-slotsync}" addons enable ingress
  minikube -p "${MINIKUBE_PROFILE:-slotsync}" addons enable metrics-server
else
  helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
    -n ingress-nginx --create-namespace -f "$ROOT/monitoring/ingress-nginx-values.yaml" --wait --timeout 10m
  kubectl apply -f "$ROOT/k8s/storageclass-gp3.yaml"
  # Only one default StorageClass: demote the legacy gp2 class if present.
  kubectl annotate storageclass gp2 storageclass.kubernetes.io/is-default-class=false --overwrite 2>/dev/null || true
fi

echo "==> Argo CD"
helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace \
  -f "$ROOT/gitops/argocd-values.yaml" --wait --timeout 10m

cat <<MSG

Platform ready.
  Grafana  : kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
             password: kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d
  Prometheus: kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
  Argo CD  : kubectl -n argocd port-forward svc/argocd-server 8080:80
             password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
MSG
