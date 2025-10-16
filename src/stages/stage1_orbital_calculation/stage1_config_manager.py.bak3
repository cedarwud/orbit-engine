"""
⚙️ Stage 1 Configuration Manager

Specialized configuration manager for Stage 1: TLE Data Loading & Orbital Initialization.
Inherits from BaseConfigManager to provide unified configuration management.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 - P1 Refactoring)

Usage:
------
```python
from stages.stage1_orbital_calculation.stage1_config_manager import Stage1ConfigManager

manager = Stage1ConfigManager()
config = manager.load_config()  # Loads from YAML + env overrides
print(config['sampling']['mode'])  # 'auto' or 'enabled' or 'disabled'
```
"""

import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from shared.configs import BaseConfigManager


class Stage1ConfigManager(BaseConfigManager):
    """
    Stage 1 Configuration Manager

    Manages configuration for TLE data loading and orbital initialization.
    Provides defaults matching existing behavior for backward compatibility.
    """

    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize Stage 1 configuration manager

        Args:
            logger_instance: Optional logger instance
        """
        super().__init__(logger_instance)

    def get_stage_number(self) -> int:
        """
        Return Stage 1 identifier

        Returns:
            int: Stage number (1)
        """
        return 1

    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default Stage 1 configuration

        Provides sensible defaults matching current hardcoded behavior.
        All defaults include SOURCE annotations for academic compliance.

        Returns:
            Dict[str, Any]: Default configuration dictionary
        """
        return {
            # ==================== 取樣模式配置 ====================
            'sampling': {
                'mode': 'auto',  # auto | enabled | disabled
                'sample_size': 50
            },

            # ==================== Epoch 動態分析配置 ====================
            'epoch_analysis': {
                'enabled': True
            },

            # ==================== Epoch 篩選配置 ====================
            'epoch_filter': {
                'enabled': True,
                'mode': 'latest_date',  # latest_date | date_range | all
                'tolerance_hours': 24
            },

            # ==================== 星座配置 ====================
            'constellation_configs': {
                'starlink': {
                    'elevation_threshold': 5.0,  # SOURCE: 3GPP TR 38.821 Section 6.1.2
                    'frequency_ghz': 12.5,
                    'target_satellites': {
                        'min': 10,
                        'max': 15
                    }
                },
                'oneweb': {
                    'elevation_threshold': 10.0,
                    'frequency_ghz': 12.75,
                    'target_satellites': {
                        'min': 3,
                        'max': 6
                    }
                }
            },

            # ==================== TLE 數據源配置 ====================
            'tle_data': {
                'data_directory': 'data/tle_data',
                'format': 'txt',
                'file_patterns': ['*.tle', '*.txt']
            },

            # ==================== 驗證配置 ====================
            'validation': {
                'tle_format_check': True,
                'tle_checksum_check': True,
                'min_unique_epochs': 5
            },

            # ==================== 輸出配置 ====================
            'output': {
                'directory': 'data/outputs/stage1',
                'filename_pattern': 'stage1_output_{timestamp}.json',
                'save_validation_snapshot': True
            },

            # ==================== 性能配置 ====================
            'performance': {
                'show_progress': True,
                'log_level': 'INFO'
            }
        }

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate Stage 1 configuration

        Checks:
        - Sampling mode is valid ('auto', 'enabled', 'disabled')
        - Sample size is positive integer
        - Epoch filter mode is valid
        - Tolerance hours is positive
        - Elevation thresholds are 0-90 degrees
        - Frequency values are positive
        - TLE data directory exists

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Validate sampling configuration
        if 'sampling' in config:
            sampling = config['sampling']

            # Check sampling mode
            if 'mode' in sampling:
                valid_modes = ['auto', 'enabled', 'disabled']
                if sampling['mode'] not in valid_modes:
                    return False, (
                        f"sampling.mode 必須是 {valid_modes} 之一，"
                        f"實際: {sampling['mode']}"
                    )

            # Check sample size
            if 'sample_size' in sampling:
                if not isinstance(sampling['sample_size'], int) or sampling['sample_size'] <= 0:
                    return False, "sampling.sample_size 必須是正整數"

        # Validate epoch filter configuration
        if 'epoch_filter' in config:
            epoch_filter = config['epoch_filter']

            # Check epoch filter mode
            if 'mode' in epoch_filter:
                valid_modes = ['latest_date', 'date_range', 'all']
                if epoch_filter['mode'] not in valid_modes:
                    return False, (
                        f"epoch_filter.mode 必須是 {valid_modes} 之一，"
                        f"實際: {epoch_filter['mode']}"
                    )

            # Check tolerance hours
            if 'tolerance_hours' in epoch_filter:
                if not isinstance(epoch_filter['tolerance_hours'], (int, float)) or \
                   epoch_filter['tolerance_hours'] <= 0:
                    return False, "epoch_filter.tolerance_hours 必須是正數"

        # Validate constellation configurations
        if 'constellation_configs' in config:
            for constellation, constellation_config in config['constellation_configs'].items():
                # Validate elevation threshold
                if 'elevation_threshold' in constellation_config:
                    elevation = constellation_config['elevation_threshold']
                    if elevation < 0 or elevation > 90:
                        return False, (
                            f"constellation_configs.{constellation}.elevation_threshold "
                            f"必須在 0-90 度範圍內，實際: {elevation}"
                        )

                # Validate frequency
                if 'frequency_ghz' in constellation_config:
                    freq = constellation_config['frequency_ghz']
                    if freq <= 0:
                        return False, (
                            f"constellation_configs.{constellation}.frequency_ghz "
                            f"必須是正數，實際: {freq}"
                        )

        # Validate TLE data configuration
        if 'tle_data' in config:
            tle_data = config['tle_data']

            # Check data directory exists (warning, not error)
            if 'data_directory' in tle_data:
                data_dir = Path(tle_data['data_directory'])
                if not data_dir.exists():
                    self.logger.warning(
                        f"⚠️ TLE 數據目錄不存在: {data_dir}（將在執行時檢查）"
                    )

        # All validations passed
        return True, None
