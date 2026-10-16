#!/usr/bin/env bash
# Tear everything down in the order AWS needs:
#   1. delete Kubernetes objects that own AWS resources (NLB, EBS volumes)
#   2. terraform destroy (VPC, NAT gateway, EKS, IAM)
# Skipping step 1 leaves an NLB/ENIs in the VPC and terraform destroy hangs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Retry throttled or dropped AWS API calls instead of failing the destroy.
export AWS_RETRY_MODE=adaptive AWS_MAX_ATTEMPTS=10

if kubectl cluster-info >/dev/null 2>&1; then
  echo "==> Removing Argo CD application and workloads"
  kubectl -n argocd delete application slotsync --ignore-not-found --wait=true --timeout=5m || true
  kubectl delete namespace slotsync --ignore-not-found --wait=true --timeout=5m || true
  helm uninstall slotsync -n slotsync-helm --wait 2>/dev/null || true
  kubectl delete namespace slotsync-helm slotsync-lab --ignore-not-found --wait=true --timeout=5m || true
  echo "==> Removing ingress-nginx (deletes the AWS load balancer)"
  helm uninstall ingress-nginx -n ingress-nginx --wait 2>/dev/null || true
  echo "==> Removing monitoring and Argo CD (and their EBS volumes)"
  helm uninstall kube-prometheus-stack -n monitoring --wait 2>/dev/null || true
  helm uninstall argocd -n argocd --wait 2>/dev/null || true
  kubectl delete pvc --all -A --wait=true --timeout=5m || true
  echo "==> Waiting 60s for AWS to release load balancer ENIs"
  sleep 60
fi

cd "$ROOT/terraform"
terraform destroy -auto-approve -parallelism=3
