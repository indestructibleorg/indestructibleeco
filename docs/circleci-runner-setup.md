# CircleCI Self-Hosted Runner Setup Guide

**Project**: IndestructibleEco
**Resource Class**: `eco/base`
**Runner Type**: Container Runner on GKE

---

## Overview

This guide walks you through setting up a CircleCI self-hosted container runner on the GKE `eco-staging` cluster. The runner will execute CircleCI pipelines with the `eco/base` resource class.

---

## Prerequisites

### 1. CircleCI Account
- CircleCI account with organization access
- Access to the `indestructibleorg` organization
- Project linked to CircleCI

### 2. CircleCI Tokens

#### Runner Token (Required)
1. Go to https://app.circleci.com/settings/user/tokens
2. Create a new personal API token with **"View and manage runners"** permission
3. Save this token — it will be used as `CIRCLECI_RUNNER_TOKEN`

#### API Token (Optional)
1. Go to https://app.circleci.com/settings/user/tokens
2. Create a new personal API token with standard permissions
3. Save this token as `CIRCLECI_API_TOKEN`

### 3. GKE Cluster Access
- Access to `eco-staging` cluster in `asia-east1` region
- Project: `my-project-ops-1991`
- `gcloud` CLI installed and authenticated
- `kubectl` CLI installed

---

## Architecture

```
CircleCI (Cloud)
       │
       │ 1. Pipeline triggers with resource_class: eco/base
       │
       ▼
┌─────────────────────────────────────┐
│  GKE Cluster: eco-staging           │
│  Namespace: circleci-runner         │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Deployment: circleci-agent   │  │
│  │  - 1 replica                  │  │
│  │  - Image: circleci/runner     │  │
│  │    :launch-agent              │  │
│  └───────────────────────────────┘  │
│             │                         │
│             │ 2. Polls for jobs       │
│             │                         │
│             ▼                         │
│  ┌───────────────────────────────┐  │
│  │  Task Pod (dynamic)           │  │
│  │  - Executes job steps         │  │
│  │  - Auto-cleanup               │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## Deployment Steps

### Step 1: Set Environment Variables

```bash
export CIRCLECI_RUNNER_TOKEN="your-runner-token-here"
export CIRCLECI_API_TOKEN="your-api-token-here"  # Optional
```

### Step 2: Run the Deployment Script

```bash
cd /workspace/repo
./scripts/deploy-circleci-runner.sh
```

The script will:
1. Get GKE credentials
2. Create the `circleci-runner` namespace
3. Create ConfigMap with runner configuration
4. Create Secret with authentication tokens
5. Create RBAC resources (ServiceAccount, Role, ClusterRole)
6. Deploy the CircleCI agent
7. Wait for deployment to be ready

### Step 3: Verify Deployment

```bash
# Check pod status
kubectl get pods -n circleci-runner

# View agent logs
kubectl logs -f deployment/circleci-agent -n circleci-runner

# Check agent connectivity
kubectl logs deployment/circleci-agent -n circleci-runner | grep "agent"
```

Expected output should show:
```
INFO: Starting CircleCI Runner Agent...
INFO: Resource class: eco/base
INFO: Connected to CircleCI
INFO: Waiting for tasks...
```

---

## CircleCI Configuration

### Update `.circleci/config.yml`

The CircleCI config should use the `eco/base` resource class:

```yaml
version: 2.1

jobs:
  build:
    docker:
      - image: cimg/python:3.11
    resource_class: eco/base  # This matches our runner
    steps:
      - checkout
      - run:
          name: "Run tests"
          command: pytest tests/

workflows:
  build-workflow:
    jobs:
      - build
```

### Multiple Jobs

```yaml
jobs:
  test:
    docker:
      - image: cimg/python:3.11
    resource_class: eco/base
    steps:
      - checkout
      - run: python -m pytest tests/

  lint:
    docker:
      - image: cimg/python:3.11
    resource_class: eco/base
    steps:
      - checkout
      - run: ruff check .

workflows:
  ci-workflow:
    jobs:
      - test
      - lint
```

---

## Monitoring and Troubleshooting

### Check Runner Status

```bash
# View all pods in the runner namespace
kubectl get pods -n circleci-runner

# View agent logs
kubectl logs -f deployment/circleci-agent -n circleci-runner
```

### Common Issues

#### 1. Runner Not Connecting
**Symptoms**: Agent shows errors connecting to CircleCI

**Solutions**:
- Verify `CIRCLECI_RUNNER_TOKEN` is correct
- Check network connectivity from GKE to CircleCI
- Review agent logs: `kubectl logs deployment/circleci-agent -n circleci-runner`

#### 2. Jobs Not Starting
**Symptoms**: Pipeline shows "Waiting for agent" but never starts

**Solutions**:
- Verify resource class matches: `eco/base`
- Check agent is running: `kubectl get pods -n circleci-runner`
- Verify RBAC permissions are correct
- Check CircleCI project settings for runner registration

#### 3. Task Pods Failing
**Symptoms**: Jobs start but task pods crash

**Solutions**:
- Check task pod logs: `kubectl logs -l task=<task-id> -n circleci-runner`
- Verify resource requests/limits are sufficient
- Check image availability
- Review CircleCI job logs for specific errors

### Scaling the Runner

To increase runner capacity:

```bash
# Scale to 2 replicas
kubectl scale deployment circleci-agent -n circleci-runner --replicas=2
```

Update `k8s/circleci/deployment.yaml` and change `replicas` for permanent changes.

---

## Resource Requirements

### Agent Pod
- **CPU**: 250m request, 2000m limit
- **Memory**: 512Mi request, 4Gi limit

### Task Pods (per job)
- Depends on job requirements
- Will inherit limits from job specification

### Total Cluster Requirements
Ensure your GKE cluster has sufficient resources:
- **CPU**: ~2 cores minimum + job requirements
- **Memory**: ~4GB minimum + job requirements

---

## Security Considerations

1. **Token Management**
   - Store `CIRCLECI_RUNNER_TOKEN` securely
   - Rotate tokens regularly
   - Use Kubernetes Secrets (already done)

2. **RBAC**
   - Runner has pod creation permissions
   - Review `k8s/circleci/rbac.yaml`
   - Follow principle of least privilege

3. **Network Policies**
   - Consider adding network policies to restrict outbound traffic
   - Firewall rules for CircleCI endpoints

---

## Updating the Runner

### Update Agent Image

Edit `k8s/circleci/deployment.yaml` and update the image:

```yaml
- name: runner-agent
  image: circleci/runner:launch-agent@<sha256-digest>
```

Then apply:

```bash
kubectl apply -f k8s/circleci/deployment.yaml
kubectl rollout status deployment/circleci-agent -n circleci-runner
```

### Update Configuration

1. Edit ConfigMap: `kubectl edit configmap circleci-agent-config -n circleci-runner`
2. Or update `k8s/circleci/configmap.yaml` and apply

---

## Removing the Runner

```bash
# Delete deployment
kubectl delete deployment circleci-agent -n circleci-runner

# Delete all resources in namespace
kubectl delete namespace circleci-runner
```

---

## Support and Resources

- [CircleCI Runner Documentation](https://circleci.com/docs/runner-overview/)
- [CircleCI Container Runner for Kubernetes](https://circleci.com/docs/container-runner/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Project Repository](https://github.com/indestructibleorg/indestructibleeco)

---

## Related Files

- `.circleci/config.yml` - CircleCI pipeline configuration
- `k8s/circleci/namespace.yaml` - Kubernetes namespace
- `k8s/circleci/configmap.yaml` - Runner configuration
- `k8s/circleci/secret.yaml` - Kubernetes secret template
- `k8s/circleci/rbac.yaml` - RBAC configuration
- `k8s/circleci/deployment.yaml` - Agent deployment
- `scripts/deploy-circleci-runner.sh` - Deployment script