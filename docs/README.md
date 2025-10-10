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
- **[Stage 3: 座標系統轉換層](stages/stage3-signal-analysis.md)** - Skyfield專業轉換
- **[Stage 4: 鏈路可行性評估層](stages/stage4-link-feasibility.md)** - 星座感知篩選
- **[Stage 5: 信號品質分析層](stages/stage5-signal-analysis.md)** - 3GPP/ITU-R標準
- **[Stage 6: 研究數據生成層](stages/stage6-research-optimization.md)** - 3GPP事件+ML

### 📚 專業標準文檔

#### 學術標準與合規
- **[學術合規性標準指南](ACADEMIC_STANDARDS.md)** - 全局學術標準規範 ⭐⭐⭐
- **[參數確定方法論](parameter_determination_methodology.md)** - D2/A5 參數確定方法 (25KB)
- **[三層級數據分析](三層級數據分析與參數選擇依據.md)** - 數據層級選擇依據 (14KB)

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

## 📂 文檔歷史歸檔

### 歸檔文檔位置
- **[歸檔說明](archive/README.md)** - 歸檔文檔索引與說明
  - `archive/reports/` - 一次性分析報告
  - `archive/retrospectives/` - 事後回顧文檔
  - `archive/clarifications/` - 歷史澄清文檔
  - `archive/development/` - 已整合的流程文檔
- **注意**: 歸檔文檔僅供參考，請勿用於開發！使用最新的活躍文檔。

## ⚠️ 開發者重要提醒

### ✅ 正確的文檔使用
1. **架構理解**: 先讀 `stages/STAGES_OVERVIEW.md`
2. **階段開發**: 參考對應的 `stages/stage*-*.md`
3. **標準合規**: 遵循各項專業標準文檔

### ❌ 禁止使用的文檔
- `archives/` 目錄下的任何文檔
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
**最後更新**: 2025-10-10 (文檔重組完成)
**維護狀態**: ✅ 當前版本，積極維護

## 📋 最近更新

### 2025-10-10 - 文檔重組與整合
- ✅ 創建 `development/CONTRIBUTING.md` - 整合所有開發流程指南
- ✅ 歸檔歷史文檔至 `archive/` (6 個文件，完整保留)
- ✅ 整合流程文檔: 3 個分散文檔 → 1 個完整指南
- ✅ 重命名模糊文件: `ts.md` → `3GPP_TS38331_EVENT_DEFINITIONS.md`
- ✅ 移動驗證文檔: `distance_calculation_validation.md` → `stages/`
- ✅ 整理結果: 主目錄文檔減少 43.75% (16→9)，活躍文檔減少 17.9%
- ✅ 零刪除政策: 所有文檔完整保留在 `archive/`

### 2025-10-02 - 文檔整理
- ✅ 移除重複的學術標準文件 (已整合至 `ACADEMIC_STANDARDS.md`)
- ✅ 合併重複的架構文檔 (`data_processing_flow.md` → `stages/STAGES_OVERVIEW.md`)
- ✅ 歸檔 Stage 4/6 重構文檔 (重構已於 2025-09-30 完成)
- ✅ 歸檔學術合規性審計報告 (問題已全部修復)