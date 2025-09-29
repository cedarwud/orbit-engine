# 📖 Orbit Engine 文檔中心

## 🎯 v3.0架構文檔導航 (當前版本)

### 🚀 必讀核心文檔

#### 1. 架構總覽 (入門必讀)
- **[六階段系統總覽](stages/STAGES_OVERVIEW.md)** - v3.0完整架構概覽 ⭐⭐⭐
- **[研究最終目標](final.md)** - NTPU衛星通訊研究目標

#### 2. 階段詳細規格 (開發必讀)
- **[Stage 1: TLE數據載入層](stages/stage1-specification.md)** - 獨立時間基準設計
- **[Stage 2: 軌道狀態傳播層](stages/stage2-orbital-computing.md)** - ✅ **已重構 - Skyfield 直接實現**
- **[Stage 3: 座標系統轉換層](stages/stage3-signal-analysis.md)** - Skyfield專業轉換
- **[Stage 4: 鏈路可行性評估層](stages/stage4-link-feasibility.md)** - 星座感知篩選
- **[Stage 5: 信號品質分析層](stages/stage5-signal-analysis.md)** - 3GPP/ITU-R標準
- **[Stage 6: 研究數據生成層](stages/stage6-research-optimization.md)** - 3GPP事件+ML

### 📚 專業標準文檔

#### 學術標準與合規
- **[學術標準澄清](academic_standards_clarification.md)** - Grade A標準定義
- **[學術數據標準](academic_data_standards.md)** - 數據品質要求
- **[距離計算驗證](distance_calculation_validation.md)** - 計算精度標準

#### 技術標準規範
- **[衛星換手標準](satellite_handover_standards.md)** - 3GPP NTN標準實現
- **[軌道週期分析標準](orbital_period_analysis_standards.md)** - 軌道分析標準
- **[數據處理流程](data_processing_flow.md)** - 系統數據流設計

### 🔧 技術規格
- **[3GPP技術規格](ts.md)** - 3GPP TS 38.331標準實現

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

### 歷史文檔位置
- **[歷史歸檔區](archives/README.md)** - v2.0文檔和廢棄文檔
- **注意**: 歷史文檔僅供參考，請勿用於開發！

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
- **概念問題**: `stages/STAGES_OVERVIEW.md`
- **實現細節**: 對應階段的詳細規格文檔
- **標準合規**: `academic_standards_clarification.md`
- **技術標準**: 對應的專業標準文檔

---

**文檔版本**: v3.0
**最後更新**: 2025-09-28
**維護狀態**: ✅ 當前版本，積極維護