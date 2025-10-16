# Phase 2 驗證器重構 - 實施計劃

**階段**: Phase 2 - Validation Logic Reorganization
**優先級**: P1 (High Priority)
**預計時間**: 4-6 小時
**開始日期**: 2025-10-12
**狀態**: 🚧 **進行中**

---

## 📋 執行摘要

基於 Phase 1 執行器重構的成功經驗（減少 38% 重複代碼），Phase 2 將對 6 個階段驗證器進行類似的重構，預計減少 **47% 重複代碼** (~660 lines)。

**核心目標**:
- 創建統一的 `StageValidator` 基類
- 使用 Template Method Pattern 消除驗證邏輯重複
- 提供 Fail-Fast 工具方法簡化字段檢查
- 保持 100% 向後兼容性

---

## 🎯 重構目標

### 定量目標

| 指標 | 當前 | 目標 | 改進 |
|------|------|------|------|
| **總行數** | 1,400 lines | ~740 lines | **-660 (-47%)** |
| **平均驗證器行數** | 233 lines | ~123 lines | **-110 (-47%)** |
| **重複代碼** | ~660 lines | 0 lines | **-660 (-100%)** |
| **基類行數** | 0 lines | 350 lines | +350 (新增) |

### 定性目標

1. **統一驗證流程**: 所有驗證器遵循相同的驗證步驟
2. **簡化字段檢查**: 提供 `check_field_exists()`, `check_field_type()` 工具方法
3. **自動取樣模式**: 基類自動檢測取樣模式並調整標準
4. **錯誤處理統一**: 集中錯誤處理邏輯
5. **代碼可讀性**: 驗證器代碼更簡潔易讀

---

## 📐 技術設計

### 基類設計 (`base_validator.py`)

```python
class StageValidator(ABC):
    """
    驗證器基類 - 使用 Template Method Pattern

    標準驗證流程:
    1. 基礎結構驗證 (stage 標識, metadata, data_summary)
    2. 驗證結果框架檢查 (5 項驗證框架)
    3. 專用驗證 (子類實現)
    """

    def __init__(self, stage_number: int, stage_identifier: str):
        self.stage_number = stage_number
        self.stage_identifier = stage_identifier

    # ========== Template Method (主流程) ==========
    def validate(self, snapshot_data: dict) -> tuple:
        """模板方法: 標準驗證流程"""

    # ========== 基礎驗證方法 ==========
    def _validate_basic_structure(self, snapshot_data: dict) -> bool:
        """驗證基礎結構 (stage, metadata, data_summary)"""

    def _validate_validation_framework(self, snapshot_data: dict) -> Optional[tuple]:
        """驗證 5 項驗證框架"""

    # ========== 取樣模式處理 ==========
    def _is_sampling_mode(self, snapshot_data: dict) -> bool:
        """檢測取樣模式"""

    def _get_min_required_checks(self, snapshot_data: dict) -> int:
        """獲取最低通過檢查數 (1/5 或 4/5)"""

    # ========== Fail-Fast 工具方法 ==========
    def check_field_exists(self, data: dict, field: str, parent: str = '') -> tuple:
        """檢查字段是否存在"""

    def check_field_type(self, value, expected_type, field_name: str) -> tuple:
        """檢查字段類型"""

    def check_field_range(self, value, min_val, max_val, field_name: str, unit: str = '') -> tuple:
        """檢查字段範圍"""

    # ========== 抽象方法 (子類實現) ==========
    @abstractmethod
    def perform_stage_specific_validation(self, snapshot_data: dict) -> tuple:
        """執行階段特定的驗證邏輯"""
        pass

    def uses_validation_framework(self) -> bool:
        """是否使用 5 項驗證框架 (默認: True)"""
        return True
```

### 子類實現模式

每個驗證器只需實現核心邏輯：

```python
class StageNValidator(StageValidator):
    def __init__(self):
        super().__init__(
            stage_number=N,
            stage_identifier='stageN_*'
        )

    def perform_stage_specific_validation(self, snapshot_data: dict) -> tuple:
        """Stage N 專用驗證"""
        # 只實現這一個方法！
        # 基礎檢查已由基類完成

        data_summary = snapshot_data['data_summary']

        # 使用工具方法進行檢查
        exists, msg = self.check_field_exists(data_summary, 'key_field')
        if not exists:
            return False, msg

        # 執行專用驗證邏輯
        # ...

        return True, "✅ Stage N 驗證通過"

    def _is_sampling_mode(self, snapshot_data: dict) -> bool:
        """自定義取樣模式判斷 (可選)"""
        # 默認使用環境變數檢測
        # 可覆蓋此方法添加特定邏輯
        return super()._is_sampling_mode(snapshot_data)
```

---

## 📅 實施步驟

### Step 1: 創建基類 (2 小時)

**文件**: `scripts/stage_validators/base_validator.py` (350 lines)

**任務**:
1. 實現 `StageValidator` 抽象基類
2. 實現所有公共方法和工具函數
3. 添加完整文檔和註釋
4. 添加類型提示

**驗收標準**:
- 基類代碼通過 Python 語法檢查
- 包含所有計劃的方法
- 文檔完整清晰

---

### Step 2: 遷移驗證器 (2-3 小時)

按從簡單到複雜的順序遷移：

#### 2.1 Stage 6 驗證器 (30 分鐘)
- **原始**: 109 lines
- **目標**: ~60 lines (-45%)
- **原因**: 最簡單，適合作為第一個遷移對象

#### 2.2 Stage 3 驗證器 (30 分鐘)
- **原始**: 140 lines
- **目標**: ~80 lines (-43%)
- **特點**: 標準驗證框架

#### 2.3 Stage 2 驗證器 (30 分鐘)
- **原始**: 170 lines
- **目標**: ~100 lines (-41%)
- **特點**: 軌道傳播驗證

#### 2.4 Stage 1 驗證器 (30 分鐘)
- **原始**: 189 lines
- **目標**: ~110 lines (-42%)
- **特點**: TLE 數據驗證，取樣模式自定義

#### 2.5 Stage 5 驗證器 (1 小時)
- **原始**: 358 lines
- **目標**: ~200 lines (-44%)
- **特點**: Grade A+ 分層驗證，複雜度高

#### 2.6 Stage 4 驗證器 (1 小時)
- **原始**: 434 lines
- **目標**: ~250 lines (-42%)
- **特點**: 最複雜，Fail-Fast 驗證，動態門檻

---

### Step 3: 測試與驗證 (1 小時)

#### 3.1 單元測試
```bash
# 測試每個驗證器的向後兼容性
python -m pytest tests/unit/validators/ -v
```

#### 3.2 集成測試
```bash
# 完整管道測試 (Stage 1-6)
export ORBIT_ENGINE_TEST_MODE=1
export ORBIT_ENGINE_SAMPLING_MODE=1
./run.sh

# 檢查所有驗證快照是否正確驗證
ls -lh data/validation_snapshots/
```

#### 3.3 性能測試
```bash
# 記錄驗證時間
time python scripts/stage_validators/stage1_validator.py
```

**驗收標準**:
- 所有驗證器通過完整管道測試
- 驗證邏輯與重構前完全一致
- 驗證時間無明顯增加 (<5%)

---

### Step 4: 文檔更新 (30 分鐘)

1. 創建 `PHASE2_COMPLETION_REPORT.md`
2. 更新 `REFACTORING_MASTER_PLAN.md` 進度
3. 添加遷移示例和最佳實踐

---

## 🚨 風險與應對

### 風險 1: 驗證邏輯差異

**描述**: Stage 4, 5 使用 Fail-Fast 驗證，與其他階段邏輯不同

**應對**:
- 提供 `check_field_exists()` 工具方法支持 Fail-Fast
- 子類可覆蓋 `uses_validation_framework()` 返回 False
- 保持專用驗證邏輯的靈活性

---

### 風險 2: 向後兼容性問題

**描述**: 修改驗證器可能影響現有測試

**應對**:
- 保留原始函數簽名 `check_stageN_validation()`
- 函數內部調用基類方法
- 完整測試所有驗證快照

```python
# 向後兼容包裝函數
def check_stage1_validation(snapshot_data: dict) -> tuple:
    """向後兼容函數"""
    validator = Stage1Validator()
    return validator.validate(snapshot_data)
```

---

### 風險 3: 取樣模式檢測不一致

**描述**: 不同階段使用不同的取樣模式判斷邏輯

**應對**:
- 基類提供統一的環境變數檢測
- 子類可覆蓋 `_is_sampling_mode()` 自定義邏輯
- Stage 1: 基於 `satellites_loaded`
- Stage 4: 基於 `total_input_satellites`
- Stage 6: 基於 `candidate_satellites_total`

---

## ✅ 驗收標準

### 功能性驗收

1. **完整管道測試通過**: `./run.sh` 執行成功，所有 6 個階段完成
2. **驗證快照正確**: 所有 6 個驗證快照都通過驗證
3. **錯誤檢測準確**: 故意損壞快照數據能被正確檢測

### 代碼質量驗收

1. **代碼減少**: 總行數減少 ≥40% (目標: 47%)
2. **重複代碼**: 無明顯重複驗證邏輯
3. **可讀性**: 驗證器代碼簡潔清晰
4. **文檔**: 所有方法都有文檔字符串

### 性能驗收

1. **驗證時間**: 無明顯增加 (<5%)
2. **內存使用**: 無增加

---

## 📊 預期成果

### 代碼統計

| 文件 | 重構前 | 重構後 | 減少 |
|------|--------|--------|------|
| `base_validator.py` | 0 | 350 | +350 (新增) |
| `stage1_validator.py` | 189 | 110 | **-79 (-42%)** |
| `stage2_validator.py` | 170 | 100 | **-70 (-41%)** |
| `stage3_validator.py` | 140 | 80 | **-60 (-43%)** |
| `stage4_validator.py` | 434 | 250 | **-184 (-42%)** |
| `stage5_validator.py` | 358 | 200 | **-158 (-44%)** |
| `stage6_validator.py` | 109 | 60 | **-49 (-45%)** |
| **總計** | **1,400** | **1,150** | **-600 (-43%)** |

**淨效果**: 1,400 → 1,150 lines (-250 lines, -18% 淨減少)

**重複代碼消除**: ~660 lines → 0 lines (-100%)

---

### 可維護性提升

1. **新增驗證器**: 只需實現 1 個方法 (`perform_stage_specific_validation()`)
2. **統一錯誤處理**: 集中在基類，修改一次全部生效
3. **取樣模式**: 自動檢測，無需每個驗證器重複實現
4. **工具方法**: 簡化字段檢查，減少樣板代碼

---

## 🔄 與 Phase 1 對比

| 指標 | Phase 1 (Executors) | Phase 2 (Validators) |
|------|---------------------|----------------------|
| **文件數量** | 6 | 6 |
| **原始總行數** | 568 | 1,400 |
| **重複代碼** | 218 (-38%) | 660 (-47%) |
| **基類行數** | 360 | 350 |
| **淨減少** | +231 | -250 |
| **實施時間** | 3 小時 | 4-6 小時 |

**Phase 2 特點**:
- 驗證器更複雜，重複代碼更多
- 重構收益更大 (47% vs 38%)
- 實施難度略高 (更多驗證邏輯變化)

---

## 📝 後續步驟 (Phase 3+)

完成 Phase 2 後，可以考慮：

1. **Phase 3**: Stage 6 配置統一 (2-3 小時)
2. **Phase 4**: 接口統一 (3-4 小時)
3. **Phase 5**: 模組重組 (4-6 小時)

---

**計劃創建時間**: 2025-10-12 05:50 UTC
**計劃創建者**: Claude Code (Orbit Engine Refactoring Team)
**下一步**: 創建 `base_validator.py` 並開始遷移
