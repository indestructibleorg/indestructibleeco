# IndestructibleEco — CircleCI Self-Hosted Runner Setup

## Phase 1: Create CircleCI Configuration
- [x] Create `.circleci/config.yml` with self-hosted runner configuration
- [x] Configure `eco/base` resource class for container runner

## Phase 2: Create Kubernetes Manifests
- [x] Create namespace manifest
- [x] Create ConfigMap with runner configuration
- [x] Create Secret manifest template
- [x] Create Deployment manifest
- [x] Create RBAC resources (ServiceAccount, Role, ClusterRole)
- [x] Create deployment script

## Phase 3: Documentation
- [x] Create comprehensive setup guide

## Phase 4: Deployment (Pending)
- [ ] Get CircleCI runner token from https://app.circleci.com/settings/user/tokens
- [ ] Set CIRCLECI_RUNNER_TOKEN environment variable
- [ ] Run deployment script: `./scripts/deploy-circleci-runner.sh`
- [ ] Verify runner connectivity
- [ ] Test with CircleCI pipeline

## Pending Tasks (from previous session)
- [ ] SSD Quota Increase — Asia-east1 region (250GB → 500GB)
- [ ] OAuth Consent Screen — Configure OAuth 2.0 client for IAP
- [ ] Production Cluster — Waiting for quota approval