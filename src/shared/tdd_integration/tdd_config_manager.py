#!/usr/bin/env python3
"""
TDD Configuration Manager - 配置管理器
=====================================

負責TDD整合系統的配置載入、環境檢測和配置管理

Author: Claude Code (Refactored from tdd_integration_coordinator.py)
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .tdd_types import ExecutionMode, TestType


class TDDConfigurationManager:
    """TDD配置管理器"""

    def __init__(self, config_path: Optional[Path] = None):
        # 檢測配置文件位置
        if config_path:
            self.config_path = config_path
        elif Path("/app/config/tdd_integration/tdd_integration_config.yml").exists():
            # 容器環境
            self.config_path = Path("/app/config/tdd_integration/tdd_integration_config.yml")
        else:
            # 開發環境
            self.config_path = Path(__file__).parent.parent.parent / "config/tdd_integration/tdd_integration_config.yml"
        self.logger = logging.getLogger("TDDConfigurationManager")
        self._config_cache = None

    def load_config(self) -> Dict[str, Any]:
        """載入TDD整合配置"""
        if self._config_cache is None:
            try:
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = yaml.safe_load(f)
                self.logger.info(f"TDD配置載入成功: {self.config_path}")
            except Exception as e:
                self.logger.warning(f"無法載入TDD配置，使用預設配置: {e}")
                self._config_cache = self._get_default_config()

        return self._config_cache

    def get_stage_config(self, stage: str) -> Dict[str, Any]:
        """獲取特定階段的TDD配置"""
        config = self.load_config()
        stages_config = config.get('stages', {})
        return stages_config.get(stage, {})

    def get_execution_mode(self, environment: str = "development") -> ExecutionMode:
        """獲取執行模式"""
        config = self.load_config()
        env_config = config.get('environment_profiles', {}).get(environment, {})
        mode_str = env_config.get('tdd_integration', {}).get('execution_mode', 'sync')

        try:
            return ExecutionMode(mode_str)
        except ValueError:
            return ExecutionMode.SYNC

    def is_enabled(self, stage: str) -> bool:
        """檢查TDD整合是否啟用"""
        config = self.load_config()
        stage_config = self.get_stage_config(stage)
        return stage_config.get('tdd_integration', {}).get('enabled', False)

    def get_test_types(self, stage: str) -> Dict[TestType, Dict[str, Any]]:
        """獲取階段的測試類型配置"""
        stage_config = self.get_stage_config(stage)
        test_types_config = stage_config.get('tdd_integration', {}).get('test_types', {})

        result = {}
        for test_type_str, test_config in test_types_config.items():
            try:
                test_type = TestType(test_type_str)
                result[test_type] = test_config
            except ValueError:
                self.logger.warning(f"未知的測試類型: {test_type_str}")
                continue

        return result

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "environment_profiles": {
                "development": {
                    "tdd_integration": {
                        "enabled": True,
                        "execution_mode": "sync"
                    }
                },
                "testing": {
                    "tdd_integration": {
                        "enabled": True,
                        "execution_mode": "hybrid"
                    }
                },
                "production": {
                    "tdd_integration": {
                        "enabled": False,
                        "execution_mode": "async"
                    }
                }
            },
            "stages": {
                "stage1": {
                    "tdd_integration": {
                        "enabled": True,
                        "test_types": {
                            "unit_tests": {"enabled": True},
                            "integration_tests": {"enabled": True}
                        }
                    }
                }
            }
        }
