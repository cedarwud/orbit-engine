"""
階段執行器模組

本模組包含六個階段的執行邏輯，每個階段一個獨立的執行器。
這是從原始的 run_all_stages_sequential() 和 run_stage_specific() 函數拆分而來。

設計原則:
- 單一職責: 每個執行器只負責一個階段的執行邏輯
- 標準化輸出: 所有執行器返回統一格式 (success, result, processor)
- 清晰的依賴: 每個階段明確聲明其輸入依賴

Author: Refactored from run_six_stages_with_validation.py
Date: 2025-10-03
"""

from .stage1_executor import execute_stage1
from .stage2_executor import execute_stage2
from .stage3_executor import execute_stage3
from .stage4_executor import execute_stage4
from .stage5_executor import execute_stage5
from .stage6_executor import execute_stage6

__all__ = [
    'execute_stage1',
    'execute_stage2',
    'execute_stage3',
    'execute4',
    'execute_stage5',
    'execute_stage6',
]
