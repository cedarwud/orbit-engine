# Phase 2 驗證器結構分析報告

**分析日期**: 2025-10-12 05:50 UTC
**分析範圍**: 所有 6 個階段驗證器
**目標**: 識別重複代碼並設計統一基類

---

## 📊 驗證器代碼統計

| 驗證器 | 行數 | 主要功能 | 複雜度 |
|--------|------|----------|--------|
| `stage1_validator.py` | 189 | TLE 數據載入驗證 | 中 |
| `stage2_validator.py` | 170 | 軌道傳播驗證 | 中 |
| `stage3_validator.py` | 140 | 座標轉換驗證 | 中 |
| `stage4_validator.py` | 434 | 鏈路可行性驗證 (最複雜) | 高 |
| `stage5_validator.py` | 358 | 信號品質驗證 (Grade A+) | 高 |
| `stage6_validator.py` | 109 | 研究數據驗證 (最簡單) | 低 |
| **總計** | **1,400** | - | - |

**平均**: 233 lines per validator

---

## 🔍 共同模式識別

### 1. **統一函數簽名** (100% 一致)

所有驗證器都遵循相同的接口：

```python
def check_stageN_validation(snapshot_data: dict) -> tuple:
    """
    Stage N 專用驗證 - <階段名稱>

    檢查項目:
    - <具體檢查項目列表>

    Args:
        snapshot_data: 驗證快照數據

    Returns:
        tuple: (validation_passed: bool, message: str)
    """
```

**重複代碼量**: 每個驗證器 ~15-20 lines (文檔字符串)

---

### 2. **基礎結構驗證** (~40 lines 重複)

所有驗證器都包含以下基礎檢查：

```python
# 檢查 stage 標識
if snapshot_data.get('stage') != 'stageN_*':
    return False, f"❌ Stage N 快照標識不正確: {snapshot_data.get('stage')}"

# 檢查基本字段存在性
if 'metadata' not in snapshot_data:
    return False, "❌ 快照缺少必需字段 'metadata'"

if 'data_summary' not in snapshot_data:
    return False, "❌ 快照缺少必需字段 'data_summary'"

# 檢查 status (舊格式兼容性)
if snapshot_data.get('status') == 'success':
    # 兼容處理
```

**重複情況**:
- Stage 1-6: 全部包含 stage 標識檢查
- Stage 3-6: 全部包含 metadata 檢查
- Stage 1-6: 全部包含 data_summary 檢查
- Stage 1-3, 6: 包含 status 兼容處理

**預計可減少**: ~30-40 lines per validator × 6 = **180-240 lines**

---

### 3. **驗證結果框架檢查** (~30 lines 重複)

大部分驗證器檢查 5 項驗證框架：

```python
if 'validation_results' in snapshot_data:
    validation_results = snapshot_data.get('validation_results', {})
    overall_status = validation_results.get('overall_status', 'UNKNOWN')

    # 新格式 (Stage 3, 6): validation_details 包含 checks_passed
    validation_details = validation_results.get('validation_details', {})
    checks_passed = validation_details.get('checks_passed', 0)
    checks_performed = validation_details.get('checks_performed', 0)

    # 舊格式 (Stage 1, 2): 直接在 validation_results 中
    checks_passed = validation_results.get('checks_passed', 0)
    checks_performed = validation_results.get('checks_performed', 0)

    # 檢查執行完整性
    if checks_performed < 5:
        return False, f"❌ Stage N 驗證不完整: 只執行了{checks_performed}/5項檢查"

    # 檢查通過率
    if checks_passed < 4:  # 或取樣模式下 < 1
        return False, f"❌ Stage N 驗證未達標: 只通過了{checks_passed}/5項檢查"
```

**重複情況**:
- Stage 1, 2, 3, 6: 全部包含驗證框架檢查
- Stage 4, 5: 使用不同的驗證邏輯 (Fail-Fast)

**預計可減少**: ~25-30 lines per validator × 4 = **100-120 lines**

---

### 4. **取樣模式檢測與調整** (~15 lines 重複)

Stage 4, 6 包含取樣模式處理：

```python
# 檢測取樣模式
is_sampling_mode = (total_input_satellites < 50) or (os.getenv('ORBIT_ENGINE_TEST_MODE') == '1')

if is_sampling_mode:
    print(f"🧪 偵測到取樣模式 ({total_input_satellites} 顆衛星)，放寬驗證標準")
    min_checks_required = 1  # 取樣模式
else:
    min_checks_required = 4  # 正常模式
```

**重複情況**:
- Stage 4: 使用 `total_input_satellites`
- Stage 6: 使用 `candidate_satellites_total`
- 邏輯相同，只是數據源不同

**預計可減少**: ~10-15 lines per validator × 2 = **20-30 lines**

---

### 5. **Fail-Fast 字段檢查** (~50 lines 重複)

Stage 4, 5 使用嚴格的 Fail-Fast 檢查：

```python
# 檢查字段存在性
if 'field_name' not in data_dict:
    return False, "❌ data_dict 缺少必需字段 'field_name'"

# 檢查字段類型
if not isinstance(field_value, expected_type):
    return False, f"❌ field_name 類型錯誤: {type(field_value).__name__} (期望: expected_type)"

# 檢查字段範圍
if field_value < min_value or field_value > max_value:
    return False, f"❌ field_name 值超出範圍: {field_value} (範圍: {min_value}-{max_value})"
```

**重複情況**:
- Stage 4: 70+ 個字段檢查
- Stage 5: 40+ 個字段檢查 (分層驗證)
- 所有驗證器都有類似的檢查邏輯

**預計可減少**: ~40-50 lines per validator × 6 = **240-300 lines**

---

### 6. **錯誤處理框架** (~10 lines 重複)

所有驗證器都包含錯誤處理：

```python
try:
    # 驗證邏輯
    ...
except KeyError as e:
    return False, f"❌ Stage N 驗證數據結構錯誤: 缺少必需字段 {e}"
except Exception as e:
    return False, f"❌ Stage N 驗證異常: {e}"
```

**重複情況**:
- Stage 1-6: 全部包含 try-except
- Stage 3: 使用 RuntimeError 拋出異常 (不同於其他階段)

**預計可減少**: ~8-10 lines per validator × 6 = **48-60 lines**

---

## 📐 重構設計方案

### 設計目標

類似 `base_executor.py`，創建 `base_validator.py` 使用 **Template Method Pattern**：

1. **統一驗證流程**: 基礎檢查 → 驗證結果檢查 → 專用驗證
2. **抽象方法**: 子類實現 `perform_stage_specific_validation()`
3. **工具方法**: 提供常用檢查方法 (`check_field_exists()`, `check_field_type()`)
4. **取樣模式**: 自動檢測並調整驗證標準

---

### 基類設計 (`StageValidator`)

```python
class StageValidator(ABC):
    def __init__(self, stage_number: int, stage_identifier: str):
        self.stage_number = stage_number
        self.stage_identifier = stage_identifier  # e.g., 'stage1_orbital_calculation'

    # ========== Template Method (主流程) ==========
    def validate(self, snapshot_data: dict) -> tuple:
        """模板方法: 定義標準驗證流程"""
        try:
            # 1. 基礎結構驗證
            if not self._validate_basic_structure(snapshot_data):
                return False, f"❌ Stage {self.stage_number} 基礎結構驗證失敗"

            # 2. 驗證結果框架檢查 (如果適用)
            if self.uses_validation_framework():
                result = self._validate_validation_framework(snapshot_data)
                if result is not None:  # 如果框架驗證完成
                    return result

            # 3. 專用驗證 (子類實現)
            return self.perform_stage_specific_validation(snapshot_data)

        except KeyError as e:
            return False, f"❌ Stage {self.stage_number} 驗證數據結構錯誤: 缺少必需字段 {e}"
        except Exception as e:
            return False, f"❌ Stage {self.stage_number} 驗證異常: {e}"

    # ========== 基礎驗證方法 (公共) ==========
    def _validate_basic_structure(self, snapshot_data: dict) -> bool:
        """驗證基礎結構"""
        # 檢查 stage 標識
        if snapshot_data.get('stage') != self.stage_identifier:
            return False

        # 檢查基本字段
        if 'metadata' not in snapshot_data:
            return False

        if 'data_summary' not in snapshot_data:
            return False

        return True

    def _validate_validation_framework(self, snapshot_data: dict) -> Optional[tuple]:
        """驗證 5 項驗證框架 (如果存在)"""
        if 'validation_results' not in snapshot_data:
            return None  # 舊格式，跳過框架檢查

        validation_results = snapshot_data['validation_results']

        # 獲取 checks_passed/performed (支持新舊格式)
        validation_details = validation_results.get('validation_details', {})
        checks_passed = validation_details.get('checks_passed',
                                              validation_results.get('checks_passed', 0))
        checks_performed = validation_details.get('checks_performed',
                                                 validation_results.get('checks_performed', 0))

        # 檢查執行完整性
        if checks_performed < 5:
            return False, f"❌ Stage {self.stage_number} 驗證不完整: 只執行了{checks_performed}/5項檢查"

        # 檢查通過率 (取樣模式調整)
        min_required = self._get_min_required_checks(snapshot_data)
        if checks_passed < min_required:
            return False, f"❌ Stage {self.stage_number} 驗證未達標: 只通過了{checks_passed}/5項檢查"

        # 檢查 overall_status
        overall_status = validation_results.get('overall_status', 'UNKNOWN')
        if overall_status == 'PASS':
            return self._build_success_message(snapshot_data, validation_results)

        return None  # 需要進一步檢查

    # ========== 取樣模式處理 ==========
    def _is_sampling_mode(self, snapshot_data: dict) -> bool:
        """檢測是否為取樣模式"""
        if os.getenv('ORBIT_ENGINE_TEST_MODE') == '1':
            return True

        # 子類可以覆蓋此方法來自定義判斷邏輯
        return False

    def _get_min_required_checks(self, snapshot_data: dict) -> int:
        """獲取最低通過檢查數"""
        if self._is_sampling_mode(snapshot_data):
            return 1  # 取樣模式: 1/5
        else:
            return 4  # 正常模式: 4/5

    # ========== Fail-Fast 工具方法 ==========
    def check_field_exists(self, data: dict, field: str, parent: str = '') -> tuple:
        """檢查字段是否存在"""
        if field not in data:
            parent_str = f"{parent}." if parent else ""
            return False, f"❌ {parent_str}{field} 字段不存在"
        return True, None

    def check_field_type(self, value, expected_type, field_name: str) -> tuple:
        """檢查字段類型"""
        if not isinstance(value, expected_type):
            return False, f"❌ {field_name} 類型錯誤: {type(value).__name__} (期望: {expected_type.__name__})"
        return True, None

    def check_field_range(self, value, min_val, max_val, field_name: str, unit: str = '') -> tuple:
        """檢查字段範圍"""
        if value < min_val or value > max_val:
            unit_str = f" {unit}" if unit else ""
            return False, f"❌ {field_name} 值超出範圍: {value}{unit_str} (範圍: {min_val}-{max_val}{unit_str})"
        return True, None

    # ========== 抽象方法 (子類實現) ==========
    @abstractmethod
    def perform_stage_specific_validation(self, snapshot_data: dict) -> tuple:
        """執行階段特定的驗證邏輯"""
        pass

    def uses_validation_framework(self) -> bool:
        """是否使用 5 項驗證框架 (默認: True)"""
        return True

    def _build_success_message(self, snapshot_data: dict, validation_results: dict) -> tuple:
        """構建成功訊息 (子類可覆蓋)"""
        checks_passed = validation_results.get('checks_passed', 0)
        checks_performed = validation_results.get('checks_performed', 0)
        return True, f"✅ Stage {self.stage_number} 驗證通過: {checks_passed}/{checks_performed} 項檢查通過"
```

---

### 子類實現示例 (Stage 1)

```python
class Stage1Validator(StageValidator):
    def __init__(self):
        super().__init__(
            stage_number=1,
            stage_identifier='stage1_orbital_calculation'
        )

    def perform_stage_specific_validation(self, snapshot_data: dict) -> tuple:
        """Stage 1 專用驗證"""
        data_summary = snapshot_data['data_summary']

        # 檢查衛星數量
        satellites_loaded = data_summary.get('satellites_loaded', 0)
        if satellites_loaded == 0:
            return False, "❌ Stage 1 未載入任何衛星"

        # 檢查星座分布
        constellation_dist = data_summary.get('constellation_distribution', {})
        if not constellation_dist:
            return False, "❌ Stage 1 星座分布數據缺失"

        # 構建成功訊息
        starlink = constellation_dist.get('starlink', 0)
        oneweb = constellation_dist.get('oneweb', 0)

        status_msg = (
            f"✅ Stage 1 TLE 數據載入驗證通過: "
            f"載入 {satellites_loaded} 顆衛星 "
            f"(Starlink: {starlink}, OneWeb: {oneweb})"
        )
        return True, status_msg

    def _is_sampling_mode(self, snapshot_data: dict) -> bool:
        """Stage 1 取樣模式判斷"""
        satellites_loaded = snapshot_data.get('data_summary', {}).get('satellites_loaded', 0)
        return satellites_loaded < 50 or super()._is_sampling_mode(snapshot_data)
```

---

## 📊 預計重構收益

| 項目 | 重複代碼量 | 預計減少 |
|------|-----------|---------|
| 基礎結構驗證 | 180-240 lines | ~200 lines |
| 驗證框架檢查 | 100-120 lines | ~110 lines |
| 取樣模式處理 | 20-30 lines | ~25 lines |
| Fail-Fast 工具 | 240-300 lines | ~270 lines |
| 錯誤處理框架 | 48-60 lines | ~54 lines |
| **總計** | **588-750 lines** | **~660 lines (-47%)** |

**與 Phase 1 對比**:
- Phase 1: 減少 218 lines (-38%)
- Phase 2: 預計減少 660 lines (-47%)
- **Phase 2 收益更大！**

---

## 🎯 實施計劃

### Step 1: 創建 base_validator.py (350 lines)
- 實現 `StageValidator` 基類
- 包含所有公共方法和工具函數
- 完整文檔和註釋

### Step 2: 遷移 Stage 1-6 驗證器
按順序遷移（從簡單到複雜）：
1. **Stage 6** (109 lines → ~60 lines, -45%)
2. **Stage 3** (140 lines → ~80 lines, -43%)
3. **Stage 2** (170 lines → ~100 lines, -41%)
4. **Stage 1** (189 lines → ~110 lines, -42%)
5. **Stage 5** (358 lines → ~200 lines, -44%)
6. **Stage 4** (434 lines → ~250 lines, -42%)

### Step 3: 測試與驗證
- 執行 `./run.sh` 完整管道測試
- 檢查所有驗證快照是否正確驗證
- 確保向後兼容性

---

## ✅ 成功標準

1. **功能性**: 所有驗證器通過完整管道測試
2. **代碼減少**: 總行數減少 ≥40% (目標: 47%)
3. **可讀性**: 驗證器代碼更簡潔易讀
4. **可維護性**: 新增驗證器只需實現 1 個方法
5. **向後兼容**: 不影響現有驗證邏輯

---

**報告生成時間**: 2025-10-12 05:50 UTC
**下一步**: 創建 `base_validator.py` 並開始遷移
