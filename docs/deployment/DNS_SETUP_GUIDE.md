# DNS 設置指南 - autoecoops.io (Cloudflare)

## 域名信息
- **域名**: autoecoops.io
- **DNS 託管**: Cloudflare
- **區域**: Taiwan (asia-east1)

---

## 📋 完整部署流程

### 第 1 步：觸發 Staging 部署

1. **推送到 main 分支觸發部署**:
   ```bash
   cd /workspace/ecosystem
   git add .
   git commit -m "chore: 添加 Ingress 配置並觸發 staging 部署"
   git push origin main
   ```

2. **監控 GitHub Actions**:
   - 前往: https://github.com/machops/ecosystem/actions
   - 查看 CI/CD workflow 執行狀態
   - 等待大約 15-20 分鐘完成

3. **驗證 Staging 部署**:
   ```bash
   # 切換到 staging cluster
   gcloud container clusters get-credentials eco-staging --region asia-east1 --project my-project-ops-1991
   
   # 檢查 pods
   kubectl get pods -n ecosystem-staging
   
   # 檢查 services（重要！）
   kubectl get svc -n ecosystem-staging
   
   # 檢查 Ingress
   kubectl get ingress -n ecosystem-staging
   ```

4. **獲取 Load Balancer IP**:
   ```bash
   kubectl get ingress ecosystem-ingress-staging -n ecosystem-staging
   ```
   記下 `ADDRESS` 欄位的 IP 地址（例如：`35.xxx.xxx.xxx`）

---

### 第 2 步：在 Cloudflare 配置 DNS 記錄（Staging）

1. **登入 Cloudflare Dashboard**:
   - 前往: https://dash.cloudflare.com
   - 選擇 `autoecoops.io` 域名

2. **添加 Staging 前端 DNS 記錄**:
   - 點擊「新增記錄」
   - **類型**: `A`
   - **名稱**: `staging`
   - **IPv4 位址**: 貼上剛取得的 staging IP
   - **代理狀態**: ✅ 橙色雲朵（已代理）- **重要！**
   - **TTL**: 自動
   - 點擊「儲存」

3. **添加 Staging API DNS 記錄**:
   - 點擊「新增記錄」
   - **類型**: `A`
   - **名稱**: `api-staging`
   - **IPv4 位址**: 貼上相同的 staging IP
   - **代理狀態**: ✅ 橙色雲朵（已代理）
   - **TTL**: 自動
   - 點擊「儲存」

4. **驗證 DNS 生效**（等待 1-5 分鐘）:
   ```bash
   # 檢查 DNS 解析
   dig staging.autoecoops.io
   dig api-staging.autoecoops.io
   
   # 或使用線上工具
   # https://dnschecker.org/
   ```

5. **測試 Staging 網站**:
   - 前端: https://staging.autoecoops.io
   - API 健康檢查: https://api-staging.autoecoops.io/health

---

### 第 3 步：部署到 Production

1. **在 GitHub Actions 批准 Production 部署**:
   - 前往: https://github.com/machops/ecosystem/actions
   - 找到剛完成的 CD workflow
   - 點擊「Deploy to Production」作業
   - 點擊「Approve」批准部署

2. **監控 Production 部署**:
   - 等待大約 10-15 分鐘
   - 查看 workflow 完成狀態

3. **驗證 Production 部署**:
   ```bash
   # 切換到 production cluster
   gcloud container clusters get-credentials eco-production --region asia-east1 --project my-project-ops-1991
   
   # 檢查 pods
   kubectl get pods -n ecosystem-production
   
   # 檢查 services
   kubectl get svc -n ecosystem-production
   
   # 檢查 Ingress
   kubectl get ingress -n ecosystem-production
   ```

4. **獲取 Production Load Balancer IP**:
   ```bash
   kubectl get ingress ecosystem-ingress-production -n ecosystem-production
   ```
   記下 `ADDRESS` 欄位的 IP 地址

---

### 第 4 步：在 Cloudflare 配置 DNS 記錄（Production）

1. **添加 Production 前端 DNS 記錄**:
   - 點擊「新增記錄」
   - **類型**: `A`
   - **名稱**: `@` （代表根域名 autoecoops.io）
   - **IPv4 位址**: 貼上 production IP
   - **代理狀態**: ✅ 橙色雲朵（已代理）
   - **TTL**: 自動
   - 點擊「儲存」

2. **添加 Production API DNS 記錄**:
   - 點擊「新增記錄」
   - **類型**: `A`
   - **名稱**: `api`
   - **IPv4 位址**: 貼上 production IP
   - **代理狀態**: ✅ 橙色雲朵（已代理）
   - **TTL**: 自動
   - 點擊「儲存」

3. **可選：添加 www 重定向**:
   - 點擊「新增記錄」
   - **類型**: `CNAME`
   - **名稱**: `www`
   - **目標**: `@` （或 `autoecoops.io`）
   - **代理狀態**: ✅ 橙色雲朵（已代理）
   - **TTL**: 自動
   - 點擊「儲存」

4. **驗證 DNS 生效**（等待 1-5 分鐘）:
   ```bash
   dig autoecoops.io
   dig api.autoecoops.io
   dig www.autoecoops.io
   ```

5. **測試 Production 網站**:
   - 前端: https://autoecoops.io
   - API 健康檢查: https://api.autoecoops.io/health
   - www: https://www.autoecoops.io

---

## 📊 DNS 記錄總結

### Staging 環境
| 子域名 | 類型 | IP/目標 | 代理狀態 |
|--------|------|---------|----------|
| staging.autoecoops.io | A | Staging LB IP | ✅ 已代理 |
| api-staging.autoecoops.io | A | Staging LB IP | ✅ 已代理 |

### Production 環境
| 子域名 | 類型 | IP/目標 | 代理狀態 |
|--------|------|---------|----------|
| autoecoops.io (@) | A | Production LB IP | ✅ 已代理 |
| api.autoecoops.io | A | Production LB IP | ✅ 已代理 |
| www.autoecoops.io | CNAME | autoecoops.io | ✅ 已代理 |

---

## 🔐 SSL 證書配置

### Cloudflare 自動 SSL（推薦）

✅ **好處**:
- 免費的 SSL/TLS 證書
- 自動續期
- 零配置
- DDoS 保護
- CDN 加速

**配置步驟**:
1. 在 Cloudflare Dashboard → SSL/TLS
2. 設置模式為 **「Flexible」** 或 **「Full」**
3. 選擇 **「Always Use HTTPS」**
4. 啟用 **「Automatic HTTPS Rewrites」**

### GKE Managed Certificates（備選方案）

我們的 Kubernetes 配置已經包含 GKE Managed Certificates，它會自動為以下域名提供 SSL:
- staging.autoecoops.io
- api-staging.autoecoops.io
- autoecoops.io
- api.autoecoops.io

**注意**: 如果使用 Cloudflare 代理（橙色雲朵），Cloudflare 會處理 SSL，GKE 證書會被終止在 Cloudflare 邊緣。

---

## 🛠️ 故障排除

### 問題 1: Load Balancer IP 沒有出現
**解決方案**:
```bash
# 檢查 Ingress 狀態
kubectl describe ingress ecosystem-ingress-staging -n ecosystem-staging

# 檢查 events
kubectl get events -n ecosystem-staging --sort-by='.lastTimestamp'

# 等 2-3 分鐘後再檢查
kubectl get ingress -n ecosystem-staging -w
```

### 問題 2: DNS 沒有解析
**解決方案**:
1. 等待 DNS 傳播（可能需要 5-30 分鐘）
2. 清除本地 DNS 快取:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Linux
   sudo systemctl restart systemd-resolved
   
   # Windows
   ipconfig /flushdns
   ```

3. 檢查 Cloudflare DNS 狀態
4. 使用線上工具驗證: https://dnschecker.org/

### 問題 3: 無法訪問網站
**檢查清單**:
```bash
# 1. 檢查 pods 是否運行
kubectl get pods -n ecosystem-staging

# 2. 檢查 pods 日誌
kubectl logs -f deployment/client -n ecosystem-staging
kubectl logs -f deployment/server -n ecosystem-staging

# 3. 檢查 services
kubectl get svc -n ecosystem-staging

# 4. 檢查 ingress
kubectl get ingress -n ecosystem-staging
kubectl describe ingress ecosystem-ingress-staging -n ecosystem-staging

# 5. 測試服務連接
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -n ecosystem-staging -- curl client
```

### 問題 4: SSL 證書錯誤
**解決方案**:
1. 確認 Cloudflare 代理已啟用（橙色雲朵）
2. 檢查 SSL/TLS 模式是否設為 Flexible 或 Full
3. 清除瀏覽器快取並使用無痕模式
4. 等待 SSL 證書生效（可能需要 15-30 分鐘）

---

## ✅ 驗證清單

### Staging 部署驗證
- [ ] GitHub Actions CI/CD 成功完成
- [ ] Pods 全部運行中（3/3）
- [ ] Load Balancer IP 已分配
- [ ] DNS 記錄已添加並生效
- [ ] HTTPS 訪問 staging.autoecoops.io 成功
- [ ] API 健康檢查 https://api-staging.autoecoops.io/health 成功

### Production 部署驗證
- [ ] Production 部署已批准並完成
- [ ] Pods 全部運行中（3/3）
- [ ] Load Balancer IP 已分配
- [ ] DNS 記錄已添加並生效
- [ ] HTTPS 訪問 autoecoops.io 成功
- [ ] API 健康檢查 https://api.autoecoops.io/health 成功
- [ ] www.autoecoops.io 重定向正常

---

## 🚀 快速開始命令

```bash
# 1. 觸發部署
cd /workspace/ecosystem
git add .
git commit -m "chore: 添加 Ingress 配置並觸發 staging 部署"
git push origin main

# 2. 監控部署（等待 15-20 分鐘）
# 前往 https://github.com/machops/ecosystem/actions

# 3. 獲取 staging IP
gcloud container clusters get-credentials eco-staging --region asia-east1 --project my-project-ops-1991
kubectl get ingress -n ecosystem-staging

# 4. 在 Cloudflare 添加 DNS 記錄
# staging.autoecoops.io → [Staging IP]
# api-staging.autoecoops.io → [Staging IP]

# 5. 測試
# 打開瀏覽器訪問:
# https://staging.autoecoops.io
# https://api-staging.autoecoops.io/health

# 6. 批准 production 部署
# 前往 GitHub Actions → Approve Deploy to Production

# 7. 獲取 production IP
gcloud container clusters get-credentials eco-production --region asia-east1 --project my-project-ops-1991
kubectl get ingress -n ecosystem-production

# 8. 在 Cloudflare 添加 production DNS 記錄
# autoecoops.io (@) → [Production IP]
# api.autoecoops.io → [Production IP]

# 9. 測試 production
# https://autoecoops.io
# https://api.autoecoops.io/health
```

---

## 📞 需要幫助？

如果遇到問題:
1. 檢查 GitHub Actions workflow 日誌
2. 查看 Kubernetes pod 日誌
3. 驗證 DNS 設置
4. 截圖錯誤信息並尋求協助

---

**準備好開始部署了嗎？** 🚀

執行第一步：`git push origin main` 觸發 staging 部署！