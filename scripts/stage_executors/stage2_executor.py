"""
Stage 2 執行器 - 軌道狀態傳播層

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


class Stage2Executor(StageExecutor):
    """
    Stage 2 執行器 - 軌道狀態傳播層 (v3.0)

    繼承自 StageExecutor，只需實現配置加載和處理器創建邏輯。
    """

    def __init__(self):
        super().__init__(
            stage_number=2,
            stage_name="軌道狀態傳播層 (v3.0 重構版本)",
            emoji="🛰️"
        )

    def load_config(self) -> Dict[str, Any]:
        """
        載入 Stage 2 配置

        從 YAML 文件載入 v3.0 軌道傳播配置，如果文件不存在則使用預設配置。

        Returns:
            Dict[str, Any]: 配置字典
        """
        config_path = project_root / "config/stage2_orbital_computing.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 2 配置: {config_path}")
        else:
            # ⚠️ 回退到預設配置 (僅用於開發環境)
            print(f"⚠️ 未找到配置文件: {config_path}")
            print("⚠️ 使用預設配置")
            config_dict = {
                'time_series_config': {'time_step_seconds': 60},
                'propagation_config': {
                    'coordinate_system': 'TEME',
                    'sgp4_library': 'skyfield'
                }
            }

        # 顯示配置摘要
        time_config = config_dict.get('time_series_config', {})
        propagation_config = config_dict.get('propagation_config', {})

        print(f"📋 配置摘要:")
        print(f"   時間步長: {time_config.get('time_step_seconds', 'N/A')}秒")
        print(f"   座標系統: {propagation_config.get('coordinate_system', 'TEME')}")
        print(f"   SGP4庫: {propagation_config.get('sgp4_library', 'skyfield')}")

        return config_dict

    def create_processor(self, config: Dict[str, Any]):
        """
        創建 Stage 2 處理器

        Args:
            config: load_config() 返回的配置字典

        Returns:
            Stage2OrbitalPropagationProcessor: 處理器實例
        """
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
        return Stage2OrbitalPropagationProcessor(config=config)


# ===== 向後兼容函數 =====

def execute_stage2(previous_results=None):
    """
    執行 Stage 2: 軌道狀態傳播層 (v3.0)

    向後兼容函數，保持原有調用方式。
    內部使用 Stage2Executor 類實現。

    Args:
        previous_results: 前序階段結果字典（必須包含 'stage1' 結果）

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage2Processor)
    """
    executor = Stage2Executor()
    return executor.execute(previous_results)
