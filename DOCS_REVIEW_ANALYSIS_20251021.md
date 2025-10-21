# Orbit-Engine 文檔審查報告

**審查日期**: 2025-10-21
**審查範圍**: docs/, README.md, CLAUDE.md
**審查目的**: 確保文檔與最新代碼變更同步

---

## 📊 近期代碼變更總結（最近 7 個 commits）

### 主要變更（2025-10-20）
1. **Dual-mode 架構實現**
   - 新增 `config/rl_training/` 完整 RL 訓練配置
   - 新增 `scripts/generate_rl_training_data.sh` 專用腳本
   - Stage 3/4/5/6 processors 支援雙模式輸出

2. **目錄重構**
   - 刪除 `handover-rl/` 子目錄（已移至父目錄）
   - 保留 `data/tle_data` → `../tle_data` 軟連接

3. **未提交變更**
   - `config/stage6_research_optimization_config.yaml` - 閾值更新（數據驅動）
   - `config/rl_training/stage1_rl_config.yaml` - 改為全量模式
   - stage3/5/6 processors - 細節調整

### 閾值重大變更（2025-10-21，未提交）
| 事件 | 舊值 | 新值 | 變更原因 |
|------|------|------|----------|
| A3 offset | 2.0 dB | 2.5 dB | 避免數據洩漏 |
| A4 threshold | -100.0 dBm | -34.5 dBm | 數據驅動（30th percentile） |
| A5 threshold1 | -41.0 dBm | -36.0 dBm | 基於 48,222 樣本統計 |
| A5 threshold2 | -34.0 dBm | -33.0 dBm | 與 threshold1 保持 3dB 間隔 |

**SOURCE**: 基於 `analyze_actual_handover_events.py` 實測數據分析

---

## 🔍 文檔問題分析

### 1. ❌ **CRITICAL** - 新增文檔缺乏歸檔管理

**發現**: 4 個新增文檔未納入 git 追蹤
```
docs/CODE_REVIEW_RSRP_CLIPPING_BUGS.md (15K)
docs/FIX_SUMMARY_RSRP_CLIPPING.md (12K)
docs/MIGRATION_COMPLETE.md (6.0K)
docs/TLE_DATA_ARCHITECTURE.md (7.8K)
```

**問題分析**:
1. **RSRP 相關文檔** (`CODE_REVIEW_*`, `FIX_SUMMARY_*`)
   - 內容: 描述 RSRP 截斷 bug 及修復過程
   - 修復時間: 2025-10-05 (commit 29b6d01)
   - 當前狀態: 代碼已修復（見 `gpp_ts38214_signal_calculator.py:170`）
   - **判定**: 歷史記錄文檔，應歸檔或整合

2. **TLE 遷移文檔** (`MIGRATION_COMPLETE.md`, `TLE_DATA_ARCHITECTURE.md`)
   - 內容: TLE 數據從 orbit-engine 移至父目錄
   - 遷移時間: 2025-10-20 (commit 6d55e00)
   - 當前狀態: 遷移已完成
   - **判定**: 有價值的架構文檔，應保留並納入索引

**建議操作**:
```bash
# A. RSRP 文檔處理（二選一）
選項 1: 歸檔到 docs/archive/fixes/
選項 2: 整合到 CLAUDE.md 的 "Common Issues" 並刪除原檔

# B. TLE 文檔處理
1. 保留 TLE_DATA_ARCHITECTURE.md（架構說明）
2. 刪除或歸檔 MIGRATION_COMPLETE.md（一次性遷移記錄）
3. 更新 docs/README.md 索引
```

---

### 2. ❌ **HIGH** - Stage 6 文檔嚴重過時

**文件**: `docs/stages/stage6-research-optimization.md`
**最後更新**: 2025-10-16
**問題**: 文檔中的閾值配置與當前代碼不符

**過時內容**:
```python
# 文檔中的範例（第 1056-1058 行）
'a4_threshold_dbm': -100.0,        # ❌ 實際已改為 -34.5
'a5_threshold1_dbm': -110.0,       # ❌ 實際已改為 -36.0
'a5_threshold2_dbm': -95.0,        # ❌ 實際已改為 -33.0
```

**影響**:
- 開發者參考錯誤閾值
- 與 `config/stage6_research_optimization_config.yaml` 不一致
- 缺少數據驅動設計的說明

**建議更新**:
1. 更新所有閾值範例代碼（16 處）
2. 新增「數據驅動閾值設計」章節
3. 引用 `analyze_actual_handover_events.py` 分析結果
4. 說明為何從地面網絡標準值調整到 LEO NTN 實測值

---

### 3. ⚠️ **MEDIUM** - README.md 缺少 dual-mode 說明

**文件**: `README.md` (374 行)
**問題**: 未提及 RL 訓練數據生成功能

**缺失內容**:
- RL 訓練專用腳本 `scripts/generate_rl_training_data.sh`
- RL 專用配置 `config/rl_training/`
- 雙模式架構設計（research vs RL training）

**建議新增章節**:
```markdown
## 🎓 RL 訓練數據生成（雙模式架構）

orbit-engine 支援兩種輸出模式：

### 模式 1: 研究數據生成（預設）
```bash
./run.sh  # 生成完整六階段分析數據
```

### 模式 2: RL 訓練數據生成
```bash
./scripts/generate_rl_training_data.sh
```

**輸出差異**:
- **研究模式**: 完整信號分析 + 3GPP 事件 + 驗證快照
- **RL 模式**: 精簡狀態-動作對 + episode 數據 + 候選衛星池

**配置位置**: `config/rl_training/stage*.yaml`
```

---

### 4. ⚠️ **MEDIUM** - docs/README.md 索引過時

**文件**: `docs/README.md`
**最後更新**: 2025-10-10
**問題**: 新增文檔未納入索引

**缺失索引**:
- `TLE_DATA_ARCHITECTURE.md` - TLE 數據架構說明
- RL 訓練數據生成流程說明

**建議新增**:
```markdown
### 🏗️ 架構文檔
- **[TLE 數據架構](TLE_DATA_ARCHITECTURE.md)** - TLE 數據組織與遷移 (7.8KB)
  - Space-Track.org 數據源
  - Starlink/OneWeb 目錄結構
  - 與 orbit-engine 的集成方式

### 📊 RL 訓練支援
- **[RL 訓練配置說明](../config/rl_training/README.md)** - 雙模式架構設計
- **[生成腳本文檔](../scripts/generate_rl_training_data.sh)** - 使用方式
```

---

### 5. ✅ **INFO** - CLAUDE.md 已包含相關說明

**文件**: `CLAUDE.md`
**狀態**: ✅ 已更新至最新

**已包含內容**:
- RSRP 截斷問題說明（Lines 79-159）
- A3 事件觸發邏輯修正（Lines 163-207）
- A5 事件為 0 的正常現象（Lines 211-228）
- Epoch 驗證警告說明（Lines 232-270）

**建議**: 無需修改，已涵蓋主要問題

---

## 📋 優先級排序的建議操作

### Priority 1: CRITICAL（必須立即處理）

**T1.1 處理新增 RSRP 文檔**
```bash
# 選項 A: 歸檔（推薦）
mkdir -p docs/archive/fixes
git mv docs/CODE_REVIEW_RSRP_CLIPPING_BUGS.md docs/archive/fixes/
git mv docs/FIX_SUMMARY_RSRP_CLIPPING.md docs/archive/fixes/

# 選項 B: 刪除（CLAUDE.md 已包含說明）
git rm docs/CODE_REVIEW_RSRP_CLIPPING_BUGS.md
git rm docs/FIX_SUMMARY_RSRP_CLIPPING.md
```

**T1.2 處理 TLE 文檔**
```bash
# 保留架構文檔
git add docs/TLE_DATA_ARCHITECTURE.md

# 歸檔遷移記錄
mkdir -p docs/archive/migrations
git mv docs/MIGRATION_COMPLETE.md docs/archive/migrations/
```

### Priority 2: HIGH（本週內處理）

**T2.1 更新 Stage 6 文檔閾值**
- 文件: `docs/stages/stage6-research-optimization.md`
- 操作: 全局替換閾值 + 新增數據驅動說明
- 預計時間: 20 分鐘

### Priority 3: MEDIUM（兩週內處理）

**T3.1 更新 README.md**
- 新增 RL 訓練數據生成章節
- 預計時間: 15 分鐘

**T3.2 更新 docs/README.md 索引**
- 新增 TLE_DATA_ARCHITECTURE.md
- 新增 RL 訓練配置鏈接
- 預計時間: 10 分鐘

---

## 📊 文檔狀態總結

| 類別 | 文檔數 | 過時 | 重複 | 缺失索引 |
|------|--------|------|------|----------|
| 根目錄 | 2 | 1 | 0 | 0 |
| docs/ | 14 | 0 | 0 | 0 |
| docs/stages/ | 8 | 1 | 0 | 0 |
| docs/architecture/ | 9 | 0 | 0 | 0 |
| docs/development/ | 3 | 0 | 0 | 0 |
| **新增未追蹤** | **4** | **-** | **2** | **2** |
| **總計** | **40** | **2** | **2** | **2** |

---

## 🎯 預期成果

完成所有建議後：
- ✅ 所有文檔納入 git 追蹤
- ✅ 消除重複和過時內容
- ✅ 閾值配置與代碼同步
- ✅ 完整索引便於查找
- ✅ dual-mode 架構有完整說明

---

**審查者**: Claude Code
**審查完成時間**: 2025-10-21 02:35
