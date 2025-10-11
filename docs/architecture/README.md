# Orbit Engine 架構文檔

本資料夾包含 Orbit Engine 六階段執行系統的完整架構文檔。

## 文檔索引

### 📖 核心文檔

| 文檔 | 說明 | 頁數 |
|------|------|------|
| [00_OVERVIEW.md](./00_OVERVIEW.md) | 系統總覽與架構概述 | 全面介紹模塊化架構和數據流動 |
| [01_EXECUTION_FLOW.md](./01_EXECUTION_FLOW.md) | 執行流程與控制邏輯 | 詳細說明三種執行模式和數據流 |
| [02_STAGES_DETAIL.md](./02_STAGES_DETAIL.md) | 六階段詳細實現 | 每個階段的執行器、處理器、配置 |
| [03_VALIDATION_SYSTEM.md](./03_VALIDATION_SYSTEM.md) | 雙層驗證系統架構 | Layer 1/2 驗證邏輯和 Fail-Fast 策略 |
| [04_SUPPORTING_MODULES.md](./04_SUPPORTING_MODULES.md) | 支持模塊與檔案清單 | 完整記錄 103 個 Python 檔案 |
| [05_FILE_USAGE_ANALYSIS.md](./05_FILE_USAGE_ANALYSIS.md) | 檔案使用狀態分析 | 初步分析（已被 06 取代） |
| [06_FINAL_USAGE_SUMMARY.md](./06_FINAL_USAGE_SUMMARY.md) | ⭐ 最終使用狀態總結 | **97.1% 確認使用，代碼庫極度乾淨** |
| [07_FOUR_FILES_DETAILED_ANALYSIS.md](./07_FOUR_FILES_DETAILED_ANALYSIS.md) | 🔍 4 個特定檔案深入檢查 | **獨立工具、已禁用檔案、待驗證檔案完整分析** |
| [08_FAIL_FAST_COMPLIANCE_FIX.md](./08_FAIL_FAST_COMPLIANCE_FIX.md) | 🚨 Fail-Fast 架構合規性修正 | **移除 fallback 機制，恢復架構一致性** |

## 快速導航

### 🎯 我想了解...

#### 整體架構
- 想知道系統如何組織？ → 閱讀 [00_OVERVIEW.md](./00_OVERVIEW.md)
- 想知道數據如何流動？ → 閱讀 [01_EXECUTION_FLOW.md](./01_EXECUTION_FLOW.md)

#### 特定階段
- 想了解 Stage N 的實現？ → 閱讀 [02_STAGES_DETAIL.md](./02_STAGES_DETAIL.md) 對應章節
- 想知道 Stage N 使用哪些文件？ → 查看該章節的「核心文件」部分

#### 驗證機制
- 想知道如何驗證階段輸出？ → 閱讀 [03_VALIDATION_SYSTEM.md](./03_VALIDATION_SYSTEM.md)
- 遇到驗證失敗？ → 查看該文檔的「驗證失敗處理」章節

#### 開發與調試
- 想修改某個階段？ → 查看 [02_STAGES_DETAIL.md](./02_STAGES_DETAIL.md) 找到對應文件
- 想添加新的驗證邏輯？ → 閱讀 [03_VALIDATION_SYSTEM.md](./03_VALIDATION_SYSTEM.md) 了解最佳實踐
- 想了解所有支持模塊？ → 閱讀 [04_SUPPORTING_MODULES.md](./04_SUPPORTING_MODULES.md) 完整清單

#### 檔案使用狀態
- 想知道哪些檔案在使用中？ → 閱讀 [06_FINAL_USAGE_SUMMARY.md](./06_FINAL_USAGE_SUMMARY.md)
- 想了解獨立工具的用途？ → 閱讀 [07_FOUR_FILES_DETAILED_ANALYSIS.md](./07_FOUR_FILES_DETAILED_ANALYSIS.md)
- 想清理未使用的代碼？ → **不需要！** 代碼庫已極度乾淨 (97.1% 確認使用)

## 文檔結構

```
docs/architecture/
├── README.md (本文檔)              # 文檔導航和快速索引
├── 00_OVERVIEW.md                  # 系統總覽
│   ├── 模塊化架構說明
│   ├── 執行流程概覽
│   ├── 配置文件系統
│   ├── 數據流動路徑
│   └── 性能特性
├── 01_EXECUTION_FLOW.md            # 執行流程
│   ├── 環境初始化
│   ├── 三種執行模式詳解
│   ├── 數據流模式
│   ├── 錯誤處理
│   └── 執行範例
├── 02_STAGES_DETAIL.md             # 六階段詳細
│   ├── Stage 1: TLE 數據載入層
│   ├── Stage 2: 軌道狀態傳播層
│   ├── Stage 3: 座標系統轉換層
│   ├── Stage 4: 鏈路可行性評估層
│   ├── Stage 5: 信號品質分析層
│   ├── Stage 6: 研究數據生成層
│   └── 共用工具模塊
├── 03_VALIDATION_SYSTEM.md         # 驗證系統
│   ├── 雙層驗證架構
│   ├── Fail-Fast 策略
│   ├── 各階段驗證器詳解
│   ├── 驗證快照範例
│   └── 最佳實踐
└── 04_SUPPORTING_MODULES.md        # 支持模塊
    ├── scripts/ 工具腳本清單
    ├── src/shared/ 共用模塊詳解
    ├── 各階段子模塊清單
    └── 103 個 Python 檔案完整記錄
```

## 核心概念速查

### 模塊化架構

```
scripts/
├── run_six_stages_with_validation.py    # 主控程序 (332 行)
├── stage_executors/                      # 執行器模塊 (6 個)
│   ├── stage1_executor.py
│   ├── stage2_executor.py
│   ├── stage3_executor.py
│   ├── stage4_executor.py
│   ├── stage5_executor.py
│   └── stage6_executor.py
└── stage_validators/                     # 驗證器模塊 (6 個)
    ├── stage1_validator.py
    ├── stage2_validator.py
    ├── stage3_validator.py
    ├── stage4_validator.py
    ├── stage5_validator.py
    └── stage6_validator.py
```

### 三種執行模式

| 模式 | 命令 | 說明 |
|------|------|------|
| 完整管道 | `./run.sh` | 順序執行所有六階段 |
| 單一階段 | `./run.sh --stage 4` | 僅執行 Stage 4 |
| 階段範圍 | `./run.sh --stages 4-6` | 執行 Stage 4-6 |

### 數據流動

```
Stage 1 → stage1_result (in-memory)
       → Stage 2 → stage2_result (in-memory)
              → Stage 3 → stage3_result (in-memory)
                     → Stage 4 → stage4_result (in-memory)
                            → Stage 5 → stage5_result (in-memory)
                                   → Stage 6 → stage6_result (in-memory)
```

### 雙層驗證

```
每個階段執行後
  ↓
Layer 1: 內建驗證 (Processor 內部)
  - processor.run_validation_checks()
  - processor.save_validation_snapshot()
  ↓
Layer 2: 快照品質檢查 (Validator 外部)
  - check_stageN_validation(snapshot_data)
  ↓
Fail-Fast: 驗證失敗立即停止
```

## 關鍵文件位置速查

### 主程序與工具

| 文件 | 說明 |
|------|------|
| `scripts/run_six_stages_with_validation.py` | 主執行腳本 (332 行) |
| `scripts/stage_executors/executor_utils.py` | 共用工具函數 |
| `run.sh` | 便捷執行腳本 (wrapper) |

### 執行器 (Executors)

| 階段 | 執行器文件 | 行數 |
|------|-----------|------|
| Stage 1 | `scripts/stage_executors/stage1_executor.py` | 74 |
| Stage 2 | `scripts/stage_executors/stage2_executor.py` | 84 |
| Stage 3 | `scripts/stage_executors/stage3_executor.py` | 83 |
| Stage 4 | `scripts/stage_executors/stage4_executor.py` | 78 |
| Stage 5 | `scripts/stage_executors/stage5_executor.py` | 154 |
| Stage 6 | `scripts/stage_executors/stage6_executor.py` | 62 |

### 處理器 (Processors)

| 階段 | 處理器文件 |
|------|-----------|
| Stage 1 | `src/stages/stage1_orbital_calculation/stage1_main_processor.py` |
| Stage 2 | `src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py` |
| Stage 3 | `src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py` |
| Stage 4 | `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py` |
| Stage 5 | `src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py` |
| Stage 6 | `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py` |

### 驗證器 (Validators)

| 階段 | 驗證器文件 | 行數 |
|------|-----------|------|
| Stage 1 | `scripts/stage_validators/stage1_validator.py` | 190 |
| Stage 2 | `scripts/stage_validators/stage2_validator.py` | ~150 |
| Stage 3 | `scripts/stage_validators/stage3_validator.py` | ~120 |
| Stage 4 | `scripts/stage_validators/stage4_validator.py` | ~100 |
| Stage 5 | `scripts/stage_validators/stage5_validator.py` | ~130 |
| Stage 6 | `scripts/stage_validators/stage6_validator.py` | ~80 |

### 配置文件 (Config)

| 階段 | 配置文件 |
|------|---------|
| Stage 1 | 隱式配置 (寫在執行器內部) |
| Stage 2 | `config/stage2_orbital_computing.yaml` |
| Stage 3 | 隱式配置 (寫在執行器內部) |
| Stage 4 | `config/stage4_link_feasibility_config.yaml` |
| Stage 5 | `config/stage5_signal_analysis_config.yaml` |
| Stage 6 | `config/stage6_research_optimization_config.yaml` |

## 常見問題

### Q: 如何執行單一階段？

```bash
./run.sh --stage 4
```

系統會自動讀取前序階段 (Stage 3) 的輸出文件。

### Q: 如何查看某個階段使用哪些文件？

閱讀 [02_STAGES_DETAIL.md](./02_STAGES_DETAIL.md) 對應章節的「核心文件」部分。

### Q: 驗證失敗如何調試？

1. 查看錯誤信息，確定失敗的驗證項目
2. 閱讀 [03_VALIDATION_SYSTEM.md](./03_VALIDATION_SYSTEM.md) 對應階段的驗證邏輯
3. 檢查 `data/validation_snapshots/stageN_validation.json` 快照內容
4. 根據驗證器代碼定位問題

### Q: 如何修改某個階段的邏輯？

1. 修改處理器: `src/stages/stageN_*/stageN_*_processor.py`
2. 修改執行器: `scripts/stage_executors/stageN_executor.py`
3. 修改驗證器: `scripts/stage_validators/stageN_validator.py`
4. 修改配置: `config/stageN_*.yaml`

### Q: 數據如何在階段間傳遞？

- **管道模式** (完整執行): 內存傳遞 (`stage_results` 字典)
- **文件模式** (單一階段): 從磁碟讀取前序輸出

詳見 [01_EXECUTION_FLOW.md](./01_EXECUTION_FLOW.md) 的「數據流模式」章節。

## 重構歷史

### 重構前 (2025-10-03 之前)

- **單一文件**: 1919 行巨型文件
- **可維護性**: 差 (單一函數 192 行)
- **Git 友好性**: 差 (多人協作衝突風險高)

### 重構後 (2025-10-03)

- **模塊化架構**: 14 個獨立模塊 (6 執行器 + 6 驗證器 + 2 工具)
- **主程序**: 332 行 (減少 75%)
- **平均函數長度**: 69 行 (減少 64%)
- **可維護性**: 優 (單一職責原則)
- **Git 友好性**: 優 (模塊獨立，衝突少)

## 架構優勢

### 1. 模塊化
- 6 個獨立執行器，易於維護和測試
- 6 個獨立驗證器，驗證邏輯清晰

### 2. 可重入性
- 支持單一階段執行
- 自動讀取前序輸出文件

### 3. Fail-Fast
- 驗證失敗立即停止
- 節省計算資源

### 4. 雙層驗證
- Layer 1: 處理器內建驗證 (算法正確性)
- Layer 2: 外部快照檢查 (數據合理性)

### 5. 學術合規
- 所有驗證基於 ITU-R, 3GPP, NASA JPL 標準
- 驗證邏輯有明確的學術依據

## 性能數據

### 完整管道執行時間 (9,015 顆衛星)

| 階段 | 首次執行 | 緩存後 |
|------|---------|--------|
| Stage 1 | ~10 秒 | ~10 秒 |
| Stage 2 | ~3-5 分鐘 | ~3-5 分鐘 |
| Stage 3 | ~25 分鐘 | ~2 分鐘 |
| Stage 4 | ~2-3 分鐘 | ~2-3 分鐘 |
| Stage 5 | ~5-8 分鐘 | ~5-8 分鐘 |
| Stage 6 | ~1-2 分鐘 | ~1-2 分鐘 |
| **總計** | **~40 分鐘** | **~15 分鐘** |

### 並行處理

- **Stage 2**: 30 個工作進程 (SGP4 軌道計算)
- **Stage 3**: 30 個工作進程 (座標轉換)
- **Stage 5**: 30 個工作進程 (信號計算)

### 緩存機制

- **Stage 3 HDF5**: ~154MB, 首次 ~25min → 緩存後 ~2min
- **IERS 數據**: 地球定向參數緩存
- **NASA JPL DE421**: 星曆表緩存

## 使用範例

### 範例 1: 完整管道執行

```bash
./run.sh
```

輸出：
```
🚀 開始六階段數據處理 (重構版本)
============================================================
📦 階段1：數據載入層
✅ 階段1完成並驗證通過
============================================================
📦 階段2：軌道狀態傳播層
✅ 階段2完成並驗證通過
...
📊 執行統計:
   執行時間: 2314.52 秒
   完成階段: 6/6
   最終狀態: ✅ 成功
```

### 範例 2: 僅執行 Stage 5

```bash
./run.sh --stage 5
```

輸出：
```
🎯 執行階段 5: 信號品質分析層
📊 階段五：信號品質分析層 (Grade A+ 模式)
✅ 已加載配置文件: stage5_signal_analysis_config.yaml
✅ Stage 5 成功完成並驗證通過

📊 執行統計:
   執行時間: 387.21 秒
   完成階段: 5/6
   最終狀態: ✅ 成功
```

### 範例 3: 執行 Stage 4-6

```bash
./run.sh --stages 4-6
```

## 環境變量

系統支持的環境變量 (自動從 `.env` 載入):

| 變量 | 說明 | 預設值 |
|------|------|--------|
| `ORBIT_ENGINE_TEST_MODE` | 測試模式 (50 顆衛星) | `0` |
| `ORBIT_ENGINE_SAMPLING_MODE` | 取樣模式 | `auto` |
| `ORBIT_ENGINE_STAGE3_NO_PREFILTER` | 禁用 Stage 3 預篩選器 | `1` |
| `ORBIT_ENGINE_MAX_WORKERS` | 並行工作進程數 | `30` |

## 相關文檔

### 項目文檔

- **總體文檔**: `docs/README.md`
- **學術標準**: `docs/ACADEMIC_STANDARDS.md`
- **快速開始**: `docs/QUICK_START.md`
- **最終規格**: `docs/final.md`

### 階段文檔

- **Stage 1**: `docs/stages/stage1-*.md`
- **Stage 2**: `docs/stages/stage2-*.md`
- **Stage 3**: `docs/stages/stage3-*.md`
- **Stage 4**: `docs/stages/stage4-*.md`
- **Stage 5**: `docs/stages/stage5-*.md`
- **Stage 6**: `docs/stages/stage6-*.md`

## 貢獻指南

### 添加新的驗證邏輯

1. 修改對應的驗證器文件 `scripts/stage_validators/stageN_validator.py`
2. 遵循「最佳實踐」章節的指導原則
3. 添加清晰的錯誤信息和閾值依據
4. 更新本文檔的驗證統計

### 修改階段邏輯

1. 修改處理器: `src/stages/stageN_*/`
2. 修改執行器: `scripts/stage_executors/stageN_executor.py`
3. 更新配置文件: `config/stageN_*.yaml`
4. 更新驗證器: `scripts/stage_validators/stageN_validator.py`
5. 更新 [02_STAGES_DETAIL.md](./02_STAGES_DETAIL.md)

## 聯繫方式

如有問題或建議，請：
1. 查閱本資料夾的文檔
2. 查閱 `docs/` 下的其他文檔
3. 聯繫項目維護者

---

**文檔版本**: v1.0
**創建日期**: 2025-10-10
**架構版本**: 重構版 (2025-10-03)
**維護者**: Orbit Engine 開發團隊
