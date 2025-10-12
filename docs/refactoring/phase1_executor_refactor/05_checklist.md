# Phase 1: 執行器重構 - 檢查清單

使用此清單逐項驗證重構完成度。

---

## 📋 實施前準備

- [ ] 已閱讀 [01_overview.md](01_overview.md)
- [ ] 已閱讀 [02_base_executor_implementation.md](02_base_executor_implementation.md)
- [ ] 已閱讀 [03_stage_executors_migration.md](03_stage_executors_migration.md)
- [ ] 已閱讀 [04_testing_strategy.md](04_testing_strategy.md)
- [ ] 已創建 git 分支: `git checkout -b refactor/phase1-executor`
- [ ] 已標記開始點: `git tag phase1-start`

---

## 🔧 基類實現

- [ ] 創建 `scripts/stage_executors/base_executor.py`
- [ ] 實現 `StageExecutor` 類
  - [ ] `__init__()` 方法
  - [ ] `execute()` 模板方法
  - [ ] `load_config()` 抽象方法
  - [ ] `create_processor()` 抽象方法
  - [ ] `requires_previous_stage()` 方法
  - [ ] `_print_stage_header()` 方法
  - [ ] `_load_previous_stage_data()` 方法
  - [ ] `_check_result()` 方法
  - [ ] `_save_validation_snapshot()` 方法
- [ ] 創建 `tests/unit/refactoring/test_base_executor.py`
- [ ] 運行單元測試: `pytest tests/unit/refactoring/test_base_executor.py -v`
- [ ] 檢查覆蓋率: `pytest tests/unit/refactoring/test_base_executor.py --cov`
- [ ] 提交: `git commit -m "refactor(phase1): implement base executor"`

---

## 🔄 Stage 1 遷移

- [ ] 創建 `Stage1Executor` 類繼承 `StageExecutor`
- [ ] 實現 `load_config()` 方法
- [ ] 實現 `create_processor()` 方法
- [ ] 實現 `requires_previous_stage()` (返回 False)
- [ ] 保留向後兼容函數 `execute_stage1()`
- [ ] 運行單元測試: `pytest tests/unit/executors/test_stage1_executor.py -v`
- [ ] 運行集成測試: `pytest tests/integration/test_stage1_full.py -v`
- [ ] 運行 Stage 1 單獨: `./run.sh --stage 1`
- [ ] 驗證輸出格式一致
- [ ] 提交: `git commit -m "refactor(phase1): migrate stage1 executor"`

---

## 🔄 Stage 2 遷移

- [ ] 創建 `Stage2Executor` 類繼承 `StageExecutor`
- [ ] 實現 `load_config()` 方法
- [ ] 實現 `create_processor()` 方法
- [ ] 保留向後兼容函數 `execute_stage2()`
- [ ] 運行單元測試
- [ ] 運行集成測試
- [ ] 運行 Stage 1-2: `./run.sh --stages 1-2`
- [ ] 驗證輸出格式一致
- [ ] 提交: `git commit -m "refactor(phase1): migrate stage2 executor"`

---

## 🔄 Stage 3 遷移

- [ ] 創建 `Stage3Executor` 類繼承 `StageExecutor`
- [ ] 實現 `load_config()` 方法
- [ ] 實現 `create_processor()` 方法
- [ ] 保留向後兼容函數 `execute_stage3()`
- [ ] 運行單元測試
- [ ] 運行集成測試
- [ ] 運行 Stage 1-3: `./run.sh --stages 1-3`
- [ ] 驗證輸出格式一致
- [ ] 提交: `git commit -m "refactor(phase1): migrate stage3 executor"`

---

## 🔄 Stage 4 遷移

- [ ] 創建 `Stage4Executor` 類繼承 `StageExecutor`
- [ ] 實現 `load_config()` 方法（處理 YAML 配置）
- [ ] 實現 `create_processor()` 方法
- [ ] 保留向後兼容函數 `execute_stage4()`
- [ ] 運行單元測試
- [ ] 運行集成測試
- [ ] 運行 Stage 1-4: `./run.sh --stages 1-4`
- [ ] 驗證輸出格式一致
- [ ] 提交: `git commit -m "refactor(phase1): migrate stage4 executor"`

---

## 🔄 Stage 5 遷移

- [ ] 創建 `Stage5Executor` 類繼承 `StageExecutor`
- [ ] 實現 `load_config()` 方法（處理 YAML 配置）
- [ ] 實現 `create_processor()` 方法
- [ ] 保留向後兼容函數 `execute_stage5()`
- [ ] 運行單元測試
- [ ] 運行集成測試
- [ ] 運行 Stage 1-5: `./run.sh --stages 1-5`
- [ ] 驗證輸出格式一致
- [ ] 提交: `git commit -m "refactor(phase1): migrate stage5 executor"`

---

## 🔄 Stage 6 遷移

- [ ] 創建 `Stage6Executor` 類繼承 `StageExecutor`
- [ ] 實現 `load_config()` 方法（處理可選配置）
- [ ] 實現 `create_processor()` 方法
- [ ] 保留向後兼容函數 `execute_stage6()`
- [ ] 運行單元測試
- [ ] 運行集成測試
- [ ] 運行完整管道: `./run.sh`
- [ ] 驗證輸出格式一致
- [ ] 提交: `git commit -m "refactor(phase1): migrate stage6 executor"`

---

## 🧪 測試驗證

### 單元測試
- [ ] Base Executor 測試通過
- [ ] Stage 1 Executor 測試通過
- [ ] Stage 2 Executor 測試通過
- [ ] Stage 3 Executor 測試通過
- [ ] Stage 4 Executor 測試通過
- [ ] Stage 5 Executor 測試通過
- [ ] Stage 6 Executor 測試通過

### 集成測試
- [ ] Stage 1 集成測試通過
- [ ] Stage 1-2 集成測試通過
- [ ] Stage 1-3 集成測試通過
- [ ] Stage 1-4 集成測試通過
- [ ] Stage 1-5 集成測試通過
- [ ] Stage 1-6 (完整管道) 集成測試通過

### 端到端測試
- [ ] 運行 `./run.sh` 成功
- [ ] 所有階段輸出文件生成
- [ ] 所有驗證快照生成
- [ ] 驗證快照格式正確

### 回歸測試
- [ ] 對比重構前後 Stage 1 輸出: 一致
- [ ] 對比重構前後 Stage 2 輸出: 一致
- [ ] 對比重構前後 Stage 3 輸出: 一致
- [ ] 對比重構前後 Stage 4 輸出: 一致
- [ ] 對比重構前後 Stage 5 輸出: 一致
- [ ] 對比重構前後 Stage 6 輸出: 一致

### 性能測試
- [ ] 記錄重構前執行時間（基準）
- [ ] 記錄重構後執行時間
- [ ] 計算性能差異: ____% （應 < 5%）
- [ ] 性能無退化

---

## 📊 代碼品質

- [ ] 代碼覆蓋率 ≥ 85%
  ```bash
  pytest tests/unit/refactoring/ --cov=scripts.stage_executors --cov-report=html
  ```
- [ ] 無 Pylint 警告（或已記錄例外）
  ```bash
  pylint scripts/stage_executors/base_executor.py
  ```
- [ ] 無 Flake8 警告
  ```bash
  flake8 scripts/stage_executors/base_executor.py
  ```
- [ ] 型別檢查通過（如使用 mypy）
  ```bash
  mypy scripts/stage_executors/base_executor.py
  ```

---

## 📝 文檔更新

- [ ] 更新 `docs/architecture/02_STAGES_DETAIL.md`
  - [ ] 添加執行器基類說明
  - [ ] 更新執行器實現章節
- [ ] 更新 `docs/CLAUDE.md`
  - [ ] 添加新增階段的執行器模板
- [ ] 更新 `README.md`（如需要）
- [ ] 添加變更日誌條目

---

## 🎯 向後兼容性

- [ ] 保留所有 `execute_stageN()` 函數
- [ ] 原有調用方式仍然工作
  ```python
  from scripts.stage_executors.stage1_executor import execute_stage1
  success, result, processor = execute_stage1()
  ```
- [ ] 新調用方式正常工作
  ```python
  from scripts.stage_executors.stage1_executor import Stage1Executor
  executor = Stage1Executor()
  success, result, processor = executor.execute()
  ```

---

## 🚀 最終驗收

- [ ] 完整管道運行 3 次，全部成功
- [ ] 所有測試套件通過
- [ ] 代碼審查完成（自我審查或團隊審查）
- [ ] 文檔審查完成
- [ ] 性能基準測試通過
- [ ] 創建 PR（如使用 PR 流程）
- [ ] 標記完成點: `git tag phase1-complete`

---

## ✅ 完成標準

### 必須滿足

- ✅ 所有測試通過（單元+集成+E2E）
- ✅ 代碼覆蓋率 ≥ 85%
- ✅ 回歸測試通過（輸出一致）
- ✅ 性能無退化（< 5%）
- ✅ 文檔更新完成
- ✅ 向後兼容保證

### 可選改進

- ⭐ 代碼覆蓋率 ≥ 90%
- ⭐ 性能提升（如有）
- ⭐ 額外測試用例
- ⭐ 更詳細的文檔

---

## 📋 問題追蹤

發現問題時，在此記錄：

| 日期 | 問題描述 | 嚴重程度 | 狀態 | 解決方案 |
|-----|---------|---------|------|---------|
| ___ | _______ | _______ | ____ | _______ |

---

## 🎓 經驗教訓

完成後記錄：

### 成功經驗
-

### 遇到的挑戰
-

### 改進建議
-

---

**最後更新**: ___________
**完成日期**: ___________
**審查者**: ___________
