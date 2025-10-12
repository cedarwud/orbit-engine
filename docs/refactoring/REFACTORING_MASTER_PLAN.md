# Orbit Engine 重構總計劃

**創建日期**: 2025-10-12
**版本**: v1.0
**狀態**: 📋 計劃中

---

## 📚 文檔結構

```
docs/refactoring/
├── REFACTORING_MASTER_PLAN.md                    (本文件 - 總覽)
│
├── phase1_executor_refactor/                     🔴 P0 - 優先級最高
│   ├── 01_overview.md                            階段概述
│   ├── 02_base_executor_implementation.md        基類實現
│   ├── 03_stage_executors_migration.md           執行器遷移
│   ├── 04_testing_strategy.md                    測試策略
│   └── 05_checklist.md                           檢查清單
│
├── phase2_validation_refactor/                   🟠 P1
│   ├── 01_overview.md                            階段概述
│   ├── 02_three_layer_architecture.md            三層驗證架構
│   ├── 03_compliance_validator_base.md           合規驗證器基類
│   ├── 04_stage_validators_migration.md          驗證器遷移
│   ├── 05_testing_strategy.md                    測試策略
│   └── 06_checklist.md                           檢查清單
│
├── phase3_config_unification/                    🟠 P1
│   ├── 01_overview.md                            階段概述
│   ├── 02_stage6_config_file.md                  Stage 6 配置文件
│   ├── 03_config_loader_implementation.md        配置加載器
│   ├── 04_testing_strategy.md                    測試策略
│   └── 05_checklist.md                           檢查清單
│
├── phase4_interface_unification/                 🟡 P2
│   ├── 01_overview.md                            階段概述
│   ├── 02_stage5_migration.md                    Stage 5 遷移
│   ├── 03_stage6_migration.md                    Stage 6 遷移
│   ├── 04_testing_strategy.md                    測試策略
│   └── 05_checklist.md                           檢查清單
│
└── phase5_module_reorganization/                 🟡 P2
    ├── 01_overview.md                            階段概述
    ├── 02_directory_structure.md                 目錄結構設計
    ├── 03_migration_strategy.md                  遷移策略
    ├── 04_deprecation_warnings.md                棄用警告
    ├── 05_testing_strategy.md                    測試策略
    └── 06_checklist.md                           檢查清單
```

---

## 🎯 重構目標

### 主要目標

1. **減少重複代碼**: 預計減少 25% 整體代碼量
2. **提升維護性**: 統一設計模式和接口
3. **增強可測試性**: 基類邏輯可獨立測試
4. **保持向後兼容**: 現有功能不受影響
5. **遵循學術標準**: 不修改核心算法邏輯

### 成功指標

- ✅ 所有測試通過（單元測試 + 集成測試）
- ✅ 完整管道執行成功（Stage 1-6）
- ✅ 驗證快照格式保持一致
- ✅ 性能無退化（執行時間誤差 < 5%）
- ✅ 代碼覆蓋率維持或提升

---

## 📊 優先級與時間規劃

### 優先級定義

- 🔴 **P0**: 必須執行，影響重大
- 🟠 **P1**: 應該執行，顯著改善
- 🟡 **P2**: 可以執行，長期優化

### 時間規劃

| Phase | 優先級 | 預估時間 | 風險 | 依賴關係 |
|-------|-------|---------|------|---------|
| **Phase 1**: 執行器重構 | 🔴 P0 | 1-2 天 | 🟢 低 | 無 |
| **Phase 2**: 驗證邏輯重組 | 🟠 P1 | 2-3 天 | 🟡 中 | Phase 1 完成 |
| **Phase 3**: 配置統一 | 🟠 P1 | 1 天 | 🟢 低 | Phase 1 完成 |
| **Phase 4**: 接口統一 | 🟡 P2 | 1-2 天 | 🟡 中 | Phase 1, 2 完成 |
| **Phase 5**: 模塊重組 | 🟡 P2 | 2-3 天 | 🟠 中高 | Phase 1-4 完成 |

**總計**: 7-11 天（可分階段執行）

---

## 🔴 Phase 1: 執行器重構 (P0)

### 概述

**問題**: 6 個執行器文件存在 70% 重複代碼
**方案**: 引入 `StageExecutor` 基類（Template Method Pattern）
**收益**: 減少 218 行代碼（-38%），統一錯誤處理

### 核心設計

```python
# scripts/stage_executors/base_executor.py (新增)
class StageExecutor(ABC):
    """執行器基類 - 統一執行流程"""

    def execute(self, previous_results):
        """Template Method - 統一流程"""
        # 1. 顯示階段頭部
        # 2. 清理舊輸出
        # 3. 載入前階段數據
        # 4. 載入配置
        # 5. 創建處理器
        # 6. 執行處理
        # 7. 保存驗證快照
        # 8. 錯誤處理

    @abstractmethod
    def load_config(self) -> Dict:
        """子類實現配置加載"""
        pass

    @abstractmethod
    def create_processor(self, config) -> Any:
        """子類實現處理器創建"""
        pass
```

### 遷移順序

1. Stage 1 (最簡單，無前置依賴)
2. Stage 2-3 (標準流程)
3. Stage 4-5 (有配置文件)
4. Stage 6 (最特殊)

### 詳細文檔

- 📄 [01_overview.md](phase1_executor_refactor/01_overview.md)
- 📄 [02_base_executor_implementation.md](phase1_executor_refactor/02_base_executor_implementation.md)
- 📄 [03_stage_executors_migration.md](phase1_executor_refactor/03_stage_executors_migration.md)
- 📄 [04_testing_strategy.md](phase1_executor_refactor/04_testing_strategy.md)
- 📄 [05_checklist.md](phase1_executor_refactor/05_checklist.md)

---

## 🟠 Phase 2: 驗證邏輯重組 (P1)

### 概述

**問題**: 驗證邏輯分散在 3 處，職責重疊
**方案**: 三層驗證架構
**收益**: 職責清晰，減少 400 行代碼（-33%）

### 三層架構

```
┌─────────────────────────────────────┐
│ Layer 1: 數據結構驗證               │
│ 位置: BaseStageProcessor            │
│ 方法: validate_input/validate_output │
│ 時機: 處理前後立即執行               │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Layer 2: 學術合規驗證               │
│ 位置: StageComplianceValidator      │
│ 方法: validate_academic_compliance  │
│ 時機: 處理器內調用                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Layer 3: 回歸測試驗證               │
│ 位置: scripts/stage_validators      │
│ 方法: check_stageN_validation       │
│ 時機: 管道執行完成後                 │
└─────────────────────────────────────┘
```

### 詳細文檔

- 📄 [01_overview.md](phase2_validation_refactor/01_overview.md)
- 📄 [02_three_layer_architecture.md](phase2_validation_refactor/02_three_layer_architecture.md)
- 📄 [03_compliance_validator_base.md](phase2_validation_refactor/03_compliance_validator_base.md)
- 📄 [04_stage_validators_migration.md](phase2_validation_refactor/04_stage_validators_migration.md)
- 📄 [05_testing_strategy.md](phase2_validation_refactor/05_testing_strategy.md)
- 📄 [06_checklist.md](phase2_validation_refactor/06_checklist.md)

---

## 🟠 Phase 3: 配置統一 (P1)

### 概述

**問題**: Stage 6 缺少 YAML 配置文件
**方案**: 創建 `stage6_research_optimization_config.yaml`
**收益**: 參數可調整，無需修改代碼

### 核心設計

```yaml
# config/stage6_research_optimization_config.yaml (新增)

event_detection:
  a3_offset_db: 3.0              # 3GPP TS 38.331 v18.5.1
  a4_threshold_dbm: -110
  a5_threshold1_dbm: -110
  a5_threshold2_dbm: -95
  hysteresis_db: 2.0
  time_to_trigger_ms: 640

handover_decision:
  evaluation_mode: "batch"       # batch | realtime
  serving_selection_strategy: "median"  # median | max_rsrp
  candidate_ranking: "rsrp"      # rsrp | elevation
```

### 詳細文檔

- 📄 [01_overview.md](phase3_config_unification/01_overview.md)
- 📄 [02_stage6_config_file.md](phase3_config_unification/02_stage6_config_file.md)
- 📄 [03_config_loader_implementation.md](phase3_config_unification/03_config_loader_implementation.md)
- 📄 [04_testing_strategy.md](phase3_config_unification/04_testing_strategy.md)
- 📄 [05_checklist.md](phase3_config_unification/05_checklist.md)

---

## 🟡 Phase 4: 接口統一 (P2)

### 概述

**問題**: Stage 5/6 重寫 `execute()`，違反 Template Method Pattern
**方案**: 統一使用 `process()` 方法
**收益**: 接口一致性，自動獲得基類功能

### 核心改動

```python
# ❌ 當前 (Stage 5/6)
class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    def execute(self, input_data):
        # 完全重寫，沒有調用 super()
        ...

# ✅ 重構後
class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    def process(self, input_data):
        # 只實現主邏輯，基類處理驗證和快照
        ...
```

### 詳細文檔

- 📄 [01_overview.md](phase4_interface_unification/01_overview.md)
- 📄 [02_stage5_migration.md](phase4_interface_unification/02_stage5_migration.md)
- 📄 [03_stage6_migration.md](phase4_interface_unification/03_stage6_migration.md)
- 📄 [04_testing_strategy.md](phase4_interface_unification/04_testing_strategy.md)
- 📄 [05_checklist.md](phase4_interface_unification/05_checklist.md)

---

## 🟡 Phase 5: 模塊重組 (P2)

### 概述

**問題**: `src/shared/` 模塊職責不清晰
**方案**: 重組為 `base/`, `coordinate_systems/`, `validation/`, `configs/`
**收益**: 模塊職責清晰，減少耦合

### 目標結構

```
src/shared/
├── base/                          # 基礎類和接口
│   ├── base_processor.py
│   └── processor_interface.py
│
├── constants/                     # 常量定義（保持不變）
│
├── coordinate_systems/            # 座標系統（整合）
│   ├── converters/               # 從 utils 移入
│   ├── iers_data_manager.py
│   └── skyfield_coordinate_engine.py
│
├── validation/                    # 驗證框架（重構）
│   ├── compliance_validator.py
│   ├── data_validator.py
│   └── snapshot_manager.py
│
├── configs/                       # 配置管理（新增）
│   └── config_loader.py
│
└── utils/                         # 通用工具（精簡）
    ├── file_utils.py
    ├── math_utils.py
    └── time_utils.py
```

### 詳細文檔

- 📄 [01_overview.md](phase5_module_reorganization/01_overview.md)
- 📄 [02_directory_structure.md](phase5_module_reorganization/02_directory_structure.md)
- 📄 [03_migration_strategy.md](phase5_module_reorganization/03_migration_strategy.md)
- 📄 [04_deprecation_warnings.md](phase5_module_reorganization/04_deprecation_warnings.md)
- 📄 [05_testing_strategy.md](phase5_module_reorganization/05_testing_strategy.md)
- 📄 [06_checklist.md](phase5_module_reorganization/06_checklist.md)

---

## 🧪 測試策略

### 測試層級

1. **單元測試**: 測試基類和新增模塊
   ```bash
   pytest tests/unit/refactoring/test_base_executor.py
   pytest tests/unit/refactoring/test_compliance_validator.py
   ```

2. **集成測試**: 測試階段執行流程
   ```bash
   pytest tests/integration/test_stage1_executor_refactored.py
   ```

3. **端到端測試**: 完整管道測試
   ```bash
   ./run.sh
   pytest tests/e2e/test_full_pipeline.py
   ```

4. **回歸測試**: 對比重構前後輸出
   ```bash
   python tests/regression/compare_outputs.py
   ```

### 測試覆蓋率目標

- 新增代碼: ≥ 90%
- 重構代碼: ≥ 80%
- 整體維持: ≥ 75%

---

## 📋 實施流程

### 每個 Phase 的標準流程

1. **📖 閱讀概述文檔**
   - 理解問題和方案
   - 確認依賴關係

2. **💻 實施重構**
   - 按照詳細文檔執行
   - 提交小的原子性 commit

3. **🧪 執行測試**
   - 單元測試 → 集成測試 → E2E 測試
   - 確保所有測試通過

4. **✅ 檢查清單**
   - 使用 checklist.md 逐項驗證
   - 記錄任何偏差或問題

5. **📝 更新文檔**
   - 更新相關技術文檔
   - 記錄重構決策

6. **🔍 代碼審查**
   - 自我審查（使用 checklist）
   - 團隊審查（如適用）

---

## ⚠️ 風險管理

### 識別的風險

| 風險 | 等級 | 緩解措施 |
|-----|------|---------|
| 破壞現有功能 | 🟠 中 | 完整測試覆蓋，分階段執行 |
| 性能退化 | 🟡 低 | 基準測試，性能監控 |
| 引入新 Bug | 🟠 中 | 小步提交，充分測試 |
| 時間超支 | 🟡 低 | 按優先級執行，可暫停 |
| 團隊協作衝突 | 🟢 低 | 分支開發，定期同步 |

### 回滾策略

1. **每個 Phase 獨立分支**
   ```bash
   git checkout -b refactor/phase1-executor
   ```

2. **頻繁提交**
   ```bash
   git commit -m "refactor(phase1): implement base executor"
   ```

3. **保留回滾點**
   ```bash
   git tag phase1-complete
   ```

4. **緊急回滾**
   ```bash
   git checkout main
   git revert <commit-hash>
   ```

---

## 📈 進度追蹤

### 當前狀態

| Phase | 狀態 | 開始日期 | 完成日期 | 備註 |
|-------|-----|---------|---------|------|
| Phase 1 | 📋 計劃中 | - | - | 文檔已準備 |
| Phase 2 | 📋 計劃中 | - | - | 文檔已準備 |
| Phase 3 | 📋 計劃中 | - | - | 文檔已準備 |
| Phase 4 | 📋 計劃中 | - | - | 文檔已準備 |
| Phase 5 | 📋 計劃中 | - | - | 文檔已準備 |

### 更新指南

執行完成後，更新此表格：
- 📋 計劃中 → 🚧 進行中 → ✅ 已完成
- 記錄實際日期
- 添加備註（如有偏差或重要決策）

---

## 🎓 學習資源

### 設計模式

- **Template Method Pattern**: Phase 1 執行器基類
- **Strategy Pattern**: Phase 2 驗證策略
- **Factory Pattern**: Phase 3 配置加載器
- **Adapter Pattern**: Phase 5 模塊遷移

### 重構原則

- **Small Steps**: 小步提交，頻繁測試
- **Keep It Working**: 每次提交保持可運行
- **Test-Driven**: 測試先行或同步
- **Backward Compatible**: 保持向後兼容

---

## 📞 支持

### 遇到問題時

1. **查閱相關文檔**
   - 檢查對應 Phase 的詳細文檔
   - 參考 checklist.md 確認遺漏步驟

2. **檢查測試**
   - 運行測試找出具體錯誤
   - 查看測試日誌定位問題

3. **回滾並重試**
   - 使用 git 回滾到上一個穩定點
   - 重新閱讀文檔並執行

4. **記錄問題**
   - 在對應 Phase 的 README 中記錄
   - 更新 checklist 添加檢查項

---

## 🏁 完成標準

### Phase 完成標準

✅ 所有代碼已實施並提交
✅ 所有測試通過（單元+集成+E2E）
✅ Checklist 全部勾選
✅ 文檔已更新
✅ 性能無退化（< 5%）
✅ 驗證快照格式一致

### 整體完成標準

✅ 所有 5 個 Phase 完成
✅ 完整管道運行成功
✅ 代碼覆蓋率達標（≥75%）
✅ 架構文檔已更新
✅ 團隊培訓完成（如適用）

---

**版本歷史**
- v1.0 (2025-10-12): 初始版本，建立重構計劃

**下一步**: 開始 [Phase 1: 執行器重構](phase1_executor_refactor/01_overview.md)
