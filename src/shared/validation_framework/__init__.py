"""
驗證框架 - 學術Grade A標準合規性驗證系統

🎓 完全符合CLAUDE.md的"REAL ALGORITHMS ONLY"原則：
❌ 禁止使用任何簡化算法或硬編碼值
✅ 基於ITU-R、3GPP、IEEE、NORAD官方標準
✅ 完全使用真實物理計算和動態驗證

核心組件：
- ValidationEngine: 驗證引擎核心
- BaseValidator: 驗證器基礎類
- ValidationResult: 驗證結果管理
- FailureCriteria: 動態失敗判定
- StageXValidator: 各階段專用驗證器
- AcademicValidationFramework: 學術標準驗證器（新增）

作者: Academic Standards Compliance Team
版本: v2.0 - 學術Grade A合規性驗證系統
標準: ITU-R P.618, 3GPP TS 38.821, IEEE 802.11, NORAD TLE Format
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

from .stage2_validator import Stage2VisibilityValidator
from .stage3_validator import Stage3SignalValidator
from .stage4_validator import Stage4TimeseriesValidator

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
    'Stage2VisibilityValidator',
    'Stage3SignalValidator',
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