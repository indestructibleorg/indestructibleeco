# Phase C: Docker Image Build Workflow

## Overview
Phase C requires building and pushing Docker images to GCP Artifact Registry before deploying to GKE.

## Prerequisites
- GCP Artifact Registry: `asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco`
- GKE Cluster: `eco-production` (currently being created)
- GitHub Actions Workflow: `.github/workflows/build-images.yaml`

## Docker Images Required

### 1. Web Frontend (web:v1.0.0)
- **Source**: `platforms/web/`
- **Dockerfile**: `platforms/web/Dockerfile`
- **Context**: `platforms/web/`
- **Image**: `asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/web:v1.0.0`
- **Port**: 80

### 2. API Service (api:v1.0.0)
- **Source**: `backend/api/`
- **Dockerfile**: `backend/api/Dockerfile` (stub needs to be created)
- **Context**: `backend/api/`
- **Image**: `asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/api:v1.0.0`
- **Port**: 3000

### 3. AI Service (ai:v1.0.0)
- **Source**: `backend/ai/`
- **Dockerfile**: `backend/ai/Dockerfile`
- **Context**: `backend/ai/`
- **Image**: `asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/ai:v1.0.0`
- **Port**: 8001

### 4. API Gateway (gateway:v1.0.0)
- **Source**: Repository root
- **Dockerfile**: `docker/Dockerfile`
- **Context**: `.`
- **Image**: `asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/gateway:v1.0.0`
- **Port**: 8000

## Build Methods

### Method 1: GitHub Actions (Recommended)
Trigger the workflow manually:
```bash
gh workflow run build-images.yaml -f service=all -f environment=production
```

Or navigate to:
- GitHub → Actions → Build and Push Docker Images → Run workflow

### Method 2: Cloud Build
```bash
gcloud builds submit \
  --tag asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/web:v1.0.0 \
  platforms/web/
```

### Method 3: Local Docker + gcloud auth
```bash
gcloud auth configure-docker asia-east1-docker.pkg.dev
docker build -t asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/web:v1.0.0 platforms/web/
docker push asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/web:v1.0.0
```

## Current Status

### ✅ Completed
- [x] Created build workflow: `.github/workflows/build-images.yaml`
- [x] Updated Kubernetes manifests with correct image references
- [x] Configured GCP Artifact Registry
- [x] Started GKE cluster creation (in progress)

### ⏳ In Progress
- [ ] GKE cluster creation (operation-1771744130135-1e27b2a1-d6fd-4761-bdc1-cd29ce8444c0)
- [ ] Build Docker images (requires GitHub Actions trigger)

### ❌ Blocked
- [ ] Docker images not yet built
- [ ] Kubernetes deployment pending cluster creation and image builds

## Next Steps

1. **Wait for GKE cluster creation** (~10-15 minutes)
2. **Trigger GitHub Actions build workflow** for all services
3. **Verify images in Artifact Registry**
4. **Deploy to GKE using converted manifests**

## Verification Commands

```bash
# Check GKE operation status
gcloud container operations list --project=my-project-ops-1991 --filter="status!=DONE"

# List built images
gcloud artifacts images list --repository=indestructibleeco --location=asia-east1

# Verify cluster
gcloud container clusters list --project=my-project-ops-1991

# Connect to cluster
gcloud container clusters get-credentials eco-production --region=asia-east1 --project=my-project-ops-1991
```

## Notes

- GKE cluster creation is quota-limited (currently using e2-medium with 1-3 nodes)
- Docker images must be built before Kubernetes deployment
- All manifests have been updated to use GCP Artifact Registry images
- GitHub Actions workflow uses Workload Identity Federation for authentication

## File Locations

- Build workflow: `/workspace/repo/.github/workflows/build-images.yaml`
- Kubernetes manifests: `/workspace/repo/k8s/production/*.qyaml`
- Cluster creation script: `/workspace/repo/k8s/production/create-gke-cluster.sh`
- Converted manifests: `/tmp/k8s-production/*.yaml`
