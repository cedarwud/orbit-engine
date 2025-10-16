# P2: 錯誤處理標準化

**優先級**: 🟠 P2 - 中等優先級（應該執行）
**預估時間**: 0.5天
**依賴**: 無
**影響範圍**: 全專案（6個階段 + shared utilities）

---

## 📊 問題分析

### 當前狀態

**問題描述**: 專案中異常處理不統一，導致錯誤追蹤和調試困難

**具體表現**:

1. **異常類型混亂**:
   ```python
   # Stage 2: 使用通用 Exception
   raise Exception(f"無法載入配置檔案: {e}")

   # Stage 4: 使用 ValueError
   raise ValueError(f"無效的配置參數: {param}")

   # Stage 5: 使用 RuntimeError
   raise RuntimeError(f"信號計算失敗: {sat_id}")

   # Stage 6: 使用 IOError
   raise IOError(f"無法保存結果: {path}")
   ```

2. **錯誤訊息格式不一致**:
   ```python
   # 不同的格式
   "❌ Stage 2 處理失敗: {error}"
   "ERROR: Stage 3 coordinate transformation failed"
   "失敗：階段4鏈路分析錯誤"
   "Stage 5 signal analysis error: {e}"
   ```

3. **缺少錯誤上下文**:
   ```python
   # ❌ 缺少上下文信息
   raise ValueError("配置參數無效")

   # ✅ 應該包含
   raise ConfigurationError(
       "配置參數無效",
       stage=4,
       parameter="elevation_threshold",
       expected_range="0-90",
       actual_value=-5
   )
   ```

4. **異常層級不明確**:
   - 何時使用 ValueError vs RuntimeError vs Exception？
   - 何時應該 Fail-Fast 終止 vs 記錄警告繼續？
   - 缺少可恢復錯誤 vs 致命錯誤的區分

### 影響分析

| 影響維度 | 嚴重程度 | 具體影響 |
|---------|---------|---------|
| **調試效率** | 🔴 高 | 錯誤訊息不明確，增加 30%+ 調試時間 |
| **日誌解析** | 🟡 中 | 格式不一致，自動化監控困難 |
| **錯誤恢復** | 🟡 中 | 無法區分可恢復 vs 致命錯誤 |
| **學術合規** | 🟢 低 | 不影響科學計算準確性 |
| **維護成本** | 🔴 高 | 新階段開發時缺少明確指引 |

---

## 🎯 設計目標

### 主要目標

1. **統一異常層級** - 建立清晰的異常類型體系
2. **標準化錯誤訊息** - 統一格式和語言（中英文）
3. **豐富錯誤上下文** - 包含足夠信息用於調試
4. **明確 Fail-Fast 策略** - 清晰定義何時終止 vs 繼續
5. **向後相容** - 保留現有異常類型為別名

### 成功指標

- ✅ 所有階段使用統一異常類型
- ✅ 錯誤訊息格式一致性 100%
- ✅ 所有自定義異常包含上下文信息
- ✅ 文檔清晰定義何時使用何種異常
- ✅ 現有測試 100% 通過（向後相容）

---

## 🏗️ 設計方案

### 異常類型層級體系

**設計原則**:
- 繼承自 Python 標準異常類型
- 提供足夠上下文信息
- 支援 Fail-Fast 和學術合規要求

**異常層級結構**:

```
Exception (Python標準)
├── OrbitEngineError (基礎異常)
    ├── ConfigurationError (配置錯誤)
    │   ├── MissingConfigError (缺少配置)
    │   └── InvalidConfigError (配置無效)
    │
    ├── DataError (數據錯誤)
    │   ├── MissingDataError (缺少數據 - Fail-Fast)
    │   ├── InvalidDataError (數據無效 - Fail-Fast)
    │   └── DataFormatError (格式錯誤)
    │
    ├── ProcessingError (處理錯誤)
    │   ├── StageExecutionError (階段執行失敗)
    │   ├── ValidationError (驗證失敗)
    │   └── CalculationError (計算錯誤)
    │
    ├── IOError (I/O錯誤) - 繼承Python標準
    │   ├── FileNotFoundError (檔案不存在)
    │   └── FileWriteError (寫入失敗)
    │
    └── AcademicComplianceError (學術合規錯誤)
        ├── MissingSourceError (缺少SOURCE標註)
        └── InvalidAlgorithmError (演算法不符合標準)
```

---

## 💻 實作細節

### 1. 基礎異常類別實作

**檔案位置**: `src/shared/exceptions.py` (新建)

```python
"""
🚨 Orbit Engine 統一異常處理模組

Standardized exception hierarchy for Grade A+ academic compliance.
All exceptions include rich context for debugging and error tracking.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)
"""

from typing import Any, Dict, Optional


class OrbitEngineError(Exception):
    """
    Orbit Engine 基礎異常類別

    All custom exceptions inherit from this base class.
    Provides structured error context for debugging and logging.

    Attributes:
        message: Error message (bilingual: Chinese + English)
        stage: Stage number where error occurred (1-6, or None for shared)
        context: Additional context dictionary
        original_exception: Original exception if wrapped
    """

    def __init__(
        self,
        message: str,
        stage: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize OrbitEngineError

        Args:
            message: Error description (should be bilingual)
            stage: Stage number (1-6) or None for shared components
            context: Additional context for debugging
            original_exception: Original exception if this is a wrapper

        Example:
            raise OrbitEngineError(
                "配置參數無效 | Invalid configuration parameter",
                stage=4,
                context={
                    'parameter': 'elevation_threshold',
                    'expected_range': '0-90',
                    'actual_value': -5
                }
            )
        """
        self.message = message
        self.stage = stage
        self.context = context or {}
        self.original_exception = original_exception

        # Construct full error message
        full_message = self._format_error_message()
        super().__init__(full_message)

    def _format_error_message(self) -> str:
        """
        Format structured error message

        Returns:
            Formatted error message with context
        """
        parts = [f"❌ {self.message}"]

        if self.stage is not None:
            parts.append(f"   📍 Stage: {self.stage}")

        if self.context:
            parts.append("   📋 Context:")
            for key, value in self.context.items():
                parts.append(f"      - {key}: {value}")

        if self.original_exception:
            parts.append(f"   🔗 Original: {type(self.original_exception).__name__}: {self.original_exception}")

        return "\n".join(parts)


# ==================== Configuration Errors ====================

class ConfigurationError(OrbitEngineError):
    """
    配置錯誤基類

    Raised when configuration loading or validation fails.
    """
    pass


class MissingConfigError(ConfigurationError):
    """
    缺少必需配置

    Raised when required configuration file or field is missing.

    Example:
        raise MissingConfigError(
            "缺少必需配置檔案 | Missing required configuration file",
            stage=4,
            context={'config_file': 'stage4_link_feasibility_config.yaml'}
        )
    """
    pass


class InvalidConfigError(ConfigurationError):
    """
    配置參數無效

    Raised when configuration parameter value is invalid.

    Example:
        raise InvalidConfigError(
            "配置參數超出有效範圍 | Configuration parameter out of valid range",
            stage=2,
            context={
                'parameter': 'time_step_minutes',
                'expected_range': '1-10',
                'actual_value': 0
            }
        )
    """
    pass


# ==================== Data Errors (Fail-Fast) ====================

class DataError(OrbitEngineError):
    """
    數據錯誤基類 - Fail-Fast Required

    Grade A+ requirement: No default values for missing/invalid data.
    All data errors should terminate processing immediately.
    """
    pass


class MissingDataError(DataError):
    """
    缺少必需數據字段 - Fail-Fast

    Raised when required data field is missing from input.

    Example:
        raise MissingDataError(
            "缺少必需數據字段 | Missing required data field",
            stage=4,
            context={
                'field': 'epoch_datetime',
                'source_stage': 1,
                'fail_fast': True
            }
        )
    """
    pass


class InvalidDataError(DataError):
    """
    數據值無效 - Fail-Fast

    Raised when data value is invalid or out of expected range.

    Example:
        raise InvalidDataError(
            "數據值超出物理有效範圍 | Data value out of physical valid range",
            stage=5,
            context={
                'field': 'elevation_angle',
                'valid_range': '0-90 degrees',
                'actual_value': 95.3,
                'satellite_id': 'SAT-12345'
            }
        )
    """
    pass


class DataFormatError(DataError):
    """
    數據格式錯誤

    Raised when data format doesn't match expected structure.

    Example:
        raise DataFormatError(
            "JSON結構不符合預期格式 | JSON structure doesn't match expected format",
            stage=3,
            context={
                'expected_keys': ['stage', 'metadata', 'satellites'],
                'actual_keys': ['stage', 'data'],
                'file_path': 'data/outputs/stage2/output.json'
            }
        )
    """
    pass


# ==================== Processing Errors ====================

class ProcessingError(OrbitEngineError):
    """
    處理錯誤基類

    Raised during stage processing operations.
    """
    pass


class StageExecutionError(ProcessingError):
    """
    階段執行失敗

    Raised when a stage execution fails completely.

    Example:
        raise StageExecutionError(
            "階段執行失敗 | Stage execution failed",
            stage=5,
            context={
                'executor': 'Stage5Executor',
                'processing_duration': '12.5 seconds',
                'satellites_processed': 234,
                'satellites_total': 500
            },
            original_exception=e
        )
    """
    pass


class ValidationError(ProcessingError):
    """
    驗證失敗

    Raised when validation checks fail.

    Example:
        raise ValidationError(
            "Epoch獨立性驗證失敗 | Epoch independence validation failed",
            stage=4,
            context={
                'validator': 'EpochValidator',
                'unique_epochs': 1200,
                'total_satellites': 9015,
                'uniqueness_ratio': 0.13,
                'required_ratio': 0.30
            }
        )
    """
    pass


class CalculationError(ProcessingError):
    """
    計算錯誤

    Raised when scientific calculation fails.

    Example:
        raise CalculationError(
            "信號強度計算失敗 | Signal strength calculation failed",
            stage=5,
            context={
                'calculator': 'GPPSignalCalculator',
                'satellite_id': 'SAT-12345',
                'distance_km': 1500.3,
                'elevation_deg': 15.6,
                'algorithm': '3GPP TS 38.214 Section 5.1.1'
            },
            original_exception=e
        )
    """
    pass


# ==================== I/O Errors ====================

class FileNotFoundError(OrbitEngineError, FileNotFoundError):
    """
    檔案不存在

    Raised when required file doesn't exist.
    Inherits from both OrbitEngineError and Python's FileNotFoundError.

    Example:
        raise FileNotFoundError(
            "上游階段輸出檔案不存在 | Upstream stage output file not found",
            stage=4,
            context={
                'required_file': 'data/outputs/stage3/stage3_output_*.json',
                'upstream_stage': 3,
                'searched_patterns': ['stage3_output_*.json', 'stage3_coordinate_*.json']
            }
        )
    """
    pass


class FileWriteError(OrbitEngineError):
    """
    檔案寫入失敗

    Raised when file writing operation fails.

    Example:
        raise FileWriteError(
            "結果檔案寫入失敗 | Result file write failed",
            stage=5,
            context={
                'file_path': 'data/outputs/stage5/signal_quality.json',
                'file_size_mb': 125.3,
                'disk_space_available_mb': 50.2
            },
            original_exception=e
        )
    """
    pass


# ==================== Academic Compliance Errors ====================

class AcademicComplianceError(OrbitEngineError):
    """
    學術合規錯誤基類

    Raised when academic standards are violated.
    """
    pass


class MissingSourceError(AcademicComplianceError):
    """
    缺少SOURCE標註

    Raised when algorithm or parameter lacks academic source citation.

    Example:
        raise MissingSourceError(
            "演算法缺少學術來源標註 | Algorithm missing academic source citation",
            stage=5,
            context={
                'function': 'calculate_atmospheric_attenuation',
                'file': 'atmospheric_model.py',
                'line': 142,
                'required_format': '# SOURCE: ITU-R P.676-13 (2022)'
            }
        )
    """
    pass


class InvalidAlgorithmError(AcademicComplianceError):
    """
    演算法不符合官方標準

    Raised when implementation doesn't match official specification.

    Example:
        raise InvalidAlgorithmError(
            "演算法實作不符合官方標準 | Algorithm implementation doesn't match official specification",
            stage=5,
            context={
                'algorithm': 'RSRP Calculation',
                'official_standard': '3GPP TS 38.214 v18.1.0 Section 5.1.1',
                'deviation': 'Using simplified path loss model instead of official formula',
                'file': 'signal_calculator.py',
                'line': 89
            }
        )
    """
    pass


# ==================== Backward Compatibility Aliases ====================

# Preserve existing exception types as aliases
class Stage2ConfigError(ConfigurationError):
    """Backward compatibility: Stage 2 configuration error"""
    pass


class Stage4ValidationError(ValidationError):
    """Backward compatibility: Stage 4 validation error"""
    pass


class Stage5CalculationError(CalculationError):
    """Backward compatibility: Stage 5 calculation error"""
    pass


# ==================== Helper Functions ====================

def format_error_context(context: Dict[str, Any]) -> str:
    """
    Format error context dictionary as human-readable string

    Args:
        context: Context dictionary

    Returns:
        Formatted multi-line string

    Example:
        >>> context = {'param': 'elevation', 'value': -5}
        >>> print(format_error_context(context))
        - param: elevation
        - value: -5
    """
    if not context:
        return "(No additional context)"

    lines = []
    for key, value in context.items():
        lines.append(f"  - {key}: {value}")

    return "\n".join(lines)


def wrap_exception(
    original: Exception,
    message: str,
    stage: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None
) -> OrbitEngineError:
    """
    Wrap external exception with OrbitEngineError

    Args:
        original: Original exception
        message: New error message
        stage: Stage number
        context: Additional context

    Returns:
        Wrapped OrbitEngineError

    Example:
        try:
            calculate_signal_strength()
        except ValueError as e:
            raise wrap_exception(
                e,
                "信號計算失敗 | Signal calculation failed",
                stage=5,
                context={'satellite_id': sat_id}
            )
    """
    return OrbitEngineError(
        message=message,
        stage=stage,
        context=context,
        original_exception=original
    )
```

---

### 2. 錯誤訊息格式標準

**統一格式規範**:

```python
# ✅ 標準格式: 中文 | English（雙語）
raise InvalidConfigError(
    "配置參數超出有效範圍 | Configuration parameter out of valid range",
    stage=4,
    context={'parameter': 'elevation_threshold', 'value': -5}
)

# ✅ 日誌輸出格式
logger.error(f"❌ Stage {stage} 處理失敗 | Stage {stage} processing failed: {error}")
logger.warning(f"⚠️ Stage {stage} 警告 | Stage {stage} warning: {message}")
logger.info(f"✅ Stage {stage} 完成 | Stage {stage} completed")

# ✅ Emoji使用規範
# ❌ - 嚴重錯誤（異常）
# ⚠️ - 警告（可繼續）
# ✅ - 成功
# 📋 - 信息
# 📍 - 位置/階段
# 🔗 - 鏈接/關聯
```

---

### 3. 階段遷移指引

**Step 1: 導入新異常模組**

```python
# 在每個階段的主要模組中
from shared.exceptions import (
    MissingDataError,
    InvalidDataError,
    ConfigurationError,
    ValidationError,
    CalculationError
)
```

**Step 2: 替換舊異常**

```python
# ❌ 舊寫法
if 'epoch_datetime' not in satellite_data:
    raise ValueError("缺少 epoch_datetime 字段")

# ✅ 新寫法
if 'epoch_datetime' not in satellite_data:
    raise MissingDataError(
        "缺少必需數據字段 | Missing required data field",
        stage=4,
        context={
            'field': 'epoch_datetime',
            'satellite_id': sat_id,
            'available_fields': list(satellite_data.keys())
        }
    )
```

**Step 3: 豐富錯誤上下文**

```python
# ❌ 舊寫法
try:
    rsrp = calculate_rsrp(distance)
except Exception as e:
    raise RuntimeError(f"計算失敗: {e}")

# ✅ 新寫法
try:
    rsrp = calculate_rsrp(distance, elevation)
except Exception as e:
    raise CalculationError(
        "RSRP計算失敗 | RSRP calculation failed",
        stage=5,
        context={
            'satellite_id': sat_id,
            'distance_km': distance,
            'elevation_deg': elevation,
            'algorithm': '3GPP TS 38.214 Section 5.1.1',
            'timestamp': timestamp
        },
        original_exception=e
    )
```

---

## 📋 實施計劃

### 階段劃分

| 階段 | 任務 | 預估時間 | 依賴 |
|-----|------|---------|------|
| **Step 1** | 創建 `src/shared/exceptions.py` | 1小時 | 無 |
| **Step 2** | 編寫異常模組單元測試 | 1小時 | Step 1 |
| **Step 3** | 遷移 Stage 2-6 異常處理 | 1.5小時 | Step 1 |
| **Step 4** | 更新 shared utilities 異常 | 0.5小時 | Step 1 |
| **Step 5** | 執行全量測試驗證向後相容 | 0.5小時 | Step 3-4 |

**總計**: 4.5小時（約 0.5天）

---

### Step 1: 創建異常模組

**任務**: 建立 `src/shared/exceptions.py`

**驗收標準**:
- ✅ 包含完整異常層級體系（14個異常類型）
- ✅ 所有異常包含 `message`, `stage`, `context`, `original_exception` 屬性
- ✅ 提供向後相容別名（Stage2ConfigError 等）
- ✅ 包含 helper 函數（`format_error_context`, `wrap_exception`）

---

### Step 2: 編寫單元測試

**檔案位置**: `tests/unit/shared/test_exceptions.py`

**測試覆蓋**:

```python
"""
Test suite for shared.exceptions module
"""

import pytest
from src.shared.exceptions import (
    OrbitEngineError,
    MissingDataError,
    InvalidConfigError,
    CalculationError,
    wrap_exception
)


def test_orbit_engine_error_basic():
    """Test basic OrbitEngineError creation"""
    error = OrbitEngineError(
        "測試錯誤 | Test error",
        stage=5,
        context={'key': 'value'}
    )

    assert "❌ 測試錯誤 | Test error" in str(error)
    assert "📍 Stage: 5" in str(error)
    assert "key: value" in str(error)


def test_missing_data_error_fail_fast():
    """Test MissingDataError with Fail-Fast context"""
    error = MissingDataError(
        "缺少必需字段 | Missing required field",
        stage=4,
        context={
            'field': 'epoch_datetime',
            'fail_fast': True
        }
    )

    assert error.stage == 4
    assert error.context['field'] == 'epoch_datetime'
    assert "epoch_datetime" in str(error)


def test_wrap_exception():
    """Test wrapping external exception"""
    original = ValueError("Invalid value")

    wrapped = wrap_exception(
        original,
        "處理失敗 | Processing failed",
        stage=3,
        context={'operation': 'coordinate_transform'}
    )

    assert isinstance(wrapped, OrbitEngineError)
    assert wrapped.original_exception is original
    assert "ValueError: Invalid value" in str(wrapped)


def test_backward_compatibility_alias():
    """Test backward compatibility aliases"""
    from src.shared.exceptions import Stage5CalculationError

    error = Stage5CalculationError(
        "計算錯誤 | Calculation error",
        stage=5
    )

    assert isinstance(error, CalculationError)
    assert isinstance(error, OrbitEngineError)
```

**驗收標準**:
- ✅ 測試覆蓋率 ≥ 90%
- ✅ 包含基本異常創建測試
- ✅ 包含上下文格式化測試
- ✅ 包含異常包裝測試
- ✅ 包含向後相容性測試

---

### Step 3: 遷移各階段異常處理

**遷移順序**: Stage 2 → Stage 3 → Stage 4 → Stage 5 → Stage 6

**遷移模式**:

```python
# 範例: Stage 4 配置載入

# ❌ 舊寫法
def load_config(config_path):
    if not config_path.exists():
        raise FileNotFoundError(f"配置檔案不存在: {config_path}")

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"配置載入失敗: {e}")

    if 'elevation_threshold' not in config:
        raise ValueError("缺少 elevation_threshold 配置")

    return config


# ✅ 新寫法
from shared.exceptions import (
    FileNotFoundError,
    InvalidConfigError,
    MissingConfigError
)

def load_config(config_path):
    if not config_path.exists():
        raise FileNotFoundError(
            "配置檔案不存在 | Configuration file not found",
            stage=4,
            context={
                'config_path': str(config_path),
                'expected_location': 'config/stage4_link_feasibility_config.yaml'
            }
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise InvalidConfigError(
            "配置檔案格式無效 | Configuration file format invalid",
            stage=4,
            context={
                'config_path': str(config_path),
                'format': 'YAML'
            },
            original_exception=e
        )

    if 'elevation_threshold' not in config:
        raise MissingConfigError(
            "缺少必需配置參數 | Missing required configuration parameter",
            stage=4,
            context={
                'parameter': 'elevation_threshold',
                'config_path': str(config_path),
                'available_keys': list(config.keys())
            }
        )

    return config
```

**驗收標準（每個階段）**:
- ✅ 所有 `raise Exception/ValueError/RuntimeError` 替換為對應異常類型
- ✅ 所有異常包含 stage 參數
- ✅ 關鍵錯誤包含豐富 context 信息
- ✅ 現有單元測試 100% 通過（向後相容）

---

### Step 4: 更新 Shared Utilities

**影響模組**:
- `src/shared/base_processor.py`
- `src/shared/base_result_manager.py`
- `src/shared/utils/coordinate_converter.py`
- `scripts/stage_executors/base_executor.py`
- `scripts/stage_validators/base_validator.py`

**遷移重點**:

```python
# base_result_manager.py 中的 Fail-Fast 檢查

# ❌ 舊寫法
def _check_required_field(self, data, field, context=''):
    if field not in data:
        self.logger.error(f"❌ {context}缺少必需字段 '{field}'")
        return False
    return True


# ✅ 新寫法
from shared.exceptions import MissingDataError

def _check_required_field(self, data, field, context=''):
    """Check required field exists (Fail-Fast)"""
    if field not in data:
        raise MissingDataError(
            f"缺少必需數據字段 | Missing required data field",
            stage=self.get_stage_number(),
            context={
                'field': field,
                'context_description': context,
                'available_fields': list(data.keys())
            }
        )
    return True
```

---

### Step 5: 全量測試驗證

**測試範圍**:

```bash
# 1. 單元測試（包含新增異常測試）
PYTHONPATH=/home/sat/orbit-engine python -m pytest tests/unit/ -v

# 2. 集成測試（確保異常正確傳播）
PYTHONPATH=/home/sat/orbit-engine python -m pytest tests/integration/ -v

# 3. E2E測試（完整管道運行）
./run.sh --stages 1-6

# 4. 錯誤場景測試（故意觸發異常）
# 測試 1: 缺少配置檔案
mv config/stage4_link_feasibility_config.yaml config/stage4_backup.yaml
./run.sh --stage 4  # 應該看到 MissingConfigError
mv config/stage4_backup.yaml config/stage4_link_feasibility_config.yaml

# 測試 2: 無效數據格式
echo "invalid json" > data/outputs/stage3/test_invalid.json
./run.sh --stage 4  # 應該看到 DataFormatError
rm data/outputs/stage3/test_invalid.json
```

**驗收標準**:
- ✅ 所有單元測試通過（100%）
- ✅ 所有集成測試通過（100%）
- ✅ E2E 測試成功執行完整管道
- ✅ 錯誤場景測試顯示正確異常類型和上下文

---

## ✅ 驗收標準

### 功能性標準

- ✅ **異常層級完整**: 14個異常類型涵蓋所有場景
- ✅ **異常格式統一**: 所有異常使用雙語訊息（中文 | English）
- ✅ **上下文完整**: 關鍵異常包含 stage, context, original_exception
- ✅ **Fail-Fast 支援**: MissingDataError 和 InvalidDataError 明確標註 fail_fast
- ✅ **向後相容**: 提供舊異常類型別名（Stage2ConfigError 等）

### 測試標準

- ✅ **異常模組單元測試覆蓋率 ≥ 90%**
- ✅ **所有階段現有測試 100% 通過**
- ✅ **錯誤場景測試覆蓋主要異常類型**

### 文檔標準

- ✅ **異常使用指引**: 文檔說明何時使用何種異常
- ✅ **遷移範例**: 提供舊寫法 → 新寫法對照
- ✅ **Docstring 完整**: 所有異常類別包含使用範例

---

## 📊 預期收益

### 量化收益

| 維度 | 改進前 | 改進後 | 提升幅度 |
|-----|-------|-------|---------|
| **錯誤訊息一致性** | ~40% | 100% | +150% |
| **調試時間** | 平均 15min | 平均 10min | -33% |
| **異常類型數** | 混亂（5種通用） | 統一（14種專用） | +180% |
| **上下文信息** | 20% 異常包含 | 80% 異常包含 | +300% |

### 質化收益

1. **開發體驗**:
   - 新階段開發時有明確異常使用指引
   - IDE 自動補全提示異常類型
   - 異常訊息雙語支援國際化

2. **運維支援**:
   - 日誌解析更容易（格式統一）
   - 錯誤追蹤更精確（上下文豐富）
   - 自動化監控更可靠（異常類型明確）

3. **學術合規**:
   - AcademicComplianceError 明確標註學術違規
   - Fail-Fast 錯誤與學術標準對齊
   - 錯誤訊息可用於學術報告

---

## ⚠️ 風險與緩解

| 風險 | 等級 | 緩解措施 |
|-----|------|---------|
| **異常類型變更破壞向後相容** | 🟡 中 | 保留舊異常類型為別名（Stage2ConfigError 等） |
| **遷移過程中遺漏部分異常** | 🟢 低 | 使用 grep 搜尋所有 `raise Exception/ValueError` 確保全覆蓋 |
| **測試用例需要更新** | 🟢 低 | 僅更新明確測試異常類型的測試，大部分測試無需修改 |
| **異常上下文過於詳細影響性能** | 🟢 低 | 異常是錯誤路徑，性能影響可忽略 |

---

## 🔗 相關文件

- [00_OVERVIEW.md](00_OVERVIEW.md) - Phase 4 總覽
- [01_CURRENT_STATUS.md](01_CURRENT_STATUS.md) - 當前架構狀態
- [05_P2_TESTING_FRAMEWORK.md](05_P2_TESTING_FRAMEWORK.md) - 測試框架完善（包含異常測試）
- [ACADEMIC_STANDARDS.md](../../ACADEMIC_STANDARDS.md) - 學術合規標準（Fail-Fast 原則）

---

**下一步**: 閱讀 [04_P2_HDF5_STRATEGY.md](04_P2_HDF5_STRATEGY.md) 了解 HDF5 儲存策略統一方案
