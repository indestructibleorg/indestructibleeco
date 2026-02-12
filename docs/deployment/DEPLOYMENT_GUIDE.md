# AutoEcoOps Ecosystem v1.0 - Deployment Guide

## Prerequisites

Before deploying AutoEcoOps Ecosystem, ensure you have the following tools and access:

- **Kubernetes Cluster**: Kubernetes 1.27+ with at least 3 worker nodes (8 CPU, 16GB RAM each)
- **kubectl**: Latest version configured with cluster access
- **Helm**: Version 3.12+
- **Terraform**: Version 1.0+
- **Docker**: Version 20.10+ for building container images
- **AWS CLI**: Version 2.0+ (if deploying on AWS)
- **Git**: Version 2.40+ for cloning repositories
- **ArgoCD CLI**: Version 2.8+ for GitOps operations

## Architecture Overview

The deployment follows a three-layer architecture:

1. **Shared Kernel** (core namespace): Authentication, event streaming, policy enforcement, audit
2. **Platforms** (platform-01, platform-02, platform-03 namespaces): Domain-specific services
3. **Observability** (observability namespace): Prometheus, Grafana, Loki, Tempo

## Step 1: Infrastructure Provisioning with Terraform

### 1.1 Initialize Terraform

```bash
cd infrastructure/terraform/environments/prod
terraform init
```

### 1.2 Review and Apply Configuration

```bash
terraform plan -out=tfplan
terraform apply tfplan
```

This creates:
- VPC with public and private subnets across 3 availability zones
- NAT Gateways for private subnet egress
- Security groups for Kubernetes and ALB
- VPC Flow Logs for network monitoring

### 1.3 Create EKS Cluster

```bash
terraform apply -target=aws_eks_cluster.main
terraform apply -target=aws_eks_node_group.main
```

### 1.4 Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name autoecoops-prod
kubectl get nodes
```

## Step 2: Deploy Shared Kernel Services

### 2.1 Create Namespaces

```bash
kubectl create namespace core
kubectl create namespace observability
kubectl create namespace platform-01
kubectl create namespace platform-02
kubectl create namespace platform-03
```

### 2.2 Configure Secrets

Create secrets for sensitive data:

```bash
kubectl create secret generic auth-service-secrets \
  --from-literal=OIDC_CLIENT_SECRET=<your-secret> \
  --from-literal=DATABASE_PASSWORD=<your-password> \
  --from-literal=JWT_SIGNING_KEY=<your-key> \
  -n core

kubectl create secret generic database-credentials \
  --from-literal=username=autoecoops \
  --from-literal=password=<your-password> \
  -n core
```

### 2.3 Deploy Auth Service

```bash
kubectl apply -f infrastructure/kustomize/base/auth-service.yaml
kubectl rollout status deployment/auth-service -n core
```

### 2.4 Deploy Memory Hub

```bash
kubectl apply -f infrastructure/kustomize/base/memory-hub.yaml
kubectl rollout status deployment/memory-hub -n core
```

### 2.5 Deploy Event Bus

```bash
kubectl apply -f infrastructure/kustomize/base/event-bus.yaml
kubectl rollout status deployment/event-bus -n core
```

### 2.6 Deploy Policy & Audit Service

```bash
kubectl apply -f infrastructure/kustomize/base/policy-audit.yaml
kubectl rollout status deployment/policy-audit -n core
```

## Step 3: Deploy Observability Stack

### 3.1 Apply Observability Manifests

```bash
kubectl apply -f infrastructure/kustomize/base/observability.yaml
```

### 3.2 Verify Observability Deployment

```bash
kubectl get pods -n observability
kubectl port-forward -n observability svc/prometheus 9090:9090
kubectl port-forward -n observability svc/grafana 3000:3000
```

Access Prometheus at `http://localhost:9090` and Grafana at `http://localhost:3000`.

## Step 4: Deploy Platform Services

### 4.1 Deploy Platform-01 (IndestructibleAutoOps)

```bash
kubectl apply -f platforms/platform-01/k8s/
kubectl rollout status deployment -n platform-01
```

### 4.2 Deploy Platform-02 (IAOps)

```bash
kubectl apply -f platforms/platform-02/k8s/
kubectl rollout status deployment -n platform-02
```

### 4.3 Deploy Platform-03 (MachineNativeOps)

```bash
kubectl apply -f platforms/platform-03/k8s/
kubectl rollout status deployment -n platform-03
```

## Step 5: Configure GitOps with ArgoCD

### 5.1 Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 5.2 Configure ArgoCD Application

```bash
kubectl apply -f ci-cd/argocd/application.yaml
```

### 5.3 Access ArgoCD UI

```bash
kubectl port-forward -n argocd svc/argocd-server 8080:443
argocd login localhost:8080 --username admin --password <initial-password>
```

## Step 6: Configure Ingress and Load Balancer

### 6.1 Install Ingress Controller

```bash
kubectl apply -f infrastructure/kustomize/base/ingress-controller.yaml
```

### 6.2 Configure Ingress Rules

```bash
kubectl apply -f infrastructure/kustomize/base/ingress.yaml
```

### 6.3 Verify Ingress

```bash
kubectl get ingress -A
kubectl describe ingress autoecoops-ingress -n core
```

## Step 7: Verify Deployment

### 7.1 Check All Pods

```bash
kubectl get pods -A
```

### 7.2 Verify Service Connectivity

```bash
kubectl exec -it <pod-name> -n core -- curl http://auth-service/health
```

### 7.3 Check Logs

```bash
kubectl logs -f deployment/auth-service -n core
kubectl logs -f deployment/prometheus -n observability
```

## Step 8: Post-Deployment Configuration

### 8.1 Configure Monitoring Alerts

```bash
kubectl apply -f observability/alertmanager/config.yaml
```

### 8.2 Set Up Log Aggregation

Verify Loki is collecting logs:

```bash
kubectl port-forward -n observability svc/loki 3100:3100
curl http://localhost:3100/loki/api/v1/query?query={job="kubernetes-pods"}
```

### 8.3 Configure Backup and Recovery

```bash
# Enable automated backups
kubectl apply -f infrastructure/kustomize/base/backup-policy.yaml
```

## Troubleshooting

### Pod Not Starting

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

### Service Connectivity Issues

```bash
kubectl exec -it <pod-name> -n <namespace> -- sh
nslookup <service-name>
```

### Resource Constraints

```bash
kubectl top nodes
kubectl top pods -A
```

## Scaling Considerations

### Horizontal Scaling

Adjust HPA settings:

```bash
kubectl patch hpa auth-service-hpa -n core -p '{"spec":{"maxReplicas":20}}'
```

### Vertical Scaling

Update resource requests/limits:

```bash
kubectl set resources deployment auth-service -n core --limits=cpu=1000m,memory=1Gi --requests=cpu=500m,memory=512Mi
```

## Security Hardening

### Enable Network Policies

```bash
kubectl apply -f infrastructure/kustomize/base/network-policies.yaml
```

### Configure Pod Security Policies

```bash
kubectl apply -f infrastructure/kustomize/base/pod-security-policies.yaml
```

### Enable RBAC

```bash
kubectl apply -f infrastructure/kustomize/base/rbac.yaml
```

## Maintenance and Updates

### Rolling Updates

```bash
kubectl set image deployment/auth-service auth-service=autoecoops/auth-service:v1.1.0 -n core
kubectl rollout status deployment/auth-service -n core
```

### Rollback

```bash
kubectl rollout undo deployment/auth-service -n core
```

## Monitoring and Observability

### Access Grafana Dashboards

```bash
kubectl port-forward -n observability svc/grafana 3000:3000
```

Default credentials: `admin:prom-operator`

### View Prometheus Metrics

```bash
kubectl port-forward -n observability svc/prometheus 9090:9090
```

### Check Distributed Traces

```bash
kubectl port-forward -n observability svc/tempo 3200:3200
```

## Next Steps

1. Configure custom monitoring dashboards in Grafana
2. Set up alerting rules and notification channels
3. Implement backup and disaster recovery procedures
4. Configure multi-cluster replication for high availability
5. Establish compliance and audit logging workflows
