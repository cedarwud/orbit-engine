"""
Validation framework for academic compliance and data integrity

🎓 Fully compliant with CLAUDE.md's "REAL ALGORITHMS ONLY" principle:
❌ No simplified algorithms or hard-coded values
✅ Based on official standards: ITU-R, 3GPP, IEEE, NORAD
✅ Real physics calculations and dynamic validation

Core Components:
- ValidationEngine: Core validation engine
- BaseValidator: Base validator class
- ValidationResult: Validation result management
- FailureCriteria: Dynamic failure criteria
- StageXValidator: Stage-specific validators
- AcademicValidationFramework: Academic standard validator (Grade A+)
- RealTimeSnapshotSystem: Validation snapshot management

Author: Orbit Engine Refactoring Team
Date: 2025-10-15
Version: 2.1.0 (Phase 5 - Module Reorganization)
Standards: ITU-R P.618, 3GPP TS 38.821, IEEE 802.11, NORAD TLE Format
"""

from .validation_engine import (
    ValidationEngine,
    BaseValidator,
    ValidationResult,
    CheckResult,
    ValidationStatus,
    FailureCriteria,
    ValidationRegistry
)

from .stage4_validator import Stage4TimeseriesValidator

# Stage2Validator 已移除（v3.0 架構重構，可見性功能移至 Stage 4）
# Stage3Validator 已移除（重構中）
# from .stage3_validator import Stage3SignalValidator

# 學術標準驗證框架（新增）
try:
    from .academic_validation_framework import (
        AcademicValidationFramework,
        PhysicsValidator,
        AcademicGrade,
        validate_satellite_data_quick,
        generate_academic_test_validator
    )
    _ACADEMIC_FRAMEWORK_AVAILABLE = True
except ImportError:
    _ACADEMIC_FRAMEWORK_AVAILABLE = False

__all__ = [
    'ValidationEngine',
    'BaseValidator',
    'ValidationResult',
    'CheckResult',
    'ValidationStatus',
    'FailureCriteria',
    'ValidationRegistry',
    # 'Stage2VisibilityValidator',  # 已移除（v3.0 架構重構）
    # 'Stage3SignalValidator',  # 已移除（重構中）
    'Stage4TimeseriesValidator'
]

# 如果學術框架可用，添加到導出列表
if _ACADEMIC_FRAMEWORK_AVAILABLE:
    __all__.extend([
        'AcademicValidationFramework',
        'PhysicsValidator',
        'AcademicGrade',
        'validate_satellite_data_quick',
        'generate_academic_test_validator'
    ])