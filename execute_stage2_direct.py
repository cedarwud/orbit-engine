#!/usr/bin/env python3
"""
直接執行 Stage 2 軌道計算層
使用 Stage 1 的輸出作為輸入
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 設置路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # 檢查環境
        if not os.path.exists('/orbit-engine'):
            print("❌ 必須在容器內執行此腳本")
            return False

        # 導入必要模組
        from src.stages.stage2_orbital_computing.optimized_stage2_processor import OptimizedStage2Processor

        # 尋找最新的 Stage 1 輸出
        stage1_output_dir = Path('/orbit-engine/data/outputs/stage1')
        if not stage1_output_dir.exists():
            print("❌ 找不到 Stage 1 輸出目錄")
            return False

        # 獲取最新的輸出文件
        stage1_files = list(stage1_output_dir.glob('tle_data_loading_output_*.json'))
        if not stage1_files:
            print("❌ 找不到 Stage 1 輸出文件")
            return False

        latest_file = max(stage1_files, key=lambda x: x.stat().st_mtime)
        print(f"📂 使用 Stage 1 輸出: {latest_file}")

        # 載入 Stage 1 數據
        with open(latest_file, 'r', encoding='utf-8') as f:
            stage1_data = json.load(f)

        print(f"✅ Stage 1 數據載入完成: {len(stage1_data.get('tle_data', []))} 顆衛星")

        # 初始化 Stage 2 處理器
        print("🚀 初始化 Stage 2 軌道計算處理器...")
        stage2_processor = OptimizedStage2Processor(enable_optimization=True)

        # 執行 Stage 2
        print("⚙️ 開始執行 Stage 2 軌道計算...")
        start_time = datetime.now()

        stage2_result = stage2_processor.execute(stage1_data)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        if stage2_result:
            print(f"✅ Stage 2 執行成功！耗時: {processing_time:.2f}秒")

            # 保存結果
            output_dir = Path('/orbit-engine/data/outputs/stage2')
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f"stage2_orbital_computing_output_{timestamp}.json"

            # 檢查結果格式並保存
            if hasattr(stage2_result, 'data'):
                # ProcessingResult 格式
                result_data = stage2_result.data
                metadata = {
                    'status': stage2_result.status.value if hasattr(stage2_result.status, 'value') else str(stage2_result.status),
                    'processing_time': processing_time,
                    'timestamp': timestamp
                }
                output_data = {'data': result_data, 'metadata': metadata}
            else:
                # 直接字典格式
                output_data = stage2_result

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"💾 結果已保存至: {output_file}")

            # 顯示統計信息
            if isinstance(stage2_result, dict):
                data_to_analyze = stage2_result
            elif hasattr(stage2_result, 'data'):
                data_to_analyze = stage2_result.data
            else:
                data_to_analyze = {}

            print("📊 Stage 2 處理統計:")
            if 'satellite_positions' in data_to_analyze:
                print(f"   - 衛星位置計算: {len(data_to_analyze['satellite_positions'])} 顆衛星")
            if 'visibility_analysis' in data_to_analyze:
                visible_count = sum(1 for v in data_to_analyze['visibility_analysis'].values() if v.get('is_visible', False))
                print(f"   - 可見性分析: {visible_count} 顆可見衛星")
            if 'coordinate_conversions' in data_to_analyze:
                print(f"   - 座標轉換: {len(data_to_analyze['coordinate_conversions'])} 筆記錄")

            return True
        else:
            print("❌ Stage 2 執行失敗")
            return False

    except Exception as e:
        logger.error(f"Stage 2 執行異常: {str(e)}")
        print(f"❌ 執行異常: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)