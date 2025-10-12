"""
Stage 3 執行器 - 座標系統轉換層

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


class Stage3Executor(StageExecutor):
    """
    Stage 3 執行器 - 座標系統轉換層 (v3.1)

    繼承自 StageExecutor，只需實現配置加載和處理器創建邏輯。
    包含特殊的配置扁平化邏輯以保持向後兼容性。
    """

    def __init__(self):
        super().__init__(
            stage_number=3,
            stage_name="座標系統轉換層 (v3.1 重構版本)",
            emoji="🌍"
        )

    def load_config(self) -> Dict[str, Any]:
        """
        載入 Stage 3 配置

        從 YAML 文件載入配置，並進行扁平化以適配現有處理器接口。
        處理取樣模式的環境變數覆蓋。

        Returns:
            Dict[str, Any]: 扁平化的配置字典
        """
        config_path = project_root / "config/stage3_coordinate_transformation.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                stage3_config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 3 配置: {config_path}")
        else:
            # ⚠️ 回退到預設配置 (僅用於開發環境)
            print(f"⚠️ 未找到配置文件: {config_path}")
            print("⚠️ 使用預設配置")
            stage3_config = {
                'geometric_prefilter': {'enabled': False},
                'coordinate_config': {
                    'source_frame': 'TEME',
                    'target_frame': 'WGS84',
                    'time_corrections': True,
                    'polar_motion': True,
                    'nutation_model': 'IAU2000A'
                },
                'precision_config': {'target_accuracy_m': 0.5}
            }

        # 向後兼容：扁平化配置結構 (適配處理器)
        config_compat = {
            'enable_geometric_prefilter': stage3_config.get('geometric_prefilter', {}).get('enabled', False),
            'coordinate_config': stage3_config.get('coordinate_config', {}),
            'precision_config': stage3_config.get('precision_config', {}),
            'cache_config': stage3_config.get('cache_config', {}),
            'parallel_config': stage3_config.get('parallel_config', {})
        }

        # 根據環境變量決定是否使用取樣模式
        use_sampling = is_sampling_mode()
        if use_sampling:
            config_compat['sample_mode'] = True
            config_compat['sample_size'] = 50

        # 顯示配置摘要
        print(f"📋 配置摘要:")
        print(f"   源座標系: {config_compat['coordinate_config']['source_frame']}")
        print(f"   目標座標系: {config_compat['coordinate_config']['target_frame']}")
        print(f"   歲差章動模型: {config_compat['coordinate_config']['nutation_model']}")
        print(f"   目標精度: {config_compat['precision_config']['target_accuracy_m']}m")
        print(f"   幾何預篩選: {'啟用' if config_compat['enable_geometric_prefilter'] else '禁用'}")
        print(f"   處理模式: {'取樣模式' if use_sampling else '完整模式'}")

        # Stage 3 特別提示（處理時間較長）
        print('⏱️ Stage 3 座標轉換處理中，預計需要 5-15 分鐘...')

        return config_compat

    def create_processor(self, config: Dict[str, Any]):
        """
        創建 Stage 3 處理器

        Args:
            config: load_config() 返回的配置字典

        Returns:
            Stage3CoordinateTransformProcessor: 處理器實例
        """
        from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
        return Stage3CoordinateTransformProcessor(config=config)

    def get_previous_stage_number(self) -> int:
        """
        Stage 3 依賴 Stage 2 的結果

        Returns:
            int: 2
        """
        return 2


# ===== 向後兼容函數 =====

def execute_stage3(previous_results=None):
    """
    執行 Stage 3: 座標系統轉換層 (v3.1)

    向後兼容函數，保持原有調用方式。
    內部使用 Stage3Executor 類實現。

    Args:
        previous_results: 前序階段結果字典（必須包含 'stage2' 結果）

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage3Processor)
    """
    executor = Stage3Executor()
    return executor.execute(previous_results)
