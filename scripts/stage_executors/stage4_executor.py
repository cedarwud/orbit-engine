"""
Stage 4 執行器 - 鏈路可行性評估層

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import json
from pathlib import Path
from .executor_utils import clean_stage_outputs, find_latest_stage_output


def execute_stage4(previous_results):
    """
    執行 Stage 4: 鏈路可行性評估層

    Args:
        previous_results: dict, 必須包含 'stage3' 結果

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage4Processor)
    """
    try:
        print('\n📡 階段四：鏈路可行性評估層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(4)

        # 尋找 Stage 3 輸出
        stage3_output = find_latest_stage_output(3)
        if not stage3_output:
            print('❌ 找不到 Stage 3 輸出文件，請先執行 Stage 3')
            return False, None, None

        from stages.stage4_link_feasibility.stage4_link_feasibility_processor import Stage4LinkFeasibilityProcessor

        # 載入 Stage 4 學術標準配置
        stage4_config_path = Path('/orbit-engine/config/stage4_link_feasibility_config.yaml')
        if stage4_config_path.exists():
            import yaml
            with open(stage4_config_path, 'r', encoding='utf-8') as f:
                stage4_config = yaml.safe_load(f)
            print(f"✅ 載入 Stage 4 配置: use_iau_standards={stage4_config.get('use_iau_standards')}")
        else:
            print("⚠️ 未找到 Stage 4 配置文件，使用預設設置")
            stage4_config = {'use_iau_standards': True, 'validate_epochs': False}

        processor = Stage4LinkFeasibilityProcessor(stage4_config)

        # 載入前階段數據
        with open(stage3_output, 'r') as f:
            stage3_data = json.load(f)

        # 執行處理（使用 process() 而非 execute()）
        result = processor.process(stage3_data)

        # 檢查 ProcessingResult 狀態
        if not result or result.status.value != 'success' or not result.data:
            error_msg = '; '.join(result.errors) if result and result.errors else "無結果或數據"
            print(f'❌ Stage 4 執行失敗: {error_msg}')
            return False, result, processor

        return True, result, processor

    except Exception as e:
        print(f'❌ Stage 4 執行異常: {e}')
        return False, None, None
