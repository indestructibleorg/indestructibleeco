<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# AI即時執行系統 - INSTANT 標準操作指南

> **目標**：3 分鐘內完成全堆疊、0 次人工介入、64-256 代理並行、關鍵操作 <100ms  
> **範圍**：對齊 `instant_execution_engine_v2.py`、`parallel-agents-config.yaml`、`event-triggers-config.yaml`

---

【1. 待完成功能清單】
- [P0] 事件觸發路由器：統一 Git/Webhook/監控事件 → Pipeline 任務，入口延遲 <100ms  
  - 依賴：workspace/config/instant-execution/event-triggers-config.yaml, workspace/src/autonomous/deployment/instant_execution_engine_v2.py  
  - 預計執行時間：<3分鐘
- [P0] 並行代理池調度：維持 64-256 Agent 池，動態分片 + 自動擴縮  
  - 依賴：workspace/config/instant-execution/parallel-agents-config.yaml, InstantExecutionEngine.ParallelAgentPool  
  - 預計執行時間：<3分鐘
- [P0] 延遲 / 自治度守門：每階段 SLA（<=100ms/500ms/5s）+ 0 人工介入自動回滾  
  - 依賴：engine status hooks, governance latency gates  
  - 預計執行時間：<3分鐘
- [P1] 即時診斷急救站：秒級瓶頸定位、熱點輸出 JSON  
  - 依賴：engine telemetry, validation-report.json  
  - 預計執行時間：<3分鐘
- [P1] 快速修復路徑：診斷 → Auto-fix → 藍綠部署全自動  
  - 依賴：instant_execution_pipeline.py, deployer-agent  
  - 預計執行時間：<3分鐘
- [P2] 儀表板與知識同步：延遲/並行度/自治度實時可視化，結果寫回 docs/knowledge-health  
  - 依賴：metrics sink, docs 更新流程  
  - 預計執行時間：<3分鐘

---

【2. 問題診斷】
| 問題類型 | 症狀 | 診斷方法 | 即時解決方案 |
| --- | --- | --- | --- |
| 延遲超標 | 單階段 >100ms/500ms/5s | `--mode status` 檢查 `latency_breakdown_ms` | 自動：提升並行度並重放；手動：`--mode optimize --input '{"target":"latency","threshold":"100ms"}'` |
| 並行度不足 | Active agents <64 | 查看 status `active_agents` / config | 啟動 auto-scaling；如仍不足，將 `min_agents` 提升至 64 後重啟池 |
| 自治度下降 | `human_intervention_count` >0 | status 中 autonomy 指標 | 觸發自動回滾並重新分派全 AI 流程 |
| 事件漏處理 | 事件無對應執行 | 檢查 `event-triggers-config.yaml` mapping | 新增 mapping，`--mode feature --input ...` 重送事件 |
| 修復未生效 | hotfix 成功率 <99% | 查看 `validation-report.json` | 提升 validation 並行度至 32，重新部署藍綠 |

備註：並行度（含 validation 32）、入口採樣率與分片延遲目標均可在 `parallel-agents-config.yaml` / `event-triggers-config.yaml` 調整。

---

【3. 深度細節補充】
模塊名稱：事件驅動路由層  
- 技術選型：Python asyncio + config 驅動觸發器  
- 實現細節：  
  - `event-triggers-config.yaml` 定義 trigger 到 pipeline mapping  
  - router 將事件封裝為 `feature/fix/optimization` 任務  
  - 入口採樣率 100%（預設，可按流量在配置下調）  
- 關鍵決策：僅允許二元狀態（已實現/未實現），超時自動回滾

模塊名稱：Parallel Agent Pool  
- 技術選型：配置化 Agent 池（64-256），並行度由負載自適應  
- 實現細節：  
  - `parallel-agents-config.yaml` 設置 min/max  
  - engine 依任務類型拆分分析/生成/驗證/部署子任務並行執行  
- 關鍵決策：預熱池，避免冷啟動；分片阻塞目標 <50ms（性能基線，可依場景調整）

模塊名稱：治理與觀測  
- 技術選型：SLA Gate + 自治度 Gate + 事件審計  
- 實現細節：status API 回傳 latency/autonomy/parallelism；失敗時立即 auto-alert + scale-up；治理檢查結果寫回 validation-report  
- 關鍵決策：所有檢查事件驅動（非輪詢），不允許人工批准流程

---

【4. 行動建議】
步驟1：熱身與配置載入（可並行預熱 Agent）  
- 執行條件：配置存在 (`parallel-agents-config.yaml`, `event-triggers-config.yaml`)  
- 預期結果：Agent 池活躍數 ≥64，入口延遲 <100ms  
- 驗證方法：`python3 workspace/src/autonomous/deployment/instant_execution_engine_v2.py --mode status` 觀察 `active_agents`、`ingest_latency_ms`  
- 執行時間：<30s

步驟2：並行交付（feature/fix/optimization）  
- 執行條件：接收到事件或提供 `--input` JSON  
- 預期結果：全流程 <3 分鐘，單階段延遲符合門檻，成功率 ≥95%  
- 驗證方法：`--mode feature|fix|optimize` 執行後檢查 `total_latency_ms`、`success=true`，並確認 validation-report.json 生成  
- 執行時間：<90s（64-256 並行）

步驟3：即時診斷與自愈  
- 執行條件：延遲/成功率異常、自治度下降  
- 預期結果：定位瓶頸、觸發 auto-fix、藍綠部署完成且 rollback-ready  
- 驗證方法：`--mode fix --input '{"error_id":"AUTO","severity":"high"}'`，查看 status 中 `auto_healing=true`、新部署版本標記，失敗自動回滾  
- 執行時間：<60s

步驟4：觀測與知識同步（與步驟3可並行）  
- 執行條件：部署或修復完成  
- 預期結果：延遲/並行/自治度指標寫入報表，docs/knowledge-health 更新  
- 驗證方法：生成或更新 validation-report.json，並同步到報表存放目錄；確認最新時間戳  
- 執行時間：<30s

> 並行提示：步驟1 預熱可與步驟4 報表同步並行；步驟2/3 由 agent 池自動分片並行執行，無需人工干預。
