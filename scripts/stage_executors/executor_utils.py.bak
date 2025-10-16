"""
執行器輔助函數

提供通用的執行器工具函數，簡化各階段執行器的實現。

Author: Created for refactored run_six_stages_with_validation.py
Date: 2025-10-03
"""

import os
from pathlib import Path


# 項目根目錄
project_root = Path(__file__).parent.parent.parent


def extract_data_from_result(result):
    """
    從 ProcessingResult 或 dict 中提取數據

    Args:
        result: ProcessingResult 對象或 dict

    Returns:
        dict: 數據部分
    """
    if hasattr(result, "data") and hasattr(result, "status"):
        return result.data
    else:
        return result


def is_sampling_mode():
    """
    檢測是否為取樣模式

    Returns:
        bool: True 如果處於取樣模式
    """
    use_sampling = os.getenv('ORBIT_ENGINE_SAMPLING_MODE', 'auto')
    if use_sampling == 'auto':
        return os.getenv('ORBIT_ENGINE_TEST_MODE') == '1'
    else:
        return use_sampling == '1'


def clean_stage_outputs(stage_number: int):
    """
    清理指定階段的輸出檔案和驗證快照

    Args:
        stage_number: 階段編號 (1-6)
    """
    try:
        # 清理輸出目錄
        output_dir = Path(f'data/outputs/stage{stage_number}')
        if output_dir.exists():
            for file in output_dir.iterdir():
                if file.is_file():
                    file.unlink()
            print(f"🗑️ 清理 Stage {stage_number} 輸出檔案")

        # 清理驗證快照
        snapshot_path = Path(f'data/validation_snapshots/stage{stage_number}_validation.json')
        if snapshot_path.exists():
            snapshot_path.unlink()
            print(f"🗑️ 清理 Stage {stage_number} 驗證快照")

    except Exception as e:
        print(f"⚠️ 清理 Stage {stage_number} 時發生錯誤: {e}")


def find_latest_stage_output(stage_number: int):
    """
    找到最新的階段輸出文件

    Args:
        stage_number: 階段編號

    Returns:
        Path | None: 最新的輸出文件路徑
    """
    output_dir = Path(f'data/outputs/stage{stage_number}')
    if not output_dir.exists():
        return None

    # 查找所有 JSON 文件
    json_files = list(output_dir.glob('*.json'))
    if not json_files:
        return None

    # 返回最新的文件
    return max(json_files, key=lambda p: p.stat().st_mtime)
