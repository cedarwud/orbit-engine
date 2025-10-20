"""
⚙️ Base Configuration Manager - Template Method Pattern

Universal configuration management for all stages.
Provides unified config loading, validation, and environment variable override.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 - P1 Refactoring)

Design Philosophy:
-----------------
1. **Template Method Pattern**: Common config workflow in base class
2. **YAML-based Configuration**: External config files for all stages
3. **Environment Variable Override**: Support runtime config override
4. **Fail-Fast Validation**: Validate config on load, reject invalid configs
5. **Backward Compatibility**: Provide sensible defaults matching current behavior

Usage Example:
--------------
```python
class Stage5ConfigManager(BaseConfigManager):
    def get_stage_number(self) -> int:
        return 5

    def get_default_config(self) -> Dict[str, Any]:
        return {
            'elevation_threshold': 5.0,
            'signal_model': 'ITU-R_P618'
        }

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if config['elevation_threshold'] < 0 or config['elevation_threshold'] > 90:
            return False, "elevation_threshold must be 0-90 degrees"
        return True, None

# Usage
manager = Stage5ConfigManager()
config = manager.load_config()  # Loads from YAML + env overrides
```
"""

import os
import logging
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class BaseConfigManager(ABC):
    """
    Base class for stage configuration management

    Uses Template Method Pattern to standardize configuration loading
    while allowing stage-specific defaults and validation.

    Template Methods (implemented here):
    ------------------------------------
    - load_config(): Standard config loading workflow
    - merge_configs(): Merge default + YAML + environment configs
    - _apply_env_overrides(): Apply environment variable overrides

    Abstract Methods (subclass must implement):
    -------------------------------------------
    - get_stage_number(): Return stage number (1-6)
    - get_default_config(): Return default configuration dictionary
    - validate_config(): Validate loaded configuration
    """

    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize base configuration manager

        Args:
            logger_instance: Optional logger instance (defaults to module logger)
        """
        self.logger = logger_instance or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    # ==================== Abstract Methods (Subclass Implementation Required) ====================

    @abstractmethod
    def get_stage_number(self) -> int:
        """
        Return stage number (1-6)

        Returns:
            Stage number

        Example:
            return 5
        """
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default configuration dictionary

        This method should provide sensible defaults that match current behavior.
        These defaults are used when YAML config file is missing or incomplete.

        Returns:
            Default configuration dictionary

        Example:
            return {
                'elevation_threshold': 5.0,  # SOURCE: 3GPP TR 38.821
                'frequency_ghz': 12.0,       # SOURCE: Starlink Ku-band
                'enable_cache': True
            }
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate loaded configuration

        This method should check all configuration parameters and return
        validation result with error message if validation fails.

        Args:
            config: Loaded configuration dictionary

        Returns:
            (is_valid: bool, error_message: Optional[str])
            - (True, None) if valid
            - (False, error_message) if invalid

        Example:
            if config['elevation_threshold'] < 0:
                return False, "elevation_threshold must be >= 0"
            return True, None
        """
        pass

    # ==================== Template Methods (Common Workflow) ====================

    def load_config(self, custom_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Template method: Load and merge configuration

        Standard workflow:
        1. Get default configuration (from subclass)
        2. Load YAML configuration (if exists)
        3. Merge configs (YAML overrides defaults)
        4. Apply environment variable overrides
        5. Validate final configuration
        6. Return final config or raise error

        Args:
            custom_path: Optional custom config file path

        Returns:
            Final merged and validated configuration

        Raises:
            FileNotFoundError: If custom_path provided but doesn't exist
            ValueError: If configuration validation fails

        Example:
            config = manager.load_config()
            print(config['elevation_threshold'])  # 5.0
        """
        stage_num = self.get_stage_number()

        # Step 1: Get default configuration
        default_config = self.get_default_config()
        self.logger.debug(f"📋 Stage {stage_num} 預設配置載入完成")

        # Step 2: Determine YAML config path
        if custom_path:
            config_path = custom_path
            if not config_path.exists():
                raise FileNotFoundError(
                    f"❌ 自定義配置檔案不存在: {config_path}"
                )
        else:
            config_path = self._get_default_config_path()

        # Step 3: Load YAML configuration (if exists)
        yaml_config = {}
        if config_path.exists():
            yaml_config = self._load_yaml(config_path)
            self.logger.info(f"📄 Stage {stage_num} YAML 配置載入: {config_path}")
        else:
            self.logger.warning(
                f"⚠️ Stage {stage_num} 配置檔案不存在（使用預設配置）: {config_path}"
            )

        # Step 4: Merge configurations (YAML overrides defaults)
        merged_config = self.merge_configs(default_config, yaml_config)

        # Step 5: Apply environment variable overrides
        final_config = self._apply_env_overrides(merged_config)

        # Step 6: Validate configuration
        is_valid, error_msg = self.validate_config(final_config)
        if not is_valid:
            raise ValueError(
                f"❌ Stage {stage_num} 配置驗證失敗: {error_msg}"
            )

        self.logger.info(f"✅ Stage {stage_num} 配置載入完成並驗證通過")
        return final_config

    def merge_configs(
        self,
        default_config: Dict[str, Any],
        yaml_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge default and YAML configurations

        Merge strategy:
        - YAML values override default values
        - Nested dictionaries are merged recursively
        - Lists are replaced (not merged)

        Args:
            default_config: Default configuration from get_default_config()
            yaml_config: Configuration loaded from YAML file

        Returns:
            Merged configuration dictionary

        Example:
            default = {'a': 1, 'b': {'c': 2}}
            yaml = {'b': {'d': 3}}
            result = {'a': 1, 'b': {'c': 2, 'd': 3}}
        """
        merged = default_config.copy()

        for key, yaml_value in yaml_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(yaml_value, dict):
                # Recursive merge for nested dictionaries
                merged[key] = self._merge_dicts(merged[key], yaml_value)
            else:
                # Direct override for other types
                merged[key] = yaml_value

        return merged

    # ==================== Helper Methods (Common Utilities) ====================

    def _get_default_config_path(self) -> Path:
        """
        Get default YAML config file path for current stage

        支援雙模式架構（前端渲染 + RL 訓練）:
        - 環境變數 ORBIT_ENGINE_CONFIG_DIR 設置時: 使用 RL 訓練配置
        - 未設置時: 使用原始前端渲染配置

        Returns:
            Path to config file (e.g., config/stage5_signal_analysis_config.yaml)
        """
        import os
        stage_num = self.get_stage_number()

        # 檢查是否使用 RL 訓練配置
        config_dir_env = os.getenv('ORBIT_ENGINE_CONFIG_DIR')

        if config_dir_env:
            # RL 訓練模式: 使用自定義配置目錄
            config_dir = Path(config_dir_env)
            config_filename = f'stage{stage_num}_rl_config.yaml'
            self.logger.info(f"🎯 RL 訓練模式: 使用配置 {config_dir / config_filename}")
        else:
            # 前端渲染模式: 使用標準配置目錄
            config_dir = Path('config')

            # Map stage number to config file name
            stage_config_names = {
                1: 'stage1_orbital_initialization_config.yaml',
                2: 'stage2_orbital_computing_config.yaml',
                3: 'stage3_coordinate_transformation_config.yaml',
                4: 'stage4_link_feasibility_config.yaml',
                5: 'stage5_signal_analysis_config.yaml',
                6: 'stage6_research_optimization_config.yaml',
            }

            config_filename = stage_config_names.get(stage_num)
            if not config_filename:
                raise ValueError(f"❌ 未知的階段編號: {stage_num}")

        return config_dir / config_filename

    def _load_yaml(self, config_path: Path) -> Dict[str, Any]:
        """
        Load YAML configuration file

        Args:
            config_path: Path to YAML config file

        Returns:
            Configuration dictionary loaded from YAML

        Raises:
            ValueError: If YAML parsing fails
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                return {}

            if not isinstance(config, dict):
                raise ValueError(f"配置檔案必須是 YAML 字典格式: {config_path}")

            return config

        except yaml.YAMLError as e:
            raise ValueError(f"❌ YAML 解析失敗: {config_path} - {e}")
        except Exception as e:
            raise ValueError(f"❌ 配置檔案讀取失敗: {config_path} - {e}")

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration

        Environment variable naming convention:
        - ORBIT_ENGINE_STAGE{N}_{CONFIG_KEY} - for top-level keys
        - ORBIT_ENGINE_STAGE{N}_{PARENT}___{CHILD}___{SUBCHILD} - for nested keys

        Nested key separator: Triple underscore (___) separates hierarchy levels

        Examples:
            # Top-level key
            ORBIT_ENGINE_STAGE5_ELEVATION_THRESHOLD=10.0
            → config['elevation_threshold'] = 10.0

            # Nested key (3 levels)
            ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=5.0
            → config['gpp_events']['a3']['offset_db'] = 5.0

            # Nested key (2 levels)
            ORBIT_ENGINE_STAGE3_CACHE_CONFIG___ENABLED=false
            → config['cache_config']['enabled'] = False

        Args:
            config: Configuration dictionary to override

        Returns:
            Configuration with environment variable overrides applied
        """
        stage_num = self.get_stage_number()
        env_prefix = f"ORBIT_ENGINE_STAGE{stage_num}_"

        overridden_config = config.copy()
        override_count = 0

        for env_key, env_value in os.environ.items():
            if env_key.startswith(env_prefix):
                # Extract config key from environment variable name
                config_key_raw = env_key[len(env_prefix):]

                # Convert environment value to appropriate type
                converted_value = self._convert_env_value(env_value)

                # Check if this is a nested key (contains triple underscore)
                if '___' in config_key_raw:
                    # Parse nested key path
                    key_path = [k.lower() for k in config_key_raw.split('___')]

                    # Get original value for logging
                    original_value = self._get_nested_value(config, key_path)

                    # Apply nested override
                    self._set_nested_value(overridden_config, key_path, converted_value)

                    # Log nested override
                    path_str = '.'.join(key_path)
                    self.logger.info(
                        f"🔧 環境變數覆寫 (nested): {path_str} = {converted_value} "
                        f"(原值: {original_value})"
                    )
                else:
                    # Simple top-level key override
                    config_key = config_key_raw.lower()
                    original_value = config.get(config_key)

                    overridden_config[config_key] = converted_value

                    self.logger.info(
                        f"🔧 環境變數覆寫: {config_key} = {converted_value} "
                        f"(原值: {original_value})"
                    )

                override_count += 1

        if override_count > 0:
            self.logger.info(
                f"✅ 套用了 {override_count} 個環境變數覆寫"
            )

        return overridden_config

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate Python type

        Conversion rules:
        - "true"/"false" → bool
        - Numeric strings → int or float
        - Otherwise → str

        Args:
            value: Environment variable value string

        Returns:
            Converted value with appropriate type

        Example:
            "true" → True
            "10" → 10
            "10.5" → 10.5
            "hello" → "hello"
        """
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Numeric conversion
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass

        # Return as string if no conversion matches
        return value

    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries

        Args:
            dict1: Base dictionary
            dict2: Override dictionary (takes priority)

        Returns:
            Merged dictionary

        Example:
            dict1 = {'a': {'b': 1, 'c': 2}}
            dict2 = {'a': {'c': 3, 'd': 4}}
            result = {'a': {'b': 1, 'c': 3, 'd': 4}}
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def _get_nested_value(self, config: Dict[str, Any], key_path: list) -> Any:
        """
        Get value from nested dictionary using key path

        Args:
            config: Configuration dictionary
            key_path: List of keys representing the path (e.g., ['gpp_events', 'a3', 'offset_db'])

        Returns:
            Value at the nested path, or None if path doesn't exist

        Example:
            config = {'gpp_events': {'a3': {'offset_db': 3.0}}}
            value = _get_nested_value(config, ['gpp_events', 'a3', 'offset_db'])
            # Returns: 3.0
        """
        current = config
        for key in key_path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _set_nested_value(self, config: Dict[str, Any], key_path: list, value: Any) -> None:
        """
        Set value in nested dictionary using key path

        Creates intermediate dictionaries if they don't exist.

        Args:
            config: Configuration dictionary (modified in-place)
            key_path: List of keys representing the path (e.g., ['gpp_events', 'a3', 'offset_db'])
            value: Value to set

        Example:
            config = {}
            _set_nested_value(config, ['gpp_events', 'a3', 'offset_db'], 5.0)
            # Result: {'gpp_events': {'a3': {'offset_db': 5.0}}}
        """
        current = config
        for key in key_path[:-1]:
            # Create intermediate dictionary if it doesn't exist
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the final value
        current[key_path[-1]] = value

    # ==================== Optional Helper Methods ====================

    def get_config_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely get configuration value with default fallback

        Args:
            config: Configuration dictionary
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            elevation = manager.get_config_value(config, 'elevation_threshold', 5.0)
        """
        return config.get(key, default)

    def validate_numeric_range(
        self,
        config: Dict[str, Any],
        key: str,
        min_value: float,
        max_value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate numeric configuration value is within range

        Args:
            config: Configuration dictionary
            key: Configuration key to validate
            min_value: Minimum valid value (inclusive)
            max_value: Maximum valid value (inclusive)

        Returns:
            (is_valid: bool, error_message: Optional[str])

        Example:
            is_valid, error = manager.validate_numeric_range(
                config, 'elevation_threshold', 0.0, 90.0
            )
        """
        if key not in config:
            return False, f"缺少必需配置參數: {key}"

        value = config[key]

        if not isinstance(value, (int, float)):
            return False, f"配置參數 '{key}' 必須是數值類型，實際: {type(value).__name__}"

        if value < min_value or value > max_value:
            return False, (
                f"配置參數 '{key}' 超出有效範圍 [{min_value}, {max_value}]，"
                f"實際值: {value}"
            )

        return True, None

    def validate_required_keys(
        self,
        config: Dict[str, Any],
        required_keys: list
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate required configuration keys exist

        Args:
            config: Configuration dictionary
            required_keys: List of required key names

        Returns:
            (is_valid: bool, error_message: Optional[str])

        Example:
            is_valid, error = manager.validate_required_keys(
                config, ['elevation_threshold', 'frequency_ghz']
            )
        """
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            return False, f"缺少必需配置參數: {', '.join(missing_keys)}"

        return True, None


# ==================== Backward Compatibility ====================

# For stages that haven't migrated yet, provide a simple factory function
def load_stage_config(stage_number: int, custom_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Factory function to load stage configuration

    ⚠️ This function will be populated as stages migrate to BaseConfigManager.

    Args:
        stage_number: Stage number (1-6)
        custom_path: Optional custom config file path

    Returns:
        Configuration dictionary

    Raises:
        NotImplementedError: If stage not yet migrated

    Example:
        config = load_stage_config(5)
        print(config['elevation_threshold'])
    """
    stage_managers = {
        # Will be populated as stages migrate:
        # 1: Stage1ConfigManager,
        # 3: Stage3ConfigManager,
        # 6: Stage6ConfigManager,
    }

    if stage_number in stage_managers:
        manager_class = stage_managers[stage_number]
        manager = manager_class()
        return manager.load_config(custom_path)
    else:
        raise NotImplementedError(
            f"Stage {stage_number} 尚未遷移至 BaseConfigManager。"
            f"已遷移階段: {list(stage_managers.keys())}"
        )
