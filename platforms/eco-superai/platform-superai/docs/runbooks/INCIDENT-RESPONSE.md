# SuperAI Platform — Incident Response Runbook

> Operational procedures for common incidents and failure scenarios.

---

## 1. API Service Unresponsive

### Symptoms
- Health check endpoint returns 5xx or times out
- Grafana alerts: `APIHighLatency` or `APIHighErrorRate`
- Users report connection failures

### Diagnosis
```bash
# Check pod status
kubectl get pods -n superai -l app=superai-api

# Check pod logs
kubectl logs -n superai -l app=superai-api --tail=200

# Check resource usage
kubectl top pods -n superai

# Check service endpoints
kubectl get endpoints -n superai superai-service
```

### Resolution

**Step 1:** Check if pods are in CrashLoopBackOff:
```bash
kubectl describe pod -n superai <pod-name>
```
If OOMKilled → increase memory limits in `helm/values.yaml` and redeploy.

**Step 2:** Check database connectivity:
```bash
kubectl exec -n superai <pod-name> -- python -c "
from src.infrastructure.config.settings import Settings
s = Settings()
print(s.DATABASE_URL)
"
```

**Step 3:** Rolling restart:
```bash
kubectl rollout restart deployment/superai-api -n superai
kubectl rollout status deployment/superai-api -n superai
```

---

## 2. Database Connection Exhaustion

### Symptoms
- API returns 503 errors with "connection pool exhausted"
- Prometheus metric: `db_pool_active_connections` at max
- Slow query responses

### Diagnosis
```bash
# Check active connections
kubectl exec -n superai <postgres-pod> -- psql -U superai -c "
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
"

# Check long-running queries
kubectl exec -n superai <postgres-pod> -- psql -U superai -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC
LIMIT 10;
"
```

### Resolution

**Step 1:** Kill long-running queries:
```bash
kubectl exec -n superai <postgres-pod> -- psql -U superai -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE duration > interval '5 minutes' AND state = 'active';
"
```

**Step 2:** Increase pool size (temporary):
Update `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW` in environment config.

**Step 3:** Investigate root cause — check for missing indexes, N+1 queries, or connection leaks.

---

## 3. Redis Cache Failure

### Symptoms
- Increased API latency (cache miss fallback to DB)
- Prometheus: `redis_connection_errors` increasing
- Grafana: cache hit ratio drops below 50%

### Diagnosis
```bash
# Check Redis pod
kubectl get pods -n superai -l app=redis

# Test Redis connectivity
kubectl exec -n superai <redis-pod> -- redis-cli ping

# Check Redis memory
kubectl exec -n superai <redis-pod> -- redis-cli info memory
```

### Resolution

**Step 1:** If Redis is down, restart:
```bash
kubectl rollout restart statefulset/redis -n superai
```

**Step 2:** If memory full, flush non-critical caches:
```bash
kubectl exec -n superai <redis-pod> -- redis-cli FLUSHDB
```

**Step 3:** The application is designed to degrade gracefully — all cache misses fall through to the database. Monitor DB load during Redis recovery.

---

## 4. Quantum Job Stuck

### Symptoms
- Quantum job status remains "submitted" or "running" beyond expected duration
- No result returned to user

### Diagnosis
```bash
# Check quantum worker logs
kubectl logs -n superai -l component=quantum-worker --tail=100

# Check job queue
kubectl exec -n superai <app-pod> -- python -c "
from src.quantum.runtime.executor import QuantumExecutor
executor = QuantumExecutor()
print(executor.list_pending_jobs())
"
```

### Resolution

**Step 1:** If backend is unresponsive, switch to simulator:
```bash
# Update QUANTUM_BACKEND to aer_simulator
kubectl set env deployment/superai-api -n superai QUANTUM_BACKEND=aer_simulator
```

**Step 2:** Retry stuck jobs:
```bash
kubectl exec -n superai <app-pod> -- python -m tools.health_check --retry-stuck-jobs
```

**Step 3:** If IBM Quantum backend issue, check [IBM Quantum Status](https://quantum-computing.ibm.com/services/resources).

---

## 5. High Memory Usage / OOM

### Symptoms
- Pods restarting with OOMKilled status
- Scientific computing or ML training jobs consuming excessive memory

### Diagnosis
```bash
# Check pod resource usage
kubectl top pods -n superai --sort-by=memory

# Check OOM events
kubectl get events -n superai --field-selector reason=OOMKilling
```

### Resolution

**Step 1:** Identify the offending workload from logs.

**Step 2:** For scientific/ML jobs, enforce memory limits:
```python
# In the ML trainer, set max dataset size
trainer = MLTrainer(max_memory_mb=2048)
```

**Step 3:** Scale vertically (increase pod memory limits) or horizontally (add replicas with load balancing).

---

## 6. Escalation Matrix

| Severity | Response Time | Escalation |
|----------|--------------|------------|
| P0 — Service Down | 15 min | On-call → Team Lead → VP Engineering |
| P1 — Degraded | 30 min | On-call → Team Lead |
| P2 — Partial Impact | 2 hours | On-call |
| P3 — Minor Issue | Next business day | Ticket queue |

---

## 7. Post-Incident Review

After every P0/P1 incident:

1. **Timeline** — Document exact sequence of events
2. **Root Cause** — Identify the underlying cause (not just symptoms)
3. **Impact** — Quantify affected users, duration, data loss
4. **Action Items** — Concrete preventive measures with owners and deadlines
5. **Lessons Learned** — Share with the broader team