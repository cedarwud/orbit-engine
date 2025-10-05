"""
Stage 3 執行器 - 座標系統轉換層 (v3.1 架構)

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

from .executor_utils import clean_stage_outputs, extract_data_from_result, is_sampling_mode


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

        # 根據環境變量決定是否使用取樣模式
        use_sampling = is_sampling_mode()

        # v3.1 重構：禁用預篩選器（Stage 1 已完成日期篩選）
        stage3_config = {
            'enable_geometric_prefilter': False,  # v3.1: 直接禁用
            'coordinate_config': {
                'source_frame': 'TEME',
                'target_frame': 'WGS84',
                'time_corrections': True,
                'polar_motion': True,
                'nutation_model': 'IAU2000A'
            },
            'skyfield_config': {
                'ephemeris_file': 'de421.bsp',
                'auto_download': True
            },
            'precision_config': {
                'target_accuracy_m': 0.5
            }
        }

        print('🆕 Stage 3: 預篩選已禁用 (v3.1) - Stage 1 已完成 Epoch 篩選')

        if use_sampling:
            stage3_config['sample_mode'] = True
            stage3_config['sample_size'] = 50

        stage3 = Stage3CoordinateTransformProcessor(config=stage3_config)
        mode_msg = "取樣模式" if use_sampling else "完整模式"
        print(f'✅ Stage 3 配置: {mode_msg}')

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
