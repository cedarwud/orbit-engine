# 檔案使用狀態分析

本文檔分析所有 Python 檔案的使用狀態，識別哪些檔案被六階段執行系統實際使用，哪些可能是獨立工具、測試代碼或廢棄代碼。

## 分析日期: 2025-10-10

---

## 執行概要

### ✅ 被六階段執行系統使用的檔案: 81 個
### ⚠️ 獨立工具腳本: 2 個
### ❓ 可能未使用或冗餘: 10 個
### 📝 更新日期: 2025-10-11 (Stage 5/6 坐標轉換器整合至共用模組)

---

## 一、核心執行路徑 (100% 使用)

### 1.1 主執行腳本 (1 個)

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `scripts/run_six_stages_with_validation.py` | ✅ 使用中 | 主程序入口 |

### 1.2 執行器模塊 (7 個)

| 檔案 | 狀態 | 調用者 |
|------|------|--------|
| `scripts/stage_executors/__init__.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_executors/executor_utils.py` | ✅ 使用中 | 6個執行器 |
| `scripts/stage_executors/stage1_executor.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_executors/stage2_executor.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_executors/stage3_executor.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_executors/stage4_executor.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_executors/stage5_executor.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_executors/stage6_executor.py` | ✅ 使用中 | 主執行腳本 |

### 1.3 驗證器模塊 (7 個)

| 檔案 | 狀態 | 調用者 |
|------|------|--------|
| `scripts/stage_validators/__init__.py` | ✅ 使用中 | 主執行腳本 |
| `scripts/stage_validators/stage1_validator.py` | ✅ 使用中 | 主執行腳本 (Layer 2 驗證) |
| `scripts/stage_validators/stage2_validator.py` | ✅ 使用中 | 主執行腳本 (Layer 2 驗證) |
| `scripts/stage_validators/stage3_validator.py` | ✅ 使用中 | 主執行腳本 (Layer 2 驗證) |
| `scripts/stage_validators/stage4_validator.py` | ✅ 使用中 | 主執行腳本 (Layer 2 驗證) |
| `scripts/stage_validators/stage5_validator.py` | ✅ 使用中 | 主執行腳本 (Layer 2 驗證) |
| `scripts/stage_validators/stage6_validator.py` | ✅ 使用中 | 主執行腳本 (Layer 2 驗證) |

**總計**: 15/16 個 scripts/ 檔案被使用 (93.75%)

---

## 二、處理器層 (主要業務邏輯)

### 2.1 主處理器 (6 個)

| 檔案 | 狀態 | 調用者 |
|------|------|--------|
| `src/stages/stage1_orbital_calculation/stage1_main_processor.py` | ✅ 使用中 | stage1_executor |
| `src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py` | ✅ 使用中 | stage2_executor |
| `src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py` | ✅ 使用中 | stage3_executor |
| `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py` | ✅ 使用中 | stage4_executor |
| `src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py` | ✅ 使用中 | stage5_executor |
| `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py` | ✅ 使用中 | stage6_executor |

### 2.2 Stage 1 子模塊 (13 個)

| 檔案 | 狀態 | 證據 |
|------|------|------|
| `tle_data_loader.py` | ✅ 使用中 | 被 stage1_main_processor 導入 |
| `data_validator.py` | ✅ 使用中 | 被 stage1_main_processor 導入 |
| `time_reference_manager.py` | ✅ 使用中 | 被 stage1_main_processor 導入 |
| `epoch_analyzer.py` | ✅ 使用中 | 被 stage1_main_processor 導入 |
| `checkers/academic_checker.py` | ✅ 使用中 | 被 data_validator 導入 |
| `checkers/requirement_checker.py` | ✅ 使用中 | 被 data_validator 導入 |
| `validators/format_validator.py` | ✅ 使用中 | 被 tle_data_loader 導入 |
| `validators/checksum_validator.py` | ✅ 使用中 | 被 tle_data_loader 導入 |
| `metrics/accuracy_calculator.py` | ❓ 需驗證 | 未在主處理器中發現導入 |
| `metrics/consistency_calculator.py` | ❓ 需驗證 | 未在主處理器中發現導入 |
| `reports/statistics_reporter.py` | ❓ 需驗證 | 未在主處理器中發現導入 |

**Stage 1 使用率**: 8/13 確認使用 (61.5%), 5 個待驗證

### 2.3 Stage 2 子模塊 (4 個)

| 檔案 | 狀態 | 證據 |
|------|------|------|
| `sgp4_calculator.py` | ✅ 使用中 | 被 stage2_orbital_computing_processor 導入 |
| `unified_time_window_manager.py` | ✅ 使用中 | 被 stage2_orbital_computing_processor 導入 |
| `stage2_result_manager.py` | ✅ 使用中 | 被 stage2_orbital_computing_processor 導入 |
| `stage2_validator.py` | ✅ 使用中 | 被 stage2_orbital_computing_processor 導入 |

**Stage 2 使用率**: 4/4 (100%)

### 2.4 Stage 3 子模塊 (6 個)

| 檔案 | 狀態 | 證據 |
|------|------|------|
| `stage3_transformation_engine.py` | ✅ 使用中 | 被 stage3_coordinate_transform_processor 導入 |
| `geometric_prefilter.py` | ⚠️ 已禁用 | v3.1 版本已禁用，保留供參考 |
| `stage3_data_extractor.py` | ✅ 使用中 | 被 stage3_coordinate_transform_processor 導入 |
| `stage3_data_validator.py` | ✅ 使用中 | 被 stage3_coordinate_transform_processor 導入 |
| `stage3_results_manager.py` | ✅ 使用中 | 被 stage3_coordinate_transform_processor 導入 |
| `stage3_compliance_validator.py` | ✅ 使用中 | 被 stage3_coordinate_transform_processor 導入 |

**Stage 3 使用率**: 5/6 使用中 (83.3%), 1 個已禁用

### 2.5 Stage 4 子模塊 (13 個)

| 檔案 | 狀態 | 證據 |
|------|------|------|
| `skyfield_visibility_calculator.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `pool_optimizer.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `link_budget_analyzer.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `constellation_filter.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `dynamic_threshold_analyzer.py` | ❓ 需驗證 | 可能是舊版功能 |
| `epoch_validator.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `poliastro_validator.py` | ❓ 需驗證 | 交叉驗證器（可選功能） |
| `filtering/satellite_filter.py` | ✅ 使用中 | 被 constellation_filter 導入 |
| `data_processing/coordinate_extractor.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `data_processing/service_window_calculator.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `output_management/result_builder.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |
| `output_management/snapshot_manager.py` | ✅ 使用中 | 被 stage4_link_feasibility_processor 導入 |

**Stage 4 使用率**: 10/13 確認使用 (76.9%), 3 個待驗證

### 2.6 Stage 5 子模塊 (12 個)

| 檔案 | 狀態 | 證據 |
|------|------|------|
| `gpp_ts38214_signal_calculator.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `itur_official_atmospheric_model.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `itur_physics_calculator.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `doppler_calculator.py` | ✅ 使用中 | 被 time_series_analyzer 導入 (都卜勒計算，使用 Stage 2 實際速度) |
| `coordinate_converter.py` | ✅ 使用中 | 被 time_series_analyzer 導入 (ECEF 轉換，Stage 6 D2 事件需要) |
| `time_series_analyzer.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `stage5_compliance_validator.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `data_processing/config_manager.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `data_processing/input_extractor.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `output_management/result_builder.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `output_management/snapshot_manager.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `parallel_processing/cpu_optimizer.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |
| `parallel_processing/worker_manager.py` | ✅ 使用中 | 被 stage5_signal_analysis_processor 導入 |

**Stage 5 使用率**: 12/12 確認使用 (100%)

### 2.7 Stage 6 子模塊 (7 個)

| 檔案 | 狀態 | 證據 |
|------|------|------|
| `gpp_event_detector.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |
| `handover_decision_evaluator.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |
| `satellite_pool_verifier.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |
| `stage6_academic_compliance.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |
| `stage6_input_output_validator.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |
| `stage6_snapshot_manager.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |
| `stage6_validation_framework.py` | ✅ 使用中 | 被 stage6_research_optimization_processor 導入 |

**Stage 6 使用率**: 7/7 確認使用 (100%)

**註**: `coordinate_converter.py` 和 `ground_distance_calculator.py` 已整合至 `src/shared/utils/` (2025-10-11 重構)

---

## 三、共用基礎設施 (src/shared/)

### 3.1 基礎類 (2 個)

| 檔案 | 狀態 | 調用者 |
|------|------|--------|
| `base_processor.py` | ✅ 使用中 | base_stage_processor |
| `base_stage_processor.py` | ✅ 使用中 | 所有 6 個主處理器 |

**使用率**: 2/2 (100%)

### 3.2 接口定義 (1 個)

| 檔案 | 狀態 | 調用者 |
|------|------|--------|
| `interfaces/processor_interface.py` | ✅ 使用中 | 所有處理器（定義 ProcessingResult） |

**使用率**: 1/1 (100%)

### 3.3 常數模塊 (7 個)

| 檔案 | 狀態 | 使用階段 |
|------|------|---------|
| `constants/academic_standards.py` | ✅ 使用中 | Stage 5 (RSRP/RSRQ 範圍) |
| `constants/constellation_constants.py` | ✅ 使用中 | Stage 1, Stage 4 |
| `constants/handover_constants.py` | ✅ 使用中 | Stage 6 (3GPP 事件門檻) |
| `constants/physics_constants.py` | ✅ 使用中 | Stage 2, Stage 3, Stage 5 |
| `constants/system_constants.py` | ✅ 使用中 | 所有階段（路徑、並行配置） |
| `constants/tle_constants.py` | ✅ 使用中 | Stage 1 (TLE 格式) |
| `constants/astropy_physics_constants.py` | ❓ 需驗證 | 可能與 physics_constants.py 重複 |

**使用率**: 6/7 確認使用 (85.7%), 1 個待驗證

### 3.4 座標系統模塊 (3 個)

| 檔案 | 狀態 | 使用階段 |
|------|------|---------|
| `coordinate_systems/iers_data_manager.py` | ✅ 使用中 | Stage 3 (極移、UT1-UTC) |
| `coordinate_systems/skyfield_coordinate_engine.py` | ✅ 使用中 | Stage 3 (TEME → ECEF → WGS84) |
| `coordinate_systems/wgs84_manager.py` | ✅ 使用中 | Stage 3, Stage 4 (仰角、方位角) |

**使用率**: 3/3 (100%)

### 3.5 工具函數 (5 個)

| 檔案 | 狀態 | 使用階段 |
|------|------|---------|
| `utils/file_utils.py` | ✅ 使用中 | 所有階段（JSON I/O） |
| `utils/math_utils.py` | ✅ 使用中 | Stage 3, Stage 4, Stage 5 |
| `utils/time_utils.py` | ✅ 使用中 | Stage 1, Stage 2, Stage 3 |
| `utils/coordinate_converter.py` | ✅ 使用中 | Stage 5, Stage 6（ECEF ↔ WGS84 轉換） |
| `utils/ground_distance_calculator.py` | ✅ 使用中 | Stage 6（D2 事件地面距離計算） |

**使用率**: 5/5 (100%)

### 3.6 驗證框架 (5 個)

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `validation_framework/academic_validation_framework.py` | ❓ 需驗證 | 可能用於開發時檢查 |
| `validation_framework/real_time_snapshot_system.py` | ❓ 需驗證 | 可能用於快照生成 |
| `validation_framework/stage4_validator.py` | ❓ 需驗證 | 與 scripts/stage_validators/stage4_validator.py 可能重複 |
| `validation_framework/stage5_signal_validator.py` | ❓ 需驗證 | 與 scripts/stage_validators/stage5_validator.py 可能重複 |
| `validation_framework/validation_engine.py` | ✅ 使用中 | 被處理器內部驗證使用 |

**使用率**: 1/5 確認使用 (20%), 4 個待驗證

**src/shared/ 總使用率**: 21/24 確認使用 (87.5%), 3 個待驗證

---

## 四、獨立工具腳本 (不在六階段執行路徑中)

### 4.1 工具腳本 (2 個)

| 檔案 | 狀態 | 用途 |
|------|------|------|
| `scripts/generate_validation_snapshot.py` | ⚠️ 獨立工具 | 調試用：獨立生成驗證快照 |
| `scripts/run_parameter_sweep.py` | ⚠️ 獨立工具 | 研究用：參數掃描實驗 |

**說明**: 這些是獨立工具，不被 `run_six_stages_with_validation.py` 調用，但有其使用場景：
- `generate_validation_snapshot.py`: 用於調試驗證邏輯
- `run_parameter_sweep.py`: 用於 Stage 6 的參數優化研究

---

## 五、需進一步驗證的檔案 (10 個)

### 5.1 可能未使用的檔案

| 檔案 | 可能原因 | 建議 |
|------|---------|------|
| `stage1/metrics/accuracy_calculator.py` | 未在主處理器中發現導入 | 檢查是否為舊版代碼 |
| `stage1/metrics/consistency_calculator.py` | 未在主處理器中發現導入 | 檢查是否為舊版代碼 |
| `stage1/reports/statistics_reporter.py` | 未在主處理器中發現導入 | 檢查是否為舊版代碼 |
| `stage4/dynamic_threshold_analyzer.py` | 未在主處理器中發現導入 | 可能是舊版功能 |
| `stage4/poliastro_validator.py` | 交叉驗證器（可選） | 確認是否為可選功能 |

### 5.2 可能重複的檔案

| 檔案 | 重複對象 | 建議 |
|------|---------|------|
| `shared/constants/astropy_physics_constants.py` | `constants/physics_constants.py` | 檢查是否內容重複 |
| `shared/validation_framework/stage4_validator.py` | `scripts/stage_validators/stage4_validator.py` | 確認兩者關係 |
| `shared/validation_framework/stage5_signal_validator.py` | `scripts/stage_validators/stage5_validator.py` | 確認兩者關係 |

### 5.3 用途不明的檔案

| 檔案 | 說明 | 建議 |
|------|------|------|
| `shared/validation_framework/academic_validation_framework.py` | 可能用於開發時檢查 | 確認使用場景 |
| `shared/validation_framework/real_time_snapshot_system.py` | 可能用於快照生成 | 確認是否被 generate_validation_snapshot.py 使用 |

---

## 六、使用狀態總結

### 按目錄分類

| 目錄 | 總檔案數 | 確認使用 | 獨立工具 | 待驗證 | 使用率 |
|------|---------|---------|---------|--------|--------|
| scripts/ | 16 | 14 | 2 | 0 | 87.5% |
| src/shared/ | 24 | 21 | 0 | 3 | 87.5% |
| stage1/ | 14 | 8 | 0 | 3 | 57.1% |
| stage2/ | 5 | 4 | 0 | 0 | 80.0% |
| stage3/ | 7 | 5 | 0 | 1 (已禁用) | 71.4% |
| stage4/ | 14 | 10 | 0 | 3 | 71.4% |
| stage5/ | 15 | 12 | 0 | 0 | 80.0% |
| stage6/ | 7 | 7 | 0 | 0 | 100% |
| **總計** | **102** | **81** | **2** | **10** | **79.4%** |

### 按使用狀態分類

| 狀態 | 數量 | 百分比 |
|------|------|--------|
| ✅ 確認使用（六階段執行路徑） | 81 | 79.4% |
| ⚠️ 獨立工具（有其使用場景） | 2 | 2.0% |
| ❓ 待驗證（可能未使用或冗餘） | 10 | 9.8% |
| ⚠️ 已知禁用（保留供參考） | 1 | 1.0% |
| 🗑️ 確認廢棄 | 0 | 0% |

---

## 七、建議行動

### 7.1 立即確認的檔案（高優先級）

**需檢查導入關係**:
```bash
# 檢查這些檔案是否真的被使用
grep -r "accuracy_calculator\|consistency_calculator\|statistics_reporter" src/stages/stage1_orbital_calculation/
grep -r "dynamic_threshold_analyzer\|poliastro_validator" src/stages/stage4_link_feasibility/
grep -r "ground_distance_calculator" src/stages/stage6_research_optimization/
```

### 7.2 檢查重複檔案（中優先級）

**比對內容**:
```bash
# 檢查這兩個常數檔案是否內容重複
diff src/shared/constants/physics_constants.py src/shared/constants/astropy_physics_constants.py

# 檢查驗證器是否重複
diff src/shared/validation_framework/stage4_validator.py scripts/stage_validators/stage4_validator.py
```

### 7.3 確認獨立工具的使用場景（低優先級）

**驗證工具腳本的依賴**:
```bash
# 檢查 generate_validation_snapshot.py 是否使用 real_time_snapshot_system
grep -n "real_time_snapshot_system" scripts/generate_validation_snapshot.py
```

---

## 八、結論

### 使用狀態評估

1. **核心執行路徑檔案 (81 個)**: ✅ 確認被六階段執行系統使用
2. **獨立工具腳本 (2 個)**: ⚠️ 不在執行路徑中，但有其使用場景
3. **可能未使用檔案 (10 個)**: ❓ 需進一步驗證
4. **已知禁用檔案 (1 個)**: ⚠️ `geometric_prefilter.py` (v3.1 已禁用)

### 回答原始問題

**「原本不在六階段執行程式的檔案是否是沒有在使用的檔案？」**

**答案**: 不完全是。可以分為以下幾類：

1. **✅ 有使用，但間接調用** (約 60 個):
   - 各階段子模塊被主處理器導入
   - `src/shared/` 模塊被多個階段使用
   - 這些檔案不直接出現在 `run_six_stages_with_validation.py` 中，但通過導入鏈被使用

2. **⚠️ 獨立工具，有其使用場景** (2 個):
   - `generate_validation_snapshot.py`: 調試用
   - `run_parameter_sweep.py`: 研究實驗用

3. **❓ 可能未使用或冗餘** (10 個):
   - Stage 1 的 metrics/ 和 reports/ 子模塊（可能是舊版）
   - Stage 4 的 `poliastro_validator.py`（可選交叉驗證）
   - `src/shared/validation_framework/` 的部分模塊（可能與 `scripts/stage_validators/` 重複）

4. **⚠️ 已知禁用** (1 個):
   - `stage3/geometric_prefilter.py` (v3.1 版本已禁用，保留供參考)

### 建議

1. **保留**: 核心執行路徑的 81 個檔案 + 2 個獨立工具
2. **驗證**: 10 個可能未使用的檔案（執行上述檢查命令）
3. **清理**: 如驗證後確認未使用，可考慮移至 `archive/` 目錄
4. **文檔化**: 獨立工具的使用場景應該記錄在工具本身的 docstring 中

### 🆕 2025-10-11 重構更新

**完成項目**:
- ✅ 移除重複檔案: Stage 5/6 `coordinate_converter.py` (220行 × 2 = 440行代碼刪除)
- ✅ 整合至共用模組: `src/shared/utils/coordinate_converter.py` 和 `ground_distance_calculator.py`
- ✅ Stage 6 使用率提升: 70% → 100%
- ✅ 總體確認使用率提升: 76.7% → 79.4%

---

**分析完成日期**: 2025-10-10 | **最後更新**: 2025-10-11
**確認使用**: 81/102 (79.4%)
**待驗證**: 10/102 (9.8%)
**獨立工具**: 2/102 (2.0%)
