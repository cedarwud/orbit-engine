"""
Stage 3 執行器 - 座標系統轉換層 (v3.1 架構)

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import yaml
from pathlib import Path
from .executor_utils import clean_stage_outputs, extract_data_from_result, is_sampling_mode, project_root


def execute_stage3(previous_results):
    """
    執行 Stage 3: 座標系統轉換層 (v3.1)

    Args:
        previous_results: dict, 必須包含 'stage2' 結果

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage3Processor)
    """
    try:
        print('\n🌍 階段三：座標系統轉換層')
        print('-' * 60)

        # 檢查前序階段
        if 'stage2' not in previous_results:
            print('❌ 缺少 Stage 2 結果')
            return False, None, None

        # 清理舊的輸出
        clean_stage_outputs(3)

        from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor

        # ✅ 從 YAML 載入配置
        config_path = project_root / "config/stage3_coordinate_transformation.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                stage3_config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 3 配置: {config_path}")
        else:
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

        print(f"📋 配置摘要:")
        print(f"   源座標系: {config_compat['coordinate_config']['source_frame']}")
        print(f"   目標座標系: {config_compat['coordinate_config']['target_frame']}")
        print(f"   歲差章動模型: {config_compat['coordinate_config']['nutation_model']}")
        print(f"   目標精度: {config_compat['precision_config']['target_accuracy_m']}m")
        print(f"   幾何預篩選: {'啟用' if config_compat['enable_geometric_prefilter'] else '禁用'}")
        print(f"   處理模式: {'取樣模式' if use_sampling else '完整模式'}")

        stage3 = Stage3CoordinateTransformProcessor(config=config_compat)

        # 提取 Stage 2 數據
        stage2_data = extract_data_from_result(previous_results['stage2'])

        # 執行處理
        print('⏱️ Stage 3 座標轉換處理中，預計需要 5-15 分鐘...')
        stage3_result = stage3.execute(stage2_data)

        if not stage3_result:
            print('❌ Stage 3 處理失敗')
            return False, None, stage3

        return True, stage3_result, stage3

    except Exception as e:
        print(f'❌ Stage 3 執行異常: {e}')
        return False, None, None
