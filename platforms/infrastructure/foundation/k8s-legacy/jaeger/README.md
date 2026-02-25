<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Distributed Tracing (Jaeger) - Enterprise Implementation

## Overview

This directory contains enterprise-grade Jaeger distributed tracing configuration for the MachineNativeOps platform, enabling comprehensive performance analysis, request tracing, and system observability.

## Architecture

### Components
- **Jaeger Agent**: Receives spans from services via UDP or gRPC
- **Jaeger Collector**: Receives and processes traces from agents
- **Jaeger Query**: Provides UI for trace search and visualization
- **Jaeger Ingester**: Ingestes traces from streaming backends (Kafka)
- **Elasticsearch/Database**: Long-term trace storage

### Key Features

#### Distributed Tracing
- **End-to-End Tracing**: Track requests across all microservices
- **Span Context Propagation**: Automatic trace context propagation
- **Sampling Strategies**: Configurable sampling rates
- **Tag and Log Support**: Rich metadata in traces

#### Performance Analysis
- **Latency Analysis**: Identify bottlenecks and slow endpoints
- **Dependency Graph**: Visualize service dependencies
- **Hotspot Detection**: Find performance hotspots
- **Historical Comparison**: Compare performance over time

#### Observability Integration
- **Prometheus Integration**: Export metrics from traces
- **Grafana Dashboards**: Visualize trace metrics
- **Alerting**: Alert on performance degradation
- **SLI/SLO Monitoring**: Track service level objectives

## Deployment

### Prerequisites
- Kubernetes cluster (v1.19+)
- Istio installed and configured
- Helm 3.x installed

### Installation Steps

1. **Add Jaeger Helm Repository:**
```bash
helm repo add jaegertracing [EXTERNAL_URL_REMOVED]
helm repo update
```

2. **Install Jaeger with Production Configuration:**
```bash
helm install jaeger jaegertracing/jaeger \
  --namespace jaeger \
  --create-namespace \
  --values k8s/jaeger/values.yaml \
  --set storage.type=elasticsearch \
  --set provisionDataStore.cassandra=false \
  --set provisionDataStore.elasticsearch=true
```

3. **Configure Istio for Jaeger Tracing:**
```bash
kubectl apply -f k8s/jaeger/istio-config.yaml
```

4. **Install Jaeger Operator (Optional):**
```bash
kubectl apply -f [EXTERNAL_URL_REMOVED] -n jaeger
```

## Configuration

### Tracing Configuration

**Application-Level Tracing:**
```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import JaegerExporter

# Configure tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent.jaeger.svc.cluster.local",
    agent_port=6831,
)

# Auto-instrument Flask app
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
```

**Istio Auto-Instrumentation:**
```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-tracing
spec:
  meshConfig:
    enableTracing: true
    defaultConfig:
      tracing:
        sampling: 10.0  # 10% sampling rate
        custom_tags:
          service:
            environment:
              value: "production"
          version:
            environment:
              value: "v1.0.0"
```

### Sampling Strategies

**Per-Service Sampling:**
```json
{
  "service_strategies": [
    {
      "service": "machine-native-ops",
      "type": "probabilistic",
      "param": 10
    },
    {
      "service": "machine-native-ops-critical",
      "type": "probabilistic",
      "param": 100
    }
  ]
}
```

**Operation-Based Sampling:**
```json
{
  "operation_strategies": [
    {
      "service": "machine-native-ops",
      "operation": "POST /api/v1/memory",
      "type": "probabilistic",
      "param": 50
    }
  ]
}
```

## Usage

### Access Jaeger UI

```bash
# Port-forward to access Jaeger UI
kubectl port-forward -n jaeger svc/jaeger-query 16686:16686

# Open browser at [EXTERNAL_URL_REMOVED]
```

### Search Traces

**Search by Service:**
- Select service name from dropdown
- Set time range
- Add tags/labels for filtering
- Click "Find Traces"

**Search by Trace ID:**
- Enter trace ID in search box
- Click "Find Traces"

**Search by Tags:**
- Add tag filters (e.g., `http.status_code=500`)
- Combine multiple tags with AND/OR

### Analyze Traces

**View Trace Details:**
- Click on any trace in results
- View span timeline
- Examine span details (tags, logs, process)
- Identify slowest spans

**Compare Traces:**
- Select multiple traces
- Use "Compare" feature
- View side-by-side comparison

**Dependency Graph:**
- Navigate to "Dependencies" tab
- View service dependency graph
- Analyze call patterns

## Integration

### Prometheus Integration

**Export Metrics from Traces:**
```yaml
# Enable metrics in Jaeger
metricsBackend: prometheus
metricsRoute: /metrics
```

**Query Trace Metrics:**
```promql
# Trace rate per service
rate(jaeger_traces_per_service_total[5m])

# Span latency P95
histogram_quantile(0.95, rate(jaeger_span_duration_milliseconds_bucket[5m]))

# Error rate
rate(jaeger_spans_total{error="true"}[5m])
```

### Grafana Integration

**Import Jaeger Dashboard:**
1. Open Grafana
2. Navigate to Dashboards → Import
3. Enter Jaeger dashboard ID (e.g., 10001)
4. Configure data source
5. View visualization

### Alerting

**Alert on High Latency:**
```yaml
# Alertmanager configuration
groups:
- name: jaeger-latency
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(jaeger_span_duration_milliseconds_bucket{service="machine-native-ops"}[5m])) > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency detected in machine-native-ops"
```

## Performance Tuning

### Storage Optimization

**Elasticsearch Configuration:**
```yaml
# Index lifecycle management
indices:
  rollover:
    conditions:
      max_age: 24h
      max_size: 50gb
    policies:
      - max_age: 7d
        hot:
          replicas: 2
        warm:
          replicas: 1
        delete:
          min_age: 30d
```

### Collector Tuning

**Optimize Collector Performance:**
```yaml
collector:
  replicas: 3
  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "2000m"
      memory: "2Gi"
  queueSize: 10000
  numWorkers: 20
```

## Best Practices

### 1. Sampling Strategy
- Use probabilistic sampling for high-traffic services (1-10%)
- Use 100% sampling for critical low-traffic services
- Implement per-operation sampling for fine-grained control

### 2. Span Design
- Keep span names meaningful and consistent
- Add relevant tags (user_id, request_id, etc.)
- Include important logs in spans
- Avoid excessive tags (performance impact)

### 3. Context Propagation
- Always propagate trace context across service boundaries
- Use W3C trace context format for interoperability
- Inject context into async operations

### 4. Performance Impact
- Monitor Jaeger performance overhead
- Adjust sampling rates based on load
- Use async exporters to minimize latency impact
- Consider local sampling in high-throughput scenarios

### 5. Data Retention
- Define retention policy based on storage capacity
- Implement index lifecycle management
- Archive old traces to cheaper storage
- Regular cleanup of expired data

## Troubleshooting

### No Traces Appearing

**Check Agent Status:**
```bash
kubectl get pods -n jaeger
kubectl logs -n jaeger jaeger-agent-xxx
```

**Check Istio Tracing Configuration:**
```bash
istioctl proxy-config bootstrap <pod-name> -o json | jq .tracing
```

**Verify Service Instrumentation:**
- Check if application is instrumented
- Verify exporter configuration
- Check network connectivity to agent

### High Memory Usage

**Check Collector Memory:**
```bash
kubectl top pods -n jaeger
```

**Adjust Queue Size:**
```yaml
collector:
  queueSize: 5000  # Reduce from default
```

**Reduce Sampling Rate:**
```yaml
sampling:
  default_strategy:
    type: probabilistic
    param: 1  # Reduce from 10
```

### Slow UI Response

**Check Elasticsearch:**
```bash
kubectl get pods -n elasticsearch
kubectl logs -n elasticsearch elasticsearch-xxx
```

**Optimize Queries:**
- Reduce time range
- Add specific service filters
- Use trace tags for filtering

## References

- [Jaeger Documentation]([EXTERNAL_URL_REMOVED])
- [OpenTelemetry Python]([EXTERNAL_URL_REMOVED])
- [Istio Distributed Tracing]([EXTERNAL_URL_REMOVED])
- [W3C Trace Context]([EXTERNAL_URL_REMOVED])