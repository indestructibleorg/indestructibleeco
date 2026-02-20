# Step 17 — Helm templates + HPA + PDB

## Tasks
- [x] Audit existing helm/templates/ (deployment, service, hpa, pdb, ingress, _helpers.tpl)
- [x] Create helm/templates/configmap.yaml (ECO_* env vars)
- [x] Create helm/templates/secrets.yaml (redis-url, supabase-url, jwt, hf-token)
- [x] Create helm/templates/serviceaccount.yaml (GKE workload identity)
- [x] Create helm/templates/networkpolicy.yaml (namespace isolation, DNS, HTTPS egress)
- [x] Create helm/templates/servicemonitor.yaml (Prometheus eco_* metrics)
- [x] Create helm/templates/NOTES.txt (post-install instructions)
- [x] Update helm/values.yaml (networkPolicy.enabled)
- [x] Update CI structure checks for 5 new template files
- [x] All 255 tests pass
- [x] CI Validator 0 errors, 0 warnings
- [x] Git commit + push
- [x] CI 5-gate ALL GREEN
