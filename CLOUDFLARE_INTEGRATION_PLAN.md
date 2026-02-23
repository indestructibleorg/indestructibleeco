# eco-base × Cloudflare 全面整合計畫

**域名：autoecoops.io | Zone ID: 3f10062913fe82ee54594594413c3d68 | Account ID: 2fead4a141ec2c677eb3bf0ac535f1d5**

---

## 衝突分析：草稿 vs 現有架構

### ✅ 可直接借鑒（無衝突）

| 草稿概念 | eco-base 對應實作 | 說明 |
|---------|-----------------|------|
| Workers Custom Domain | `api.autoecoops.io` → Workers | 邊緣 API 代理 GKE |
| Pages 前端部署 | `eco-base-web` Pages 專案 | 已有 deploy-web.yml |
| R2 Storage | `eco-base-assets` bucket | 靜態資源 + 備份 |
| Workers KV | `ECO_CACHE` namespace | Session/Rate Limiting 快取 |
| WAF + Rate Limiting | autoecoops.io 全域套用 | 保護 API 端點 |
| Argo Smart Routing | Pro 方案已包含 | 減少 33% 延遲 |
| Security Headers | HTTP Response Transform | HSTS/CSP/X-Frame |
| GitHub Actions OIDC | 現有 deploy-web.yml | 無密碼認證 |
| SBOM + Attestation | 現有 CI/CD pipeline | SLSA Level 3 |

### ⚠️ 需要調整（有衝突）

| 衝突點 | 草稿做法 | eco-base 正確做法 | 原因 |
|--------|---------|-----------------|------|
| 資料庫 | PlanetScale + Drizzle | **Supabase Pro + PostgreSQL** | eco-base 使用 Supabase，不用 PlanetScale |
| 根域名 A record | GitHub Pages 185.199.x.x | **GKE Ingress IP** | eco-base 部署在 GKE，不是 GitHub Pages |
| 動態 IP 解決方案 | Cloudflare Tunnel | **GKE 固定 LoadBalancer IP** | GKE 有固定外部 IP，不需要 Tunnel |
| 文件站 | Read the Docs CNAME | **不需要**（有 GitHub Pages） | eco-base 用 GitHub Pages 作文件 |
| Workers 框架 | 獨立 wrangler.toml | **整合至 backend/cloudflare/** | 已有 IM Integration Worker |
| D1 資料庫 | D1 綁定 | **不使用**（用 Supabase） | 避免雙重資料庫 |

### 🔴 不可引用（直接衝突）

| 項目 | 原因 |
|------|------|
| Zone ID `5803b95939d51643e2d38823c65122cd` | 是 19911208.work 的 Zone，不是 autoecoops.io |
| `username.github.io` CNAME | eco-base 前端用 Cloudflare Pages，不是 GitHub Pages |
| PlanetScale 相關所有配置 | eco-base 使用 Supabase Pro |
| `app.19911208.work` 所有 hostname | 域名不同 |

---

## eco-base 完整 Cloudflare 架構設計

### DNS 記錄完整方案（autoecoops.io）

```
# === 根域名 → Cloudflare Pages（前端）===
CNAME  @                    eco-base-web.pages.dev          Proxied=Yes  TTL=Auto

# === API 子域名 → Workers（邊緣代理 → GKE）===
A      api                  <GKE_INGRESS_IP>                Proxied=Yes  TTL=Auto

# === 應用子域名 → GKE Ingress ===
A      app                  <GKE_INGRESS_IP>                Proxied=Yes  TTL=Auto

# === 監控子域名 → GKE Ingress ===
A      monitoring            <GKE_INGRESS_IP>                Proxied=Yes  TTL=Auto
A      grafana               <GKE_INGRESS_IP>                Proxied=Yes  TTL=Auto

# === Supabase 自訂域名（如需要）===
CNAME  db                   <SUPABASE_PROJECT>.supabase.co  Proxied=No   TTL=3600

# === GitHub Pages（文件）===
CNAME  docs                 indestructibleorg.github.io     Proxied=No   TTL=3600

# === 郵件安全 ===
TXT    @    "v=spf1 include:_spf.google.com ~all"           TTL=3600
TXT    _dmarc  "v=DMARC1; p=quarantine; rua=mailto:security@autoecoops.io; pct=100"  TTL=3600

# === SSL 控制 ===
CAA    @    issue "letsencrypt.org"                          TTL=3600
CAA    @    issue "digicert.com"                             TTL=3600
CAA    @    issuewild "letsencrypt.org"                      TTL=3600
CAA    @    iodef "mailto:security@autoecoops.io"            TTL=3600
```

### Workers 架構（backend/cloudflare/）

```
workers/
  ├── api-gateway/          # API 代理 + 認證驗證（新增）
  │   ├── src/index.ts      # 路由 → GKE eco-api-svc
  │   └── wrangler.toml     # api.autoecoops.io custom domain
  ├── im-integration/       # 現有 IM webhook router（已有）
  │   └── wrangler.toml     # im.autoecoops.io
  └── health-check/         # 健康檢查 Worker（新增）
      └── src/index.ts      # /health → 各服務狀態
```

**api-gateway wrangler.toml：**
```toml
name = "eco-api-gateway"
main = "src/index.ts"
compatibility_date = "2025-01-01"
compatibility_flags = ["nodejs_compat"]

[[routes]]
pattern = "api.autoecoops.io/*"
custom_domain = true

[vars]
GKE_API_URL = "https://app.autoecoops.io/api"
ENVIRONMENT = "production"

[[kv_namespaces]]
binding = "RATE_LIMIT_KV"
id = "<ECO_CACHE_KV_ID>"

[[r2_buckets]]
binding = "ASSETS"
bucket_name = "eco-base-assets"
```

### R2 Storage 用途

| Bucket | 用途 | 存取方式 |
|--------|------|---------|
| `eco-base-assets` | 前端靜態資源、用戶上傳檔案 | Workers 綁定 |
| `eco-base-backups` | Supabase 資料庫備份、K8s etcd 備份 | 定時 GitHub Actions |
| `eco-base-logs` | 審計日誌長期儲存（不可變）| Append-only |

### Workers KV 用途

| Namespace | 用途 |
|-----------|------|
| `ECO_CACHE` | API 回應快取（TTL 60-300s）|
| `ECO_RATE_LIMIT` | Rate Limiting 計數器 |
| `ECO_SESSION` | Edge Session 儲存 |

---

## Pro 方案功能啟用清單

- [ ] Argo Smart Routing（`/argo/smart_routing` → on）
- [ ] Tiered Cache（`/argo/tiered_caching` → on）
- [ ] WAF Managed Ruleset（Cloudflare + OWASP）
- [ ] Rate Limiting（`/api/` 100 req/min, `/api/auth/` 5 req/min）
- [ ] Security Headers（HSTS + CSP + X-Frame-Options）
- [ ] Cache Rules（`/api/public/*` 24h, 靜態資源 7d）
- [ ] Bot Management（Verified Bot 排除）
- [ ] Load Balancing（GKE 多節點 pool）

---

## GitHub Actions 工作流程整合

| 工作流程 | 觸發 | 功能 |
|---------|------|------|
| `deploy-web.yml` | push main | 建置前端 → Cloudflare Pages |
| `deploy-im-integration.yml` | push main | 部署 IM Worker |
| `deploy-workers.yml`（新增）| push main | 部署 api-gateway Worker |
| `setup-r2.yml`（新增）| workflow_dispatch | 建立 R2 buckets + KV namespaces |
| `backup-to-r2.yml`（新增）| cron 每日 02:00 | Supabase → R2 備份 |

---

## 端對端驗證檢查清單

### GKE 層
- [ ] 所有 pods Running（eco-api, eco-web, eco-ai, postgres, redis）
- [ ] Ingress 有外部 IP
- [ ] `/health` 端點回應 200

### DNS 層
- [ ] `autoecoops.io` → Pages（200 OK）
- [ ] `api.autoecoops.io` → Workers → GKE（200 OK）
- [ ] `app.autoecoops.io` → GKE Ingress（200 OK）

### HTTPS 層
- [ ] TLS 1.3 有效
- [ ] Cloudflare Origin Certificate 有效
- [ ] HSTS 標頭存在

### Supabase 層
- [ ] eco-api 可連接 Supabase（`/api/health` 回應 db: ok）
- [ ] Supabase Auth 端點可達

### Workers 層
- [ ] `api.autoecoops.io/health` → 200
- [ ] Rate Limiting 生效（第 6 次請求 429）
- [ ] R2 存取正常

### GitHub Actions CI
- [ ] IndestructibleEco CI/CD ✅
- [ ] Deploy to GKE eco-staging ✅
- [ ] Deploy Web ✅
- [ ] YAML Governance Lint ✅
