#!/usr/bin/env python3
"""
TDD Integration Module - TDD整合模組
===================================

重構後的TDD整合系統，將原始2,737行的單一文件拆分為模組化結構

模組結構：
- tdd_types: 類型定義和數據類
- tdd_config_manager: 配置管理
- tdd_test_executor: 測試執行引擎
- tdd_results_integrator: 結果整合器
- tdd_failure_handler: 故障處理器
- tdd_coordinator: 主協調器

Author: Claude Code
Version: 1.0.0
"""

# 核心類型導出
from .tdd_types import (
    ExecutionMode,
    TestType,
    TDDTestResult,
    TDDIntegrationResults
)

# 核心組件導出
from .tdd_config_manager import TDDConfigurationManager
from .tdd_test_executor import TestExecutor
from .tdd_results_integrator import ResultsIntegrator
from .tdd_failure_handler import FailureHandler
from .tdd_coordinator import (
    TDDIntegrationCoordinator,
    get_tdd_coordinator,
    reset_tdd_coordinator
)

# 便捷別名（兼容性）
TDDCoordinator = TDDIntegrationCoordinator

__all__ = [
    # 類型
    'ExecutionMode',
    'TestType',
    'TDDTestResult',
    'TDDIntegrationResults',
    # 核心組件
    'TDDConfigurationManager',
    'TestExecutor',
    'ResultsIntegrator',
    'FailureHandler',
    'TDDIntegrationCoordinator',
    'TDDCoordinator',  # 別名
    # 全局函數
    'get_tdd_coordinator',
    'reset_tdd_coordinator',
]

__version__ = '1.0.0'
