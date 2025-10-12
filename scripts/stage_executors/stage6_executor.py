"""
Stage 6 執行器 - 研究數據生成層

重構版本：使用 StageExecutor 基類，減少重複代碼。

Author: Orbit Engine Refactoring Team
Date: 2025-10-12
Version: 2.0 (Refactored)
"""

from typing import Dict, Any

from .base_executor import StageExecutor


class Stage6Executor(StageExecutor):
    """
    Stage 6 執行器 - 研究數據生成層

    繼承自 StageExecutor，只需實現配置加載和處理器創建邏輯。
    Stage 6 不需要特殊配置，使用處理器預設值。
    """

    def __init__(self):
        super().__init__(
            stage_number=6,
            stage_name="研究數據生成層 (重構版本)",
            emoji="💾"
        )

    def load_config(self) -> Dict[str, Any]:
        """
        載入 Stage 6 配置

        Stage 6 不需要特殊配置，返回空字典。

        Returns:
            Dict[str, Any]: 空配置字典
        """
        # Stage 6 使用處理器內部預設配置
        print("📋 Stage 6 使用處理器預設配置")
        return {}

    def create_processor(self, config: Dict[str, Any]):
        """
        創建 Stage 6 處理器

        Args:
            config: load_config() 返回的配置字典（空字典）

        Returns:
            Stage6ResearchOptimizationProcessor: 處理器實例
        """
        from stages.stage6_research_optimization.stage6_research_optimization_processor import Stage6ResearchOptimizationProcessor
        return Stage6ResearchOptimizationProcessor()

    def get_previous_stage_number(self) -> int:
        """
        Stage 6 依賴 Stage 5 的結果

        Returns:
            int: 5
        """
        return 5


# ===== 向後兼容函數 =====

def execute_stage6(previous_results=None):
    """
    執行 Stage 6: 研究數據生成層

    向後兼容函數，保持原有調用方式。
    內部使用 Stage6Executor 類實現。

    Args:
        previous_results: 前序階段結果字典（必須包含 'stage5' 結果）

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage6Processor)
    """
    executor = Stage6Executor()
    return executor.execute(previous_results)
