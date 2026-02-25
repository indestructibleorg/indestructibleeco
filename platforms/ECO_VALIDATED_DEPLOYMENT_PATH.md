# ECO 平台部署路徑與排序 — 驗證結果

**版本**: 1.0.1（修正後）  
**日期**: 2026-02-26  
**狀態**: 已驗證 ✅

---

## 驗證摘要

| 檢查項 | 結果 |
|--------|------|
| 舊命名空間引用殘留 | **0** ✅ |
| `indestructible-eco` 標籤殘留 | **0** ✅ |
| `managed-by: kubectl/kustomize` 殘留 | **0** ✅ |
| 含 `eco_namespace` 的 Manifest | **6/6** ✅ |
| 含 `eco_env_prefix` 的 Manifest | **6/6** ✅ |
| K8s namespace.yaml 對齊 | **6/6** ✅ |
| 端口衝突 | **0** ✅ |

---

## 原始排序（已修正）

原始提出的部署排序存在以下問題：

```
原始排序:
Phase 0  GKE 叢集 + VPC + Workload Identity
Phase 1  platform-seccompops (eco-seccompops)
Phase 2  platform-govops (eco-govops)
Phase 3  platform-dataops (eco-dataops)
Phase 4  platform-observops (eco-observops)
Phase 5  platform-superai (eco-superai)
```

**問題 1**: `platform-core` 缺失 — 所有平台依賴共享內核（Auth、Event Bus、Memory Hub、Policy & Audit、Infra Manager），必須最先部署。

**問題 2**: `platform-observops` 排在第 4 位過晚 — 可觀測性應在安全基線之後、業務平台之前部署，以確保所有後續平台的指標、追蹤、日誌從第一天起即可收集。

**問題 3**: `platform-superai` 缺少 `.platform/manifest.yaml` 和 ECO 命名空間對齊 — 已修正。

---

## 修正後的部署排序

```
Phase 0   GKE 叢集 + VPC + Workload Identity + Artifact Registry
          ↓
Phase 1   platform-core (eco-core)
          Auth Service, Memory Hub, Event Bus, Policy & Audit, Infra Manager
          ↓ 所有平台的根依賴
Phase 2   platform-seccompops (eco-seccompops)
          安全基線、合規掃描、策略執行
          ↓ 安全基線就緒
Phase 3   platform-observops (eco-observops)
          指標收集、告警管理、分散式追蹤、日誌聚合
          ↓ 可觀測性就緒
Phase 4   platform-govops (eco-govops)
          治理策略、合規報告、ETL 管線
          ↓ 治理就緒
Phase 5   platform-dataops (eco-dataops)
          資料管線、異常偵測、證據鏈、語意處理
          ↓ 資料平台就緒
Phase 6   platform-superai (eco-superai)
          量子模擬、量子優化、量子 ML、FPGA 控制
```

---

## 修正理由（依賴關係圖）

```
                    ┌─────────────────┐
                    │  GKE + VPC      │
                    │  (Phase 0)      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  platform-core  │  ← 根依賴（無上游）
                    │  eco-core       │
                    │  Port: 8080     │
                    │  (Phase 1)      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐    │    ┌─────────▼─────────┐
     │ seccompops       │    │    │ observops          │
     │ eco-seccompops   │    │    │ eco-observops      │
     │ Port: 8095       │    │    │ Port: 8094         │
     │ (Phase 2)        │    │    │ (Phase 3)          │
     └────────┬────────┘    │    └─────────┬──────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐    │    ┌─────────▼─────────┐
     │ govops           │    │    │ dataops            │
     │ eco-govops       │    │    │ eco-dataops        │
     │ Port: 8091       │    │    │ Port: 8093         │
     │ (Phase 4)        │    │    │ (Phase 5)          │
     └─────────────────┘    │    └────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ superai          │
                    │ eco-superai      │
                    │ Port: 8096       │
                    │ (Phase 6)        │
                    └─────────────────┘
```

---

## 完整命名空間映射表

| Phase | 平台 | K8s 命名空間 | API 端口 | Metrics 端口 | ECO URI | 環境變數前綴 |
|-------|------|-------------|---------|-------------|---------|------------|
| 0 | GKE Infra | — | — | — | — | — |
| 1 | platform-core | `eco-core` | 8080 | 9080 | `eco-base://k8s/platform-core/namespace/eco-core` | `PLATFORM_CORE_` |
| 2 | platform-seccompops | `eco-seccompops` | 8095 | 9095 | `eco-base://k8s/platform-seccompops/namespace/eco-seccompops` | `PLATFORM_SECCOMPOPS_` |
| 3 | platform-observops | `eco-observops` | 8094 | 9094 | `eco-base://k8s/platform-observops/namespace/eco-observops` | `PLATFORM_OBSERVOPS_` |
| 4 | platform-govops | `eco-govops` | 8091 | 9091 | `eco-base://k8s/platform-govops/namespace/eco-govops` | `PLATFORM_GOVOPS_` |
| 5 | platform-dataops | `eco-dataops` | 8093 | 9093 | `eco-base://k8s/platform-dataops/namespace/eco-dataops` | `PLATFORM_DATAOPS_` |
| 6 | platform-superai | `eco-superai` | 8096 | 9096 | `eco-base://k8s/platform-superai/namespace/eco-superai` | `PLATFORM_SUPERAI_` |

---

## 已修正的問題清單

| # | 問題 | 修正 | 狀態 |
|---|------|------|------|
| 1 | `platform-core` 缺少 `.platform/manifest.yaml` | 已建立，含 eco_namespace | ✅ |
| 2 | `platform-core` 缺少 `k8s/base/namespace.yaml` | 已建立，含 ECO 標籤/註解 | ✅ |
| 3 | `platform-core` 缺少 `.platform/dependencies.yaml` | 已建立 | ✅ |
| 4 | `platform-superai` 命名空間為 `superai`（非 `eco-superai`） | 已修正所有 k8s/argocd/security 檔案 | ✅ |
| 5 | `platform-superai` 缺少 `.platform/manifest.yaml` | 已建立，含 eco_namespace | ✅ |
| 6 | `platform-superai` 缺少 `.platform/dependencies.yaml` | 已建立 | ✅ |
| 7 | `platform-superai` 標籤為 `indestructible-eco` | 已修正為 `eco-base` | ✅ |
| 8 | `platform-superai` managed-by 為 `kustomize` | 已修正為 `argocd` | ✅ |
| 9 | `platform-observops` 缺少 `eco_env_prefix` | 已補充 `PLATFORM_OBSERVOPS_` | ✅ |
| 10 | `platform-observops` 缺少 mandatory_labels/annotations | 已補充 | ✅ |
| 11 | 部署排序缺少 `platform-core` | 已加入 Phase 1 | ✅ |
| 12 | `platform-observops` 排序過晚 | 已調整至 Phase 3（安全基線之後） | ✅ |
| 13 | `platform-eco` 目錄為空 | 保留為未來擴展（非部署目標） | ⚠️ |

---

## `platform-eco` 狀態說明

`platform-eco` 目錄目前為空。根據 `platforms.zip` 中的 `DECENTRALIZED-ARCHITECTURE.md`，此目錄可能用於：
- 平台間的共享配置模板
- ECO 規範的參考實作
- 跨平台整合測試

**此目錄不在部署路徑中，不影響生產環境。**
