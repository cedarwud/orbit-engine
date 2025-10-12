"""
Stage 5 執行器 - 信號品質分析層

重構版本：使用 StageExecutor 基類，減少重複代碼。

Author: Orbit Engine Refactoring Team
Date: 2025-10-12
Version: 2.0 (Refactored)
"""

import yaml
from typing import Dict, Any, Tuple
from pathlib import Path

from .base_executor import StageExecutor
from .executor_utils import project_root


def validate_stage5_config(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    驗證 Stage 5 配置完整性

    Args:
        config: 配置字典

    Returns:
        tuple: (valid: bool, message: str)
    """
    # 檢查必要章節
    required_sections = ['signal_calculator', 'atmospheric_model']

    for section in required_sections:
        if section not in config:
            return False, f"配置缺少必要部分: {section}"

    # 驗證 signal_calculator 必要參數
    signal_calc = config['signal_calculator']
    required_signal_params = [
        'bandwidth_mhz',
        'subcarrier_spacing_khz',
        'noise_figure_db',
        'temperature_k'
    ]

    for param in required_signal_params:
        if param not in signal_calc:
            return False, f"signal_calculator 缺少參數: {param}"

    # 驗證 atmospheric_model 必要參數
    atmos_model = config['atmospheric_model']
    required_atmos_params = [
        'temperature_k',
        'pressure_hpa',
        'water_vapor_density_g_m3'
    ]

    for param in required_atmos_params:
        if param not in atmos_model:
            return False, f"atmospheric_model 缺少參數: {param}"

    return True, "配置驗證通過"


class Stage5Executor(StageExecutor):
    """
    Stage 5 執行器 - 信號品質分析層 (Grade A+ 模式)

    繼承自 StageExecutor，只需實現配置加載和處理器創建邏輯。
    包含特殊的配置驗證邏輯以確保學術合規性。
    """

    def __init__(self):
        super().__init__(
            stage_number=5,
            stage_name="信號品質分析層 (Grade A+ 重構版本)",
            emoji="📊"
        )

    def load_config(self) -> Dict[str, Any]:
        """
        載入 Stage 5 配置

        從 YAML 文件載入配置並進行完整性驗證。

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            FileNotFoundError: 當配置文件不存在時
            ValueError: 當配置驗證失敗時
        """
        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'

        if not config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                f"請確保配置文件存在於 config/stage5_signal_analysis_config.yaml"
            )

        # 載入 YAML 配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 驗證配置完整性
        valid, message = validate_stage5_config(config)
        if not valid:
            raise ValueError(f"配置驗證失敗: {message}")

        print(f'✅ 已加載配置文件: {config_path.name}')
        print(f'✅ 配置驗證: {message}')

        return config

    def create_processor(self, config: Dict[str, Any]):
        """
        創建 Stage 5 處理器

        Args:
            config: load_config() 返回的配置字典

        Returns:
            Stage5SignalAnalysisProcessor: 處理器實例
        """
        from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor
        return Stage5SignalAnalysisProcessor(config)

    def get_previous_stage_number(self) -> int:
        """
        Stage 5 依賴 Stage 4 的結果

        Returns:
            int: 4
        """
        return 4


# ===== 向後兼容函數 =====

def execute_stage5(previous_results=None):
    """
    執行 Stage 5: 信號品質分析層 (Grade A+ 模式)

    向後兼容函數，保持原有調用方式。
    內部使用 Stage5Executor 類實現。

    Args:
        previous_results: 前序階段結果字典（必須包含 'stage4' 結果）

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage5Processor)
    """
    try:
        executor = Stage5Executor()
        return executor.execute(previous_results)
    except (FileNotFoundError, ValueError) as e:
        # 處理配置錯誤，提供友好的錯誤信息
        print(f'❌ 配置文件錯誤: {e}')
        import traceback
        traceback.print_exc()
        return False, None, None
