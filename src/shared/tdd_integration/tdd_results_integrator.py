#!/usr/bin/env python3
"""
TDD Results Integrator - 結果整合器
==================================

負責整合TDD測試結果，計算品質分數，生成建議和增強驗證快照

Author: Claude Code (Refactored from tdd_integration_coordinator.py)
Version: 1.0.0
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from .tdd_types import TestType, TDDTestResult, TDDIntegrationResults, ExecutionMode


class ResultsIntegrator:
    """結果整合器"""

    def __init__(self):
        self.logger = logging.getLogger("ResultsIntegrator")

    def integrate_results(
        self,
        stage: str,
        test_results: Dict[TestType, TDDTestResult],
        execution_mode: ExecutionMode,
        total_execution_time_ms: int
    ) -> TDDIntegrationResults:
        """整合測試結果"""

        # 計算整體品質分數
        quality_score = self._calculate_quality_score(test_results)

        # 收集關鍵問題和警告
        critical_issues = []
        warnings = []

        for test_result in test_results.values():
            critical_issues.extend(test_result.critical_failures)
            warnings.extend(test_result.warnings)

        # 生成建議
        recommendations = self._generate_recommendations(test_results, stage)

        return TDDIntegrationResults(
            stage=stage,
            execution_timestamp=datetime.now(timezone.utc),
            execution_mode=execution_mode,
            total_execution_time_ms=total_execution_time_ms,
            test_results=test_results,
            overall_quality_score=quality_score,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            post_hook_triggered=True,
            validation_snapshot_enhanced=True
        )

    def _calculate_quality_score(self, test_results: Dict[TestType, TDDTestResult]) -> float:
        """計算整體品質分數"""
        if not test_results:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        # 不同測試類型的權重
        weights = {
            TestType.REGRESSION: 0.3,
            TestType.COMPLIANCE: 0.3,
            TestType.PERFORMANCE: 0.2,
            TestType.INTEGRATION: 0.15,
            TestType.UNIT: 0.05
        }

        for test_type, result in test_results.items():
            if result.executed and result.total_tests > 0:
                success_rate = result.passed_tests / result.total_tests
                weight = weights.get(test_type, 0.1)
                total_score += success_rate * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _generate_recommendations(
        self,
        test_results: Dict[TestType, TDDTestResult],
        stage: str
    ) -> List[str]:
        """生成改進建議"""
        recommendations = []

        for test_type, result in test_results.items():
            if result.failed_tests > 0:
                recommendations.append(
                    f"{test_type.value} 有 {result.failed_tests} 個失敗測試需要修復"
                )

            if result.execution_time_ms > 5000:  # 超過5秒
                recommendations.append(
                    f"{test_type.value} 執行時間過長 ({result.execution_time_ms}ms)，建議優化"
                )

        return recommendations

    def enhance_validation_snapshot(
        self,
        original_snapshot: Dict[str, Any],
        tdd_results: TDDIntegrationResults
    ) -> Dict[str, Any]:
        """增強驗證快照包含TDD結果"""
        enhanced_snapshot = original_snapshot.copy()

        # 添加TDD整合結果
        enhanced_snapshot['tdd_integration'] = {
            'enabled': True,
            'execution_mode': tdd_results.execution_mode.value,
            'execution_timestamp': tdd_results.execution_timestamp.isoformat(),
            'total_execution_time_ms': tdd_results.total_execution_time_ms,
            'overall_quality_score': tdd_results.overall_quality_score,
            'post_hook_triggered': tdd_results.post_hook_triggered,
            'validation_snapshot_enhanced': tdd_results.validation_snapshot_enhanced,
            'test_results': {
                test_type.value: {
                    'executed': result.executed,
                    'total_tests': result.total_tests,
                    'passed_tests': result.passed_tests,
                    'failed_tests': result.failed_tests,
                    'execution_time_ms': result.execution_time_ms,
                    'critical_failures': result.critical_failures,
                    'warnings': result.warnings
                }
                for test_type, result in tdd_results.test_results.items()
            },
            'critical_issues': tdd_results.critical_issues,
            'warnings': tdd_results.warnings,
            'recommendations': tdd_results.recommendations
        }

        return enhanced_snapshot
