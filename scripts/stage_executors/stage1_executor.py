"""
Stage 1 執行器 - TLE 數據載入層

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import os
from .executor_utils import clean_stage_outputs, is_sampling_mode


def execute_stage1(previous_results=None):
    """
    執行 Stage 1: TLE 數據載入層

    Args:
        previous_results: 前序階段結果 (Stage 1 不需要)

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage1Processor)
    """
    try:
        print('\n📦 階段一：數據載入層 (重構版本)')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(1)

        # 使用統一的重構版本
        from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor

        # 根據環境變量決定是否使用取樣模式
        use_sampling = is_sampling_mode()

        # Stage 1 配置（含 Epoch 分析）
        config = {
            'sample_mode': use_sampling,
            'sample_size': 50,
            # Epoch 分析配置
            'epoch_analysis': {
                'enabled': True  # 啟用 epoch 動態分析
            },
            # Epoch 篩選配置（符合規格文檔標準）
            'epoch_filter': {
                'enabled': True,           # 啟用 epoch 篩選
                'mode': 'latest_date',     # 篩選模式：保留最新日期衛星
                'tolerance_hours': 24      # 容差範圍：± 24 小時（基於 SGP4 精度分析）
            }
        }

        # 創建處理器
        stage1_processor = create_stage1_processor(config)

        print(f'🔧 配置: {"取樣模式" if use_sampling else "完整模式"}')
        print(f'🔧 Epoch 篩選: 啟用 (latest_date 模式，容差 ±{config["epoch_filter"]["tolerance_hours"]}h)')

        # 執行處理
        stage1_result = stage1_processor.execute()

        # 檢查執行結果
        if not stage1_result or not stage1_result.data:
            return False, stage1_result, stage1_processor

        # 顯示處理結果統計
        print(f'📊 處理狀態: {stage1_result.status}')
        print(f'📊 處理時間: {stage1_result.metrics.duration_seconds:.3f}秒')
        print(f'📊 處理衛星: {len(stage1_result.data.get("satellites", []))}顆')

        return True, stage1_result, stage1_processor

    except Exception as e:
        print(f'❌ Stage 1 執行異常: {e}')
        return False, None, None
