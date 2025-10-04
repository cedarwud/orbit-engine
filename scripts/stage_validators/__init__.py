"""
階段驗證器模組

本模組包含六個階段的驗證邏輯，每個階段一個獨立的驗證器。
這是從原始的 check_validation_snapshot_quality() 函數拆分而來。

設計原則:
- Layer 2 驗證: 檢查驗證快照的合理性與架構合規性
- 信任 Layer 1 結果: 不重複詳細驗證邏輯
- 單一職責: 每個驗證器只負責一個階段

Author: Refactored from run_six_stages_with_validation.py
Date: 2025-10-03
"""

from .stage1_validator import check_stage1_validation
from .stage2_validator import check_stage2_validation
from .stage3_validator import check_stage3_validation
from .stage4_validator import check_stage4_validation
from .stage5_validator import check_stage5_validation
from .stage6_validator import check_stage6_validation

__all__ = [
    'check_stage1_validation',
    'check_stage2_validation',
    'check_stage3_validation',
    'check_stage4_validation',
    'check_stage5_validation',
    'check_stage6_validation',
]
