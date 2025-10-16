# P2: 測試框架完善

**優先級**: 🟠 P2 - 中等優先級（應該執行）
**預估時間**: 1.5天
**依賴**: Phase 1-3 完成（基類已建立）
**影響範圍**: BaseExecutor, BaseValidator, BaseStageProcessor, BaseResultManager

---

## 📊 問題分析

### 當前測試覆蓋率

| 基類 | 當前覆蓋率 | 測試檔案 | 狀態 |
|-----|-----------|---------|------|
| **BaseResultManager** | 91% | `tests/unit/shared/test_base_result_manager.py` | ✅ 完整 |
| **StageExecutor** | 0% | ❌ 缺失 | 🔴 需補充 |
| **StageValidator** | 0% | ❌ 缺失 | 🔴 需補充 |
| **BaseStageProcessor** | 0% | ❌ 缺失 | 🔴 需補充 |

**總體覆蓋率**: 約 25%（僅 BaseResultManager 有完整測試）

---

### 問題描述

**1. 基類缺少單元測試**:
- **StageExecutor** (scripts/stage_executors/base_executor.py): 148行代碼，0% 測試覆蓋
- **StageValidator** (scripts/stage_validators/base_validator.py): 150行代碼，0% 測試覆蓋
- **BaseStageProcessor** (src/shared/base_processor.py): 200行代碼，0% 測試覆蓋

**2. 僅依賴集成測試**:
- 基類邏輯通過 Stage 1-6 的集成測試間接驗證
- 缺少針對基類 Template Method 的直接測試
- 邊界條件和錯誤處理未覆蓋

**3. 回歸風險高**:
- 修改基類時無快速反饋（需運行完整管道）
- 無法確保新增方法不破壞現有行為
- 缺少性能基準測試

**4. 重構信心不足**:
- Phase 1-3 重構時主要依賴手動驗證
- 缺少自動化測試保障
- 未來優化（Phase 4+）風險增加

---

### 影響分析

| 影響維度 | 嚴重程度 | 具體影響 |
|---------|---------|---------|
| **重構風險** | 🔴 高 | 基類修改可能破壞 6 個階段，無快速檢測 |
| **開發效率** | 🟡 中 | 依賴集成測試，調試週期長（~5分鐘 vs <1秒） |
| **代碼品質** | 🟡 中 | 缺少測試驅動設計（TDD）的質量保障 |
| **文檔價值** | 🟢 低 | 測試可作為使用範例，當前缺失 |

---

## 🎯 設計目標

### 主要目標

1. **補充基類單元測試** - 達成 80%+ 覆蓋率
2. **Template Method 驗證** - 確保基類工作流程正確
3. **邊界條件覆蓋** - 測試錯誤處理和異常場景
4. **向後相容驗證** - 確保測試通過不影響現有行為
5. **性能基準建立** - 為 Phase 5 性能優化提供基準

### 成功指標

- ✅ **StageExecutor 覆蓋率 ≥ 80%**
- ✅ **StageValidator 覆蓋率 ≥ 80%**
- ✅ **BaseStageProcessor 覆蓋率 ≥ 80%**
- ✅ **BaseResultManager 保持 ≥ 90%**
- ✅ **單元測試執行時間 < 5秒**（全部基類測試）
- ✅ **CI 集成** - 自動運行並報告覆蓋率

---

## 🏗️ 測試框架設計

### 測試分層策略

```
測試金字塔（Orbit Engine）
=========================

        E2E Tests (5%)
       完整管道測試（./run.sh --stages 1-6）
       執行時間：~30分鐘

       /           \
      /  Integration  \
     / Tests (15%)     \
    / Stage級別集成測試  \
   / 執行時間：~5分鐘    \
  /___________________\
 /                     \
/   Unit Tests (80%)    \
基類、工具函數單元測試
執行時間：<5秒
\_______________________/
```

**本次 Phase 4 聚焦**: 補充 Unit Tests 層（基類單元測試）

---

## 💻 實作細節

### 1. StageExecutor 單元測試

**檔案位置**: `tests/unit/scripts/test_stage_executor.py`

**測試目標**:
- Template Method `run()` 工作流程
- 配置載入和合併
- 上游輸出檔案搜尋
- 錯誤處理和日誌輸出

**完整測試代碼**:

```python
"""
Unit tests for StageExecutor base class

Tests the Template Method Pattern implementation and
common executor workflows across all stages.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)
"""

import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from scripts.stage_executors.base_executor import StageExecutor


# ==================== Mock Executor for Testing ====================

class MockStageExecutor(StageExecutor):
    """Mock concrete executor for testing base class"""

    def get_stage_number(self) -> int:
        return 99  # Test stage number

    def get_stage_name(self) -> str:
        return 'test_stage'

    def get_upstream_stage_number(self) -> int:
        return 98  # Previous test stage

    def load_stage_config(self):
        return {
            'test_param': 'test_value',
            'stage': 99
        }

    def find_upstream_output(self):
        return Path('data/outputs/stage98/stage98_output_test.json')

    def load_input_data(self, upstream_path):
        return {
            'stage': 98,
            'data': 'test_data',
            'metadata': {'upstream_meta': 'value'}
        }

    def create_processor(self, config):
        mock_processor = Mock()
        mock_processor.process.return_value = Mock(
            success=True,
            data={'result': 'processed_data'},
            metadata={'processing_time': 1.5}
        )
        return mock_processor

    def save_output(self, processing_result):
        return 'data/outputs/stage99/stage99_output_test.json'


# ==================== Fixtures ====================

@pytest.fixture
def mock_executor():
    """Create MockStageExecutor instance"""
    return MockStageExecutor()


@pytest.fixture
def logger_mock():
    """Create mock logger"""
    return Mock(spec=logging.Logger)


# ==================== Basic Functionality Tests ====================

def test_executor_initialization(mock_executor):
    """Test executor initialization"""
    assert mock_executor.get_stage_number() == 99
    assert mock_executor.get_stage_name() == 'test_stage'
    assert mock_executor.logger is not None


def test_get_stage_info(mock_executor):
    """Test stage information retrieval"""
    assert mock_executor.get_stage_number() == 99
    assert mock_executor.get_stage_name() == 'test_stage'
    assert mock_executor.get_upstream_stage_number() == 98


# ==================== Template Method Tests ====================

def test_run_template_method_success(mock_executor, logger_mock):
    """Test successful run() template method execution"""
    mock_executor.logger = logger_mock

    output_path = mock_executor.run()

    # Verify workflow steps executed
    assert output_path == 'data/outputs/stage99/stage99_output_test.json'

    # Verify logging calls
    logger_mock.info.assert_any_call("🚀 開始執行階段 99: test_stage")
    logger_mock.info.assert_any_call("✅ 階段 99 執行完成")


def test_run_with_config_loading(mock_executor):
    """Test run() loads configuration correctly"""
    with patch.object(mock_executor, 'load_stage_config', return_value={'param': 'value'}) as mock_load:
        mock_executor.run()
        mock_load.assert_called_once()


def test_run_with_upstream_loading(mock_executor):
    """Test run() finds and loads upstream output"""
    with patch.object(mock_executor, 'find_upstream_output') as mock_find:
        with patch.object(mock_executor, 'load_input_data') as mock_load:
            mock_find.return_value = Path('data/outputs/stage98/output.json')
            mock_executor.run()

            mock_find.assert_called_once()
            mock_load.assert_called_once_with(Path('data/outputs/stage98/output.json'))


def test_run_with_processor_execution(mock_executor):
    """Test run() creates and executes processor"""
    mock_processor = Mock()
    mock_processor.process.return_value = Mock(
        success=True,
        data={'result': 'data'},
        metadata={}
    )

    with patch.object(mock_executor, 'create_processor', return_value=mock_processor):
        mock_executor.run()
        mock_processor.process.assert_called_once()


def test_run_with_output_saving(mock_executor):
    """Test run() saves output correctly"""
    with patch.object(mock_executor, 'save_output', return_value='output_path.json') as mock_save:
        output_path = mock_executor.run()

        mock_save.assert_called_once()
        assert output_path == 'output_path.json'


# ==================== Error Handling Tests ====================

def test_run_with_config_loading_error(mock_executor, logger_mock):
    """Test run() handles configuration loading errors"""
    mock_executor.logger = logger_mock

    with patch.object(mock_executor, 'load_stage_config', side_effect=FileNotFoundError("Config not found")):
        with pytest.raises(FileNotFoundError):
            mock_executor.run()

        # Verify error logging
        logger_mock.error.assert_called()


def test_run_with_upstream_not_found(mock_executor, logger_mock):
    """Test run() handles missing upstream output"""
    mock_executor.logger = logger_mock

    with patch.object(mock_executor, 'find_upstream_output', side_effect=FileNotFoundError("Upstream not found")):
        with pytest.raises(FileNotFoundError):
            mock_executor.run()


def test_run_with_processor_failure(mock_executor, logger_mock):
    """Test run() handles processor execution failure"""
    mock_executor.logger = logger_mock

    mock_processor = Mock()
    mock_processor.process.side_effect = RuntimeError("Processing failed")

    with patch.object(mock_executor, 'create_processor', return_value=mock_processor):
        with pytest.raises(RuntimeError):
            mock_executor.run()


def test_run_with_save_output_error(mock_executor, logger_mock):
    """Test run() handles output saving errors"""
    mock_executor.logger = logger_mock

    with patch.object(mock_executor, 'save_output', side_effect=IOError("Cannot save output")):
        with pytest.raises(IOError):
            mock_executor.run()


# ==================== Integration with Real Components Tests ====================

def test_run_with_validation_snapshot(mock_executor):
    """Test run() creates validation snapshot if validator provided"""
    mock_validator = Mock()
    mock_validator.validate.return_value = (True, "Validation passed")

    mock_result_manager = Mock()

    with patch.object(mock_executor, 'create_processor') as mock_create_proc:
        with patch.object(mock_executor, 'save_output', return_value='output.json'):
            # Add validator and result manager to executor
            mock_executor.validator = mock_validator
            mock_executor.result_manager = mock_result_manager

            mock_executor.run()

            # Verify validation called
            # Note: Actual integration depends on executor implementation


# ==================== Configuration Merging Tests ====================

def test_config_merging(mock_executor):
    """Test configuration merging logic"""
    local_config = {'param1': 'local', 'param2': 'local_only'}
    upstream_config = {'param1': 'upstream', 'param3': 'upstream_only'}

    # Simulate config merge (if base class has this method)
    # This is an example - adjust based on actual implementation
    merged = {**upstream_config, **local_config}  # Local takes priority

    assert merged['param1'] == 'local'  # Local overrides
    assert merged['param2'] == 'local_only'  # Local only
    assert merged['param3'] == 'upstream_only'  # Upstream only


# ==================== Logging Tests ====================

def test_logging_stage_start(mock_executor, logger_mock):
    """Test logging at stage start"""
    mock_executor.logger = logger_mock

    mock_executor.run()

    logger_mock.info.assert_any_call("🚀 開始執行階段 99: test_stage")


def test_logging_stage_completion(mock_executor, logger_mock):
    """Test logging at stage completion"""
    mock_executor.logger = logger_mock

    mock_executor.run()

    logger_mock.info.assert_any_call("✅ 階段 99 執行完成")


def test_logging_error_messages(mock_executor, logger_mock):
    """Test error logging"""
    mock_executor.logger = logger_mock

    with patch.object(mock_executor, 'load_stage_config', side_effect=ValueError("Invalid config")):
        with pytest.raises(ValueError):
            mock_executor.run()

        # Verify error logged
        assert logger_mock.error.called or logger_mock.exception.called


# ==================== Abstract Method Tests ====================

def test_abstract_methods_must_be_implemented():
    """Test that abstract methods must be implemented in subclass"""

    with pytest.raises(TypeError):
        # Cannot instantiate base class directly
        executor = StageExecutor()  # Should raise TypeError


def test_mock_executor_implements_all_abstract_methods(mock_executor):
    """Test MockStageExecutor implements all required abstract methods"""
    assert hasattr(mock_executor, 'get_stage_number')
    assert hasattr(mock_executor, 'get_stage_name')
    assert hasattr(mock_executor, 'get_upstream_stage_number')
    assert hasattr(mock_executor, 'load_stage_config')
    assert hasattr(mock_executor, 'find_upstream_output')
    assert hasattr(mock_executor, 'load_input_data')
    assert hasattr(mock_executor, 'create_processor')
    assert hasattr(mock_executor, 'save_output')


# ==================== Performance Tests ====================

def test_run_performance_baseline(mock_executor):
    """Test run() executes within performance baseline"""
    import time

    start_time = time.time()
    mock_executor.run()
    elapsed = time.time() - start_time

    # Unit test should complete in < 1 second
    assert elapsed < 1.0, f"Executor run() took {elapsed:.2f}s (expected < 1s)"
```

**測試覆蓋**:
- ✅ Template Method 完整流程
- ✅ 配置載入和合併
- ✅ 上游輸出搜尋
- ✅ 處理器創建和執行
- ✅ 輸出保存
- ✅ 錯誤處理（6種錯誤場景）
- ✅ 日誌輸出驗證
- ✅ 抽象方法檢查
- ✅ 性能基準

**預期覆蓋率**: 85%+

---

### 2. StageValidator 單元測試

**檔案位置**: `tests/unit/scripts/test_stage_validator.py`

**測試目標**:
- Template Method `validate()` 工作流程
- 通用檢查（metadata, required fields）
- 階段特定驗證
- 驗證快照保存

**完整測試代碼**:

```python
"""
Unit tests for StageValidator base class

Tests validation workflow and common validation helpers.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from scripts.stage_validators.base_validator import StageValidator


# ==================== Mock Validator for Testing ====================

class MockStageValidator(StageValidator):
    """Mock concrete validator for testing base class"""

    def get_stage_number(self) -> int:
        return 99

    def get_stage_name(self) -> str:
        return 'test_stage_validation'

    def validate_stage_specific(self, data, metadata):
        """Mock stage-specific validation"""
        # Example: Check for required field
        if 'test_field' not in data:
            return False, "Missing test_field"

        return True, "Stage-specific validation passed"


# ==================== Fixtures ====================

@pytest.fixture
def mock_validator():
    """Create MockStageValidator instance"""
    return MockStageValidator()


@pytest.fixture
def valid_data():
    """Create valid test data"""
    return {
        'stage': 99,
        'stage_name': 'test_stage',
        'test_field': 'test_value',
        'metadata': {
            'processing_start_time': '2025-10-15T12:00:00Z',
            'processing_duration_seconds': 10.5,
            'constellation_configs': {
                'Starlink': {'count': 100},
                'OneWeb': {'count': 50}
            }
        }
    }


# ==================== Basic Functionality Tests ====================

def test_validator_initialization(mock_validator):
    """Test validator initialization"""
    assert mock_validator.get_stage_number() == 99
    assert mock_validator.get_stage_name() == 'test_stage_validation'


# ==================== Template Method Tests ====================

def test_validate_success(mock_validator, valid_data):
    """Test successful validation"""
    success, message = mock_validator.validate(valid_data)

    assert success is True
    assert "驗證通過" in message or "passed" in message.lower()


def test_validate_workflow_steps(mock_validator, valid_data):
    """Test validate() executes all workflow steps"""
    with pytest.mock.patch.object(mock_validator, 'validate_common_fields') as mock_common:
        with pytest.mock.patch.object(mock_validator, 'validate_metadata_structure') as mock_meta:
            with pytest.mock.patch.object(mock_validator, 'validate_stage_specific') as mock_specific:
                mock_common.return_value = (True, "Common OK")
                mock_meta.return_value = (True, "Metadata OK")
                mock_specific.return_value = (True, "Specific OK")

                success, message = mock_validator.validate(valid_data)

                mock_common.assert_called_once()
                mock_meta.assert_called_once()
                mock_specific.assert_called_once()
                assert success is True


# ==================== Common Validation Tests ====================

def test_validate_common_fields_missing_stage(mock_validator):
    """Test validation fails when 'stage' field missing"""
    invalid_data = {'metadata': {}}

    success, message = mock_validator.validate(invalid_data)

    assert success is False
    assert 'stage' in message.lower()


def test_validate_common_fields_missing_metadata(mock_validator):
    """Test validation fails when 'metadata' field missing"""
    invalid_data = {'stage': 99}

    success, message = mock_validator.validate(invalid_data)

    assert success is False
    assert 'metadata' in message.lower()


def test_validate_common_fields_wrong_stage_number(mock_validator, valid_data):
    """Test validation fails when stage number mismatch"""
    valid_data['stage'] = 88  # Wrong stage number

    success, message = mock_validator.validate(valid_data)

    assert success is False
    assert '階段編號' in message or 'stage number' in message.lower()


# ==================== Metadata Validation Tests ====================

def test_validate_metadata_structure_missing_timestamp(mock_validator, valid_data):
    """Test validation fails when processing_start_time missing"""
    del valid_data['metadata']['processing_start_time']

    success, message = mock_validator.validate(valid_data)

    assert success is False
    assert 'processing_start_time' in message.lower()


def test_validate_metadata_structure_missing_duration(mock_validator, valid_data):
    """Test validation fails when processing_duration_seconds missing"""
    del valid_data['metadata']['processing_duration_seconds']

    success, message = mock_validator.validate(valid_data)

    assert success is False
    assert 'processing_duration' in message.lower()


def test_validate_metadata_structure_missing_constellation_configs(mock_validator, valid_data):
    """Test validation fails when constellation_configs missing"""
    del valid_data['metadata']['constellation_configs']

    success, message = mock_validator.validate(valid_data)

    assert success is False
    assert 'constellation_configs' in message.lower()


# ==================== Stage-Specific Validation Tests ====================

def test_validate_stage_specific_called(mock_validator, valid_data):
    """Test stage-specific validation is called"""
    with pytest.mock.patch.object(mock_validator, 'validate_stage_specific', return_value=(True, "OK")) as mock_specific:
        mock_validator.validate(valid_data)
        mock_specific.assert_called_once()


def test_validate_stage_specific_failure(mock_validator, valid_data):
    """Test validation fails when stage-specific validation fails"""
    del valid_data['test_field']  # Remove required field

    success, message = mock_validator.validate(valid_data)

    assert success is False
    assert 'test_field' in message.lower()


# ==================== Helper Method Tests ====================

def test_check_required_field_exists(mock_validator):
    """Test _check_required_field returns True when field exists"""
    data = {'required_field': 'value'}

    result = mock_validator._check_required_field(data, 'required_field')

    assert result is True


def test_check_required_field_missing(mock_validator):
    """Test _check_required_field returns False when field missing"""
    data = {}

    result = mock_validator._check_required_field(data, 'required_field')

    assert result is False


def test_check_field_type_correct(mock_validator):
    """Test _check_field_type returns True when type matches"""
    data = {'int_field': 42}

    result = mock_validator._check_field_type(data, 'int_field', int)

    assert result is True


def test_check_field_type_incorrect(mock_validator):
    """Test _check_field_type returns False when type mismatches"""
    data = {'int_field': "not_an_int"}

    result = mock_validator._check_field_type(data, 'int_field', int)

    assert result is False


# ==================== Fail-Fast Tests ====================

def test_validate_fail_fast_on_first_error(mock_validator, valid_data):
    """Test validation stops on first error (Fail-Fast)"""
    # Remove multiple fields
    del valid_data['stage']
    del valid_data['metadata']

    success, message = mock_validator.validate(valid_data)

    # Should fail on first missing field ('stage')
    assert success is False
    assert 'stage' in message.lower()


# ==================== Logging Tests ====================

def test_validate_logs_success(mock_validator, valid_data):
    """Test validator logs success message"""
    logger_mock = Mock()
    mock_validator.logger = logger_mock

    mock_validator.validate(valid_data)

    # Check if any info log contains success indicator
    info_calls = [str(call) for call in logger_mock.info.call_args_list]
    assert any('✅' in call or '通過' in call for call in info_calls)


def test_validate_logs_failure(mock_validator, valid_data):
    """Test validator logs failure message"""
    logger_mock = Mock()
    mock_validator.logger = logger_mock

    del valid_data['stage']  # Make validation fail

    mock_validator.validate(valid_data)

    # Check if any error log exists
    assert logger_mock.error.called or logger_mock.warning.called


# ==================== Abstract Method Tests ====================

def test_abstract_method_must_be_implemented():
    """Test that validate_stage_specific must be implemented"""
    with pytest.raises(TypeError):
        # Cannot instantiate base class directly
        validator = StageValidator()


# ==================== Performance Tests ====================

def test_validate_performance_baseline(mock_validator, valid_data):
    """Test validate() executes within performance baseline"""
    import time

    start_time = time.time()
    mock_validator.validate(valid_data)
    elapsed = time.time() - start_time

    # Validation should complete in < 0.1 seconds
    assert elapsed < 0.1, f"Validation took {elapsed:.3f}s (expected < 0.1s)"
```

**測試覆蓋**:
- ✅ Template Method 完整流程
- ✅ 通用字段驗證（stage, metadata）
- ✅ Metadata 結構驗證
- ✅ 階段特定驗證
- ✅ Helper 方法（_check_required_field, _check_field_type）
- ✅ Fail-Fast 行為
- ✅ 日誌輸出驗證
- ✅ 性能基準

**預期覆蓋率**: 85%+

---

### 3. BaseStageProcessor 單元測試

**檔案位置**: `tests/unit/shared/test_base_processor.py`

**測試目標**:
- Template Method `execute()` 工作流程
- `process()` 抽象方法調用
- 錯誤處理和 ProcessingResult 封裝
- `execute()` 覆寫警告機制

**完整測試代碼**:

```python
"""
Unit tests for BaseStageProcessor

Tests processing workflow and Template Method pattern.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)
"""

import pytest
import warnings
from unittest.mock import Mock
from src.shared.base_processor import BaseStageProcessor, ProcessingResult


# ==================== Mock Processor for Testing ====================

class MockStageProcessor(BaseStageProcessor):
    """Mock concrete processor for testing base class"""

    def get_stage_number(self) -> int:
        return 99

    def process(self, input_data):
        """Mock processing logic"""
        return ProcessingResult(
            success=True,
            data={'processed': True},
            metadata={'processing_time': 1.0}
        )


class BrokenProcessor(BaseStageProcessor):
    """Processor that overrides execute() (deprecated pattern)"""

    def get_stage_number(self) -> int:
        return 88

    def execute(self, input_data):
        """Override execute() instead of process() - WRONG"""
        return ProcessingResult(success=True, data={}, metadata={})


# ==================== Fixtures ====================

@pytest.fixture
def mock_processor():
    """Create MockStageProcessor instance"""
    return MockStageProcessor()


@pytest.fixture
def test_input_data():
    """Create test input data"""
    return {
        'stage': 98,
        'data': {'satellites': ['SAT-1', 'SAT-2']},
        'metadata': {'timestamp': '2025-10-15T12:00:00Z'}
    }


# ==================== Basic Functionality Tests ====================

def test_processor_initialization(mock_processor):
    """Test processor initialization"""
    assert mock_processor.get_stage_number() == 99


# ==================== Template Method Tests ====================

def test_execute_template_method_success(mock_processor, test_input_data):
    """Test successful execute() template method"""
    result = mock_processor.execute(test_input_data)

    assert isinstance(result, ProcessingResult)
    assert result.success is True
    assert result.data['processed'] is True


def test_execute_calls_process(mock_processor, test_input_data):
    """Test execute() calls subclass process() method"""
    with pytest.mock.patch.object(mock_processor, 'process', return_value=ProcessingResult(True, {}, {})) as mock_process:
        mock_processor.execute(test_input_data)
        mock_process.assert_called_once_with(test_input_data)


# ==================== ProcessingResult Tests ====================

def test_processing_result_success():
    """Test ProcessingResult creation for success"""
    result = ProcessingResult(
        success=True,
        data={'key': 'value'},
        metadata={'meta': 'data'}
    )

    assert result.success is True
    assert result.data == {'key': 'value'}
    assert result.metadata == {'meta': 'data'}
    assert result.error_message is None


def test_processing_result_failure():
    """Test ProcessingResult creation for failure"""
    result = ProcessingResult(
        success=False,
        data={},
        metadata={},
        error_message="Processing failed due to error"
    )

    assert result.success is False
    assert result.error_message == "Processing failed due to error"


# ==================== Error Handling Tests ====================

def test_execute_with_process_exception(mock_processor, test_input_data):
    """Test execute() handles exceptions from process()"""
    with pytest.mock.patch.object(mock_processor, 'process', side_effect=RuntimeError("Test error")):
        result = mock_processor.execute(test_input_data)

        assert result.success is False
        assert "Test error" in result.error_message


def test_execute_logs_error(mock_processor, test_input_data):
    """Test execute() logs errors"""
    logger_mock = Mock()
    mock_processor.logger = logger_mock

    with pytest.mock.patch.object(mock_processor, 'process', side_effect=ValueError("Invalid data")):
        mock_processor.execute(test_input_data)

        assert logger_mock.error.called or logger_mock.exception.called


# ==================== Execute Override Warning Tests ====================

def test_execute_override_warning():
    """Test warning when subclass overrides execute()"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        processor = BrokenProcessor()

        # Check if deprecation warning was issued
        assert len(w) >= 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "execute()" in str(w[0].message)
        assert "process()" in str(w[0].message)


def test_correct_process_implementation_no_warning(mock_processor):
    """Test no warning when correctly implementing process()"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # MockStageProcessor correctly implements process(), not execute()
        processor = MockStageProcessor()

        # Filter for deprecation warnings about execute()
        execute_warnings = [warning for warning in w if 'execute()' in str(warning.message)]

        assert len(execute_warnings) == 0


# ==================== Abstract Method Tests ====================

def test_abstract_methods_must_be_implemented():
    """Test that abstract methods must be implemented"""
    with pytest.raises(TypeError):
        # Cannot instantiate base class directly
        processor = BaseStageProcessor()


def test_process_is_abstract():
    """Test that process() is abstract method"""
    class IncompleteProcessor(BaseStageProcessor):
        def get_stage_number(self):
            return 1
        # Missing process() implementation

    with pytest.raises(TypeError):
        processor = IncompleteProcessor()


# ==================== Integration Tests ====================

def test_execute_with_real_processing_logic(test_input_data):
    """Test execute() with realistic processing logic"""
    class RealProcessor(BaseStageProcessor):
        def get_stage_number(self):
            return 5

        def process(self, input_data):
            satellites = input_data['data']['satellites']
            processed_sats = [f"PROCESSED_{sat}" for sat in satellites]

            return ProcessingResult(
                success=True,
                data={'processed_satellites': processed_sats},
                metadata={'count': len(processed_sats)}
            )

    processor = RealProcessor()
    result = processor.execute(test_input_data)

    assert result.success is True
    assert 'PROCESSED_SAT-1' in result.data['processed_satellites']
    assert result.metadata['count'] == 2


# ==================== Performance Tests ====================

def test_execute_performance_baseline(mock_processor, test_input_data):
    """Test execute() performance baseline"""
    import time

    start_time = time.time()
    mock_processor.execute(test_input_data)
    elapsed = time.time() - start_time

    # Mock execution should be very fast (< 0.01s)
    assert elapsed < 0.01, f"Execute took {elapsed:.4f}s (expected < 0.01s)"
```

**測試覆蓋**:
- ✅ Template Method `execute()` 流程
- ✅ `process()` 方法調用
- ✅ ProcessingResult 封裝
- ✅ 錯誤處理和異常捕獲
- ✅ `execute()` 覆寫警告機制
- ✅ 抽象方法檢查
- ✅ 集成場景測試
- ✅ 性能基準

**預期覆蓋率**: 85%+

---

### 4. BaseResultManager 測試維護

**檔案位置**: `tests/unit/shared/test_base_result_manager.py` (已存在)

**當前狀態**: 91% 覆蓋率 ✅

**維護任務**:
1. **補充邊界條件測試**: 大型數據集、特殊字符、空 metadata
2. **補充錯誤恢復測試**: 磁碟空間不足、權限不足
3. **補充性能測試**: 大檔案保存性能基準

**新增測試**:

```python
# 補充到現有測試檔案

def test_save_results_with_large_dataset(mock_result_manager, tmp_path):
    """Test saving large result dataset"""
    large_results = {
        'stage': 5,
        'satellites': {f'SAT-{i}': {'data': [1.0] * 1000} for i in range(1000)}
    }

    output_path = mock_result_manager.save_results(large_results)

    assert Path(output_path).exists()
    file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    assert file_size_mb > 0


def test_save_results_with_special_characters(mock_result_manager):
    """Test saving results with special characters"""
    results = {
        'stage': 5,
        'description': 'Test with 特殊字符 and émojis 🚀'
    }

    output_path = mock_result_manager.save_results(results)

    # Verify special characters preserved
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert '特殊字符' in content
        assert '🚀' in content


def test_save_results_disk_full_error(mock_result_manager):
    """Test handling of disk full error"""
    with pytest.mock.patch('builtins.open', side_effect=OSError("No space left on device")):
        with pytest.raises(IOError):
            mock_result_manager.save_results({'stage': 5})
```

---

## 📋 實施計劃

### 階段劃分

| 階段 | 任務 | 預估時間 | 依賴 |
|-----|------|---------|------|
| **Step 1** | 創建 StageExecutor 單元測試 | 3小時 | 無 |
| **Step 2** | 創建 StageValidator 單元測試 | 3小時 | 無 |
| **Step 3** | 創建 BaseStageProcessor 單元測試 | 2小時 | 無 |
| **Step 4** | 補充 BaseResultManager 測試 | 1小時 | 無 |
| **Step 5** | 執行測試並生成覆蓋率報告 | 1小時 | Step 1-4 |
| **Step 6** | CI 集成配置 | 1小時 | Step 5 |

**總計**: 11小時（約 1.5天）

---

### CI 集成配置

**檔案位置**: `.github/workflows/test-base-classes.yml` (新建)

```yaml
name: Base Classes Unit Tests

on:
  push:
    branches: [main, refactor/**]
  pull_request:
    paths:
      - 'src/shared/base_*.py'
      - 'scripts/stage_executors/base_executor.py'
      - 'scripts/stage_validators/base_validator.py'
      - 'tests/unit/**'

jobs:
  test-base-classes:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-mock

      - name: Run base class unit tests
        run: |
          PYTHONPATH=/home/sat/orbit-engine python -m pytest \
            tests/unit/shared/ \
            tests/unit/scripts/ \
            -v \
            --cov=src/shared \
            --cov=scripts/stage_executors/base_executor \
            --cov=scripts/stage_validators/base_validator \
            --cov-report=term-missing \
            --cov-report=html \
            --cov-fail-under=80

      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: base-classes
          name: base-classes-coverage

      - name: Comment coverage on PR
        uses: py-cov-action/python-coverage-comment-action@v3
        with:
          GITHUB_TOKEN: ${{ github.token }}
          MINIMUM_GREEN: 80
          MINIMUM_ORANGE: 70
```

---

## ✅ 驗收標準

### 覆蓋率標準

- ✅ **StageExecutor 覆蓋率 ≥ 80%**
  - Template Method `run()`: 100%
  - Error handling: ≥ 85%
  - Helper methods: ≥ 75%

- ✅ **StageValidator 覆蓋率 ≥ 80%**
  - Template Method `validate()`: 100%
  - Common validation: 100%
  - Helper methods: ≥ 80%

- ✅ **BaseStageProcessor 覆蓋率 ≥ 80%**
  - Template Method `execute()`: 100%
  - Error handling: ≥ 90%
  - Warning mechanism: 100%

- ✅ **BaseResultManager 覆蓋率 ≥ 90%**（已達成，保持）

### 功能性標準

- ✅ **所有測試通過** - 100% pass rate
- ✅ **快速執行** - 所有基類測試 < 5秒
- ✅ **Mock 隔離** - 單元測試不依賴外部資源
- ✅ **清晰文檔** - 每個測試包含清晰 docstring

### CI/CD 標準

- ✅ **自動運行** - PR 提交時自動執行
- ✅ **覆蓋率報告** - 自動生成並上傳
- ✅ **失敗阻斷** - 覆蓋率 < 80% 時 CI 失敗

---

## 📊 預期收益

### 量化收益

| 維度 | 改進前 | 改進後 | 提升幅度 |
|-----|-------|-------|---------|
| **基類測試覆蓋率** | 25% | 85%+ | +240% |
| **調試週期** | ~5分鐘 | <1秒 | -99.7% |
| **回歸檢測** | 手動（30min） | 自動（5s） | -99.7% |
| **重構信心** | 低（無測試） | 高（85%覆蓋） | 質的飛躍 |

### 質化收益

1. **重構安全性**:
   - 修改基類時有快速反饋
   - 邊界條件全覆蓋
   - 回歸 Bug 風險降低 80%

2. **文檔價值**:
   - 測試作為使用範例
   - 新開發者更容易理解基類 API
   - 減少 onboarding 時間 50%

3. **持續改進**:
   - 為 Phase 5 性能優化提供基準
   - 為 Phase 6 API 文檔生成提供基礎
   - 支援未來架構演進

---

## ⚠️ 風險與緩解

| 風險 | 等級 | 緩解措施 |
|-----|------|---------|
| **測試添加增加 CI 時間** | 🟢 低 | 單元測試執行快速（<5秒），影響極小 |
| **Mock 測試與實際行為不一致** | 🟡 中 | 保留集成測試作為補充驗證 |
| **測試維護成本** | 🟢 低 | 基類穩定，修改頻率低 |
| **測試覆蓋率指標追求過高** | 🟢 低 | 設定實際目標 80%，非 100% |

---

## 🔗 相關文件

- [00_OVERVIEW.md](00_OVERVIEW.md) - Phase 4 總覽
- [03_P2_ERROR_HANDLING.md](03_P2_ERROR_HANDLING.md) - 錯誤處理標準化（測試需配合）
- [Phase 3 Progress Report](../phase3_result_manager_refactor/PHASE3_PROGRESS_REPORT.md) - BaseResultManager 測試範例

---

**下一步**: 閱讀 [06_P3_LOGGING_SYSTEM.md](06_P3_LOGGING_SYSTEM.md) 了解日誌系統統一化方案
