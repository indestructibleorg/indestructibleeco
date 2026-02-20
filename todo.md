# GKE eco-staging Deployment

## Phase 1: Dockerfiles
- [ ] Create web frontend Dockerfile (platforms/web/Dockerfile)
- [ ] Fix AI backend Dockerfile for GKE (add README.md copy, healthcheck)
- [ ] Fix API backend Dockerfile for GKE (add .npmrc handling)

## Phase 2: K8s Staging Overlay (.qyaml)
- [ ] k8s/staging/namespace.qyaml (eco-staging namespace + SA + RBAC)
- [ ] k8s/staging/configmap.qyaml (eco-staging ConfigMap + Secrets)
- [ ] k8s/staging/api-gateway.qyaml (API gateway deployment + svc + HPA)
- [ ] k8s/staging/ai-service.qyaml (AI service deployment + svc)
- [ ] k8s/staging/web-frontend.qyaml (Web frontend deployment + svc)
- [ ] k8s/staging/redis.qyaml (Redis StatefulSet + svc)
- [ ] k8s/staging/postgres.qyaml (Postgres StatefulSet + svc)
- [ ] k8s/staging/ingress.qyaml (Ingress for eco-staging)

## Phase 3: Argo CD
- [ ] k8s/argocd/argo-app-eco-staging.yaml (Argo CD app for eco-staging)

## Phase 4: Deploy workflow + script
- [ ] .github/workflows/deploy-gke.yaml (CI/CD for GKE)
- [ ] deploy.sh (manual deployment script)

## Phase 5: Commit, push, verify CI
- [ ] Commit all changes
- [ ] Push to main
- [ ] Verify CI green