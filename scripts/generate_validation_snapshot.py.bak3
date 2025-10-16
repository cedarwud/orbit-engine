#!/usr/bin/env python3
"""
手動生成驗證快照工具

用途：
- 從已保存的 Stage 輸出文件手動生成驗證快照
- 可用於重新驗證已完成的處理結果
- 適用於所有 Stage (1-6)

使用方法：
    python3 scripts/generate_validation_snapshot.py --stage 3
    python3 scripts/generate_validation_snapshot.py --stage 3 --input-file data/outputs/stage3/stage3_xxx.json
    python3 scripts/generate_validation_snapshot.py --stages 1-3
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import glob

# 添加專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_processor
from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import create_stage3_processor


def find_latest_output_file(stage_num: int) -> str:
    """查找最新的輸出文件"""
    stage_dirs = {
        1: "data/outputs/stage1",
        2: "data/outputs/stage2",
        3: "data/outputs/stage3",
        4: "data/outputs/stage4",
        5: "data/outputs/stage5",
        6: "data/outputs/stage6"
    }

    output_dir = stage_dirs.get(stage_num)
    if not output_dir:
        raise ValueError(f"不支持的 Stage: {stage_num}")

    # 查找所有 JSON 文件
    pattern = f"{output_dir}/*.json"
    files = glob.glob(pattern)

    if not files:
        raise FileNotFoundError(f"找不到 Stage {stage_num} 的輸出文件: {pattern}")

    # 返回最新的文件
    latest_file = max(files, key=lambda f: Path(f).stat().st_mtime)
    return latest_file


def load_output_file(file_path: str) -> dict:
    """載入輸出文件"""
    print(f"📂 載入輸出文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✅ 成功載入輸出文件")
    return data


def generate_snapshot_stage1(input_file: str = None):
    """生成 Stage 1 驗證快照"""
    print("\n" + "="*60)
    print("📋 生成 Stage 1 驗證快照")
    print("="*60)

    # 查找或使用指定的輸入文件
    if input_file is None:
        input_file = find_latest_output_file(1)

    # 載入輸出數據
    output_data = load_output_file(input_file)

    # 創建處理器
    processor = create_stage1_processor()

    # 生成驗證快照
    print("\n🔍 執行驗證檢查...")
    success = processor.save_validation_snapshot(output_data)

    if success:
        print("✅ Stage 1 驗證快照生成成功")
        print(f"📋 快照位置: data/validation_snapshots/stage1_validation.json")
        return True
    else:
        print("❌ Stage 1 驗證快照生成失敗")
        return False


def generate_snapshot_stage2(input_file: str = None):
    """生成 Stage 2 驗證快照"""
    print("\n" + "="*60)
    print("📋 生成 Stage 2 驗證快照")
    print("="*60)

    # 查找或使用指定的輸入文件
    if input_file is None:
        input_file = find_latest_output_file(2)

    # 載入輸出數據
    output_data = load_output_file(input_file)

    # 創建處理器
    processor = Stage2OrbitalPropagationProcessor()

    # 生成驗證快照
    print("\n🔍 執行驗證檢查...")
    success = processor.save_validation_snapshot(output_data)

    if success:
        print("✅ Stage 2 驗證快照生成成功")
        print(f"📋 快照位置: data/validation_snapshots/stage2_validation.json")
        return True
    else:
        print("❌ Stage 2 驗證快照生成失敗")
        return False


def generate_snapshot_stage3(input_file: str = None):
    """生成 Stage 3 驗證快照"""
    print("\n" + "="*60)
    print("📋 生成 Stage 3 驗證快照")
    print("="*60)

    # 查找或使用指定的輸入文件
    if input_file is None:
        input_file = find_latest_output_file(3)

    # 載入輸出數據
    output_data = load_output_file(input_file)

    # 創建處理器
    processor = create_stage3_processor()

    # 生成驗證快照
    print("\n🔍 執行驗證檢查...")
    success = processor.save_validation_snapshot(output_data)

    if success:
        print("✅ Stage 3 驗證快照生成成功")
        print(f"📋 快照位置: data/validation_snapshots/stage3_validation.json")
        return True
    else:
        print("❌ Stage 3 驗證快照生成失敗")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="手動生成驗證快照工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 為 Stage 3 生成驗證快照（使用最新輸出文件）
  python3 scripts/generate_validation_snapshot.py --stage 3

  # 使用指定的輸出文件
  python3 scripts/generate_validation_snapshot.py --stage 3 --input-file data/outputs/stage3/stage3_xxx.json

  # 為多個 Stage 生成驗證快照
  python3 scripts/generate_validation_snapshot.py --stages 1-3
        """
    )

    parser.add_argument(
        '--stage',
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help='指定單一 Stage 編號 (1-6)'
    )

    parser.add_argument(
        '--stages',
        type=str,
        help='指定 Stage 範圍 (例如: 1-3)'
    )

    parser.add_argument(
        '--input-file',
        type=str,
        help='指定輸入文件路徑（可選，默認使用最新文件）'
    )

    args = parser.parse_args()

    # 解析 Stage 範圍
    stages_to_process = []

    if args.stage:
        stages_to_process = [args.stage]
    elif args.stages:
        # 解析範圍 (例如: "1-3")
        if '-' in args.stages:
            start, end = map(int, args.stages.split('-'))
            stages_to_process = list(range(start, end + 1))
        else:
            stages_to_process = [int(args.stages)]
    else:
        parser.print_help()
        sys.exit(1)

    # 處理器映射
    generators = {
        1: generate_snapshot_stage1,
        2: generate_snapshot_stage2,
        3: generate_snapshot_stage3,
        # 可以添加 Stage 4-6
    }

    # 執行生成
    success_count = 0
    total_count = len(stages_to_process)

    print(f"\n🚀 開始生成驗證快照")
    print(f"📊 計劃處理: {total_count} 個 Stage")
    print(f"📋 Stage 清單: {stages_to_process}")

    for stage_num in stages_to_process:
        if stage_num not in generators:
            print(f"\n⚠️ Stage {stage_num} 尚未實現驗證快照生成")
            continue

        try:
            # 只有第一個 Stage 或明確指定 input_file 時才使用
            input_file = args.input_file if (stage_num == stages_to_process[0] or args.input_file) else None

            success = generators[stage_num](input_file)
            if success:
                success_count += 1
        except Exception as e:
            print(f"❌ Stage {stage_num} 驗證快照生成失敗: {e}")
            import traceback
            traceback.print_exc()

    # 總結
    print("\n" + "="*60)
    print("📊 驗證快照生成總結")
    print("="*60)
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 所有驗證快照生成成功！")
        sys.exit(0)
    else:
        print("\n⚠️ 部分驗證快照生成失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
