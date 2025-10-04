"""
Stage 6 執行器 - 研究數據生成層

Author: Extracted from run_six_stages_with_validation.py
Date: 2025-10-03
"""

import json
from .executor_utils import clean_stage_outputs, find_latest_stage_output


def execute_stage6(previous_results):
    """
    執行 Stage 6: 研究數據生成層

    Args:
        previous_results: dict, 必須包含 'stage5' 結果

    Returns:
        tuple: (success: bool, result: ProcessingResult, processor: Stage6Processor)
    """
    try:
        print('\n💾 階段六：研究數據生成層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(6)

        # 尋找 Stage 5 輸出
        stage5_output = find_latest_stage_output(5)
        if not stage5_output:
            print('❌ 找不到 Stage 5 輸出文件，請先執行 Stage 5')
            return False, None, None

        from stages.stage6_research_optimization.stage6_research_optimization_processor import Stage6ResearchOptimizationProcessor
        processor = Stage6ResearchOptimizationProcessor()

        # 載入前階段數據
        with open(stage5_output, 'r') as f:
            stage5_data = json.load(f)

        # 執行處理
        result = processor.execute(stage5_data)

        if not result:
            print('❌ Stage 6 執行失敗')
            return False, None, processor

        # 保存 Stage 6 驗證快照
        if hasattr(processor, 'save_validation_snapshot'):
            snapshot_saved = processor.save_validation_snapshot(result)
            if snapshot_saved:
                print('✅ Stage 6 驗證快照已保存')
            else:
                print('⚠️ Stage 6 驗證快照保存失敗')

        return True, result, processor

    except Exception as e:
        print(f'❌ Stage 6 執行異常: {e}')
        return False, None, None
