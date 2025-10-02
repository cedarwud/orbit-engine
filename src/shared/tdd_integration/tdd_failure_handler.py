#!/usr/bin/env python3
"""
TDD Failure Handler - 故障處理器
================================

負責處理TDD測試失敗，分析失敗類型並提供恢復建議

Author: Claude Code (Refactored from tdd_integration_coordinator.py)
Version: 1.0.0
"""

import logging
from typing import Dict, Any

from .tdd_types import TDDIntegrationResults, TestType


class FailureHandler:
    """故障處理器"""

    def __init__(self):
        self.logger = logging.getLogger("FailureHandler")

    def handle_test_failures(
        self,
        tdd_results: TDDIntegrationResults,
        stage_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理測試失敗"""
        failure_analysis = self._analyze_failures(tdd_results)

        if failure_analysis['has_critical_failures']:
            return self._handle_critical_failures(failure_analysis, stage_context)
        elif failure_analysis['has_performance_regressions']:
            return self._handle_performance_regressions(failure_analysis, stage_context)
        elif failure_analysis['has_compliance_violations']:
            return self._handle_compliance_violations(failure_analysis, stage_context)
        else:
            return self._handle_minor_issues(failure_analysis, stage_context)

    def _analyze_failures(self, tdd_results: TDDIntegrationResults) -> Dict[str, Any]:
        """分析失敗類型"""
        analysis = {
            'has_critical_failures': len(tdd_results.critical_issues) > 0,
            'has_performance_regressions': False,
            'has_compliance_violations': False,
            'failure_details': []
        }

        for test_type, result in tdd_results.test_results.items():
            if result.failed_tests > 0:
                if test_type == TestType.PERFORMANCE:
                    analysis['has_performance_regressions'] = True
                elif test_type == TestType.COMPLIANCE:
                    analysis['has_compliance_violations'] = True

                analysis['failure_details'].append({
                    'test_type': test_type.value,
                    'failed_count': result.failed_tests,
                    'critical_failures': result.critical_failures
                })

        return analysis

    def _handle_critical_failures(
        self,
        analysis: Dict[str, Any],
        stage_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理關鍵失敗"""
        self.logger.error("檢測到關鍵TDD測試失敗，觸發緊急處理")

        return {
            'action': 'stop_pipeline',
            'reason': 'critical_tdd_test_failures',
            'details': analysis['failure_details'],
            'recovery_suggestions': [
                '檢查核心算法實現是否符合預期',
                '驗證輸入數據完整性',
                '檢查配置參數是否正確'
            ]
        }

    def _handle_performance_regressions(
        self,
        analysis: Dict[str, Any],
        stage_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理性能回歸"""
        self.logger.warning("檢測到性能回歸，建議優化")

        return {
            'action': 'continue_with_warning',
            'reason': 'performance_regression_detected',
            'details': analysis['failure_details'],
            'recovery_suggestions': [
                '分析性能瓶頸',
                '檢查記憶體使用情況',
                '考慮算法優化'
            ]
        }

    def _handle_compliance_violations(
        self,
        analysis: Dict[str, Any],
        stage_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理合規違反"""
        self.logger.error("檢測到學術合規違反，需要立即修復")

        return {
            'action': 'stop_pipeline',
            'reason': 'academic_compliance_violation',
            'details': analysis['failure_details'],
            'recovery_suggestions': [
                '檢查是否使用了簡化算法',
                '驗證所有物理參數的真實性',
                '確認符合ITU-R標準'
            ]
        }

    def _handle_minor_issues(
        self,
        analysis: Dict[str, Any],
        stage_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理輕微問題"""
        self.logger.info("檢測到輕微問題，記錄並繼續")

        return {
            'action': 'continue',
            'reason': 'minor_issues_detected',
            'details': analysis['failure_details'],
            'recovery_suggestions': []
        }
