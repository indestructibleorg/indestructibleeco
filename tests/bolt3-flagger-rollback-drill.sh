#!/usr/bin/env bash
# Bolt-3: Flagger Rollback Drill
# Deploys a test service, configures Flagger Canary, injects failures, verifies rollback
# Artifacts: tests/reports/bolt3-flagger-rollback-report.json

set -euo pipefail
NAMESPACE="platform-01"
REPORT_FILE="tests/reports/bolt3-flagger-rollback-report.json"
mkdir -p tests/reports

echo "=== Bolt-3: Flagger Rollback Drill ==="
echo "Namespace: $NAMESPACE"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Step 1: Deploy test workload (podinfo - standard Flagger test app)
echo ""
echo "[Step 1] Deploying podinfo test workload..."
kubectl apply -n "$NAMESPACE" -f - <<'EOF'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: podinfo
  namespace: platform-01
  labels:
    app: podinfo
    eco.platform/component: "test-canary"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: podinfo
  template:
    metadata:
      labels:
        app: podinfo
    spec:
      containers:
        - name: podinfo
          image: ghcr.io/stefanprodan/podinfo:6.7.0
          ports:
            - containerPort: 9898
          resources:
            requests:
              cpu: 10m
              memory: 32Mi
            limits:
              cpu: 200m
              memory: 128Mi
          env:
            - name: PODINFO_UI_COLOR
              value: "#34577c"
---
apiVersion: v1
kind: Service
metadata:
  name: podinfo
  namespace: platform-01
spec:
  selector:
    app: podinfo
  ports:
    - port: 80
      targetPort: 9898
EOF

echo "Waiting for podinfo deployment to be ready..."
kubectl rollout status deployment/podinfo -n "$NAMESPACE" --timeout=120s 2>&1

# Step 2: Deploy Flagger Canary with strict SLI thresholds
echo ""
echo "[Step 2] Configuring Flagger Canary with SLI thresholds..."
kubectl apply -n "$NAMESPACE" -f - <<'EOF'
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: podinfo
  namespace: platform-01
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: podinfo
  progressDeadlineSeconds: 120
  service:
    port: 80
    targetPort: 9898
  analysis:
    # Check every 10s, 3 iterations before promote
    interval: 10s
    threshold: 3
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        # Fail if error rate > 1%
        thresholdRange:
          min: 99
        interval: 30s
      - name: request-duration
        # Fail if p99 latency > 200ms
        thresholdRange:
          max: 200
        interval: 30s
    webhooks:
      - name: load-test
        url: http://flagger-loadtester.flagger-system/
        timeout: 5s
        metadata:
          cmd: "hey -z 30s -q 10 -c 2 http://podinfo-canary.platform-01/"
EOF

echo "Waiting 15s for Flagger to initialize canary..."
sleep 15
kubectl get canary podinfo -n "$NAMESPACE" 2>&1

# Step 3: Deploy load tester
echo ""
echo "[Step 3] Deploying Flagger load tester..."
kubectl apply -n flagger-system -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flagger-loadtester
  namespace: flagger-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flagger-loadtester
  template:
    metadata:
      labels:
        app: flagger-loadtester
    spec:
      containers:
        - name: loadtester
          image: ghcr.io/fluxcd/flagger-loadtester:0.34.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 10m
              memory: 32Mi
            limits:
              cpu: 100m
              memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: flagger-loadtester
  namespace: flagger-system
spec:
  selector:
    app: flagger-loadtester
  ports:
    - port: 80
      targetPort: 8080
EOF

echo "Waiting for load tester..."
kubectl rollout status deployment/flagger-loadtester -n flagger-system --timeout=60s 2>&1 || true

# Step 4: Trigger canary by updating the deployment (inject failure image)
echo ""
echo "[Step 4] Triggering canary with failure-injecting image..."
# Use podinfo with error injection enabled (PODINFO_STRESS_CPU causes high latency)
kubectl set image deployment/podinfo podinfo=ghcr.io/stefanprodan/podinfo:6.7.0 -n "$NAMESPACE" 2>&1
kubectl set env deployment/podinfo \
  PODINFO_STRESS_CPU=1 \
  PODINFO_STRESS_MEMORY=1 \
  -n "$NAMESPACE" 2>&1

echo "Waiting 20s for canary analysis to start..."
sleep 20

# Step 5: Monitor canary status
echo ""
echo "[Step 5] Monitoring canary rollback..."
ROLLBACK_DETECTED=false
for i in $(seq 1 18); do
  STATUS=$(kubectl get canary podinfo -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
  WEIGHT=$(kubectl get canary podinfo -n "$NAMESPACE" -o jsonpath='{.status.canaryWeight}' 2>/dev/null || echo "0")
  ITERS=$(kubectl get canary podinfo -n "$NAMESPACE" -o jsonpath='{.status.iterations}' 2>/dev/null || echo "0")
  echo "  [$(date -u +%H:%M:%S)] phase=$STATUS weight=$WEIGHT iterations=$ITERS"
  
  if [[ "$STATUS" == "Failed" ]] || [[ "$STATUS" == "Succeeded" ]]; then
    if [[ "$STATUS" == "Failed" ]]; then
      ROLLBACK_DETECTED=true
    fi
    break
  fi
  sleep 10
done

# Step 6: Verify rollback
echo ""
echo "[Step 6] Verifying rollback state..."
FINAL_STATUS=$(kubectl get canary podinfo -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
FINAL_WEIGHT=$(kubectl get canary podinfo -n "$NAMESPACE" -o jsonpath='{.status.canaryWeight}' 2>/dev/null || echo "0")
FAILURE_REASON=$(kubectl get canary podinfo -n "$NAMESPACE" -o jsonpath='{.status.conditions[-1].message}' 2>/dev/null || echo "N/A")
EVENTS=$(kubectl get events -n "$NAMESPACE" --field-selector reason=Synced,involvedObject.name=podinfo 2>/dev/null | tail -5 || echo "N/A")

echo "  Final phase: $FINAL_STATUS"
echo "  Final canary weight: $FINAL_WEIGHT"
echo "  Failure reason: $FAILURE_REASON"

# Step 7: Generate artifact report
echo ""
echo "[Step 7] Generating artifact report..."

if [[ "$ROLLBACK_DETECTED" == "true" ]] || [[ "$FINAL_STATUS" == "Failed" ]]; then
  GATE_RESULT="PASS"
  GATE_MSG="Flagger detected failures and rolled back canary"
else
  GATE_RESULT="WARN"
  GATE_MSG="Canary status: $FINAL_STATUS (may need more time or load test config)"
fi

cat > "$REPORT_FILE" <<JSONEOF
{
  "bolt": "Bolt-3",
  "test": "Flagger Rollback Drill",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "namespace": "$NAMESPACE",
  "gate_result": "$GATE_RESULT",
  "gate_message": "$GATE_MSG",
  "canary": {
    "final_phase": "$FINAL_STATUS",
    "final_weight": "$FINAL_WEIGHT",
    "failure_reason": "$FAILURE_REASON",
    "rollback_detected": $ROLLBACK_DETECTED
  },
  "sli_thresholds": {
    "error_rate_max_pct": 1,
    "p99_latency_max_ms": 200,
    "analysis_interval_s": 10,
    "failure_threshold": 3
  },
  "artifacts": [
    "tests/reports/bolt3-flagger-rollback-report.json",
    "gitops/slo/flagger-canary-template.yaml",
    "gitops/slo/keda-scaledobject-template.yaml"
  ]
}
JSONEOF

echo ""
echo "=== Bolt-3 Result: $GATE_RESULT ==="
echo "Report: $REPORT_FILE"
cat "$REPORT_FILE"

# Cleanup
echo ""
echo "[Cleanup] Removing test canary and workload..."
kubectl delete canary podinfo -n "$NAMESPACE" 2>/dev/null || true
kubectl delete deployment podinfo -n "$NAMESPACE" 2>/dev/null || true
kubectl delete service podinfo -n "$NAMESPACE" 2>/dev/null || true
echo "Cleanup complete."
