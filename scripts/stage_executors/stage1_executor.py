"""
Stage 1 執行器 - TLE 數據載入層

重構版本：使用 StageExecutor 基類，減少重複代碼。

Author: Orbit Engine Refactoring Team
Date: 2025-10-12
Version: 2.0 (Refactored)
"""

import yaml
from typing import Dict, Any
from pathlib import Path

from .base_executor import StageExecutor
from .executor_utils import project_root, is_sampling_mode


class Stage1Executor(StageExecutor):
    """
    Stage 1 執行器 - TLE 數據載入層

    繼承自 StageExecutor，只需實現配置加載和處理器創建邏輯。
    """

    def __init__(self):
        super().__init__(
            stage_number=1,
            stage_name="TLE 數據載入層 (重構版本)",
            emoji="📦"
        )

    def load_config(self) -> Dict[str, Any]:
        """
        載入 Stage 1 配置

        從 YAML 文件載入配置，如果文件不存在則使用預設配置。
        處理取樣模式的環境變數覆蓋。

        Returns:
            Dict[str, Any]: 配置字典
        """
        config_path = project_root / "config/stage1_orbital_calculation.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 1 配置: {config_path}")
        else:
            # ⚠️ 回退到預設配置 (僅用於開發環境)
            print(f"⚠️ 未找到配置文件: {config_path}")
            print("⚠️ 使用預設配置")
            config = {
                'sampling': {'mode': 'auto', 'sample_size': 50},
                'epoch_analysis': {'enabled': True},
                'epoch_filter': {
                    'enabled': True,
                    'mode': 'latest_date',
                    'tolerance_hours': 24
                }
            }

        # ✅ 處理取樣模式 (支持環境變數覆蓋)
        sampling_mode = config.get('sampling', {}).get('mode', 'auto')
        if sampling_mode == 'auto':
            use_sampling = is_sampling_mode()  # 從環境變數讀取
        else:
            use_sampling = (sampling_mode == 'enabled')

        # 更新配置中的 sample_mode (向後兼容)
        config['sample_mode'] = use_sampling
        config['sample_size'] = config.get('sampling', {}).get('sample_size', 50)

        # 顯示配置摘要
        print(f"📋 配置摘要:")
        print(f"   取樣模式: {'啟用' if use_sampling else '禁用'}")
        if use_sampling:
            print(f"   取樣數量: {config['sample_size']} 顆衛星")
        print(f"   Epoch 篩選: {config['epoch_filter']['mode']}")
        print(f"   容差範圍: ±{config['epoch_filter']['tolerance_hours']} 小時")

        return config

    def create_processor(self, config: Dict[str, Any]):
        """
        創建 Stage 1 處理器

        Args:
            config: load_config() 返回的配置字典

        Returns:
            Stage1MainProcessor: 處理器實例
        """
        from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor
        return create_stage1_processor(config)

    def requires_previous_stage(self) -> bool:
        """
        Stage 1 不需要前階段數據

        Returns:
            bool: False
        """
        return False


# ===== 向後兼容函數 =====

def execute_stage1(previous_results=None):
    """
    執行 Stage 1: TLE 數據載入層

    向後兼容函數，保持原有調用方式。
    內部使用 Stage1Executor 類實現。

    Args:
        previous_results: 前序階段結果 (Stage 1 不需要)

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage1Processor)
    """
    executor = Stage1Executor()
    return executor.execute(previous_results)
