"""
Unit tests for BaseResultManager

Tests Template Method Pattern implementation for result/snapshot management.

Coverage Target: 80%
Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 3 Refactoring - Option D)
"""

import json
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest

from src.shared.base_result_manager import BaseResultManager


# ==================== Test Fixtures ====================

class ConcreteResultManager(BaseResultManager):
    """
    Concrete implementation for testing abstract BaseResultManager

    Implements all 4 abstract methods with simple test behaviors.
    """

    def __init__(self, stage_num: int = 5, logger_instance=None):
        super().__init__(logger_instance)
        self._stage_num = stage_num

    def get_stage_number(self) -> int:
        return self._stage_num

    def get_stage_identifier(self) -> str:
        return f'stage{self._stage_num}_test'

    def build_stage_results(self, **kwargs) -> Dict[str, Any]:
        """Build test results structure"""
        return {
            'stage': self._stage_num,
            'stage_name': f'stage{self._stage_num}_test',
            'data': kwargs.get('data', {}),
            'metadata': kwargs.get('metadata', {})
        }

    def build_snapshot_data(
        self,
        processing_results: Dict[str, Any],
        processing_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build test snapshot structure"""
        return {
            'metadata': processing_results.get('metadata', {}),
            'data_summary': {
                'total_items': processing_stats.get('total_items', 0),
                'processed_items': processing_stats.get('processed_items', 0)
            },
            'validation_status': 'passed' if processing_stats.get('success', True) else 'failed'
        }


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def manager():
    """Create ConcreteResultManager instance for testing"""
    return ConcreteResultManager(stage_num=5)


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    return Mock(spec=logging.Logger)


# ==================== Test Abstract Method Implementation ====================

def test_abstract_methods_must_be_implemented():
    """Test that BaseResultManager cannot be instantiated directly"""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseResultManager()


def test_concrete_implementation_works(manager):
    """Test that concrete implementation can be instantiated"""
    assert isinstance(manager, BaseResultManager)
    assert manager.get_stage_number() == 5
    assert manager.get_stage_identifier() == 'stage5_test'


# ==================== Test Helper Methods ====================

def test_merge_upstream_metadata(manager):
    """Test _merge_upstream_metadata() merges correctly"""
    upstream = {
        'constellation_configs': {'Starlink': {}},
        'processing_start_time': '2025-10-15T10:00:00Z',
        'common_field': 'upstream_value'
    }

    current = {
        'signal_calculations': 12345,
        'processing_duration': 30.5,
        'common_field': 'current_value'  # Should override upstream
    }

    result = manager._merge_upstream_metadata(upstream, current)

    # Check upstream fields preserved
    assert result['constellation_configs'] == upstream['constellation_configs']
    assert result['processing_start_time'] == upstream['processing_start_time']

    # Check current fields added
    assert result['signal_calculations'] == 12345
    assert result['processing_duration'] == 30.5

    # Check current overrides upstream
    assert result['common_field'] == 'current_value'


def test_create_output_directory(manager):
    """Test _create_output_directory() creates correct path"""
    # Test actual directory creation (will be cleaned up automatically)
    output_dir = manager._create_output_directory(5)

    # Check path ends with correct directory
    assert str(output_dir).endswith('stage5')
    assert 'outputs' in str(output_dir)

    # Check directory was actually created
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_create_validation_directory(manager):
    """Test _create_validation_directory() creates correct path"""
    # Test actual directory creation (will be cleaned up automatically)
    validation_dir = manager._create_validation_directory()

    # Check path ends with correct directory
    assert str(validation_dir).endswith('validation_snapshots')

    # Check directory was actually created
    assert validation_dir.exists()
    assert validation_dir.is_dir()


def test_generate_timestamp(manager):
    """Test _generate_timestamp() returns correct format"""
    timestamp = manager._generate_timestamp()

    # Check format: YYYYMMDD_HHMMSS
    assert len(timestamp) == 15  # "20251015_143052"
    assert timestamp[8] == '_'

    # Check parsable as datetime
    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
    assert isinstance(dt, datetime)


def test_save_json(manager, temp_dir):
    """Test _save_json() saves correct JSON format"""
    test_data = {
        'stage': 5,
        'data': {'key': 'value'},
        'metadata': {'count': 100}
    }

    json_file = temp_dir / 'test_output.json'
    manager._save_json(test_data, json_file)

    # Check file exists
    assert json_file.exists()

    # Check content
    with open(json_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data


def test_save_json_with_datetime(manager, temp_dir):
    """Test _save_json() handles datetime objects"""
    test_data = {
        'timestamp': datetime.now(timezone.utc),
        'date': datetime(2025, 10, 15, 14, 30, 0)
    }

    json_file = temp_dir / 'test_datetime.json'
    manager._save_json(test_data, json_file)

    # Check file saved (datetime converted to string)
    assert json_file.exists()

    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check datetime was converted to string
    assert '2025-10-15' in content


# ==================== Test Fail-Fast Helper Methods ====================

def test_check_required_field_exists(manager):
    """Test _check_required_field() returns True when field exists"""
    data = {'field1': 'value1', 'field2': 'value2'}

    assert manager._check_required_field(data, 'field1') is True
    assert manager._check_required_field(data, 'field2') is True


def test_check_required_field_missing(manager, mock_logger):
    """Test _check_required_field() returns False and logs when field missing"""
    manager.logger = mock_logger
    data = {'field1': 'value1'}

    result = manager._check_required_field(data, 'missing_field', 'test_context')

    assert result is False
    mock_logger.error.assert_called_once()
    error_msg = mock_logger.error.call_args[0][0]
    assert 'missing_field' in error_msg
    assert 'test_context' in error_msg


def test_check_required_fields_all_exist(manager):
    """Test _check_required_fields() returns True when all fields exist"""
    data = {
        'field1': 'value1',
        'field2': 'value2',
        'field3': 'value3'
    }

    success, error = manager._check_required_fields(
        data,
        ['field1', 'field2', 'field3'],
        'test_context'
    )

    assert success is True
    assert error is None


def test_check_required_fields_some_missing(manager, mock_logger):
    """Test _check_required_fields() returns False when fields missing"""
    manager.logger = mock_logger
    data = {'field1': 'value1'}

    success, error = manager._check_required_fields(
        data,
        ['field1', 'missing1', 'missing2'],
        'test_context'
    )

    assert success is False
    assert error is not None
    assert 'missing1' in error
    assert 'missing2' in error
    assert 'test_context' in error


def test_check_field_type_correct(manager):
    """Test _check_field_type() returns True for correct type"""
    data = {
        'count': 100,
        'name': 'test',
        'values': [1, 2, 3],
        'metadata': {'key': 'value'}
    }

    assert manager._check_field_type(data, 'count', int) is True
    assert manager._check_field_type(data, 'name', str) is True
    assert manager._check_field_type(data, 'values', list) is True
    assert manager._check_field_type(data, 'metadata', dict) is True


def test_check_field_type_incorrect(manager, mock_logger):
    """Test _check_field_type() returns False for incorrect type"""
    manager.logger = mock_logger
    data = {'count': '100'}  # String instead of int

    result = manager._check_field_type(data, 'count', int, 'test_context')

    assert result is False
    mock_logger.error.assert_called_once()
    error_msg = mock_logger.error.call_args[0][0]
    assert 'count' in error_msg
    assert 'int' in error_msg
    assert 'str' in error_msg


def test_check_field_type_missing_field(manager, mock_logger):
    """Test _check_field_type() returns False when field missing"""
    manager.logger = mock_logger
    data = {}

    result = manager._check_field_type(data, 'missing_field', int)

    assert result is False


# ==================== Test Template Methods ====================

def test_save_results_standard_workflow(manager, temp_dir):
    """Test save_results() standard workflow"""
    # Change working directory to temp for test
    with patch('src.shared.base_result_manager.Path') as mock_path:
        mock_path.return_value = temp_dir

        test_results = {
            'stage': 5,
            'data': {'satellites': 50},
            'metadata': {'duration': 30.5}
        }

        # Mock directory creation and file operations
        output_dir = temp_dir / 'outputs' / 'stage5'
        output_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(manager, '_create_output_directory', return_value=output_dir):
            with patch.object(manager, '_generate_timestamp', return_value='20251015_143052'):
                output_file = manager.save_results(test_results)

        # Check file was created
        output_path = Path(output_file)
        assert output_path.exists()
        assert 'stage5_test_output_20251015_143052.json' in str(output_path)

        # Check content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data == test_results


def test_save_results_with_custom_filename(manager, temp_dir):
    """Test save_results() with custom filename"""
    output_dir = temp_dir / 'outputs' / 'stage5'
    output_dir.mkdir(parents=True, exist_ok=True)

    test_results = {'stage': 5, 'data': {}}

    with patch.object(manager, '_create_output_directory', return_value=output_dir):
        output_file = manager.save_results(test_results, custom_filename='custom_output')

    output_path = Path(output_file)
    assert output_path.exists()
    assert 'custom_output.json' in str(output_path)


def test_save_results_error_handling(manager, mock_logger):
    """Test save_results() error handling"""
    manager.logger = mock_logger

    # Force an error by providing invalid output directory
    with patch.object(manager, '_create_output_directory', side_effect=PermissionError("Cannot create directory")):
        with pytest.raises(IOError, match="無法保存 Stage 5 結果"):
            manager.save_results({'stage': 5})

    mock_logger.error.assert_called_once()


def test_save_validation_snapshot_standard_workflow(manager, temp_dir):
    """Test save_validation_snapshot() standard workflow"""
    validation_dir = temp_dir / 'validation_snapshots'
    validation_dir.mkdir(parents=True, exist_ok=True)

    processing_results = {
        'stage': 5,
        'metadata': {'constellation': 'Starlink'},
        'data': {}
    }

    processing_stats = {
        'total_items': 100,
        'processed_items': 95,
        'success': True
    }

    with patch.object(manager, '_create_validation_directory', return_value=validation_dir):
        result = manager.save_validation_snapshot(processing_results, processing_stats)

    assert result is True

    # Check snapshot file created
    snapshot_file = validation_dir / 'stage5_validation.json'
    assert snapshot_file.exists()

    # Check snapshot content
    with open(snapshot_file, 'r') as f:
        snapshot_data = json.load(f)

    assert snapshot_data['stage'] == 'stage5_test'
    assert snapshot_data['stage_number'] == 5
    assert 'timestamp' in snapshot_data
    assert snapshot_data['validation_status'] == 'passed'
    assert snapshot_data['validation_passed'] is True
    assert snapshot_data['data_summary']['total_items'] == 100


def test_save_validation_snapshot_auto_validation_passed(manager, temp_dir):
    """Test save_validation_snapshot() auto-adds validation_passed field"""
    validation_dir = temp_dir / 'validation_snapshots'
    validation_dir.mkdir(parents=True, exist_ok=True)

    processing_results = {'metadata': {}}
    processing_stats = {'total_items': 50, 'success': False}  # Failed

    with patch.object(manager, '_create_validation_directory', return_value=validation_dir):
        result = manager.save_validation_snapshot(processing_results, processing_stats)

    assert result is True

    snapshot_file = validation_dir / 'stage5_validation.json'
    with open(snapshot_file, 'r') as f:
        snapshot_data = json.load(f)

    # Check validation_passed reflects validation_status
    assert snapshot_data['validation_status'] == 'failed'
    assert snapshot_data['validation_passed'] is False


def test_save_validation_snapshot_error_handling(manager, mock_logger):
    """Test save_validation_snapshot() error handling"""
    manager.logger = mock_logger

    # Force error in build_snapshot_data
    with patch.object(manager, 'build_snapshot_data', side_effect=ValueError("Invalid data")):
        result = manager.save_validation_snapshot({}, {})

    assert result is False
    mock_logger.error.assert_called_once()
    error_msg = mock_logger.error.call_args[0][0]
    assert 'Stage 5' in error_msg
    assert '驗證快照保存失敗' in error_msg


# ==================== Test Extension Points ====================

def test_get_output_filename_pattern(manager):
    """Test get_output_filename_pattern() returns correct pattern"""
    pattern = manager.get_output_filename_pattern()

    assert 'stage5_test' in pattern
    assert '{timestamp}' in pattern
    assert '.json' in pattern


def test_get_output_filename_pattern_override():
    """Test subclass can override get_output_filename_pattern()"""

    class CustomManager(ConcreteResultManager):
        def get_output_filename_pattern(self) -> str:
            return "custom_pattern_{timestamp}.json"

    custom_manager = CustomManager()
    pattern = custom_manager.get_output_filename_pattern()

    assert pattern == "custom_pattern_{timestamp}.json"


# ==================== Test Logger Integration ====================

def test_default_logger_initialization():
    """Test BaseResultManager creates default logger if none provided"""
    manager = ConcreteResultManager()

    assert manager.logger is not None
    assert isinstance(manager.logger, logging.Logger)


def test_custom_logger_injection(mock_logger):
    """Test BaseResultManager accepts custom logger"""
    manager = ConcreteResultManager(logger_instance=mock_logger)

    assert manager.logger is mock_logger


# ==================== Integration Tests ====================

def test_full_workflow_integration(manager, temp_dir):
    """Integration test: Full result saving + snapshot creation workflow"""
    output_dir = temp_dir / 'outputs' / 'stage5'
    validation_dir = temp_dir / 'validation_snapshots'
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Build results
    results = manager.build_stage_results(
        data={'satellites': 50},
        metadata={'constellation': 'Starlink', 'duration': 30.5}
    )

    # Step 2: Save results
    with patch.object(manager, '_create_output_directory', return_value=output_dir):
        with patch.object(manager, '_generate_timestamp', return_value='20251015_150000'):
            output_file = manager.save_results(results)

    # Step 3: Create validation snapshot
    processing_stats = {'total_items': 50, 'processed_items': 50, 'success': True}

    with patch.object(manager, '_create_validation_directory', return_value=validation_dir):
        snapshot_success = manager.save_validation_snapshot(results, processing_stats)

    # Verify results
    assert Path(output_file).exists()
    assert snapshot_success is True

    # Verify result file content
    with open(output_file, 'r') as f:
        saved_results = json.load(f)
    assert saved_results['stage'] == 5
    assert saved_results['data']['satellites'] == 50

    # Verify snapshot content
    snapshot_file = validation_dir / 'stage5_validation.json'
    with open(snapshot_file, 'r') as f:
        snapshot = json.load(f)
    assert snapshot['validation_passed'] is True
    assert snapshot['data_summary']['total_items'] == 50


# ==================== Edge Cases ====================

def test_empty_metadata_merge(manager):
    """Test metadata merge with empty dictionaries"""
    result = manager._merge_upstream_metadata({}, {})
    assert result == {}

    result = manager._merge_upstream_metadata({'key': 'value'}, {})
    assert result == {'key': 'value'}

    result = manager._merge_upstream_metadata({}, {'key': 'value'})
    assert result == {'key': 'value'}


def test_check_required_fields_empty_list(manager):
    """Test _check_required_fields() with empty field list"""
    success, error = manager._check_required_fields({'key': 'value'}, [])
    assert success is True
    assert error is None


def test_save_json_unicode_characters(manager, temp_dir):
    """Test _save_json() handles unicode correctly"""
    test_data = {
        'chinese': '階段五信號分析',
        'japanese': 'ステージ',
        'emoji': '✅🚀📊'
    }

    json_file = temp_dir / 'unicode_test.json'
    manager._save_json(test_data, json_file)

    # Read back and verify
    with open(json_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data


# ==================== Test Coverage Summary ====================

"""
Coverage Summary (Expected):
============================

Methods Covered:
1. ✅ __init__() - logger initialization
2. ✅ _merge_upstream_metadata() - metadata merging
3. ✅ _create_output_directory() - directory creation
4. ✅ _create_validation_directory() - validation dir creation
5. ✅ _generate_timestamp() - timestamp generation
6. ✅ _save_json() - JSON saving
7. ✅ _check_required_field() - single field validation
8. ✅ _check_required_fields() - batch field validation
9. ✅ _check_field_type() - type validation
10. ✅ save_results() - result saving workflow
11. ✅ save_validation_snapshot() - snapshot creation workflow
12. ✅ get_output_filename_pattern() - filename pattern

Test Categories:
- Unit tests: 25+ tests
- Integration tests: 1 full workflow test
- Edge cases: 3 tests
- Error handling: 3 tests

Expected Coverage: 85%+ (exceeds 80% target)
"""
