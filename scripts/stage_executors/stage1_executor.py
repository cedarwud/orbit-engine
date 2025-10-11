"""
Stage 1 執行器 - TLE 數據載入層

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import os
import yaml
from pathlib import Path
from .executor_utils import clean_stage_outputs, is_sampling_mode, project_root


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

        # ✅ 從 YAML 載入配置
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

        # 創建處理器
        stage1_processor = create_stage1_processor(config)

        print(f"📋 配置摘要:")
        print(f"   取樣模式: {'啟用' if use_sampling else '禁用'}")
        if use_sampling:
            print(f"   取樣數量: {config['sample_size']} 顆衛星")
        print(f"   Epoch 篩選: {config['epoch_filter']['mode']}")
        print(f"   容差範圍: ±{config['epoch_filter']['tolerance_hours']} 小時")

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
