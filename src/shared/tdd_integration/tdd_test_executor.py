#!/usr/bin/env python3
"""
TDD Test Executor - 測試執行器
=================================

測試執行引擎的簡化包裝器
目前階段：過渡期間直接使用原始 TestExecutionEngine

Author: Claude Code (Refactored from tdd_integration_coordinator.py)
Version: 1.0.0 (Transition Phase)
"""

import logging
from typing import Dict, Any

from .tdd_types import TestType, TDDTestResult, ExecutionMode
from .tdd_config_manager import TDDConfigurationManager

# 🚧 過渡期：直接從原始文件導入 TestExecutionEngine
# TODO: 未來將 TestExecutionEngine 完整重構為獨立模組
try:
    from ..tdd_integration_coordinator import TestExecutionEngine as OriginalTestExecutionEngine
except ImportError:
    # 如果原始文件被移除，使用空殼實現
    class OriginalTestExecutionEngine:
        def __init__(self, config_manager):
            self.config_manager = config_manager
            self.logger = logging.getLogger("TestExecutionEngine")

        async def execute_tests_for_stage(self, stage: str, stage_results: Dict[str, Any], execution_mode: ExecutionMode) -> Dict[TestType, TDDTestResult]:
            self.logger.warning("原始 TestExecutionEngine 不可用，返回空結果")
            return {}


class TestExecutor:
    """
    測試執行器包裝類

    當前實現：
    - 直接代理到原始 TestExecutionEngine
    - 保持接口一致性

    未來規劃：
    - 將 TestExecutionEngine (2,070 lines) 拆分為：
      - tdd_validators/regression_validator.py
      - tdd_validators/performance_validator.py
      - tdd_validators/integration_validator.py
      - tdd_validators/compliance_validator.py
      - tdd_validators/unit_validator.py
    - 每個驗證器獨立可測試
    - TestExecutor 作為統一調度層
    """

    def __init__(self, config_manager: TDDConfigurationManager):
        """初始化測試執行器"""
        self.config_manager = config_manager
        self.logger = logging.getLogger("TestExecutor")

        # 使用原始 TestExecutionEngine
        self._engine = OriginalTestExecutionEngine(config_manager)
        self.logger.info("TestExecutor 初始化完成 (使用原始引擎)")

    async def execute_tests_for_stage(
        self,
        stage: str,
        stage_results: Dict[str, Any],
        execution_mode: ExecutionMode
    ) -> Dict[TestType, TDDTestResult]:
        """
        為特定階段執行TDD測試

        Args:
            stage: 階段名稱 (例如 "stage1")
            stage_results: 階段處理結果
            execution_mode: 執行模式 (sync/async/hybrid)

        Returns:
            測試結果字典 {TestType: TDDTestResult}
        """
        self.logger.info(f"開始執行 {stage} 的TDD測試 (模式: {execution_mode.value})")

        # 代理到原始引擎
        test_results = await self._engine.execute_tests_for_stage(
            stage,
            stage_results,
            execution_mode
        )

        self.logger.info(
            f"{stage} TDD測試完成: {len(test_results)} 個測試類型執行"
        )

        return test_results

    def get_supported_test_types(self, stage: str) -> list[TestType]:
        """
        獲取階段支持的測試類型

        Args:
            stage: 階段名稱

        Returns:
            支持的測試類型列表
        """
        stage_config = self.config_manager.get_stage_config(stage)
        enabled_tests = stage_config.get('tests', ['regression'])

        test_types = []
        for test_type_str in enabled_tests:
            try:
                test_type = TestType(test_type_str + "_tests")
                test_types.append(test_type)
            except ValueError:
                self.logger.warning(f"未知測試類型: {test_type_str}")

        return test_types
