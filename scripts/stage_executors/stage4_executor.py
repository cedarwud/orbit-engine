"""
Stage 4 執行器 - 鏈路可行性評估層

重構版本：使用 StageExecutor 基類，減少重複代碼。

Author: Orbit Engine Refactoring Team
Date: 2025-10-12
Version: 2.0 (Refactored)
"""

import yaml
from typing import Dict, Any
from pathlib import Path

from .base_executor import StageExecutor
from .executor_utils import project_root


class Stage4Executor(StageExecutor):
    """
    Stage 4 執行器 - 鏈路可行性評估層

    繼承自 StageExecutor，只需實現配置加載和處理器創建邏輯。

    注意: Stage 4 processor 使用 process() 而非 execute() 方法。
    """

    def __init__(self):
        super().__init__(
            stage_number=4,
            stage_name="鏈路可行性評估層 (重構版本)",
            emoji="📡"
        )

    def load_config(self) -> Dict[str, Any]:
        """
        載入 Stage 4 配置

        從 YAML 文件載入學術標準配置。

        Returns:
            Dict[str, Any]: 配置字典
        """
        config_path = project_root / "config/stage4_link_feasibility_config.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 4 配置: use_iau_standards={config.get('use_iau_standards')}")
        else:
            # ⚠️ 回退到預設配置 (僅用於開發環境)
            print(f"⚠️ 未找到配置文件: {config_path}")
            print("⚠️ 使用預設設置")
            config = {'use_iau_standards': True, 'validate_epochs': False}

        return config

    def create_processor(self, config: Dict[str, Any]):
        """
        創建 Stage 4 處理器

        Args:
            config: load_config() 返回的配置字典

        Returns:
            Stage4LinkFeasibilityProcessor: 處理器實例
        """
        from stages.stage4_link_feasibility.stage4_link_feasibility_processor import Stage4LinkFeasibilityProcessor
        return Stage4LinkFeasibilityProcessor(config)

    def execute(self, previous_results=None):
        """
        執行 Stage 4 處理（覆蓋基類方法）

        Stage 4 processor 使用 process() 而非 execute()，需要特殊處理。

        Args:
            previous_results: 前序階段結果字典

        Returns:
            tuple: (success: bool, result: ProcessingResult, processor: Processor)
        """
        try:
            # Steps 1-6: 使用基類的標準流程
            self._print_stage_header()

            from .executor_utils import clean_stage_outputs
            clean_stage_outputs(self.stage_number)

            input_data = None
            if self.requires_previous_stage():
                input_data = self._load_previous_stage_data()
                if input_data is None:
                    return False, None, None

            config = self.load_config()
            processor = self.create_processor(config)

            # Step 7: 使用 process() 而非 execute()
            self.logger.info(f"🚀 調用 processor.process() (Stage 4 特殊接口)")
            result = processor.process(input_data)

            # Step 8-10: 使用基類的檢查和快照保存
            if not self._check_result(result):
                return False, result, processor

            self._print_result_summary(result)
            self._save_validation_snapshot(processor, result)

            return True, result, processor

        except Exception as e:
            error_msg = f'❌ Stage {self.stage_number} 執行異常: {e}'
            self.logger.error(error_msg, exc_info=True)
            print(error_msg)
            return False, None, None

    def get_previous_stage_number(self) -> int:
        """
        Stage 4 依賴 Stage 3 的結果

        Returns:
            int: 3
        """
        return 3


# ===== 向後兼容函數 =====

def execute_stage4(previous_results=None):
    """
    執行 Stage 4: 鏈路可行性評估層

    向後兼容函數，保持原有調用方式。
    內部使用 Stage4Executor 類實現。

    Args:
        previous_results: 前序階段結果字典（必須包含 'stage3' 結果）

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage4Processor)
    """
    executor = Stage4Executor()
    return executor.execute(previous_results)
