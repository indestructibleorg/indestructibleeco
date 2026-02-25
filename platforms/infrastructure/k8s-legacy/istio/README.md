<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Service Mesh (Istio) - Enterprise Implementation

## Overview

This directory contains enterprise-grade Istio Service Mesh configuration for the MachineNativeOps platform, providing advanced traffic management, security policies, and observability capabilities.

## Architecture

### Components
- **Istio Control Plane**: Manages service mesh configuration and policies
- **Envoy Proxies**: Sidecar proxies deployed with each pod for traffic interception
- **Pilot**: Service discovery and traffic management
- **Citadel**: Certificate management and mTLS
- **Galley**: Configuration validation and distribution
- **Sidecar Injector**: Automatic sidecar injection

### Key Features

#### Traffic Management
- **VirtualServices**: Advanced traffic routing rules
- **DestinationRules**: Traffic policies and load balancing
- **Gateway**: Ingress/egress traffic management
- **ServiceEntry**: External service integration

#### Security
- **mTLS (Mutual TLS)**: Automatic encryption between services
- **PeerAuthentication**: Service-to-service authentication policies
- **RequestAuthentication**: End-user authentication (JWT/OIDC)
- **AuthorizationPolicy**: Fine-grained access control

#### Observability
- **Metrics**: Prometheus integration for performance monitoring
- **Distributed Tracing**: Jaeger integration for request tracing
- **Access Logging**: Detailed traffic logging
- **Kiali**: Service mesh visualization and monitoring

## Deployment

### Prerequisites
- Kubernetes cluster (v1.19+)
- kubectl configured with cluster access
- Helm 3.x installed

### Installation Steps

1. **Install Istio:**
```bash
# Download Istio
curl -L [EXTERNAL_URL_REMOVED] | sh -
cd istio-*

# Install with custom profile
istioctl install --set profile=default -y

# Enable automatic sidecar injection
kubectl label namespace default istio-injection=enabled
```

2. **Deploy MachineNativeOps Resources:**
```bash
# Apply namespace configuration
kubectl apply -f k8s/istio/namespace.yaml

# Deploy gateway
kubectl apply -f k8s/istio/gateway.yaml

# Deploy virtual services
kubectl apply -f k8s/istio/virtualservices/

# Deploy destination rules
kubectl apply -f k8s/istio/destination-rules/

# Apply security policies
kubectl apply -f k8s/istio/security/
```

## Configuration

### Traffic Management

**Canary Deployments:**
```yaml
# 10% traffic to v2, 90% to v1
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: machine-native-ops
spec:
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: machine-native-ops
        subset: v2
  - route:
    - destination:
        host: machine-native-ops
        subset: v1
      weight: 90
    - destination:
        host: machine-native-ops
        subset: v2
      weight: 10
```

**Circuit Breaking:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: machine-native-ops
spec:
  host: machine-native-ops
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 30s
      baseEjectionTime: 30s
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 3
```

### Security

**Enable mTLS:**
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: STRICT
```

**Authorization Policy:**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: machine-native-ops-policy
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: machine-native-ops
  action: ALLOW
  rules:
  - from:
    - source:
        namespaces: ["machine-native-ops"]
  - to:
    - operation:
        methods: ["GET", "POST"]
```

## Monitoring

### Kiali Dashboard
```bash
# Port-forward to access Kiali
istioctl dashboard kiali
```

### Metrics
Metrics are exposed to Prometheus and can be queried:
```promql
# Request rate
rate(istio_requests_total[1m])

# Error rate
rate(istio_requests_total{response_code=~"5.."}[1m])

# Latency P95
histogram_quantile(0.95, rate(istio_request_duration_seconds_bucket[5m]))
```

## Troubleshooting

### Check Sidecar Injection
```bash
kubectl get pod -n machine-native-ops -o jsonpath='{.items[*].metadata.annotations.sidecar\.istio\.io/inject}'
```

### View Proxy Logs
```bash
kubectl logs -n machine-native-ops <pod-name> -c istio-proxy
```

### Check Mesh Configuration
```bash
istioctl proxy-status
istioctl proxy-config routes <pod-name> -n machine-native-ops
```

## Performance Considerations

- **Sidecar Resource Limits**: Configure CPU/memory limits for sidecar proxies
- **Connection Pooling**: Optimize connection pool settings
- **Telemetry Sampling**: Adjust sampling rates for metrics and traces
- **Cache Size**: Tune sidecar cache sizes for performance

## Security Best Practices

1. **Enable mTLS**: Use STRICT mode for all inter-service communication
2. **Network Policies**: Combine Istio with Kubernetes Network Policies
3. **Principle of Least Privilege**: Use AuthorizationPolicy for granular control
4. **Regular Certificate Rotation**: Certificates are automatically rotated by Citadel
5. **Audit Logging**: Enable access logging for security auditing

## References

- [Istio Documentation]([EXTERNAL_URL_REMOVED])
- [Traffic Management]([EXTERNAL_URL_REMOVED])
- [Security]([EXTERNAL_URL_REMOVED])
- [Observability]([EXTERNAL_URL_REMOVED])