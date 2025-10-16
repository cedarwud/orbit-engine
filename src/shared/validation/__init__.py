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

Note: Stage-specific validators have been moved to scripts/stage_validators/
      as part of Phase 2 refactoring (2025-10-12)

Author: Orbit Engine Refactoring Team
Date: 2025-10-16 (Cleanup: Removed unused legacy validators)
Version: 2.2.0 (Phase 5 - Module Reorganization + Cleanup)
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

__all__ = [
    'ValidationEngine',
    'BaseValidator',
    'ValidationResult',
    'CheckResult',
    'ValidationStatus',
    'FailureCriteria',
    'ValidationRegistry',
]
