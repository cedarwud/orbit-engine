#!/usr/bin/env python3
"""
TDD Integration Types - 數據類型定義
====================================

包含所有TDD整合系統使用的枚舉、數據類和類型定義

Author: Claude Code (Refactored from tdd_integration_coordinator.py)
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ExecutionMode(Enum):
    """TDD執行模式"""
    SYNC = "sync"           # 同步執行 - 開發環境
    ASYNC = "async"         # 異步執行 - 生產環境
    HYBRID = "hybrid"       # 混合執行 - 測試環境


class TestType(Enum):
    """測試類型"""
    UNIT = "unit_tests"
    INTEGRATION = "integration_tests"
    PERFORMANCE = "performance_tests"
    COMPLIANCE = "compliance_tests"
    REGRESSION = "regression_tests"


@dataclass
class TDDTestResult:
    """TDD測試結果數據類"""
    test_type: TestType
    executed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_ms: int
    critical_failures: List[str]
    warnings: List[str]
    coverage_percentage: Optional[float] = None
    baseline_comparison: Optional[str] = None


@dataclass
class TDDIntegrationResults:
    """TDD整合測試完整結果"""
    stage: str
    execution_timestamp: datetime
    execution_mode: ExecutionMode
    total_execution_time_ms: int
    test_results: Dict[TestType, TDDTestResult]
    overall_quality_score: float
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    post_hook_triggered: bool
    validation_snapshot_enhanced: bool
