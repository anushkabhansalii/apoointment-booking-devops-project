#!/usr/bin/env bash
# Hand the slotsync namespace over to Argo CD:
#   namespace (Pod Security "restricted") -> database Secret -> Argo CD Application
# The database password is generated here, in the cluster, and never committed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NS=slotsync

kubectl apply -f "$ROOT/k8s/namespace.yaml"

if ! kubectl -n "$NS" get secret slotsync-db >/dev/null 2>&1; then
  PASSWORD="$(openssl rand -hex 16)"
  kubectl -n "$NS" create secret generic slotsync-db \
    --from-literal=POSTGRES_PASSWORD="$PASSWORD" \
    --from-literal=DATABASE_URL="postgresql+psycopg://slotsync:${PASSWORD}@slotsync-postgres:5432/slotsync"
  echo "Created secret $NS/slotsync-db"
fi

kubectl apply -f "$ROOT/gitops/argocd-application.yaml"
echo "Argo CD application created. Watch it with:"
echo "  kubectl -n argocd get application slotsync -w"
