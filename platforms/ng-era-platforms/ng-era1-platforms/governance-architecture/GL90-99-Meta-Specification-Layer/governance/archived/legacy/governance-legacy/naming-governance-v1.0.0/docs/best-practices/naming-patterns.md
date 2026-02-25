# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# 命名模式最佳實踐 v1.0.0

## 概述

本文檔提供命名治理的最佳實踐模式和常見場景的解決方案。

---

## 一、標準命名模式

### 1.1 應用部署

#### 標準格式
```
{environment}-{app}-{resource_type}-{version}[-{suffix}]
```

#### 示例

```yaml
# 部署
prod-payment-deploy-v1.2.3
staging-order-deploy-v1.0.0-canary
dev-inventory-deploy-v0.9.0-beta

# 服務
prod-payment-svc-v1.2.3
staging-order-svc-v1.0.0

# ConfigMap
prod-payment-cm-v1.2.3
```

### 1.2 微服務架構

#### 服務命名
```
{environment}-{domain}-{service}-{resource_type}-{version}
```

#### 示例

```yaml
# 用戶服務
prod-user-auth-svc-v2.1.0
prod-user-profile-svc-v2.1.0

# 訂單服務
prod-order-process-svc-v1.5.0
prod-order-payment-svc-v1.5.0

# 庫存服務
prod-inventory-manage-svc-v1.2.0
prod-inventory-notify-svc-v1.2.0
```

### 1.3 多租戶架構

#### 租戶隔離命名
```
{environment}-{tenant}-{app}-{resource_type}-{version}
```

#### 示例

```yaml
# 租戶 A
prod-clienta-payment-deploy-v1.2.3
prod-clienta-order-deploy-v1.2.3

# 租戶 B
prod-clientb-payment-deploy-v1.2.3
prod-clientb-order-deploy-v1.2.3
```

---

## 二、環境策略

### 2.1 環境分層

#### 推薦環境列表

| 環境 | 用途 | 命名前綴 | 生存週期 |
|------|------|----------|----------|
| `dev` | 開發測試 | `dev-` | 短期（數天） |
| `test` | 集成測試 | `test-` | 中期（數週） |
| `staging` | 預發布 | `staging-` | 中期（數週） |
| `prod` | 生產環境 | `prod-` | 長期（數月） |
| `learn` | 學習環境 | `learn-` | 短期（數天） |

### 2.2 藍綠部署

#### 藍環境
```yaml
prod-payment-blue-deploy-v1.2.3
prod-payment-blue-svc-v1.2.3
```

#### 綠環境
```yaml
prod-payment-green-deploy-v1.3.0
prod-payment-green-svc-v1.3.0
```

### 2.3 金絲雀發布

#### 金絲雀版本
```yaml
prod-payment-deploy-v1.3.0-canary
prod-payment-svc-v1.3.0-canary
```

#### 穩定版本
```yaml
prod-payment-deploy-v1.2.3
prod-payment-svc-v1.2.3
```

---

## 三、版本號管理

### 3.1 SemVer 規範

#### 格式
```
v{major}.{minor}.{patch}[-{prerelease}][+{buildmetadata}]
```

#### 示例

```yaml
# 穩定版本
v1.0.0
v1.2.3
v2.0.0

# 預發布版本
v1.0.0-alpha
v1.0.0-beta.1
v1.0.0-rc.1
v1.2.3-canary

# 帶構建元數據（不推薦用於 K8s）
v1.0.0+20130313144700
v1.0.0-alpha+001
```

### 3.2 版本升級策略

#### Major 版本（不兼容的 API 變更）
```yaml
v1.0.0 → v2.0.0
prod-api-deploy-v2.0.0
```

#### Minor 版本（向後兼容的功能新增）
```yaml
v1.0.0 → v1.1.0
prod-api-deploy-v1.1.0
```

#### Patch 版本（向後兼容的問題修復）
```yaml
v1.0.0 → v1.0.1
prod-api-deploy-v1.0.1
```

### 3.3 預發布標識

#### 常用標識
- `alpha`: 內部測試
- `beta`: 公開測試
- `rc`: 發布候選
- `canary`: 金絲雀發布

#### 示例
```yaml
v1.0.0-alpha.1
v1.0.0-beta.2
v1.0.0-rc.1
v1.2.3-canary
```

---

## 四、標籤最佳實踐

### 4.1 必要標籤

#### 標準標籤集
```yaml
metadata:
  labels:
    app.kubernetes.io/name: payment
    app.kubernetes.io/managed-by: platform-team
    environment: prod
    tenant: finance
    version: v1.2.3
```

### 4.2 推薦標籤

#### 額外資訊標籤
```yaml
metadata:
  labels:
    # 業務標籤
    business-unit: finance
    cost-center: cc-12345
    
    # 運維標籤
    owner: team-payment
    support-level: tier-1
    
    # 監控標籤
    monitored: "true"
    alerting: "true"
```

### 4.3 標籤選擇器

#### 常用選擇器模式

```yaml
# 按應用選擇
selector:
  matchLabels:
    app.kubernetes.io/name: payment

# 按環境選擇
selector:
  matchLabels:
    environment: prod

# 按租戶選擇
selector:
  matchLabels:
    tenant: finance

# 組合選擇
selector:
  matchExpressions:
    - key: environment
      operator: In
      values: ["prod", "staging"]
    - key: app.kubernetes.io/name
      operator: In
      values: ["payment", "order"]
```

---

## 五、常見場景

### 5.1 數據庫命名

#### 主數據庫
```yaml
prod-postgres-leader-v1.0.0
prod-mysql-primary-v1.0.0
```

#### 從庫
```yaml
prod-postgres-replica-v1.0.0
prod-mysql-follower-v1.0.0
```

#### 備份
```yaml
prod-postgres-backup-v1.0.0-daily
prod-postgres-backup-v1.0.0-weekly
```

### 5.2 消息隊列

#### Kafka Topic
```yaml
prod-payment-events-v1.0.0
prod-order-events-v1.0.0
```

#### RabbitMQ Queue
```yaml
prod-payment-queue-v1.0.0
prod-order-queue-v1.0.0
```

### 5.3 緩存服務

#### Redis
```yaml
prod-redis-leader-v1.0.0
prod-redis-replica-v1.0.0
```

#### Memcached
```yaml
prod-memcached-v1.0.0
```

### 5.4 Ingress 配置

#### 單一服務
```yaml
prod-payment-ing-v1.2.3
```

#### 多路徑
```yaml
prod-api-ing-v1.0.0
```

### 5.5 ConfigMap 與 Secret

#### 配置文件
```yaml
prod-payment-cm-v1.2.3
prod-payment-config-v1.2.3
```

#### 密鑰
```yaml
prod-payment-secret-v1.2.3
prod-payment-db-credentials-v1.2.3
```

---

## 六、跨環境遷移

### 6.1 Dev → Staging → Prod

#### 環境升級
```bash
# 生成各環境的資源名稱
python naming_generator.py \
  --environment dev \
  --app payment \
  --version v1.2.3 \
  --tenant finance
# 輸出: dev-payment-deploy-v1.2.3

python naming_generator.py \
  --environment staging \
  --app payment \
  --version v1.2.3 \
  --tenant finance
# 輸出: staging-payment-deploy-v1.2.3

python naming_generator.py \
  --environment prod \
  --app payment \
  --version v1.2.3 \
  --tenant finance
# 輸出: prod-payment-deploy-v1.2.3
```

### 6.2 版本回滾

#### 回滾到前一版本
```yaml
# 當前版本
prod-payment-deploy-v1.3.0

# 回滾到前一版本
prod-payment-deploy-v1.2.3
```

#### 金絲雀回滾
```yaml
# 金絲雀失敗，回滾
prod-payment-deploy-v1.3.0-canary → prod-payment-deploy-v1.2.3
```

---

## 七、命名衝突解決

### 7.1 常見衝突場景

#### 問題 1: 相同名稱不同團隊
```yaml
# 衝突
prod-payment-deploy-v1.0.0 (Team A)
prod-payment-deploy-v1.0.0 (Team B)
```

#### 解決方案: 添加域前綴
```yaml
prod-finance-payment-deploy-v1.0.0 (Team A)
prod-commerce-payment-deploy-v1.0.0 (Team B)
```

### 7.2 命名空間隔離

#### 使用命名空間避免衝突
```yaml
# 命名空間: finance
metadata:
  name: prod-payment-deploy-v1.0.0
  namespace: finance

# 命名空間: commerce
metadata:
  name: prod-payment-deploy-v1.0.0
  namespace: commerce
```

### 7.3 租戶隔離

#### 多租戶場景
```yaml
# 租戶 A
prod-tenanta-payment-deploy-v1.0.0

# 租戶 B
prod-tenantb-payment-deploy-v1.0.0
```

---

## 八、反模式（應避免）

### 8.1 避免的模式

#### ❌ 使用大寫字母
```yaml
PROD-Payment-Deploy-v1.2.3
```

#### ✅ 正確做法
```yaml
prod-payment-deploy-v1.2.3
```

### 8.2 避免過長的名稱

#### ❌ 過長
```yaml
prod-payment-service-deployment-with-very-long-name-v1.2.3
# 長度: 64+ 字元
```

#### ✅ 簡潔
```yaml
prod-payment-deploy-v1.2.3
# 長度: 25 字元
```

### 8.3 避免特殊字元

#### ❌ 特殊字元
```yaml
prod-payment_deploy-v1.2.3
prod-payment.deploy-v1.2.3
prod_payment_deploy_v1.2.3
```

#### ✅ 使用連字符
```yaml
prod-payment-deploy-v1.2.3
```

### 8.4 避免無版本號

#### ❌ 缺少版本號
```yaml
prod-payment-deploy
```

#### ✅ 包含版本號
```yaml
prod-payment-deploy-v1.2.3
```

### 8.5 避免硬編碼環境

#### ❌ 硬編碼
```yaml
production-payment-deploy-v1.2.3
```

#### ✅ 使用標準前綴
```yaml
prod-payment-deploy-v1.2.3
```

---

## 九、遷移指南

### 9.1 舊系統遷移

#### 步驟 1: 現狀分析
```bash
# 掃描現有資源
python naming_validator.py \
  --directory legacy-k8s \
  --output legacy-audit.json
```

#### 步驟 2: 制定遷移計畫
```yaml
migration_plan:
  phase_1:
    target: "critical-services"
    action: "rename-following-standard"
  
  phase_2:
    target: "important-services"
    action: "rename-following-standard"
  
  phase_3:
    target: "other-services"
    action: "rename-following-standard"
```

#### 步驟 3: 執行遷移
```bash
# 生成新名稱
python naming_generator.py \
  --environment prod \
  --app payment \
  --version v1.2.3 \
  --tenant finance
```

#### 步驟 4: 驗證
```bash
# 驗證新命名
python naming_validator.py \
  --directory migrated-k8s \
  --strict
```

### 9.2 漸進式重命名

#### 使用 Ingress 實現無停機遷移
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prod-payment-ing-v1.2.3
spec:
  rules:
  - host: payment.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prod-payment-svc-v1.2.3  # 新服務
            port:
              number: 80
```

---

## 十、工具使用示例

### 10.1 批量重命名

#### 腳本示例
```bash
#!/bin/bash
# batch-rename.sh

OLD_PREFIX="legacy-payment"
NEW_PREFIX="prod-payment-deploy-v1.2.3"

for file in k8s/*.yaml; do
  sed -i "s/$OLD_PREFIX/$NEW_PREFIX/g" "$file"
done
```

### 10.2 自動化驗證

#### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

python naming_validator.py \
  --directory k8s \
  --strict

if [ $? -ne 0 ]; then
  echo "❌ 命名驗證失敗，請修正後再提交"
  exit 1
fi
```

### 10.3 CI/CD 集成

#### GitHub Actions
```yaml
- name: Validate Naming
  run: |
    python naming_validator.py \
      --directory k8s \
      --strict
```

---

## 十一、監控與稽核

### 11.1 關鍵指標

#### 合規率
```promql
naming:compliance:rate * 100
```

#### 違規數量
```promql
naming:violations:total
```

### 11.2 稽核報告

#### 生成報告
```bash
python naming_validator.py \
  --directory k8s \
  --output audit-report.json \
  --format json
```

---

## 十二、總結

### 核心原則

1. **一致性**: 全組織使用統一的命名標準
2. **可讀性**: 名稱應清晰表達資源用途
3. **可追溯性**: 包含版本號和環境信息
4. **可維護性**: 易於理解和維護
5. **自動化**: 支持自動化檢查和生成

### 最佳實踐清單

- [ ] 使用小寫字母和連字符
- [ ] 包含環境前綴
- [ ] 包含應用名稱
- [ ] 包含資源類型
- [ ] 包含版本號
- [ ] 添加必要標籤
- [ ] 定期執行稽核
- [ ] 使用 CI/CD 驗證
- [ ] 設置監控警報
- [ ] 文檔化命名規範

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-01-18