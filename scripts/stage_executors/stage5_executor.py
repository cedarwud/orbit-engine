"""
Stage 5 執行器 - 信號品質分析層

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
Updated: 2025-10-04 - 添加配置文件加载支持 (Grade A+ 合规)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple
from .executor_utils import clean_stage_outputs, find_latest_stage_output


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


def load_stage5_config() -> Dict[str, Any]:
    """
    載入 Stage 5 配置文件

    Returns:
        dict: 配置字典

    Raises:
        FileNotFoundError: 當配置文件不存在時
        yaml.YAMLError: 當配置文件格式錯誤時
    """
    # 構建配置文件路徑
    executor_dir = Path(__file__).parent
    project_root = executor_dir.parent.parent
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


def execute_stage5(previous_results):
    """
    執行 Stage 5: 信號品質分析層

    Args:
        previous_results: dict, 必須包含 'stage4' 結果

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage5Processor)
    """
    try:
        print('\n📊 階段五：信號品質分析層 (Grade A+ 模式)')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(5)

        # ✅ 新增：加載 Stage 5 配置文件
        try:
            config = load_stage5_config()
        except FileNotFoundError as e:
            print(f'⚠️  {e}')
            print('⚠️  使用空配置（可能導致 Grade A 驗證失敗）')
            config = {}
        except (yaml.YAMLError, ValueError) as e:
            print(f'❌ 配置文件錯誤: {e}')
            return False, None, None

        # 尋找 Stage 4 輸出
        stage4_output = find_latest_stage_output(4)
        if not stage4_output:
            print('❌ 找不到 Stage 4 輸出文件，請先執行 Stage 4')
            return False, None, None

        # ✅ 傳入配置參數創建處理器
        from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor
        processor = Stage5SignalAnalysisProcessor(config)

        # 載入前階段數據
        with open(stage4_output, 'r') as f:
            stage4_data = json.load(f)

        # 執行處理
        result = processor.execute(stage4_data)

        if not result:
            print('❌ Stage 5 執行失敗')
            return False, None, processor

        return True, result, processor

    except Exception as e:
        print(f'❌ Stage 5 執行異常: {e}')
        import traceback
        traceback.print_exc()
        return False, None, None
