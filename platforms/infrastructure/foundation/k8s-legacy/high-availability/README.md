# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# High Availability (Multi-AZ) - Enterprise Implementation

## Overview

This directory contains enterprise-grade high availability configuration for the MachineNativeOps platform, providing multi-availability zone deployment, automatic failover, and fault tolerance.

## Architecture

### Multi-AZ Deployment Strategy

#### Zone Distribution
```
Region: us-east-1
├── Zone A (us-east-1a)
│   ├── Control Plane nodes (3)
│   ├── Worker nodes (5)
│   ├── Application pods (replicas 1-3)
│   └── Database primary
├── Zone B (us-east-1b)
│   ├── Control Plane nodes (2)
│   ├── Worker nodes (5)
│   ├── Application pods (replicas 4-6)
│   └── Database replica
└── Zone C (us-east-1c)
    ├── Control Plane nodes (2)
    ├── Worker nodes (5)
    ├── Application pods (replicas 7-9)
    └── Database replica
```

### Key Features

#### Fault Tolerance
- **Pod Anti-Affinity**: Distribute pods across zones
- **Node Anti-Affinity**: Prevent single point of failure
- **Zone Topology Spread**: Balanced distribution
- **Automatic Failover**: Self-healing capabilities

#### Load Balancing
- **Zone-aware Routing**: Route to nearest zone
- **Cross-Zone Load Balancing**: Global distribution
- **Health Checks**: Zone-level health monitoring
- **Circuit Breaking**: Automatic zone isolation

#### Data Replication
- **Synchronous Replication**: Primary-Secondary
- **Asynchronous Replication**: Multi-leader
- **Automatic Failover**: Promote replicas
- **Data Consistency**: Strong consistency guarantees

## Deployment

### Prerequisites
- Kubernetes cluster spanning 3+ AZs
- AWS/Azure/GCP multi-AZ support
- Load balancer with cross-zone support
- Regional storage (EBS Regional, Azure ZRS)

### Installation Steps

1. **Deploy Multi-AZ Infrastructure:**
```bash
# Apply namespace configuration
kubectl apply -f k8s/high-availability/namespace.yaml

# Deploy topology-aware deployments
kubectl apply -f k8s/high-availability/deployments/

# Deploy cross-zone services
kubectl apply -f k8s/high-availability/services/

# Apply failover policies
kubectl apply -f k8s/high-availability/failover/
```

2. **Configure Zone Topology:**
```bash
# Label nodes with zone information
kubectl label node node-1 topology.kubernetes.io/zone=us-east-1a
kubectl label node node-2 topology.kubernetes.io/zone=us-east-1b
kubectl label node node-3 topology.kubernetes.io/zone=us-east-1c
```

3. **Verify Distribution:**
```bash
# Check pod distribution across zones
kubectl get pods -o wide -n machine-native-ops

# Check zone topology constraints
kubectl describe pod <pod-name> | grep topology
```

## Multi-AZ Configuration

### Pod Topology Spread Constraints

**Zone-Balanced Distribution:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: machine-native-ops
  namespace: platform-03
spec:
  replicas: 9
  template:
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: machine-native-ops
      - maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: machine-native-ops
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app.kubernetes.io/name: machine-native-ops
              topologyKey: kubernetes.io/hostname
```

### Node Affinity

**Zone-Specific Deployment:**
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values:
          - us-east-1a
          - us-east-1b
          - us-east-1c
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
          - m5.xlarge
          - m5.2xlarge
```

### Storage Replication

**Multi-AZ Persistent Volumes:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: platform-03
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: gp3-regional  # Regional storage
  resources:
    requests:
      storage: 100Gi
  volumeMode: Filesystem
```

## Failover Configuration

### Automatic Failover Policies

**Zone-Level Failover:**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: machine-native-ops-pdb
  namespace: platform-03
spec:
  minAvailable: 66%  # Ensure 2/3 availability
  selector:
    matchLabels:
      app.kubernetes.io/name: machine-native-ops
```

**Health-Based Failover:**
```yaml
# Istio DestinationRule with zone failover
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: zone-failover
  namespace: platform-03
spec:
  host: machine-native-ops
  trafficPolicy:
    loadBalancer:
      simple: ROUND_ROBIN
      localityLbSetting:
        enabled: true
        failover:
        - from: us-east-1a
          to: us-east-1b
        - from: us-east-1b
          to: us-east-1c
        - from: us-east-1c
          to: us-east-1a
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 30s
      baseEjectionTime: 60s
      maxEjectionPercent: 50
```

### Database Failover

**PostgreSQL High Availability:**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: platform-03
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      synchronous_commit: "on"
  bootstrap:
    initdb:
      database: machine_native_ops
      owner: postgres
  storage:
    size: 100Gi
    storageClass: gp3-regional
  instances:
    - name: postgres-1
      nodeAffinity:
        required:
          nodeSelectorTerms:
          - matchExpressions:
            - key: topology.kubernetes.io/zone
              operator: In
              values:
              - us-east-1a
      replicas:
        - name: postgres-replica-1
          nodeAffinity:
            required:
              nodeSelectorTerms:
              - matchExpressions:
                - key: topology.kubernetes.io/zone
                  operator: In
                  values:
                  - us-east-1b
        - name: postgres-replica-2
          nodeAffinity:
            required:
              nodeSelectorTerms:
              - matchExpressions:
                - key: topology.kubernetes.io/zone
                  operator: In
                  values:
                  - us-east-1c
```

**Redis Cluster with Multi-AZ:**
```yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: redis-cluster
  namespace: platform-03
spec:
  size: 6  # 3 leader + 3 replicas
  clusterSize: 3
  persistence:
    enabled: true
    storageClassName: gp3-regional
    storageSize: 25Gi
  redisExporter:
    enabled: true
  nodeSelector:
    topology.kubernetes.io/zone: us-east-1a,us-east-1b,us-east-1c
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: rediscluster
```

## Load Balancing

### Global Load Balancer

**AWS Application Load Balancer:**
```yaml
apiVersion: elbv2.k8s.aws/v1beta1
kind: TargetGroupBinding
metadata:
  name: machine-native-ops-tgb
  namespace: platform-03
spec:
  serviceRef:
    name: machine-native-ops
    port: 8080
  targetGroupARN: arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/machine-native-ops/abc123
  targetType: ip
  networking:
    ingress:
    - from:
      - securityGroup:
          groupID: sg-12345678
      - ipBlock:
          cidr: 0.0.0.0/0
---
# AWS Load Balancer Controller
apiVersion: v1
kind: Service
metadata:
  name: machine-native-ops
  namespace: platform-03
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-protocol: HTTP
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-path: /health
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-interval-seconds: "30"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-timeout-seconds: "5"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-healthy-threshold: "2"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-unhealthy-threshold: "3"
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local
  selector:
    app.kubernetes.io/name: machine-native-ops
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
  - name: https
    port: 443
    targetPort: 8080
    protocol: TCP
```

### Zone-Aware Routing

**Istio DestinationRule:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: zone-aware-routing
  namespace: platform-03
spec:
  host: machine-native-ops
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
      localityLbSetting:
        enabled: true
        distribute:
        - from: us-east-1a/us-east-1a/*
          to:
            us-east-1a/us-east-1a/*: 80
            us-east-1b/us-east-1b/*: 20
        - from: us-east-1b/us-east-1b/*
          to:
            us-east-1b/us-east-1b/*: 80
            us-east-1c/us-east-1c/*: 20
        - from: us-east-1c/us-east-1c/*
          to:
            us-east-1c/us-east-1c/*: 80
            us-east-1a/us-east-1a/*: 20
```

## Monitoring and Alerting

### Multi-AZ Health Monitoring

**Zone Health Checks:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: zone-health-config
  namespace: platform-03
data:
  zones.yaml: |
    zones:
      us-east-1a:
        nodes: 5
        expected_pods: 3
        health_endpoint: [EXTERNAL_URL_REMOVED]
      us-east-1b:
        nodes: 5
        expected_pods: 3
        health_endpoint: [EXTERNAL_URL_REMOVED]
      us-east-1c:
        nodes: 5
        expected_pods: 3
        health_endpoint: [EXTERNAL_URL_REMOVED]
```

**Prometheus Alerts:**
```yaml
groups:
- name: multi-az-alerts
  rules:
  - alert: ZoneUnavailable
    expr: count(kube_node_status_condition{condition="Ready",status="true"} == 0) by (topology_kubernetes_io_zone) > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Zone {{ $labels.topology_kubernetes_io_zone }} is unavailable"
      
  - alert: PodDistributionImbalanced
    expr: max by (topology_kubernetes_io_zone) (count(kube_pod_info) by (topology_kubernetes_io_zone)) - min by (topology_kubernetes_io_zone) (count(kube_pod_info) by (topology_kubernetes_io_zone)) > 2
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Pod distribution is imbalanced across zones"
      
  - alert: CrossZoneLatencyHigh
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{cross_zone="true"}[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High cross-zone latency detected: {{ $value }}s"
      
  - alert: DatabaseReplicationLag
    expr: pg_replication_lag_seconds > 30
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Database replication lag: {{ $value }}s"
```

## Disaster Recovery

### Zone Failure Recovery

**Automatic Zone Failover:**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: zone-failover-pdb
  namespace: platform-03
spec:
  minAvailable: 2
  maxUnavailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: machine-native-ops
```

**Zone Isolation:**
```yaml
# Istio Circuit Breaking for Zone Isolation
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: zone-isolation
  namespace: platform-03
spec:
  host: machine-native-ops
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 300s  # 5 minutes
      maxEjectionPercent: 100  # Eject entire zone
      minHealthPercent: 0  # Allow full ejection
```

## Performance Optimization

### Cross-Zone Optimization

**Reduce Cross-Zone Traffic:**
```yaml
# Istio Locality-aware Load Balancing
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: locality-aware
  namespace: platform-03
spec:
  host: machine-native-ops
  trafficPolicy:
    loadBalancer:
      simple: ROUND_ROBIN
      localityLbSetting:
        enabled: true
        failover:
        - from: us-east-1a/us-east-1a/*
          to: us-east-1b/us-east-1b/*
        - from: us-east-1b/us-east-1b/*
          to: us-east-1c/us-east-1c/*
        - from: us-east-1c/us-east-1c/*
          to: us-east-1a/us-east-1a/*
```

**Connection Pooling:**
```yaml
connectionPool:
  tcp:
    maxConnections: 100
  http:
    http1MaxPendingRequests: 50
    maxRequestsPerConnection: 3
    idleTimeout: 300s
```

## Testing

### Failover Testing

**Simulate Zone Failure:**
```bash
# Cordon nodes in zone us-east-1a
kubectl cordon -l topology.kubernetes.io/zone=us-east-1a

# Evict pods
kubectl drain -l topology.kubernetes.io/zone=us-east-1a --ignore-daemonsets --delete-emptydir-data

# Verify failover
kubectl get pods -o wide -n machine-native-ops

# Test connectivity
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -- curl [EXTERNAL_URL_REMOVED]
```

**Test Database Failover:**
```bash
# Stop primary PostgreSQL instance
kubectl exec -it postgres-0 -n machine-native-ops -- psql -U postgres -c "SELECT pg_ctl stop;"

# Verify replica promotion
kubectl exec -it postgres-1 -n machine-native-ops -- psql -U postgres -c "SELECT pg_is_in_recovery();"

# Test application connectivity
kubectl run test-pod --rm -it --image=postgres:15 --restart=Never -- psql -h postgres.machine-native-ops.svc -U postgres -d machine_native_ops -c "SELECT 1;"
```

## Best Practices

### 1. Zone Distribution
- Distribute replicas evenly across all zones
- Use PodDisruptionBudgets for minimum availability
- Enable automatic zone failover
- Monitor zone health continuously

### 2. Data Replication
- Use synchronous replication for critical data
- Implement automatic failover for databases
- Replicate backups to multiple regions
- Test failover procedures regularly

### 3. Load Balancing
- Use zone-aware routing to minimize latency
- Enable cross-zone load balancing for resilience
- Configure health checks for all endpoints
- Monitor load balancer metrics

### 4. Monitoring
- Track pod distribution across zones
- Monitor cross-zone latency
- Alert on zone failures
- Track replication lag

### 5. Testing
- Regularly test zone failover
- Simulate zone failures
- Verify automatic failover
- Document recovery procedures

## Troubleshooting

### Zone Isolation Issues

**Check Pod Distribution:**
```bash
kubectl get pods -o wide -n machine-native-ops | awk '{print $7}' | sort | uniq -c
```

**Check Zone Health:**
```bash
kubectl get nodes -L topology.kubernetes.io/zone
kubectl describe nodes | grep -A 5 "Conditions:"
```

**Check Topology Constraints:**
```bash
kubectl describe deployment machine-native-ops -n machine-native-ops | grep -A 10 topologySpreadConstraints
```

### Failover Issues

**Check PDB Status:**
```bash
kubectl get pdb -n machine-native-ops
kubectl describe pdb machine-native-ops-pdb -n machine-native-ops
```

**Check Pod Status:**
```bash
kubectl get pods -n machine-native-ops -o wide
kubectl describe pod <pod-name> -n machine-native-ops
```

**Check Istio Configuration:**
```bash
istioctl pc destinationrule <pod-name> -n machine-native-ops
istioctl pc route <pod-name> -n machine-native-ops
```

## References

- [Kubernetes Topology Constraints]([EXTERNAL_URL_REMOVED])
- [AWS Multi-AZ Deployments]([EXTERNAL_URL_REMOVED])
- [Istio Locality-aware Load Balancing]([EXTERNAL_URL_REMOVED])
- [PostgreSQL High Availability]([EXTERNAL_URL_REMOVED])