#!/usr/bin/env python3
"""
測試修復版混合處理器
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    """主函數"""
    print("🔬 測試修復版混合處理器")

    # 載入配置
    import yaml
    config_path = "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    # 載入階段一輸出
    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # 使用完整數據集進行測試
    total_input = len(input_data['satellites'])
    print(f"📊 測試數據: {total_input} 顆衛星")

    try:
        # 載入修復版混合處理器
        from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor

        print("⚡ 初始化混合處理器...")
        processor = HybridStage2Processor(config=stage2_config)
        print("✅ 混合處理器初始化完成")

        # 執行處理
        print("🚀 開始執行混合處理器...")
        start_time = time.time()
        result = processor.execute(input_data)
        execution_time = time.time() - start_time

        # 提取結果統計
        if hasattr(result, 'data') and isinstance(result.data, dict):
            satellites = result.data.get('satellites', [])
            metadata = result.data.get('metadata', {})
        else:
            satellites = result.get('satellites', []) if isinstance(result, dict) else []
            metadata = result.get('metadata', {}) if isinstance(result, dict) else {}

        # 統計結果
        total_satellites = len(satellites)
        visible_count = metadata.get('visible_satellites_count', 0)
        feasible_count = metadata.get('feasible_satellites_count', 0)

        # 計算相對於輸入的篩選率
        visibility_rate = (visible_count / total_input * 100) if total_input > 0 else 0
        feasibility_rate = (feasible_count / total_input * 100) if total_input > 0 else 0
        output_rate = (total_satellites / total_input * 100) if total_input > 0 else 0

        print(f"\n📊 混合處理器測試結果:")
        print(f"   執行時間: {execution_time:.2f} 秒")
        print(f"   輸入衛星: {total_input} 顆")
        print(f"   輸出衛星: {total_satellites} 顆 ({output_rate:.1f}%)")
        print(f"   可見衛星: {visible_count} 顆 ({visibility_rate:.1f}%)")
        print(f"   可行衛星: {feasible_count} 顆 ({feasibility_rate:.1f}%)")

        # 檢查結果是否合理
        print(f"\n🤔 結果分析:")
        if feasibility_rate < 30:
            print(f"   ✅ 可行率 {feasibility_rate:.1f}% 看起來合理（預期 15-25%）")
        else:
            print(f"   ❌ 可行率 {feasibility_rate:.1f}% 看起來太高，可能沒有正確篩選")

        if output_rate < 50:
            print(f"   ✅ 輸出率 {output_rate:.1f}% 表示有篩選")
        else:
            print(f"   ❌ 輸出率 {output_rate:.1f}% 太高，篩選不夠嚴格")

        if visible_count > 0 and feasible_count > 0 and feasibility_rate < 30:
            print("✅ 混合處理器修復成功")
        else:
            print("❌ 混合處理器仍有問題")

        # 檢查前幾個衛星的詳細信息
        if len(satellites) > 0:
            print(f"\n📋 前5個衛星的詳細信息:")
            for i, sat in enumerate(satellites[:5]):
                is_visible = sat.get('is_visible', False)
                is_feasible = sat.get('is_feasible', False)
                elevation = sat.get('elevation_deg', 0)
                constellation = sat.get('constellation', 'unknown')
                print(f"   {i+1}. {sat.get('name', 'N/A')} ({constellation}): "
                      f"可見={is_visible}, 可行={is_feasible}, 仰角={elevation:.1f}°")

    except Exception as e:
        print(f"❌ 混合處理器測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()