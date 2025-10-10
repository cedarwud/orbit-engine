# Orbit Engine 六階段執行系統 - 架構總覽

## 文檔目錄

本資料夾包含 Orbit Engine 六階段執行系統的完整架構文檔：

- **00_OVERVIEW.md** (本文檔) - 系統總覽與導航
- **01_EXECUTION_FLOW.md** - 執行流程與控制邏輯
- **02_STAGE1_DATA_LOADING.md** - 階段1: TLE 數據載入層
- **03_STAGE2_ORBITAL_PROPAGATION.md** - 階段2: 軌道狀態傳播層
- **04_STAGE3_COORDINATE_TRANSFORM.md** - 階段3: 座標系統轉換層
- **05_STAGE4_LINK_FEASIBILITY.md** - 階段4: 鏈路可行性評估層
- **06_STAGE5_SIGNAL_ANALYSIS.md** - 階段5: 信號品質分析層
- **07_STAGE6_RESEARCH_OPTIMIZATION.md** - 階段6: 研究數據生成層
- **08_VALIDATION_SYSTEM.md** - 雙層驗證系統架構

## 系統總覽

### 核心腳本

```
scripts/run_six_stages_with_validation.py (主程序, 332行)
```

**重構歷史**:
- 原始版本: 1919 行單一文件
- 重構日期: 2025-10-03
- 重構後: 332 行主程序 + 14 個模塊 (6個執行器 + 6個驗證器 + 2個工具模塊)
- 代碼量減少: **75%** (1919行 → 332行)
- 平均函數長度減少: **64%** (192行 → 69行)

### 模塊化架構

```
scripts/
├── run_six_stages_with_validation.py    # 主控程序
├── stage_executors/                      # 執行器模塊 (Executors)
│   ├── __init__.py
│   ├── executor_utils.py                 # 共用工具函數
│   ├── stage1_executor.py                # Stage 1 執行邏輯
│   ├── stage2_executor.py                # Stage 2 執行邏輯
│   ├── stage3_executor.py                # Stage 3 執行邏輯
│   ├── stage4_executor.py                # Stage 4 執行邏輯
│   ├── stage5_executor.py                # Stage 5 執行邏輯
│   └── stage6_executor.py                # Stage 6 執行邏輯
└── stage_validators/                     # 驗證器模塊 (Validators)
    ├── __init__.py
    ├── stage1_validator.py               # Stage 1 驗證邏輯
    ├── stage2_validator.py               # Stage 2 驗證邏輯
    ├── stage3_validator.py               # Stage 3 驗證邏輯
    ├── stage4_validator.py               # Stage 4 驗證邏輯
    ├── stage5_validator.py               # Stage 5 驗證邏輯
    └── stage6_validator.py               # Stage 6 驗證邏輯
```

### 處理器實現

各階段的核心處理器位於 `src/stages/`:

```
src/stages/
├── stage1_orbital_calculation/
│   └── stage1_main_processor.py          # Stage 1 處理器
├── stage2_orbital_computing/
│   └── stage2_orbital_computing_processor.py  # Stage 2 處理器
├── stage3_coordinate_transformation/
│   └── stage3_coordinate_transform_processor.py  # Stage 3 處理器
├── stage4_link_feasibility/
│   └── stage4_link_feasibility_processor.py  # Stage 4 處理器
├── stage5_signal_analysis/
│   └── stage5_signal_analysis_processor.py  # Stage 5 處理器
└── stage6_research_optimization/
    └── stage6_research_optimization_processor.py  # Stage 6 處理器
```

## 執行流程概覽

### 順序執行模式 (完整管道)

```
./run.sh
```

```
開始六階段數據處理
  ↓
┌─────────────────────────────────────────┐
│ Stage 1: TLE 數據載入層                 │
│ - 執行: stage1_executor.execute_stage1() │
│ - 驗證: stage1_validator.check_validation│
│ - 輸出: stage1_output.json               │
└─────────────────────────────────────────┘
  ↓ (傳遞 stage1_result)
┌─────────────────────────────────────────┐
│ Stage 2: 軌道狀態傳播層                 │
│ - 執行: stage2_executor.execute_stage2() │
│ - 驗證: stage2_validator.check_validation│
│ - 輸出: orbital_propagation_output.json  │
└─────────────────────────────────────────┘
  ↓ (傳遞 stage2_result)
┌─────────────────────────────────────────┐
│ Stage 3: 座標系統轉換層                 │
│ - 執行: stage3_executor.execute_stage3() │
│ - 驗證: stage3_validator.check_validation│
│ - 輸出: stage3_coordinate_transformation.json │
└─────────────────────────────────────────┘
  ↓ (傳遞 stage3_result)
┌─────────────────────────────────────────┐
│ Stage 4: 鏈路可行性評估層               │
│ - 執行: stage4_executor.execute_stage4() │
│ - 驗證: stage4_validator.check_validation│
│ - 輸出: stage4_link_analysis.json        │
└─────────────────────────────────────────┘
  ↓ (傳遞 stage4_result)
┌─────────────────────────────────────────┐
│ Stage 5: 信號品質分析層                 │
│ - 執行: stage5_executor.execute_stage5() │
│ - 驗證: stage5_validator.check_validation│
│ - 輸出: stage5_signal_analysis.json      │
└─────────────────────────────────────────┘
  ↓ (傳遞 stage5_result)
┌─────────────────────────────────────────┐
│ Stage 6: 研究數據生成層                 │
│ - 執行: stage6_executor.execute_stage6() │
│ - 驗證: stage6_validator.check_validation│
│ - 輸出: stage6_research.json             │
└─────────────────────────────────────────┘
  ↓
執行完成
```

### 單一階段執行模式

```bash
./run.sh --stage 4
```

- 自動讀取前序階段輸出 (Stage 3 輸出文件)
- 僅執行指定階段
- 驗證並保存輸出

### 階段範圍執行模式

```bash
./run.sh --stages 4-6
```

- 執行階段 4、5、6
- 保持階段間數據流動

## 雙層驗證系統

每個階段執行後立即進行雙層驗證：

### Layer 1: 內建驗證 (Processor 內部)

```python
processor.run_validation_checks(data)
```

- 由各階段處理器自行實現
- 驗證算法正確性、數據完整性
- 返回詳細驗證結果 (validation_status, overall_status)

### Layer 2: 快照品質檢查 (Validator 外部)

```python
validator(snapshot_data)
```

- 讀取 `data/validation_snapshots/stageN_validation.json`
- 檢查數據結構、合理性、架構合規性
- 信任 Layer 1 結果，不重複詳細驗證

**驗證策略**: Fail-Fast (任一階段失敗立即停止)

## 配置文件系統

每個階段有獨立的配置文件：

```
config/
├── stage1_config.yaml                    # Stage 1 配置 (隱式，寫在執行器內)
├── stage2_orbital_computing.yaml         # Stage 2 配置
├── stage3_config.yaml                    # Stage 3 配置 (隱式)
├── stage4_link_feasibility_config.yaml   # Stage 4 配置
├── stage5_signal_analysis_config.yaml    # Stage 5 配置
└── stage6_research_optimization_config.yaml  # Stage 6 配置
```

## 數據流動路徑

### 管道模式 (Pipeline)

```
Stage 1 → stage1_result (in-memory)
       → Stage 2 → stage2_result (in-memory)
              → Stage 3 → stage3_result (in-memory)
                     → Stage 4 → stage4_result (in-memory)
                            → Stage 5 → stage5_result (in-memory)
                                   → Stage 6 → stage6_result (in-memory)
```

### 文件模式 (File-based)

當執行單一階段時，從磁碟讀取前序輸出：

```
data/outputs/stage3/*.json
   ↓ (讀取)
Stage 4 執行
   ↓ (保存)
data/outputs/stage4/*.json
```

## 環境變量

系統支持以下環境變量 (自動從 `.env` 載入):

- **ORBIT_ENGINE_TEST_MODE**: `0` (全量) / `1` (測試模式 50 顆)
- **ORBIT_ENGINE_SAMPLING_MODE**: `0` (無取樣) / `1` (取樣模式) / `auto` (跟隨 TEST_MODE)
- **ORBIT_ENGINE_STAGE3_NO_PREFILTER**: `1` (禁用 Stage 3 預篩選器)
- **ORBIT_ENGINE_MAX_WORKERS**: 並行工作進程數 (預設 30)

## 關鍵設計原則

### 1. 單一職責原則 (SRP)
- 每個執行器只負責一個階段的執行邏輯
- 每個驗證器只負責一個階段的驗證邏輯

### 2. 標準化接口
所有執行器返回統一格式：
```python
(success: bool, result: ProcessingResult, processor: Processor)
```

### 3. 依賴聲明清晰
每個階段明確聲明其輸入依賴：
- Stage 1: 無依賴 (讀取 TLE 文件)
- Stage 2: 依賴 Stage 1 結果
- Stage 3: 依賴 Stage 2 結果
- Stage 4: 依賴 Stage 3 結果
- Stage 5: 依賴 Stage 4 結果
- Stage 6: 依賴 Stage 5 結果

### 4. 可重入性 (Reusability)
- 各階段輸出保存到磁碟
- 可獨立執行單一階段，自動讀取前序輸出
- 支持部分管道重跑

## 性能特性

### 並行處理
- **Stage 2**: 30 個工作進程 (SGP4 軌道計算)
- **Stage 3**: 30 個工作進程 (座標轉換)
- **Stage 5**: 30 個工作進程 (信號計算)

### 緩存機制
- **Stage 3**: HDF5 座標緩存 (`data/cache/stage3/`, ~154MB)
- **IERS**: 地球定向參數緩存 (`data/cache/iers/`)
- **Ephemeris**: NASA JPL DE421 星曆表緩存 (`data/ephemeris/`)

### 典型執行時間 (9,015 顆衛星)
- 完整管道: **30-40 分鐘**
- Stage 1: ~10 秒
- Stage 2: ~3-5 分鐘
- Stage 3: 首次 ~25 分鐘, 緩存後 ~2 分鐘
- Stage 4: ~2-3 分鐘
- Stage 5: ~5-8 分鐘
- Stage 6: ~1-2 分鐘

## 輸出文件結構

```
data/
├── outputs/
│   ├── stage1/
│   │   └── stage1_output_YYYYMMDD_HHMMSS.json
│   ├── stage2/
│   │   ├── orbital_propagation_output_YYYYMMDD_HHMMSS.json
│   │   └── orbital_propagation_output_YYYYMMDD_HHMMSS.h5
│   ├── stage3/
│   │   └── stage3_coordinate_transformation_real_YYYYMMDD_HHMMSS.json
│   ├── stage4/
│   │   └── stage4_link_analysis_YYYYMMDD_HHMMSS.json
│   ├── stage5/
│   │   └── stage5_signal_analysis_YYYYMMDD_HHMMSS.json
│   └── stage6/
│       └── stage6_research_YYYYMMDD_HHMMSS.json
└── validation_snapshots/
    ├── stage1_validation.json
    ├── stage2_validation.json
    ├── stage3_validation.json
    ├── stage4_validation.json
    ├── stage5_validation.json
    └── stage6_validation.json
```

## 使用方式

### 完整管道執行

```bash
./run.sh
```

### 單一階段執行

```bash
./run.sh --stage 1    # 執行 Stage 1
./run.sh --stage 4    # 執行 Stage 4 (自動讀取 Stage 3 輸出)
```

### 階段範圍執行

```bash
./run.sh --stages 1-3   # 執行 Stage 1-3
./run.sh --stages 4-6   # 執行 Stage 4-6
```

### Python 直接執行

```bash
python scripts/run_six_stages_with_validation.py
python scripts/run_six_stages_with_validation.py --stage 5
python scripts/run_six_stages_with_validation.py --stages 2-4
```

## 學術合規性

所有階段嚴格遵循以下標準：

- **ITU-R**: 國際電信聯盟無線電通信部門標準
- **3GPP**: 第三代合作夥伴計劃 (NTN 標準)
- **NASA JPL**: 美國航空航天局噴氣推進實驗室 (星曆表、SGP4)
- **IAU**: 國際天文學聯合會 (時間系統、座標系統)

所有算法實現均有 SOURCE 注釋標註官方來源。

## 下一步閱讀

- **執行流程**: 閱讀 [01_EXECUTION_FLOW.md](./01_EXECUTION_FLOW.md) 了解詳細執行邏輯
- **各階段詳細**: 閱讀 `02_STAGE1_*.md` ~ `07_STAGE6_*.md` 了解各階段實現
- **驗證系統**: 閱讀 [08_VALIDATION_SYSTEM.md](./08_VALIDATION_SYSTEM.md) 了解驗證機制

---

**文檔版本**: v1.0
**創建日期**: 2025-10-10
**架構版本**: 重構版 (2025-10-03)
