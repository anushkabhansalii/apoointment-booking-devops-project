# Troubleshooting labs

Three deliberately broken manifests, each teaching one Kubernetes failure mode.
They deploy into their own `slotsync-lab` namespace so they never touch the real app.

| Lab | Symptom | Root cause | Commands that reveal it |
|-----|---------|------------|-------------------------|
| `broken-image.yaml` | `ImagePullBackOff` | image tag does not exist in GHCR | `kubectl describe pod` → Events |
| `broken-service.yaml` | Service reachable by name but requests time out | Service selector matches no pod labels → no endpoints | `kubectl get endpoints`, `kubectl get pods --show-labels` |
| `broken-readiness.yaml` | Pod `Running` but `0/1` ready | `/ready` returns 503 because the database is unreachable | `kubectl describe pod` (probe events), `kubectl logs` |

Clean up with `kubectl delete namespace slotsync-lab`.

## Debugging checklist

```text
kubectl get pods -n <ns>                         what state is it in?
kubectl describe pod <pod> -n <ns>               Events: scheduling, pulling, probes
kubectl logs <pod> -n <ns> [--previous]          application output (previous = before the crash)
kubectl get events -n <ns> --sort-by=.lastTimestamp
kubectl get svc,endpoints -n <ns>                does the Service select any pods?
kubectl get pods -n <ns> --show-labels           do labels match selectors?
kubectl exec -it <pod> -n <ns> -- sh             test from inside the network
```
