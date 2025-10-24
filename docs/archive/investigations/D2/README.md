# D2 Event Investigation Archives

本目錄包含 D2 事件調查的歷史文件，已歸檔以保持主文檔結構清晰。

## 歸檔日期
2025-10-24

## 歸檔原因
這些文件記錄了 D2 事件整合的早期研究和調查過程，具有歷史參考價值，但與當前主要文檔 `docs/development_plans/d2_integration/README.md` 有內容重疊。為避免重複，將早期調查文件歸檔。

## 檔案清單

### 1. D2_INVESTIGATION_COMPLETE_SUMMARY.md (528 行)
**內容**：D2 事件調查的完整總結
- D2 事件定義與標準（3GPP TS 38.331）
- 實施方案評估
- 決策優化策略
- 未來改進方向

**歷史價值**：記錄了 D2 事件整合的初始研究過程

### 2. D2_TEMPORAL_ANALYSIS_FINDINGS.md (345 行)
**內容**：D2 事件時間序列分析結果
- Temporal feature 設計依據
- FSPL-based 預測方法驗證
- 時間窗口優化研究

**歷史價值**：為時間特徵（velocity, predicted RSRP）的設計提供了理論基礎

## 當前主要參考文檔

如需了解 D2 事件的**當前實施狀態**，請參閱：
- **主文檔**：`docs/development_plans/d2_integration/README.md` (700+ 行)
- **配置**：`config/stage6_research_optimization_config.yaml`
- **實現**：`src/stages/stage6_research_optimization/gpp_event_detector.py`

## 相關提案

- Proposal 003：RL Training Pipeline Evaluation
  - Phase 1：Temporal features integration ✅ 已完成
  - 實施時間：2025-10-24

## 學術引用

這些調查文件使用的標準和參考文獻：
- 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a (D2 event definition)
- ITU-R P.525-4 (Free Space Path Loss)
- Badini et al. (2024) IEEE TAES (Velocity features for predictive handover)

---

**注意**：這些文件已不再更新，僅供歷史參考。請以主文檔為準。
