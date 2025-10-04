"""
Stage 5 執行器 - 信號品質分析層

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import json
from .executor_utils import clean_stage_outputs, find_latest_stage_output


def execute_stage5(previous_results):
    """
    執行 Stage 5: 信號品質分析層

    Args:
        previous_results: dict, 必須包含 'stage4' 結果

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage5Processor)
    """
    try:
        print('\n📊 階段五：信號品質分析層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(5)

        # 尋找 Stage 4 輸出
        stage4_output = find_latest_stage_output(4)
        if not stage4_output:
            print('❌ 找不到 Stage 4 輸出文件，請先執行 Stage 4')
            return False, None, None

        from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor
        processor = Stage5SignalAnalysisProcessor()

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
        return False, None, None
