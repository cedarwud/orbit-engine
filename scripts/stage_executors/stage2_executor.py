"""
Stage 2 執行器 - 軌道狀態傳播層 (v3.0 架構)

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

from pathlib import Path
from .executor_utils import clean_stage_outputs, extract_data_from_result, project_root


def load_stage2_config(config_path: str) -> dict:
    """載入 Stage 2 配置文件"""
    import yaml
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        time_config = config_dict.get('time_series_config', {})
        propagation_config = config_dict.get('propagation_config', {})

        print(f'📊 v3.0 軌道傳播配置載入成功:')
        print(f'   時間步長: {time_config.get("time_step_seconds", "N/A")}秒')
        print(f'   座標系統: {propagation_config.get("coordinate_system", "TEME")}')
        print(f'   SGP4庫: {propagation_config.get("sgp4_library", "skyfield")}')

        return config_dict
    except Exception as e:
        print(f'❌ 配置載入失敗: {e}')
        return {}


def execute_stage2(previous_results):
    """
    執行 Stage 2: 軌道狀態傳播層 (v3.0)

    Args:
        previous_results: dict, 必須包含 'stage1' 結果

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage2Processor)
    """
    try:
        print('\n🛰️ 階段二：軌道狀態傳播層')
        print('-' * 60)

        # 檢查前序階段
        if 'stage1' not in previous_results:
            print('❌ 缺少 Stage 1 結果')
            return False, None, None

        # 清理舊的輸出
        clean_stage_outputs(2)

        # 載入 v3.0 軌道傳播配置
        config_path = project_root / "config/stage2_orbital_computing.yaml"

        if config_path.exists():
            print(f'📄 載入 v3.0 配置: {config_path}')
            config_dict = load_stage2_config(str(config_path))

            from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
            stage2 = Stage2OrbitalPropagationProcessor(config=config_dict)
        else:
            print('⚠️ 配置文件不存在，使用 v3.0 預設處理器')
            from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
            stage2 = Stage2OrbitalPropagationProcessor()

        # 提取 Stage 1 數據
        stage1_data = extract_data_from_result(previous_results['stage1'])

        # 執行處理
        stage2_result = stage2.execute(stage1_data)

        if not stage2_result:
            print('❌ Stage 2 處理失敗')
            return False, None, stage2

        return True, stage2_result, stage2

    except Exception as e:
        print(f'❌ Stage 2 執行異常: {e}')
        return False, None, None
