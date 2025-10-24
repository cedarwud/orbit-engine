# 📖 Orbit Engine 文檔中心

## 🎯 v3.0架構文檔導航 (當前版本)

### 🚀 必讀核心文檔

#### 0. 貢獻指南 (開發必讀) ⭐⭐⭐
- **[CONTRIBUTING.md](development/CONTRIBUTING.md)** - 完整貢獻指南
  - 學術合規性原則
  - 代碼注釋標準
  - 文檔同步流程
  - 代碼審查清單
  - 提交流程規範

#### 1. 架構總覽 (入門必讀)
- **[六階段系統總覽](stages/STAGES_OVERVIEW.md)** - v3.0完整架構概覽 ⭐⭐⭐
- **[研究最終目標](final.md)** - NTPU衛星通訊研究目標
- **[快速開始指南](QUICK_START.md)** - 零配置執行指南

#### 2. 階段詳細規格 (開發必讀)
- **[Stage 1: TLE數據載入層](stages/stage1-specification.md)** - 獨立時間基準設計
- **[Stage 2: 軌道狀態傳播層](stages/stage2-orbital-computing.md)** - ✅ **已重構 - Skyfield 直接實現**
- **[Stage 3: 座標系統轉換層](stages/stage3-coordinate-transformation.md)** - Skyfield專業轉換
- **[Stage 4: 鏈路可行性評估層](stages/stage4-link-feasibility.md)** - 星座感知篩選
- **[Stage 5: 信號品質分析層](stages/stage5-signal-analysis.md)** - 3GPP/ITU-R標準
- **[Stage 6: 研究數據生成層](stages/stage6-research-optimization.md)** - 3GPP事件+ML

### 📚 專業標準文檔

#### 學術標準與合規
- **[學術合規性標準指南](ACADEMIC_STANDARDS.md)** - 全局學術標準規範 ⭐⭐⭐
- **[參數確定方法論](parameter_determination_methodology.md)** - D2/A5 參數確定方法 (25KB)
- **[三層級數據分析](hierarchical_data_analysis.md)** - 數據層級選擇依據 (14KB)

#### 技術標準規範
- **[衛星換手標準](satellite_handover_standards.md)** - 3GPP NTN標準實現 (26KB)
- **[3GPP 事件定義](3GPP_TS38331_EVENT_DEFINITIONS.md)** - 3GPP TS 38.331 事件規範
- **[軌道週期分析標準](orbital_period_analysis_standards.md)** - 軌道分析標準
- **[距離計算驗證](stages/distance_calculation_validation.md)** - 計算精度標準

#### Stage 驗證與合規
- **[Stage 4 驗證矩陣](stages/STAGE4_VERIFICATION_MATRIX.md)** - 驗證狀態唯一真相來源
- **[Stage 6 合規清單](stages/STAGE6_COMPLIANCE_CHECKLIST.md)** - 學術合規檢查清單

### 🛠️ 開發指南
- **[CONTRIBUTING.md](development/CONTRIBUTING.md)** - 完整貢獻指南 ⭐
- **[代碼審查清單](development/CODE_REVIEW_CHECKLIST.md)** - Code Review 標準
- **[元數據一致性指南](development/METADATA_CONSISTENCY_GUIDE.md)** - 元數據規範

### 🏗️ 架構與數據組織
- **[TLE 數據架構](TLE_DATA_ARCHITECTURE.md)** - TLE 數據組織與遷移 (7.8KB)
  - Space-Track.org 數據源管理
  - Starlink/OneWeb 目錄結構
  - 與 orbit-engine 的集成方式

### 📊 RL 訓練支援
- **[handover-rl 項目](../../handover-rl/)** - RL 訓練框架（讀取 orbit-engine Stage 4-6 輸出）
- **訓練數據**: orbit-engine 產生的優化池（~100 顆衛星）用於 RL 環境

### 📦 歷史文檔歸檔

#### 架構分析歸檔（2025-10-24）
- **[Architecture Analysis Archive](archive/architecture_analysis_2025/)** - 代碼庫結構詳細分析（8 個文件，150KB，5,377 行）
  - 記錄 103 個 Python 文件的使用狀態分析（97.1% 使用率）
  - 包含執行流程、階段詳細、驗證系統、支援模組等詳細分析
  - 歷史快照價值，日常開發請參考 `architecture/README.md` + `architecture/00_OVERVIEW.md`

#### 已完成提案歸檔（2025-10-24）
- **[Completed Proposals Archive](archive/proposals_completed/)** - 已完成並實施的提案文檔（3 個提案，37 個文件，628KB）
  - **[Proposal 001: Stage 4 軌道面多樣性](archive/proposals_completed/001-stage4-orbital-diversity/)** (7 個文件，96KB)
    - ✅ 已實現但未啟用（文獻研究不支持）
    - Stage 4: 軌道面多樣性篩選邏輯
  - **[Proposal 002: 訓練數據多樣性增強](archive/proposals_completed/002-training-data-diversity-enhancement/)** (15 個文件，280KB)
    - ✅ 已完成 (2025-10-22)，功能預設禁用 (`scenario_diversity.enabled = false`)
    - Stage 5: 動態傳播條件（三態 Markov + Loo 通道）
    - Stage 6: 流量類型多樣性 + 衛星負載多樣性
  - **[Proposal 003: RL Training Pipeline](archive/proposals_completed/003-rl-training-pipeline-evaluation/)** (15 個文件，252KB)
    - ✅ 已完成 (2025-10-23)，4 階段全部完成
    - ML Data Generator + DQN Baseline + Training Pipeline + Evaluation Framework

#### 文檔清理報告歸檔（2025-10-24）
- **[Cleanup Reports](archive/cleanup_reports/2025-10-24/)** - 兩輪文檔整理報告（4 個文件，17.6KB）
  - DOCUMENTATION_CLEANUP_RECOMMENDATIONS.md - 第一輪分析
  - DOCUMENTATION_DEEP_CLEANUP_ROUND2.md - 第二輪深度分析
  - 清理效益: 86 → 35 個活躍文檔 (-59.3%)

#### 廢棄文檔歸檔（2025-10-24）
- **[Deprecated Archive](archive/deprecated/)** - 已廢棄但保留的文檔
  - proposal_003_v1_deprecated.md (30KB) - Proposal 003 舊版（已被結構化文檔取代）

#### D2 事件調查歸檔（2025-10-24）
- **[D2 Investigation Archive](archive/investigations/D2/)** - D2 事件整合的早期調查文件
  - D2_INVESTIGATION_COMPLETE_SUMMARY.md - 完整調查總結
  - D2_TEMPORAL_ANALYSIS_FINDINGS.md - 時間序列分析結果
  - 當前主文檔：[D2 Integration](development_plans/d2_integration/README.md)

#### 問題修復記錄歸檔
- **[RSRP 截斷問題審查](archive/fixes/CODE_REVIEW_RSRP_CLIPPING_BUGS.md)** - 信號計算修復記錄
- **[RSRP 修復摘要](archive/fixes/FIX_SUMMARY_RSRP_CLIPPING.md)** - 問題分析與解決方案
- **[TLE 數據遷移完成](archive/migrations/MIGRATION_COMPLETE.md)** - 2025-10-20 遷移記錄

## 🎯 v3.0核心特點

### 概念修正 (vs v2.0)
- **Stage 2**: ❌ 可見性篩選 → ✅ 軌道狀態傳播 (TEME座標輸出)
- **Stage 3**: ❌ 信號分析 → ✅ 座標系統轉換 (WGS84地理座標)
- **Stage 4**: ✅ 全新設計 - 鏈路可行性評估 (星座感知篩選)
- **Stage 5**: ✅ 重新定位 - 信號品質分析 (3GPP/ITU-R標準)

### 學術標準嚴格合規 ✅ **Stage 2 實測達成**
- **Grade A++ 強制要求**: 杜絕所有簡化算法和估算值
- **🚀 專業庫直接實現**: Skyfield 直接軌道計算 (183% 效能提升)
- **📊 NASA JPL 精度**: 軌道距離 6,716-7,579km，速度 7.253-7.699km/s
- **✅ 零失敗率驗證**: 9,040顆衛星 100% 成功處理，84秒完成
- **國際標準**: 3GPP TS 38.331, ITU-R P.618, IAU 2000/2006
- **時間基準**: 每筆TLE記錄獨立epoch_datetime

### 研究目標完全對齊
- **NTPU特定**: 24°56'39"N 121°22'17"E 精確地面站
- **星座感知**: Starlink (5°) vs OneWeb (10°) 差異化門檻
- **3GPP NTN**: A4/A5/D2事件完整支援
- **強化學習**: DQN/A3C/PPO/SAC多算法訓練數據

## ⚠️ 開發者重要提醒

### ✅ 正確的文檔使用
1. **架構理解**: 先讀 `stages/STAGES_OVERVIEW.md`
2. **階段開發**: 參考對應的 `stages/stage*-*.md`
3. **標準合規**: 遵循各項專業標準文檔

### ❌ 禁止使用的文檔
- 任何標示為 v2.0 的文檔
- 任何與當前 v3.0 定義衝突的文檔

### 🔍 快速查找
- **如何貢獻**: `development/CONTRIBUTING.md` ⭐
- **概念問題**: `stages/STAGES_OVERVIEW.md`
- **實現細節**: 對應階段的詳細規格文檔
- **標準合規**: `ACADEMIC_STANDARDS.md`
- **驗證狀態**: `stages/STAGE4_VERIFICATION_MATRIX.md`, `stages/STAGE6_COMPLIANCE_CHECKLIST.md`
- **技術標準**: 對應的專業標準文檔
- **開發工具**: `../tools/` - 學術合規檢查器等工具

---

**文檔版本**: v3.0
**最後更新**: 2025-10-24 (文檔深度清理 - 第二輪優化)
**維護狀態**: ✅ 當前版本，積極維護

## 📋 最近更新

### 2025-10-24 - 文檔深度清理（兩輪優化完成）
**第一輪（保守歸檔）**:
- ✅ 修正 Proposal 002 狀態標記（規劃中 → 已完成但禁用）
- ✅ 歸檔架構分析文檔（8 個文件，150KB）至 `archive/architecture_analysis_2025/`
- ✅ 歸檔已完成 Proposal 002（15 個文件，280KB）至 `archive/proposals_completed/`
- ✅ 結果：86 → 58 個活躍文檔 (-27.5%)

**第二輪（深度清理）**:
- ✅ 修正 Proposal 003 狀態矛盾（README 說規劃中，實際全部完成）
- ✅ 歸檔 Proposal 001（7 個文件，96KB）- 已實現但未啟用
- ✅ 歸檔 Proposal 003（15 個文件，252KB）- 4 階段全部完成
- ✅ 歸檔臨時清理報告（4 個文件，17.6KB）至 `archive/cleanup_reports/`
- ✅ 歸檔廢棄文檔（1 個文件，30KB）至 `archive/deprecated/`
- ✅ 結果：58 → 35 個活躍文檔 (-39.7%)

**總效益**:
- **活躍文檔**: 86 → 35 個 **(-59.3%)**
- **歸檔文檔**: 6 → 56 個 (+833%)
- **Proposals 主目錄**: 3 個 → 0 個（全部已完成歸檔）
- **清理報告**: 已歸檔至 `archive/cleanup_reports/2025-10-24/`

### 2025-10-21 - 數據驅動閾值與 RL 訓練支援
- ✅ 更新 Stage 6 文檔閾值（A4/A5 基於 48,000+ 樣本統計）
- ✅ 新增「數據驅動閾值設計」章節
- ✅ 新增 TLE 數據架構文檔索引
- ✅ 新增 RL 訓練配置文檔索引
- ✅ 歸檔 RSRP 修復記錄至 `archive/fixes/`
- ✅ 歸檔 TLE 遷移記錄至 `archive/migrations/`

### 2025-10-16 - 文檔清理與優化
- ✅ 刪除過時重構文檔 (`docs/refactoring/` 整個目錄，660KB)
- ✅ 刪除臨時測試報告 (`FINAL_VERIFIED_METRICS_20251010.md`)
- ✅ 刪除過時歸檔文檔 (`docs/archive/` 整個目錄，84KB)
- ✅ 修正損壞鏈接 (三層級數據分析)
- ✅ 清理結果: 釋放 ~837KB，文檔更清晰易維護

### 2025-10-10 - 文檔重組與整合
- ✅ 創建 `development/CONTRIBUTING.md` - 整合所有開發流程指南
- ✅ 整合流程文檔: 3 個分散文檔 → 1 個完整指南
- ✅ 重命名模糊文件: `ts.md` → `3GPP_TS38331_EVENT_DEFINITIONS.md`
- ✅ 移動驗證文檔: `distance_calculation_validation.md` → `stages/`

### 2025-10-02 - 文檔整理
- ✅ 移除重複的學術標準文件 (已整合至 `ACADEMIC_STANDARDS.md`)
- ✅ 合併重複的架構文檔 (`data_processing_flow.md` → `stages/STAGES_OVERVIEW.md`)
- ✅ 歸檔 Stage 4/6 重構文檔 (重構已於 2025-09-30 完成)
- ✅ 歸檔學術合規性審計報告 (問題已全部修復)