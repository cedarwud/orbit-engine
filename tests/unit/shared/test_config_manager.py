"""
🧪 BaseConfigManager Unit Tests

Tests for unified configuration management system.
Validates Template Method Pattern implementation, YAML loading,
environment variable overrides, and validation mechanisms.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 - P1 Refactoring)

Test Coverage Target: ≥ 80%
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from unittest.mock import patch, MagicMock

from src.shared.config_manager import BaseConfigManager


# ==================== Test Fixtures ====================

class MockConfigManager(BaseConfigManager):
    """Mock implementation of BaseConfigManager for testing"""

    def __init__(self, stage_num: int = 5):
        super().__init__()
        self._stage_num = stage_num

    def get_stage_number(self) -> int:
        return self._stage_num

    def get_default_config(self) -> Dict[str, Any]:
        return {
            'elevation_threshold': 5.0,
            'frequency_ghz': 12.5,
            'enable_cache': True,
            'nested': {
                'param_a': 10,
                'param_b': 20
            },
            'list_param': [1, 2, 3]
        }

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        # Simple validation: elevation_threshold must be 0-90
        if 'elevation_threshold' in config:
            if config['elevation_threshold'] < 0 or config['elevation_threshold'] > 90:
                return False, "elevation_threshold must be 0-90 degrees"
        return True, None


@pytest.fixture
def mock_manager():
    """Fixture providing mock config manager"""
    return MockConfigManager(stage_num=5)


@pytest.fixture
def temp_config_file():
    """Fixture providing temporary config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'elevation_threshold': 10.0,
            'frequency_ghz': 14.0,
            'nested': {
                'param_b': 30,
                'param_c': 40
            }
        }
        yaml.dump(config_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# ==================== Test Default Configuration ====================

def test_get_default_config(mock_manager):
    """Test default configuration retrieval"""
    config = mock_manager.get_default_config()

    assert config['elevation_threshold'] == 5.0
    assert config['frequency_ghz'] == 12.5
    assert config['enable_cache'] is True
    assert config['nested']['param_a'] == 10


def test_get_stage_number(mock_manager):
    """Test stage number retrieval"""
    assert mock_manager.get_stage_number() == 5


# ==================== Test YAML Loading ====================

def test_load_yaml_valid_file(mock_manager, temp_config_file):
    """Test loading valid YAML configuration file"""
    yaml_config = mock_manager._load_yaml(temp_config_file)

    assert yaml_config['elevation_threshold'] == 10.0
    assert yaml_config['frequency_ghz'] == 14.0
    assert yaml_config['nested']['param_b'] == 30


def test_load_yaml_missing_file(mock_manager):
    """Test loading non-existent YAML file"""
    missing_path = Path('/tmp/nonexistent_config_12345.yaml')

    with pytest.raises(ValueError, match="配置檔案讀取失敗"):
        mock_manager._load_yaml(missing_path)


def test_load_yaml_invalid_format(mock_manager):
    """Test loading invalid YAML format"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [[[")
        invalid_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="YAML 解析失敗"):
            mock_manager._load_yaml(invalid_path)
    finally:
        invalid_path.unlink()


def test_load_yaml_empty_file(mock_manager):
    """Test loading empty YAML file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        empty_path = Path(f.name)

    try:
        result = mock_manager._load_yaml(empty_path)
        assert result == {}
    finally:
        empty_path.unlink()


# ==================== Test Configuration Merging ====================

def test_merge_configs_simple_override(mock_manager):
    """Test simple configuration value override"""
    default = {'param_a': 1, 'param_b': 2}
    override = {'param_b': 3}

    merged = mock_manager.merge_configs(default, override)

    assert merged['param_a'] == 1
    assert merged['param_b'] == 3


def test_merge_configs_nested_dict(mock_manager):
    """Test nested dictionary merge"""
    default = {
        'nested': {
            'param_a': 1,
            'param_b': 2
        }
    }
    override = {
        'nested': {
            'param_b': 3,
            'param_c': 4
        }
    }

    merged = mock_manager.merge_configs(default, override)

    assert merged['nested']['param_a'] == 1  # Preserved from default
    assert merged['nested']['param_b'] == 3  # Overridden
    assert merged['nested']['param_c'] == 4  # Added


def test_merge_configs_list_replacement(mock_manager):
    """Test list replacement (not merge)"""
    default = {'list_param': [1, 2, 3]}
    override = {'list_param': [4, 5]}

    merged = mock_manager.merge_configs(default, override)

    assert merged['list_param'] == [4, 5]  # Replaced, not merged


def test_merge_configs_deep_nested(mock_manager):
    """Test deep nested dictionary merge"""
    default = {
        'level1': {
            'level2': {
                'param_a': 1,
                'param_b': 2
            }
        }
    }
    override = {
        'level1': {
            'level2': {
                'param_b': 3
            },
            'level2_new': {
                'param_c': 4
            }
        }
    }

    merged = mock_manager.merge_configs(default, override)

    assert merged['level1']['level2']['param_a'] == 1
    assert merged['level1']['level2']['param_b'] == 3
    assert merged['level1']['level2_new']['param_c'] == 4


# ==================== Test Environment Variable Overrides ====================

def test_apply_env_overrides_integer(mock_manager):
    """Test environment variable override with integer value"""
    config = {'elevation_threshold': 5.0}

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_ELEVATION_THRESHOLD': '10'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['elevation_threshold'] == 10


def test_apply_env_overrides_float(mock_manager):
    """Test environment variable override with float value"""
    config = {'frequency_ghz': 12.5}

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_FREQUENCY_GHZ': '14.25'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['frequency_ghz'] == 14.25


def test_apply_env_overrides_boolean_true(mock_manager):
    """Test environment variable override with boolean true"""
    config = {'enable_cache': False}

    for true_value in ['true', 'True', 'TRUE', 'yes', 'Yes', '1']:
        with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_ENABLE_CACHE': true_value}):
            overridden = mock_manager._apply_env_overrides(config)
            assert overridden['enable_cache'] is True


def test_apply_env_overrides_boolean_false(mock_manager):
    """Test environment variable override with boolean false"""
    config = {'enable_cache': True}

    for false_value in ['false', 'False', 'FALSE', 'no', 'No', '0']:
        with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_ENABLE_CACHE': false_value}):
            overridden = mock_manager._apply_env_overrides(config)
            assert overridden['enable_cache'] is False


def test_apply_env_overrides_string(mock_manager):
    """Test environment variable override with string value"""
    config = {'log_level': 'INFO'}

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_LOG_LEVEL': 'DEBUG'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['log_level'] == 'DEBUG'


def test_apply_env_overrides_no_matching_vars(mock_manager):
    """Test environment variable override with no matching variables"""
    config = {'elevation_threshold': 5.0}

    with patch.dict(os.environ, {'OTHER_VAR': '10'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['elevation_threshold'] == 5.0  # Unchanged


def test_apply_env_overrides_different_stage(mock_manager):
    """Test environment variable override for different stage"""
    config = {'elevation_threshold': 5.0}

    # Env var for stage 3, but manager is stage 5
    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE3_ELEVATION_THRESHOLD': '10'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['elevation_threshold'] == 5.0  # Unchanged


# ==================== Test Value Conversion ====================

def test_convert_env_value_integer(mock_manager):
    """Test environment value conversion to integer"""
    assert mock_manager._convert_env_value("123") == 123
    assert mock_manager._convert_env_value("0") == 0
    assert mock_manager._convert_env_value("-456") == -456


def test_convert_env_value_float(mock_manager):
    """Test environment value conversion to float"""
    assert mock_manager._convert_env_value("12.5") == 12.5
    assert mock_manager._convert_env_value("-3.14") == -3.14
    assert mock_manager._convert_env_value("0.001") == 0.001


def test_convert_env_value_boolean(mock_manager):
    """Test environment value conversion to boolean"""
    assert mock_manager._convert_env_value("true") is True
    assert mock_manager._convert_env_value("TRUE") is True
    assert mock_manager._convert_env_value("yes") is True
    assert mock_manager._convert_env_value("1") is True

    assert mock_manager._convert_env_value("false") is False
    assert mock_manager._convert_env_value("FALSE") is False
    assert mock_manager._convert_env_value("no") is False
    assert mock_manager._convert_env_value("0") is False


def test_convert_env_value_string(mock_manager):
    """Test environment value conversion to string"""
    assert mock_manager._convert_env_value("hello") == "hello"
    assert mock_manager._convert_env_value("INFO") == "INFO"


# ==================== Test Validation ====================

def test_validate_config_valid(mock_manager):
    """Test configuration validation with valid config"""
    config = {'elevation_threshold': 45.0}

    is_valid, error_msg = mock_manager.validate_config(config)

    assert is_valid is True
    assert error_msg is None


def test_validate_config_invalid(mock_manager):
    """Test configuration validation with invalid config"""
    config = {'elevation_threshold': 95.0}  # Invalid: > 90

    is_valid, error_msg = mock_manager.validate_config(config)

    assert is_valid is False
    assert "elevation_threshold must be 0-90 degrees" in error_msg


def test_validate_numeric_range_valid(mock_manager):
    """Test numeric range validation with valid value"""
    config = {'elevation_threshold': 45.0}

    is_valid, error_msg = mock_manager.validate_numeric_range(
        config, 'elevation_threshold', 0.0, 90.0
    )

    assert is_valid is True
    assert error_msg is None


def test_validate_numeric_range_below_min(mock_manager):
    """Test numeric range validation with value below minimum"""
    config = {'elevation_threshold': -5.0}

    is_valid, error_msg = mock_manager.validate_numeric_range(
        config, 'elevation_threshold', 0.0, 90.0
    )

    assert is_valid is False
    assert "超出有效範圍" in error_msg


def test_validate_numeric_range_above_max(mock_manager):
    """Test numeric range validation with value above maximum"""
    config = {'elevation_threshold': 95.0}

    is_valid, error_msg = mock_manager.validate_numeric_range(
        config, 'elevation_threshold', 0.0, 90.0
    )

    assert is_valid is False
    assert "超出有效範圍" in error_msg


def test_validate_numeric_range_missing_key(mock_manager):
    """Test numeric range validation with missing key"""
    config = {}

    is_valid, error_msg = mock_manager.validate_numeric_range(
        config, 'elevation_threshold', 0.0, 90.0
    )

    assert is_valid is False
    assert "缺少必需配置參數" in error_msg


def test_validate_numeric_range_wrong_type(mock_manager):
    """Test numeric range validation with wrong type"""
    config = {'elevation_threshold': 'invalid'}

    is_valid, error_msg = mock_manager.validate_numeric_range(
        config, 'elevation_threshold', 0.0, 90.0
    )

    assert is_valid is False
    assert "必須是數值類型" in error_msg


def test_validate_required_keys_all_present(mock_manager):
    """Test required keys validation with all keys present"""
    config = {'elevation_threshold': 5.0, 'frequency_ghz': 12.5}

    is_valid, error_msg = mock_manager.validate_required_keys(
        config, ['elevation_threshold', 'frequency_ghz']
    )

    assert is_valid is True
    assert error_msg is None


def test_validate_required_keys_missing(mock_manager):
    """Test required keys validation with missing keys"""
    config = {'elevation_threshold': 5.0}

    is_valid, error_msg = mock_manager.validate_required_keys(
        config, ['elevation_threshold', 'frequency_ghz']
    )

    assert is_valid is False
    assert "缺少必需配置參數" in error_msg
    assert "frequency_ghz" in error_msg


# ==================== Test Full Config Loading Workflow ====================

def test_load_config_default_only(mock_manager):
    """Test loading config with defaults only (no YAML file)"""
    with patch.object(mock_manager, '_get_default_config_path') as mock_path:
        mock_path.return_value = Path('/tmp/nonexistent_config.yaml')

        config = mock_manager.load_config()

    # Should use default config
    assert config['elevation_threshold'] == 5.0
    assert config['frequency_ghz'] == 12.5


def test_load_config_yaml_override(mock_manager, temp_config_file):
    """Test loading config with YAML override"""
    config = mock_manager.load_config(custom_path=temp_config_file)

    # YAML overrides defaults
    assert config['elevation_threshold'] == 10.0
    assert config['frequency_ghz'] == 14.0

    # Default preserved for unspecified keys
    assert config['enable_cache'] is True


def test_load_config_env_override(mock_manager, temp_config_file):
    """Test loading config with environment variable override"""
    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_ELEVATION_THRESHOLD': '20'}):
        config = mock_manager.load_config(custom_path=temp_config_file)

    # Environment variable has highest priority
    assert config['elevation_threshold'] == 20

    # YAML override still applies for other keys
    assert config['frequency_ghz'] == 14.0


def test_load_config_validation_failure(mock_manager):
    """Test loading config with validation failure"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        invalid_config = {'elevation_threshold': 95.0}  # Invalid
        yaml.dump(invalid_config, f)
        invalid_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="配置驗證失敗"):
            mock_manager.load_config(custom_path=invalid_path)
    finally:
        invalid_path.unlink()


def test_load_config_custom_path_missing(mock_manager):
    """Test loading config with missing custom path"""
    missing_path = Path('/tmp/nonexistent_config_67890.yaml')

    with pytest.raises(FileNotFoundError, match="自定義配置檔案不存在"):
        mock_manager.load_config(custom_path=missing_path)


# ==================== Test Configuration Path Resolution ====================

def test_get_default_config_path_stage1(mock_manager):
    """Test default config path for Stage 1"""
    mock_manager._stage_num = 1
    path = mock_manager._get_default_config_path()

    assert path == Path('config/stage1_orbital_initialization_config.yaml')


def test_get_default_config_path_stage3(mock_manager):
    """Test default config path for Stage 3"""
    mock_manager._stage_num = 3
    path = mock_manager._get_default_config_path()

    assert path == Path('config/stage3_coordinate_transformation_config.yaml')


def test_get_default_config_path_stage6(mock_manager):
    """Test default config path for Stage 6"""
    mock_manager._stage_num = 6
    path = mock_manager._get_default_config_path()

    assert path == Path('config/stage6_research_optimization_config.yaml')


def test_get_default_config_path_invalid_stage(mock_manager):
    """Test default config path with invalid stage number"""
    mock_manager._stage_num = 99

    with pytest.raises(ValueError, match="未知的階段編號"):
        mock_manager._get_default_config_path()


# ==================== Test Helper Methods ====================

def test_get_config_value_exists(mock_manager):
    """Test getting existing config value"""
    config = {'elevation_threshold': 5.0}

    value = mock_manager.get_config_value(config, 'elevation_threshold')

    assert value == 5.0


def test_get_config_value_missing_with_default(mock_manager):
    """Test getting missing config value with default"""
    config = {}

    value = mock_manager.get_config_value(config, 'elevation_threshold', default=10.0)

    assert value == 10.0


def test_get_config_value_missing_no_default(mock_manager):
    """Test getting missing config value without default"""
    config = {}

    value = mock_manager.get_config_value(config, 'elevation_threshold')

    assert value is None


# ==================== Test _merge_dicts Helper ====================

def test_merge_dicts_simple(mock_manager):
    """Test simple dictionary merge"""
    dict1 = {'a': 1, 'b': 2}
    dict2 = {'b': 3, 'c': 4}

    merged = mock_manager._merge_dicts(dict1, dict2)

    assert merged == {'a': 1, 'b': 3, 'c': 4}


def test_merge_dicts_nested(mock_manager):
    """Test nested dictionary merge"""
    dict1 = {'nested': {'a': 1, 'b': 2}}
    dict2 = {'nested': {'b': 3, 'c': 4}}

    merged = mock_manager._merge_dicts(dict1, dict2)

    assert merged == {'nested': {'a': 1, 'b': 3, 'c': 4}}


# ==================== Test Nested Environment Variable Overrides ====================

def test_apply_env_overrides_nested_2_levels(mock_manager):
    """Test environment variable override with 2-level nested key"""
    config = {
        'nested': {
            'param_a': 10
        }
    }

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_NESTED___PARAM_A': '20'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['nested']['param_a'] == 20


def test_apply_env_overrides_nested_3_levels(mock_manager):
    """Test environment variable override with 3-level nested key"""
    config = {
        'gpp_events': {
            'a3': {
                'offset_db': 3.0
            }
        }
    }

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_GPP_EVENTS___A3___OFFSET_DB': '5.0'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['gpp_events']['a3']['offset_db'] == 5.0


def test_apply_env_overrides_nested_creates_missing_path(mock_manager):
    """Test nested override creates intermediate dictionaries if missing"""
    config = {}

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_NEW___NESTED___VALUE': '42'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['new']['nested']['value'] == 42


def test_apply_env_overrides_nested_boolean(mock_manager):
    """Test nested override with boolean value"""
    config = {
        'cache_config': {
            'enabled': True
        }
    }

    with patch.dict(os.environ, {'ORBIT_ENGINE_STAGE5_CACHE_CONFIG___ENABLED': 'false'}):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['cache_config']['enabled'] is False


def test_apply_env_overrides_mixed_flat_and_nested(mock_manager):
    """Test mixed flat and nested environment variable overrides"""
    config = {
        'top_level': 10,
        'nested': {
            'value': 20
        }
    }

    with patch.dict(os.environ, {
        'ORBIT_ENGINE_STAGE5_TOP_LEVEL': '100',
        'ORBIT_ENGINE_STAGE5_NESTED___VALUE': '200'
    }):
        overridden = mock_manager._apply_env_overrides(config)

    assert overridden['top_level'] == 100
    assert overridden['nested']['value'] == 200


def test_get_nested_value_exists(mock_manager):
    """Test getting existing nested value"""
    config = {
        'gpp_events': {
            'a3': {
                'offset_db': 3.0
            }
        }
    }

    value = mock_manager._get_nested_value(config, ['gpp_events', 'a3', 'offset_db'])

    assert value == 3.0


def test_get_nested_value_missing(mock_manager):
    """Test getting non-existent nested value"""
    config = {
        'gpp_events': {
            'a3': {}
        }
    }

    value = mock_manager._get_nested_value(config, ['gpp_events', 'a3', 'offset_db'])

    assert value is None


def test_set_nested_value_existing_path(mock_manager):
    """Test setting nested value on existing path"""
    config = {
        'gpp_events': {
            'a3': {
                'offset_db': 3.0
            }
        }
    }

    mock_manager._set_nested_value(config, ['gpp_events', 'a3', 'offset_db'], 5.0)

    assert config['gpp_events']['a3']['offset_db'] == 5.0


def test_set_nested_value_creates_path(mock_manager):
    """Test setting nested value creates missing path"""
    config = {}

    mock_manager._set_nested_value(config, ['new', 'nested', 'value'], 42)

    assert config['new']['nested']['value'] == 42


def test_set_nested_value_overwrites_non_dict(mock_manager):
    """Test setting nested value overwrites non-dict intermediate value"""
    config = {
        'parent': 'string_value'  # Will be overwritten with dict
    }

    mock_manager._set_nested_value(config, ['parent', 'child'], 10)

    assert config['parent']['child'] == 10


# ==================== Test Complete Workflow Integration ====================

def test_complete_workflow_integration(mock_manager, temp_config_file):
    """Test complete configuration loading workflow integration"""
    # Setup environment override
    with patch.dict(os.environ, {
        'ORBIT_ENGINE_STAGE5_ENABLE_CACHE': 'false',
        'ORBIT_ENGINE_STAGE5_FREQUENCY_GHZ': '15.5'
    }):
        config = mock_manager.load_config(custom_path=temp_config_file)

    # Verify precedence: env > YAML > default
    assert config['enable_cache'] is False  # From environment
    assert config['frequency_ghz'] == 15.5  # From environment (overrides YAML)
    assert config['elevation_threshold'] == 10.0  # From YAML
    assert config['nested']['param_a'] == 10  # From default
    assert config['nested']['param_b'] == 30  # From YAML
    assert config['nested']['param_c'] == 40  # From YAML


def test_complete_workflow_with_nested_env_override(mock_manager, temp_config_file):
    """Test complete workflow with nested environment variable override"""
    # Setup nested environment override
    with patch.dict(os.environ, {
        'ORBIT_ENGINE_STAGE5_NESTED___PARAM_B': '99',
        'ORBIT_ENGINE_STAGE5_NESTED___PARAM_C': '88'
    }):
        config = mock_manager.load_config(custom_path=temp_config_file)

    # Verify nested overrides work in full workflow
    assert config['nested']['param_a'] == 10  # From default
    assert config['nested']['param_b'] == 99  # From environment (nested override)
    assert config['nested']['param_c'] == 88  # From environment (nested override)


# ==================== Performance Tests ====================

def test_load_config_performance(mock_manager, temp_config_file, benchmark=None):
    """Test configuration loading performance (optional benchmark)"""
    if benchmark:
        # If pytest-benchmark available
        result = benchmark(mock_manager.load_config, temp_config_file)
        assert result is not None
    else:
        # Simple performance check
        import time
        start = time.time()
        config = mock_manager.load_config(custom_path=temp_config_file)
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should complete in < 100ms
        assert config is not None
