# 重構計劃 03: 統一處理器接口

**優先級**: 🟠 P1 (重要)
**風險等級**: 🟡 中風險
**預估時間**: 2 小時
**狀態**: ⏸️ 待執行

---

## 📋 目標

統一所有 Stage 處理器的接口規範：
- 子類僅實現 `process()` 方法
- 禁止子類覆蓋 `execute()` 方法
- 基類 `execute()` 統一處理驗證、快照、錯誤處理

---

## 🔍 現狀分析

### 當前混亂狀態

**Stage 2 (複雜實現)**:
```python
class Stage2OrbitalPropagationProcessor(BaseStageProcessor):
    def process(self, input_data) -> ProcessingResult:
        # 主要業務邏輯
        return create_processing_result(...)

    def execute(self, input_data=None) -> Dict:
        # ❌ 覆蓋基類 execute，繞過驗證流程
        result = self.process(input_data)
        if result.status == ProcessingStatus.SUCCESS:
            output_file = self.result_manager.save_results(result.data)
            return result.data
        return {'success': False, 'error': ...}
```

**Stage 4 (類似問題)**:
```python
class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    def execute(self, input_data) -> Dict[str, Any]:
        # ❌ 完全重寫 execute，繞過基類驗證
        result = self._process_link_feasibility(wgs84_data)
        return result

    def process(self, input_data) -> ProcessingResult:
        # 包裝 execute 結果
        result_data = self.execute(input_data)
        return create_processing_result(...)
```

**Stage 1, 3, 6**:
- 實現模式各不相同
- 有些覆蓋 `execute()`，有些僅實現 `process()`

### 問題根源

**基類設計** (`base_processor.py:77-197`):
```python
class BaseStageProcessor:
    def execute(self, input_data) -> ProcessingResult:
        """標準執行流程 (Template Method)"""
        # 1. 輸入驗證
        validation_result = self.validate_input(input_data)

        # 2. 調用 process (子類實現)
        result = self.process(input_data)

        # 3. 輸出驗證
        output_validation = self.validate_output(result.data)

        # 4. 保存快照
        self._save_validation_snapshot(result)

        return result
```

**問題**: 子類覆蓋 `execute()` 後，基類的驗證邏輯被繞過。

---

## 🎯 執行步驟

### Step 1: 備份當前狀態
```bash
cd /home/sat/orbit-engine

git add .
git commit -m "Backup before refactoring: Unify processor interface"
```

### Step 2: 修改基類設計

**2.1 標記基類 `execute()` 為 final (文檔註解)**

編輯 `src/shared/base_processor.py`:
```python
def execute(self, input_data: Optional[Dict[str, Any]] = None) -> ProcessingResult:
    """
    執行階段處理流程 (Template Method Pattern)

    ⚠️ **WARNING**: 子類不應覆蓋此方法！

    此方法實現標準化流程：
    1. 輸入驗證
    2. 調用 process() (子類實現)
    3. 輸出驗證
    4. 保存驗證快照
    5. 錯誤處理

    子類應實現 `process()` 方法，而非覆蓋 `execute()`。

    Args:
        input_data: 輸入數據

    Returns:
        ProcessingResult: 標準化處理結果
    """
    try:
        # ... (保持原有實現)
```

**2.2 添加覆蓋檢測**

在基類 `__init__` 中添加檢測：
```python
def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict] = None):
    # ... 原有初始化

    # 🚨 檢測子類是否覆蓋 execute()
    if self.__class__.execute is not BaseStageProcessor.execute:
        import warnings
        warnings.warn(
            f"⚠️ {self.__class__.__name__} 覆蓋了 execute() 方法\n"
            f"   建議僅實現 process() 方法，讓基類處理標準流程\n"
            f"   Ref: docs/refactoring/REFACTOR_PLAN_03",
            DeprecationWarning,
            stacklevel=2
        )
```

### Step 3: 重構 Stage 2

**3.1 移除 `execute()` 覆蓋**

編輯 `src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py`:
```python
# ❌ 刪除這個方法:
# def execute(self, input_data=None) -> Dict[str, Any]:
#     ...

# ✅ 保留並調整 process():
def process(self, input_data: Any) -> ProcessingResult:
    """主要處理方法"""
    start_time = datetime.now(timezone.utc)

    try:
        # 原有業務邏輯
        ...

        # ✅ 在 process 內部保存結果
        if result_data:
            output_file = self.result_manager.save_results(result_data)
            result_data['output_file'] = output_file

        return create_processing_result(
            status=ProcessingStatus.SUCCESS,
            data=result_data,
            message="Stage 2 處理成功"
        )
    except Exception as e:
        return create_processing_result(
            status=ProcessingStatus.FAILED,
            data={},
            message=f"Stage 2 處理失敗: {e}"
        )
```

### Step 4: 重構 Stage 4

編輯 `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`:
```python
# ❌ 刪除或重命名 execute() 為 _execute_legacy()

# ✅ 調整 process() 成為主要接口
def process(self, input_data: Any) -> ProcessingResult:
    """主要處理方法 (符合基類規範)"""
    start_time = time.time()

    try:
        # 原有業務邏輯 (從舊 execute 移過來)
        result_data = self.execute(input_data)  # 臨時調用舊方法

        processing_time = time.time() - start_time

        return create_processing_result(
            status=ProcessingStatus.SUCCESS,
            data=result_data,
            message="Stage 4 鏈路可行性評估成功",
            metadata={
                'stage': 4,
                'processing_time': processing_time
            }
        )
    except Exception as e:
        return create_processing_result(
            status=ProcessingStatus.FAILED,
            data={},
            message=f"Stage 4 處理失敗: {e}"
        )

# ✅ 將原 execute() 重命名為內部方法
def _execute_internal(self, input_data: Any) -> Dict[str, Any]:
    """內部執行邏輯 (原 execute 方法)"""
    # 原有業務邏輯
    ...
```

### Step 5: 重構其他 Stages (1, 3, 6)

對每個 Stage 進行類似調整：
1. 檢查是否覆蓋 `execute()`
2. 如有覆蓋，移除或重命名為 `_execute_internal()`
3. 確保 `process()` 返回 `ProcessingResult`

### Step 6: 更新執行器

編輯 `scripts/stage_executors/stage2_executor.py` (及其他):
```python
def execute_stage2(previous_results):
    # ...
    processor = Stage2OrbitalPropagationProcessor(config)

    # ✅ 統一調用 execute() (基類方法)
    # ❌ 不再需要判斷調用 process() 還是 execute()
    result = processor.execute(stage1_data)

    # result 已經是 ProcessingResult 類型
    if result.status == ProcessingStatus.SUCCESS:
        return True, result, processor
    else:
        return False, result, processor
```

### Step 7: 運行測試
```bash
# 測試每個 Stage
for stage in {1..6}; do
    echo "Testing Stage $stage..."
    ./run.sh --stage $stage
    if [ $? -ne 0 ]; then
        echo "❌ Stage $stage failed"
        exit 1
    fi
done

# 測試完整流程
./run.sh --stages 1-6

# 單元測試
make test
```

### Step 8: 提交變更
```bash
git add .
git commit -m "Refactor: Unify processor interface to Template Method Pattern

統一處理器接口規範:
- 子類僅實現 process() 方法
- 基類 execute() 處理標準流程 (驗證、快照、錯誤處理)
- 移除 Stage 2, 4 的 execute() 覆蓋
- 添加覆蓋檢測警告

變更:
- src/shared/base_processor.py: 添加 execute() 覆蓋檢測
- src/stages/stage2_*: 移除 execute() 覆蓋
- src/stages/stage4_*: 移除 execute() 覆蓋
- scripts/stage_executors: 統一調用 execute()

測試:
- 所有 Stages (1-6) 執行成功
- 接口一致性: 100%

Ref: docs/refactoring/REFACTOR_PLAN_03
"
```

---

## ✅ 驗證檢查清單

- [ ] 基類 `execute()` 添加文檔警告
- [ ] 基類 `__init__` 添加覆蓋檢測
- [ ] Stage 2 移除 `execute()` 覆蓋
- [ ] Stage 4 移除 `execute()` 覆蓋
- [ ] Stage 1, 3, 6 檢查並調整
- [ ] 所有執行器統一調用 `execute()`
- [ ] Stage 1-6 獨立測試通過
- [ ] 完整流程測試通過
- [ ] 無 DeprecationWarning (或僅在預期位置)

---

## 🔄 回滾方案

```bash
# 回滾到重構前
git reset --hard HEAD~1

# 或選擇性回滾單個 Stage
git checkout HEAD~1 -- src/stages/stage2_orbital_computing/
git checkout HEAD~1 -- src/stages/stage4_link_feasibility/
```

---

## 📊 預期效益

- **接口一致性**: 60% → 100%
- **驗證流程覆蓋**: 70% → 100% (無繞過)
- **新人理解成本**: -40%
- **錯誤處理一致性**: +50%

---

## 📝 注意事項

1. **分階段重構**: 先 Stage 2, 4 (複雜)，再其他 (簡單)
2. **測試優先**: 每修改一個 Stage，立即測試
3. **保留舊方法**: 如有疑慮，先重命名為 `_legacy_execute()`，確認無問題再刪除

---

## 🔗 相關資源

- [架構優化分析報告](../architecture/ARCHITECTURE_OPTIMIZATION_REPORT.md#2-處理器接口不一致---process-vs-execute)
- [Template Method Pattern](https://refactoring.guru/design-patterns/template-method)
- [BaseStageProcessor 實現](../../src/shared/base_processor.py)

---

**創建日期**: 2025-10-11
**負責人**: Development Team
**審查者**: TBD
