#!/usr/bin/env python3
"""
TDD Integration Coordinator - TDD整合協調器
===========================================

負責管理整個TDD整合自動化流程的核心協調類別

Author: Claude Code (Refactored from tdd_integration_coordinator.py)
Version: 1.0.0
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from .tdd_types import TDDIntegrationResults, ExecutionMode
from .tdd_config_manager import TDDConfigurationManager
from .tdd_test_executor import TestExecutor
from .tdd_results_integrator import ResultsIntegrator
from .tdd_failure_handler import FailureHandler


class TDDIntegrationCoordinator:
    """
    TDD整合協調器 - 核心協調類別

    職責：
    1. 配置管理和載入
    2. 測試執行協調
    3. 結果整合和驗證快照增強
    4. 故障處理和恢復

    使用方式：
    ```python
    coordinator = TDDIntegrationCoordinator()
    results = await coordinator.execute_post_hook_tests(
        stage="stage1",
        stage_results={...},
        validation_snapshot={...}
    )
    ```
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化TDD整合協調器

        Args:
            config_path: 配置文件路徑 (可選，默認自動檢測)
        """
        self.config_manager = TDDConfigurationManager(config_path)
        self.test_executor = TestExecutor(self.config_manager)
        self.results_integrator = ResultsIntegrator()
        self.failure_handler = FailureHandler()
        self.logger = logging.getLogger("TDDIntegrationCoordinator")

        self.logger.info("TDD整合協調器初始化完成")

    async def execute_post_hook_tests(
        self,
        stage: str,
        stage_results: Dict[str, Any],
        validation_snapshot: Dict[str, Any],
        environment: str = "development"
    ) -> TDDIntegrationResults:
        """
        執行後置鉤子TDD測試

        Args:
            stage: 階段名稱 (如 "stage1", "stage2")
            stage_results: 階段處理結果
            validation_snapshot: 原始驗證快照
            environment: 執行環境 (development/testing/production)

        Returns:
            TDDIntegrationResults: 完整的TDD整合測試結果

        Raises:
            不會拋出異常，所有錯誤都被捕獲並返回錯誤結果
        """
        start_time = time.perf_counter()

        try:
            # 檢查TDD是否啟用
            if not self.config_manager.is_enabled(stage):
                self.logger.info(f"階段 {stage} TDD整合已禁用，跳過測試")
                return self._create_disabled_result(stage)

            # 獲取執行模式
            execution_mode = self.config_manager.get_execution_mode(environment)
            self.logger.info(f"開始執行 {stage} TDD整合測試 (模式: {execution_mode.value})")

            # 執行測試
            test_results = await self.test_executor.execute_tests_for_stage(
                stage, stage_results, execution_mode
            )

            # 計算總執行時間
            total_execution_time = int((time.perf_counter() - start_time) * 1000)

            # 整合結果
            integrated_results = self.results_integrator.integrate_results(
                stage, test_results, execution_mode, total_execution_time
            )

            self.logger.info(
                f"TDD整合測試完成 - 階段: {stage}, "
                f"品質分數: {integrated_results.overall_quality_score:.2f}, "
                f"執行時間: {total_execution_time}ms"
            )

            return integrated_results

        except Exception as e:
            execution_time = int((time.perf_counter() - start_time) * 1000)
            self.logger.error(f"TDD整合測試執行失敗 - 階段: {stage}, 錯誤: {e}", exc_info=True)

            return self._create_error_result(stage, str(e), execution_time)

    def enhance_validation_snapshot(
        self,
        original_snapshot: Dict[str, Any],
        tdd_results: TDDIntegrationResults
    ) -> Dict[str, Any]:
        """
        增強驗證快照包含TDD結果

        Args:
            original_snapshot: 原始驗證快照
            tdd_results: TDD測試結果

        Returns:
            增強後的驗證快照
        """
        return self.results_integrator.enhance_validation_snapshot(
            original_snapshot, tdd_results
        )

    def handle_test_failures(
        self,
        tdd_results: TDDIntegrationResults,
        stage_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        處理測試失敗情況

        Args:
            tdd_results: TDD測試結果
            stage_context: 階段上下文信息

        Returns:
            失敗處理決策 {
                'action': 'stop_pipeline' | 'continue_with_warning' | 'continue',
                'reason': str,
                'details': [...],
                'recovery_suggestions': [...]
            }
        """
        return self.failure_handler.handle_test_failures(tdd_results, stage_context)

    def _create_disabled_result(self, stage: str) -> TDDIntegrationResults:
        """
        創建禁用狀態的結果

        Args:
            stage: 階段名稱

        Returns:
            禁用狀態的TDD結果
        """
        return TDDIntegrationResults(
            stage=stage,
            execution_timestamp=datetime.now(timezone.utc),
            execution_mode=ExecutionMode.SYNC,
            total_execution_time_ms=0,
            test_results={},
            overall_quality_score=1.0,
            critical_issues=[],
            warnings=["TDD整合已禁用"],
            recommendations=[],
            post_hook_triggered=False,
            validation_snapshot_enhanced=False
        )

    def _create_error_result(
        self,
        stage: str,
        error_message: str,
        execution_time: int
    ) -> TDDIntegrationResults:
        """
        創建錯誤狀態的結果

        Args:
            stage: 階段名稱
            error_message: 錯誤消息
            execution_time: 執行時間(毫秒)

        Returns:
            錯誤狀態的TDD結果
        """
        return TDDIntegrationResults(
            stage=stage,
            execution_timestamp=datetime.now(timezone.utc),
            execution_mode=ExecutionMode.SYNC,
            total_execution_time_ms=execution_time,
            test_results={},
            overall_quality_score=0.0,
            critical_issues=[f"TDD整合執行錯誤: {error_message}"],
            warnings=[],
            recommendations=["檢查TDD配置和系統狀態"],
            post_hook_triggered=True,
            validation_snapshot_enhanced=False
        )


# ======================
# 全局實例管理（單例模式）
# ======================

_tdd_coordinator_instance: Optional[TDDIntegrationCoordinator] = None


def get_tdd_coordinator() -> TDDIntegrationCoordinator:
    """
    獲取TDD整合協調器的全局實例（單例模式）

    Returns:
        TDDIntegrationCoordinator實例

    使用方式：
    ```python
    coordinator = get_tdd_coordinator()
    results = await coordinator.execute_post_hook_tests(...)
    ```
    """
    global _tdd_coordinator_instance

    if _tdd_coordinator_instance is None:
        _tdd_coordinator_instance = TDDIntegrationCoordinator()

    return _tdd_coordinator_instance


def reset_tdd_coordinator():
    """
    重置TDD整合協調器實例

    主要用於：
    - 單元測試
    - 配置熱重載
    - 清理資源
    """
    global _tdd_coordinator_instance
    _tdd_coordinator_instance = None
