# Phase 4: 實施路線圖

**創建日期**: 2025-10-15
**狀態**: 📋 計劃中
**預估總時間**: 4天（必須項）+ 3.5天（可選項）= 7.5天

---

## 📊 執行摘要

Phase 4 聚焦於剩餘架構優化機會，分為 **P1（必須）**、**P2（應該）**、**P3（可選）** 三個優先級。本文檔提供詳細的週次執行計劃、依賴關係和檢查點。

---

## 🗓️ 週次計劃

### 第1週: P1 優先級（必須執行）

**目標**: 完成配置管理統一

#### Day 1-1: 配置管理統一（8小時）

**文檔**: [02_P1_CONFIGURATION_UNIFICATION.md](02_P1_CONFIGURATION_UNIFICATION.md)

**任務清單**:

**上午（4小時）**:
- [ ] **08:00-09:30** 創建 `src/shared/config_manager.py`（BaseConfigManager 基類）
  - 實作 Template Method Pattern
  - 實作 load_config(), validate_config()
  - 實作環境變數覆寫機制
  - **檢查點**: BaseConfigManager 類別完整（150行代碼）

- [ ] **09:30-10:00** 創建 `config/stage1_orbital_initialization_config.yaml`
  - 外部化 latest_date 配置
  - 外部化 constellation 篩選配置
  - **檢查點**: Stage 1 YAML 配置完整

- [ ] **10:00-10:30** 創建 `config/stage3_coordinate_transformation_config.yaml`
  - 外部化坐標轉換參數
  - 外部化緩存配置
  - **檢查點**: Stage 3 YAML 配置完整

- [ ] **10:30-11:00** 創建 `config/stage6_research_optimization_config.yaml`
  - 外部化 3GPP 事件門檻
  - 外部化 RL 訓練參數
  - **檢查點**: Stage 6 YAML 配置完整

- [ ] **11:00-12:00** 編寫 BaseConfigManager 單元測試
  - 測試配置載入
  - 測試環境變數覆寫
  - 測試驗證機制
  - **檢查點**: 測試覆蓋率 ≥ 80%

**下午（4小時）**:
- [ ] **13:00-14:00** 遷移 Stage 1 Executor 使用 BaseConfigManager
  - 修改 stage1_executor.py
  - 移除硬編碼配置
  - **檢查點**: Stage 1 配置外部化完成

- [ ] **14:00-15:00** 遷移 Stage 3 Processor 使用 BaseConfigManager
  - 修改 stage3_processor.py
  - 移除硬編碼參數
  - **檢查點**: Stage 3 配置外部化完成

- [ ] **15:00-16:00** 遷移 Stage 6 Processor 使用 BaseConfigManager
  - 創建 Stage6ConfigManager
  - 修改 stage6_processor.py
  - **檢查點**: Stage 6 配置外部化完成

- [ ] **16:00-17:00** 執行全量測試
  - 運行 `./run.sh --stages 1-6`
  - 驗證配置載入正確
  - 驗證輸出結果不變
  - **檢查點**: 所有測試通過，輸出一致

**里程碑**: ✅ P1 配置管理統一完成

---

### 第2週: P2 優先級（應該執行）

**目標**: 完成錯誤處理標準化和 HDF5 策略統一

#### Day 2-1: 錯誤處理標準化（4小時）

**文檔**: [03_P2_ERROR_HANDLING.md](03_P2_ERROR_HANDLING.md)

**任務清單**:

**上午（2小時）**:
- [ ] **08:00-09:00** 創建 `src/shared/exceptions.py`
  - 實作 OrbitEngineError 基類
  - 實作 14個專用異常類型
  - 實作向後相容別名
  - **檢查點**: 異常模組完整（450行代碼）

- [ ] **09:00-10:00** 編寫異常模組單元測試
  - 測試異常創建和格式化
  - 測試 wrap_exception() helper
  - 測試向後相容別名
  - **檢查點**: 測試覆蓋率 ≥ 90%

**下午（2小時）**:
- [ ] **13:00-14:30** 遷移 Stage 2-6 異常處理
  - 批量替換 ValueError → InvalidDataError
  - 批量替換 FileNotFoundError → 自定義 FileNotFoundError
  - 添加上下文信息
  - **檢查點**: 每個階段至少5處異常遷移

- [ ] **14:30-15:30** 更新 shared utilities 異常處理
  - 遷移 BaseResultManager Fail-Fast 檢查
  - 遷移坐標轉換器異常
  - **檢查點**: shared 模組異常統一

- [ ] **15:30-16:00** 執行測試驗證
  - 運行單元測試
  - 測試錯誤場景（故意觸發異常）
  - **檢查點**: 所有測試通過

**里程碑**: ✅ 錯誤處理標準化完成

---

#### Day 2-2: HDF5 策略統一（4小時）

**文檔**: [04_P2_HDF5_STRATEGY.md](04_P2_HDF5_STRATEGY.md)

**任務清單**:

**上午（2小時）**:
- [ ] **08:00-09:30** 創建 `src/shared/hdf5_handler.py`
  - 實作 BaseHDF5Handler 基類
  - 實作 HDF5OutputStrategy（Stage 2）
  - 實作 HDF5CacheStrategy（Stage 3）
  - **檢查點**: HDF5 handler 完整（350行代碼）

- [ ] **09:30-10:00** 編寫 HDF5 handler 單元測試
  - 測試 save/load 操作
  - 測試緩存驗證邏輯
  - **檢查點**: 測試覆蓋率 ≥ 80%

**下午（2小時）**:
- [ ] **13:00-13:30** 遷移 Stage 2 使用 HDF5OutputStrategy
  - 修改 Stage2ResultManager
  - 移除自定義 HDF5 代碼
  - **檢查點**: Stage 2 HDF5 輸出正常

- [ ] **13:30-14:00** 遷移 Stage 3 使用 HDF5CacheStrategy
  - 修改 Stage3HDF5Cache
  - 簡化為 strategy 包裝類
  - **檢查點**: Stage 3 緩存正常

- [ ] **14:00-15:00** 執行集成測試
  - 測試 Stage 2 雙格式輸出
  - 測試 Stage 3 緩存加速
  - 驗證性能無退化
  - **檢查點**: HDF5 功能正常，性能符合預期

**里程碑**: ✅ HDF5 策略統一完成

---

### 第3週: P2 優先級（測試框架）

**目標**: 補充基類單元測試，達成 80%+ 覆蓋率

#### Day 3-1: Executor 和 Validator 測試（8小時）

**文檔**: [05_P2_TESTING_FRAMEWORK.md](05_P2_TESTING_FRAMEWORK.md)

**任務清單**:

**上午（4小時）**:
- [ ] **08:00-11:00** 創建 `tests/unit/scripts/test_stage_executor.py`
  - 實作 MockStageExecutor
  - 編寫 Template Method 測試（15個測試用例）
  - 編寫錯誤處理測試（6個測試用例）
  - 編寫性能基準測試
  - **檢查點**: StageExecutor 覆蓋率 ≥ 85%

- [ ] **11:00-12:00** 創建 `tests/unit/scripts/test_stage_validator.py`
  - 實作 MockStageValidator
  - 編寫 Template Method 測試（10個測試用例）
  - 編寫通用驗證測試（8個測試用例）
  - **檢查點**: StageValidator 覆蓋率 ≥ 85%

**下午（4小時）**:
- [ ] **13:00-15:00** 創建 `tests/unit/shared/test_base_processor.py`
  - 實作 MockStageProcessor
  - 編寫 execute() 測試（8個測試用例）
  - 編寫 execute() 覆寫警告測試
  - 編寫 ProcessingResult 測試
  - **檢查點**: BaseStageProcessor 覆蓋率 ≥ 85%

- [ ] **15:00-16:00** 補充 `tests/unit/shared/test_base_result_manager.py`
  - 添加大型數據集測試
  - 添加特殊字符測試
  - 添加磁碟空間錯誤測試
  - **檢查點**: BaseResultManager 覆蓋率保持 ≥ 90%

- [ ] **16:00-17:00** 執行測試並生成覆蓋率報告
  - 運行 `pytest tests/unit/ --cov`
  - 生成 HTML 覆蓋率報告
  - 驗證所有基類覆蓋率 ≥ 80%
  - **檢查點**: 測試覆蓋率達標

**里程碑**: ✅ 基類單元測試完成

---

#### Day 3-2: CI 集成（2小時）

**文檔**: [05_P2_TESTING_FRAMEWORK.md](05_P2_TESTING_FRAMEWORK.md)

**任務清單**:

**上午（2小時）**:
- [ ] **08:00-09:00** 創建 `.github/workflows/test-base-classes.yml`
  - 配置 GitHub Actions 工作流
  - 設置覆蓋率門檻（80%）
  - 配置 codecov 上傳
  - **檢查點**: CI workflow 配置完整

- [ ] **09:00-10:00** 測試 CI 流程
  - 創建測試 PR
  - 驗證 CI 自動運行
  - 驗證覆蓋率報告生成
  - **檢查點**: CI 正常運行

**里程碑**: ✅ 測試框架完善完成

---

### 第4週: P3 優先級（可選執行）

**目標**: 日誌系統統一化和模塊重組

#### Day 4-1: 日誌系統統一化（4小時）

**文檔**: [06_P3_LOGGING_SYSTEM.md](06_P3_LOGGING_SYSTEM.md)

**任務清單**:

**上午（2小時）**:
- [ ] **08:00-09:00** 創建 `src/shared/logging_config.py`
  - 實作 StructuredFormatter
  - 實作 get_logger() 函數
  - 實作 configure_logging() 函數
  - **檢查點**: 日誌配置模組完整（200行代碼）

- [ ] **09:00-10:00** 定義日誌標準文檔
  - 編寫日誌級別使用指引
  - 編寫 Emoji 使用規範
  - 編寫結構化日誌範例
  - **檢查點**: 日誌標準文檔完整

**下午（2小時）**:
- [ ] **13:00-14:30** 遷移 Stage 2-6 日誌調用
  - 替換 logging.getLogger() 為 get_logger()
  - 添加結構化字段（extra）
  - 統一日誌格式
  - **檢查點**: 每個階段主要日誌遷移

- [ ] **14:30-15:00** 更新 shared utilities 日誌
  - 遷移基類日誌調用
  - 統一格式
  - **檢查點**: shared 模組日誌統一

- [ ] **15:00-16:00** 執行測試驗證
  - 測試日誌輸出格式
  - 測試環境變數控制
  - 測試結構化字段
  - **檢查點**: 日誌功能正常

**里程碑**: ✅ 日誌系統統一化完成

---

#### Day 4-2 ~ 4-4: 模塊重組（2-3天，高風險可選）

**文檔**: [07_P3_MODULE_REORGANIZATION.md](07_P3_MODULE_REORGANIZATION.md)

**任務清單**:

**Day 4-2 上午（4小時）**:
- [ ] **08:00-10:00** 創建新目錄結構
  - 創建 src/shared/{base,core,storage,geometry,time,math}/
  - 複製（不移動）檔案到新位置
  - **檢查點**: 新目錄結構完整

- [ ] **10:00-12:00** 實作向後相容層
  - 修改 src/shared/__init__.py
  - 修改 src/shared/utils/__init__.py
  - 創建 alias 檔案
  - **檢查點**: 舊 import 路徑仍然有效

**Day 4-2 下午（4小時）**:
- [ ] **13:00-15:00** 創建 import 遷移工具
  - 編寫 tools/migrate_imports.py
  - 定義 import 映射規則
  - **檢查點**: 遷移工具完整（150行代碼）

- [ ] **15:00-16:00** 執行 dry-run 測試
  - 運行 `python tools/migrate_imports.py --dry-run`
  - 檢查預覽變更
  - **檢查點**: 工具正確識別所有 import

**Day 4-3 全天（8小時）**:
- [ ] **08:00-10:00** 執行 import 遷移
  - 運行 `python tools/migrate_imports.py --execute`
  - 手動檢查複雜情況
  - **檢查點**: Import 遷移完成

- [ ] **10:00-12:00** 執行單元測試
  - 運行 `pytest tests/unit/`
  - 修復測試中的 import 問題
  - **檢查點**: 單元測試 100% 通過

- [ ] **13:00-15:00** 執行集成測試
  - 運行 `pytest tests/integration/`
  - 修復集成測試中的問題
  - **檢查點**: 集成測試 100% 通過

- [ ] **15:00-17:00** 執行 E2E 測試
  - 運行 `./run.sh --stages 1-6`
  - 驗證完整管道正常
  - **檢查點**: E2E 測試通過

**Day 4-4 上午（2小時）**:
- [ ] **08:00-10:00** 更新文檔
  - 更新 CLAUDE.md import 路徑
  - 更新 README.md
  - 創建 import 指引文檔
  - **檢查點**: 文檔更新完成

**里程碑**: ✅ 模塊重組完成（可選）

---

## 📊 優先級執行策略

### 必須執行（4天）

```
Week 1: P1 - Configuration Management (1 day)
Week 2: P2 - Error Handling (0.5 day) + HDF5 Strategy (0.5 day)
Week 3: P2 - Testing Framework (1.5 day)
───────────────────────────────────────────────
Total: 4 days
```

**如果時間有限，建議執行此部分。**

---

### 推薦執行（7.5天）

```
Week 1: P1 - Configuration Management (1 day)
Week 2: P2 - Error Handling (0.5 day) + HDF5 Strategy (0.5 day)
Week 3: P2 - Testing Framework (1.5 day)
Week 4: P3 - Logging System (0.5 day) + Module Reorganization (2-3 days)
────────────────────────────────────────────────────────────────────
Total: 7.5 days
```

**推薦完整執行，包含可選項，長期收益更大。**

---

## 🚦 檢查點和里程碑

### 檢查點類型

**🟢 綠色檢查點** - 功能完整性檢查
- 代碼實作完整
- 基本功能可運行

**🟡 黃色檢查點** - 質量檢查
- 測試覆蓋率達標
- 代碼審查通過

**🔴 紅色檢查點** - 門禁檢查（必須通過才能繼續）
- 所有測試通過
- 向後相容性 100%
- 性能無退化

---

### 里程碑定義

| 里程碑 | 完成標準 | 檢查方式 |
|-------|---------|---------|
| **P1 完成** | Stage 1/3/6 配置外部化，所有測試通過 | `./run.sh --stages 1-6` 成功 |
| **P2 錯誤處理完成** | 異常模組測試覆蓋率 ≥ 90%，所有階段遷移 | `pytest tests/unit/shared/test_exceptions.py -v` |
| **P2 HDF5 完成** | Stage 2/3 使用新 handler，性能無退化 | `./run.sh --stage 2 && ./run.sh --stage 3` |
| **P2 測試完成** | 基類覆蓋率 ≥ 80%，CI 正常運行 | `pytest --cov tests/unit/ --cov-fail-under=80` |
| **P3 日誌完成** | 日誌格式一致性 ≥ 90% | 手動檢查日誌輸出 |
| **P3 重組完成** | Import 遷移完成，所有測試通過 | `pytest tests/ && ./run.sh --stages 1-6` |

---

## 📋 每日工作流程

### 標準工作流程

**每日開始（15分鐘）**:
1. Review 前一天工作成果
2. 檢查 Git 狀態（確保在 feature branch）
3. 拉取最新代碼（如多人協作）
4. Review 今日任務清單

**實施階段（6-7小時）**:
5. 按照任務清單逐項執行
6. 每完成一項任務，立即運行相關測試
7. 通過檢查點後，提交 Git commit
8. 記錄遇到的問題和解決方案

**每日結束（15分鐘）**:
9. 運行全量測試（如可行）
10. 推送到 remote branch
11. 更新進度文檔
12. 記錄明日待辦事項

---

### Commit Message 規範

**格式**: `<type>(<scope>): <subject>`

**類型（type）**:
- `feat`: 新功能
- `refactor`: 重構
- `test`: 測試
- `docs`: 文檔
- `fix`: 修復

**範圍（scope）**:
- `phase4`: Phase 4 相關
- `config`: 配置管理
- `exceptions`: 異常處理
- `hdf5`: HDF5 策略
- `testing`: 測試框架
- `logging`: 日誌系統
- `structure`: 模塊重組

**範例**:
```
feat(phase4): add BaseConfigManager for unified configuration
refactor(phase4): migrate Stage 2-6 to use new exception types
test(phase4): add unit tests for StageExecutor base class
docs(phase4): create Phase 4 implementation roadmap
```

---

## 🔄 滾動調整策略

### 如果進度落後

**策略 1: 調整優先級**
- 優先完成 P1（必須）
- P2 按影響範圍排序（Testing > Error Handling > HDF5）
- P3 可延後到 Phase 5

**策略 2: 減少範圍**
- 配置管理：僅遷移 Stage 1, 6（Stage 3 延後）
- 錯誤處理：僅遷移關鍵異常（MissingDataError, ConfigurationError）
- 測試框架：僅補充 StageExecutor 測試（其他延後）

**策略 3: 增加資源**
- P2 任務可並行執行（Error Handling + HDF5 同時進行）
- 測試編寫可外包給團隊成員

---

### 如果進度超前

**策略 1: 提前執行 P3**
- 完成日誌系統統一化
- 評估模塊重組風險後決定是否執行

**策略 2: 提升質量**
- 提高測試覆蓋率目標（80% → 90%）
- 補充更多邊界條件測試
- 補充性能基準測試

**策略 3: 準備 Phase 5**
- 閱讀 Phase 5 性能優化文檔（如已準備）
- Profiling 當前管道找出瓶頸
- 準備性能優化方案

---

## ⚠️ 風險管理

### 高風險任務

| 任務 | 風險 | 緩解措施 | 回退方案 |
|-----|------|---------|---------|
| **模塊重組** | Import 遷移破壞代碼 | 保留向後相容層，漸進式遷移 | 回退到舊結構，僅保留新目錄 |
| **HDF5 策略** | 性能退化 | 保持原有壓縮參數和算法 | 回退到原實作 |
| **配置外部化** | 配置變更影響行為 | 保持預設值與現有行為一致 | 硬編碼配置作為 fallback |

---

### 緊急停止條件

**立即停止並回退，如果**:
- 🔴 測試通過率 < 90%（持續 2天）
- 🔴 E2E 測試失敗無法修復（超過 4小時）
- 🔴 性能退化 > 10%（持續）
- 🔴 生產環境（如有）受到影響

---

## ✅ 最終驗收標準

**Phase 4 完成條件**（必須全部達成）:

### 功能性標準
- ✅ P1 任務 100% 完成
- ✅ P2 任務中至少 2項完成（推薦全部完成）
- ✅ 所有單元測試通過（100%）
- ✅ 所有集成測試通過（100%）
- ✅ E2E 測試通過（`./run.sh --stages 1-6` 成功）

### 質量標準
- ✅ 基類測試覆蓋率 ≥ 80%
- ✅ 新增模組測試覆蓋率 ≥ 80%
- ✅ 向後相容性 100%（無破壞性變更）
- ✅ 性能退化 < 5%

### 文檔標準
- ✅ 所有新模組包含完整 docstring
- ✅ CLAUDE.md 更新（如有 import 路徑變更）
- ✅ Phase 4 完成報告編寫

---

## 📚 參考資料

- [00_OVERVIEW.md](00_OVERVIEW.md) - Phase 4 總覽
- [01_CURRENT_STATUS.md](01_CURRENT_STATUS.md) - 當前狀態分析
- [02-07 詳細設計文檔](.) - 各任務詳細設計
- [09_CHECKLIST.md](09_CHECKLIST.md) - 檢查清單

---

## 🎯 下一步行動

1. **確認執行範圍**: 決定執行 P1+P2（必須），還是包含 P3（推薦）
2. **創建 Feature Branch**: `git checkout -b refactor/phase4-optimizations`
3. **開始第1週 Day 1-1**: 配置管理統一
4. **定期同步**: 每天結束時推送進度，每週進行 review

---

**準備好了嗎？讓我們開始 Phase 4 的旅程！🚀**
