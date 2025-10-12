# Phase 1: 執行器重構 - 概述

**優先級**: 🔴 P0 (必須執行)
**預估時間**: 1-2 天
**風險等級**: 🟢 低
**依賴關係**: 無

---

## 📋 問題描述

### 當前狀況

6 個執行器文件 (`scripts/stage_executors/stage1_executor.py` ~ `stage6_executor.py`) 存在嚴重的代碼重複：

```
scripts/stage_executors/
├── stage1_executor.py    (92 行)
├── stage2_executor.py    (83 行)
├── stage3_executor.py    (99 行)
├── stage4_executor.py    (77 行)
├── stage5_executor.py    (153 行)
└── stage6_executor.py    (64 行)
─────────────────────────────────
總計:                     568 行
```

### 重複模式分析

每個執行器都包含相同的結構：

```python
def execute_stageN(previous_results):
    try:
        print('\n📦 階段N：...')              # ✅ 100% 重複
        print('-' * 60)                       # ✅ 100% 重複

        clean_stage_outputs(N)                # ✅ 100% 重複

        # 尋找前階段輸出 (Stage 2-6)         # ✅ 85% 重複
        stageN_output = find_latest_stage_output(N-1)
        if not stageN_output:
            print(f'❌ 找不到...')
            return False, None, None

        # 載入配置                           # ⚠️ 70% 重複（細節不同）
        config = load_config(...)

        # 創建處理器                          # ⚠️ 60% 重複（導入路徑不同）
        processor = StageNProcessor(config)

        # 載入前階段數據                      # ✅ 85% 重複
        with open(stageN_output, 'r') as f:
            data = json.load(f)

        # 執行處理                            # ⚠️ 50% 重複（方法名不一致）
        result = processor.execute(data)     # 或 processor.process(data)

        # 檢查結果                            # ✅ 80% 重複
        if not result or result.status != ProcessingStatus.SUCCESS:
            return False, result, processor

        # 保存快照                            # ✅ 90% 重複
        if hasattr(processor, 'save_validation_snapshot'):
            processor.save_validation_snapshot(result.data)

        return True, result, processor

    except Exception as e:                    # ✅ 100% 重複
        print(f'❌ Stage {N} 執行異常: {e}')
        return False, None, None
```

### 具體重複率

| 模塊 | 重複率 | 說明 |
|-----|-------|------|
| 階段頭部顯示 | 100% | 完全相同模式 |
| 清理輸出 | 100% | 完全相同調用 |
| 錯誤處理 | 100% | 完全相同結構 |
| 載入前階段數據 | 85% | 僅文件名不同 |
| 檢查結果 | 80% | 檢查邏輯相同 |
| 保存快照 | 90% | 僅日誌不同 |
| **平均重複率** | **70%** | - |

---

## 🎯 解決方案

### 核心設計：Template Method Pattern

引入 `StageExecutor` 基類，將重複邏輯提取到基類的 `execute()` 模板方法中：

```python
class StageExecutor(ABC):
    """執行器基類 - 統一執行流程"""

    def execute(self, previous_results):
        """模板方法 - 定義統一執行流程"""
        try:
            # 1. 顯示階段頭部 (統一實現)
            self._print_stage_header()

            # 2. 清理舊輸出 (統一實現)
            clean_stage_outputs(self.stage_number)

            # 3. 載入前階段數據 (統一實現)
            input_data = None
            if self.requires_previous_stage():
                input_data = self._load_previous_stage_data()
                if input_data is None:
                    return False, None, None

            # 4. 載入配置 (子類實現) ⭐
            config = self.load_config()

            # 5. 創建處理器 (子類實現) ⭐
            processor = self.create_processor(config)

            # 6. 執行處理 (統一實現)
            result = processor.execute(input_data)

            # 7. 檢查結果 (統一實現)
            if not self._check_result(result):
                return False, result, processor

            # 8. 保存驗證快照 (統一實現)
            self._save_validation_snapshot(processor, result)

            return True, result, processor

        except Exception as e:
            print(f'❌ Stage {self.stage_number} 執行異常: {e}')
            return False, None, None

    # === 子類只需實現這兩個方法 ===

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """載入階段配置（子類實現）"""
        pass

    @abstractmethod
    def create_processor(self, config: Dict[str, Any]) -> Any:
        """創建處理器實例（子類實現）"""
        pass
```

### 設計優勢

1. **減少重複**: 70% 的重複代碼移到基類
2. **統一流程**: 所有階段使用相同執行流程
3. **易於擴展**: 新增階段只需實現 2-3 個方法
4. **統一錯誤處理**: 基類統一處理異常
5. **統一日誌格式**: 基類控制日誌輸出
6. **向後兼容**: 保留原有 `execute_stageN()` 函數

---

## 📊 預期收益

### 代碼量減少

```
當前: 568 行 (6 個執行器)
├── 重複代碼: ~400 行 (70%)
└── 特殊邏輯: ~168 行 (30%)

重構後: ~350 行
├── base_executor.py: ~180 行 (基類)
└── 6 個子類: ~170 行 (平均每個 ~28 行)

減少: 218 行 (-38%)
```

### 維護性提升

| 指標 | 重構前 | 重構後 | 改善 |
|-----|-------|-------|------|
| 新增階段工作量 | ~80 行 | ~30 行 | ⬇️ 63% |
| 修改執行流程 | 修改 6 個文件 | 修改 1 個基類 | ⬇️ 83% |
| 測試複雜度 | 6 個獨立測試 | 1 個基類測試 + 6 個簡單測試 | ⬇️ 40% |
| Bug 修復範圍 | 可能影響 6 個文件 | 僅影響 1 個基類 | ⬇️ 83% |

### 可測試性提升

```python
# ✅ 可單獨測試基類邏輯
def test_base_executor_error_handling():
    """測試統一錯誤處理"""
    ...

def test_base_executor_validation_snapshot():
    """測試統一快照保存"""
    ...

# ✅ 子類測試簡化
def test_stage1_executor_config_loading():
    """只需測試配置加載邏輯"""
    ...
```

---

## 🗺️ 實施計劃

### Step 1: 實現基類 (Day 1 上午)

**任務**:
1. 創建 `scripts/stage_executors/base_executor.py`
2. 實現 `StageExecutor` 基類
3. 編寫單元測試

**輸出**:
- ✅ `base_executor.py` (~180 行)
- ✅ `test_base_executor.py` (~150 行)
- ✅ 所有基類測試通過

**詳細文檔**: [02_base_executor_implementation.md](02_base_executor_implementation.md)

---

### Step 2: 遷移執行器 (Day 1 下午 ~ Day 2 上午)

**遷移順序** (從簡單到複雜):

1. **Stage 1** (最簡單)
   - 無前置依賴
   - 配置加載直接
   - 測試範例

2. **Stage 2, 3** (標準流程)
   - 有前置依賴
   - 配置加載標準

3. **Stage 4, 5** (有配置文件)
   - 複雜配置加載
   - 配置合併邏輯

4. **Stage 6** (最特殊)
   - 配置可選
   - 最後遷移確保模式穩定

**每個階段的遷移步驟**:
1. 創建子類 (保留原函數)
2. 運行單元測試
3. 運行集成測試
4. 運行完整管道測試
5. 提交 git commit

**輸出**:
- ✅ 6 個子類執行器 (~170 行總計)
- ✅ 所有測試通過
- ✅ 向後兼容保證

**詳細文檔**: [03_stage_executors_migration.md](03_stage_executors_migration.md)

---

### Step 3: 測試驗證 (Day 2 下午)

**測試層級**:

1. **單元測試** (快速)
   ```bash
   pytest tests/unit/refactoring/test_base_executor.py -v
   pytest tests/unit/refactoring/test_stage1_executor.py -v
   # ... Stage 2-6
   ```

2. **集成測試** (中速)
   ```bash
   pytest tests/integration/test_stage1_executor_refactored.py -v
   # ... Stage 2-6
   ```

3. **端到端測試** (慢速，完整管道)
   ```bash
   ./run.sh
   pytest tests/e2e/test_full_pipeline.py -v
   ```

4. **回歸測試** (對比重構前後輸出)
   ```bash
   python tests/regression/compare_refactored_outputs.py
   ```

**驗收標準**:
- ✅ 所有單元測試通過
- ✅ 所有集成測試通過
- ✅ E2E 測試通過（6 階段完整運行）
- ✅ 輸出格式一致（回歸測試）
- ✅ 性能無退化（執行時間誤差 < 5%）

**詳細文檔**: [04_testing_strategy.md](04_testing_strategy.md)

---

### Step 4: 文檔更新 (Day 2 下午)

**需要更新的文檔**:

1. **架構文檔**
   - `docs/architecture/02_STAGES_DETAIL.md`
   - 更新執行器實現說明

2. **開發指南**
   - `docs/CLAUDE.md`
   - 添加新增階段的執行器模板

3. **API 文檔** (如有)
   - 執行器接口文檔

**輸出**:
- ✅ 文檔更新完成
- ✅ 範例代碼更新

---

## ⚠️ 風險與緩解

### 識別的風險

| 風險 | 等級 | 影響 | 緩解措施 |
|-----|------|------|---------|
| 破壞現有功能 | 🟡 中 | 管道無法運行 | 保留向後兼容接口，充分測試 |
| 引入新 Bug | 🟡 中 | 特定階段失敗 | 小步遷移，每步測試 |
| 性能退化 | 🟢 低 | 執行時間增加 | 基準測試，性能監控 |
| 測試覆蓋不足 | 🟡 中 | 隱藏 Bug | 編寫完整測試套件 |

### 緩解策略

1. **保留向後兼容**:
   ```python
   # 保留原有函數（向後兼容）
   def execute_stage1(previous_results=None):
       executor = Stage1Executor()
       return executor.execute(previous_results)
   ```

2. **分支開發**:
   ```bash
   git checkout -b refactor/phase1-executor
   ```

3. **小步提交**:
   ```bash
   git commit -m "refactor(phase1): implement base executor"
   git commit -m "refactor(phase1): migrate stage1 executor"
   # ... 每個階段一個 commit
   ```

4. **回滾準備**:
   ```bash
   git tag phase1-start    # 開始前
   git tag phase1-complete # 完成後
   ```

---

## ✅ 完成標準

### 必須滿足的條件

- [ ] `base_executor.py` 實現完成
- [ ] 6 個階段執行器遷移完成
- [ ] 所有單元測試通過
- [ ] 所有集成測試通過
- [ ] E2E 測試通過（完整管道）
- [ ] 回歸測試通過（輸出一致）
- [ ] 性能測試通過（< 5% 退化）
- [ ] 代碼覆蓋率 ≥ 85%
- [ ] 文檔更新完成
- [ ] Checklist 全部勾選

### 驗收測試命令

```bash
# 1. 單元測試
pytest tests/unit/refactoring/ -v --cov=scripts/stage_executors

# 2. 集成測試
pytest tests/integration/ -v

# 3. 完整管道
./run.sh

# 4. 回歸測試
python tests/regression/compare_outputs.py \
  --baseline data/baseline_outputs/ \
  --current data/outputs/

# 5. 性能測試
python tests/performance/benchmark_executors.py
```

---

## 📚 相關文檔

- [02_base_executor_implementation.md](02_base_executor_implementation.md) - 基類實現細節
- [03_stage_executors_migration.md](03_stage_executors_migration.md) - 遷移步驟詳解
- [04_testing_strategy.md](04_testing_strategy.md) - 測試策略
- [05_checklist.md](05_checklist.md) - 檢查清單

---

## 🔄 下一步

完成 Phase 1 後，可以選擇：

1. **繼續 Phase 2** (推薦): 驗證邏輯重組
2. **繼續 Phase 3** (簡單): 配置統一
3. **暫停重構**: 穩定觀察一段時間

---

**創建日期**: 2025-10-12
**最後更新**: 2025-10-12
**狀態**: 📋 待開始
