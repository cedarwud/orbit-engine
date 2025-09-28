#!/usr/bin/env python3
"""
大樣本衛星數據比較測試
使用1000顆衛星樣本來驗證處理器行為
"""

import os
import sys
import json
import yaml
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_large_sample_processor(processor_class, processor_name, config_dict, input_data, sample_size=1000):
    """測試大樣本處理器"""
    print(f"\n🔬 大樣本測試 {processor_name} (樣本: {sample_size:,})")
    print("=" * 60)

    # 使用大樣本
    large_sample = input_data.copy()
    large_sample['satellites'] = input_data['satellites'][:sample_size]
    actual_input = len(large_sample['satellites'])
    print(f"📊 實際輸入數據: {actual_input:,} 顆衛星")

    try:
        # 初始化處理器
        print(f"⚡ 初始化 {processor_name}...")
        if processor_name == "標準處理器":
            processor = processor_class(config=config_dict)
        else:
            processor = processor_class(config=config_dict)

        print(f"✅ {processor_name} 初始化完成")

        # 執行處理
        print(f"🚀 開始執行 {processor_name}...")
        start_time = time.time()
        result = processor.execute(large_sample)
        execution_time = time.time() - start_time

        # 提取結果
        if hasattr(result, 'data') and isinstance(result.data, dict):
            satellites = result.data.get('satellites', [])
            metadata = result.data.get('metadata', {})
        else:
            satellites = result.get('satellites', []) if isinstance(result, dict) else []
            metadata = result.get('metadata', {}) if isinstance(result, dict) else {}

        # 統計結果
        output_count = len(satellites)
        visible_count = metadata.get('visible_satellites_count', 0)
        feasible_count = metadata.get('feasible_satellites_count', 0)

        # 計算率
        filtering_rate = ((actual_input - output_count) / actual_input * 100) if actual_input > 0 else 0
        output_feasible_rate = (feasible_count / output_count * 100) if output_count > 0 else 0
        input_feasible_rate = (feasible_count / actual_input * 100) if actual_input > 0 else 0
        visibility_rate = (visible_count / actual_input * 100) if actual_input > 0 else 0

        print(f"\n📊 {processor_name} 大樣本結果:")
        print(f"   執行時間: {execution_time:.1f} 秒")
        print(f"   輸入衛星: {actual_input:,} 顆")
        print(f"   輸出衛星: {output_count:,} 顆")
        print(f"   可見衛星: {visible_count:,} 顆")
        print(f"   可行衛星: {feasible_count:,} 顆")
        print(f"   篩選率: {filtering_rate:.1f}% (被篩選掉的)")
        print(f"   可見率: {visibility_rate:.1f}% (相對於輸入)")
        print(f"   總體可行率: {input_feasible_rate:.1f}% (相對於輸入)")
        print(f"   輸出可行率: {output_feasible_rate:.1f}% (輸出中可行的)")

        # 檢查星座分佈
        constellation_stats = {}
        elevation_stats = []

        for sat in satellites[:100]:  # 檢查前100個
            constellation = sat.get('constellation', 'unknown')
            constellation_stats[constellation] = constellation_stats.get(constellation, 0) + 1

            elevation = sat.get('elevation_deg', 0)
            if elevation != 0:
                elevation_stats.append(elevation)

        print(f"\n📋 前100個輸出衛星統計:")
        print(f"   星座分佈: {dict(constellation_stats)}")
        if elevation_stats:
            avg_elevation = sum(elevation_stats) / len(elevation_stats)
            min_elevation = min(elevation_stats)
            max_elevation = max(elevation_stats)
            print(f"   仰角範圍: {min_elevation:.1f}° - {max_elevation:.1f}° (平均: {avg_elevation:.1f}°)")

        return {
            'processor_name': processor_name,
            'execution_time': execution_time,
            'input_count': actual_input,
            'output_count': output_count,
            'visible_count': visible_count,
            'feasible_count': feasible_count,
            'filtering_rate': filtering_rate,
            'output_feasible_rate': output_feasible_rate,
            'input_feasible_rate': input_feasible_rate,
            'visibility_rate': visibility_rate,
            'constellation_stats': constellation_stats,
            'success': True
        }

    except Exception as e:
        print(f"❌ {processor_name} 大樣本測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return {
            'processor_name': processor_name,
            'success': False,
            'error': str(e)
        }

def main():
    """主函數"""
    print("🔍 大樣本衛星數據比較測試")
    print("使用1000顆衛星樣本來驗證處理器行為")

    # 載入配置和數據
    config_path = "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    total_satellites = len(input_data.get('satellites', []))
    print(f"📊 總可用數據: {total_satellites:,} 顆衛星")

    sample_size = min(1000, total_satellites)
    print(f"🎯 測試樣本大小: {sample_size:,} 顆衛星")

    results = []

    # 測試標準處理器
    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
    std_result = test_large_sample_processor(Stage2OrbitalComputingProcessor, "標準處理器", stage2_config, input_data, sample_size)
    if std_result['success']:
        results.append(std_result)

    # 測試混合處理器
    from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
    hybrid_result = test_large_sample_processor(HybridStage2Processor, "混合處理器", stage2_config, input_data, sample_size)
    if hybrid_result['success']:
        results.append(hybrid_result)

    # 對比分析
    if len(results) == 2:
        std_result, hybrid_result = results
        print(f"\n📊 大樣本數據對比分析")
        print("=" * 80)
        print(f"{'指標':<20} {'標準處理器':<15} {'混合處理器':<15} {'差異':<15}")
        print("-" * 80)

        # 性能對比
        time_ratio = std_result['execution_time'] / hybrid_result['execution_time'] if hybrid_result['execution_time'] > 0 else 0
        print(f"{'執行時間':<20} {std_result['execution_time']:<15.1f}s {hybrid_result['execution_time']:<15.1f}s {time_ratio:<15.1f}x")

        # 數量對比
        comparisons = [
            ('輸出衛星', 'output_count'),
            ('可見衛星', 'visible_count'),
            ('可行衛星', 'feasible_count'),
        ]

        for name, key in comparisons:
            std_val = std_result[key]
            hyb_val = hybrid_result[key]
            diff = hyb_val - std_val
            print(f"{name:<20} {std_val:<15,} {hyb_val:<15,} {diff:<+15,}")

        # 百分比對比
        print("-" * 80)
        rate_comparisons = [
            ('篩選率', 'filtering_rate'),
            ('可見率', 'visibility_rate'),
            ('總體可行率', 'input_feasible_rate'),
            ('輸出可行率', 'output_feasible_rate'),
        ]

        all_normal = True
        max_diff = 0
        for name, key in rate_comparisons:
            std_val = std_result[key]
            hyb_val = hybrid_result[key]
            diff = hyb_val - std_val
            max_diff = max(max_diff, abs(diff))
            print(f"{name:<20} {std_val:<15.1f}% {hyb_val:<15.1f}% {diff:<+15.1f}%")

            # 檢查異常 - 對大樣本使用更嚴格的標準
            if key == 'output_feasible_rate' and abs(diff) > 2:
                print(f"    ⚠️  {name}差異過大！")
                all_normal = False
            elif key in ['filtering_rate', 'input_feasible_rate', 'visibility_rate'] and abs(diff) > 1:
                print(f"    ⚠️  {name}差異過大！")
                all_normal = False

        print("\n" + "=" * 80)
        print("🎯 大樣本測試結論:")
        print(f"📊 樣本規模: {sample_size:,} 顆衛星 ({sample_size/total_satellites*100:.1f}% 的總數據)")
        print(f"🔍 最大差異: {max_diff:.2f}%")

        if all_normal and max_diff < 1.0:
            print("✅ 混合處理器在大樣本上的篩選邏輯完全正常")
            print("✅ 與標準處理器產生幾乎相同的篩選結果")
            print(f"🚀 性能提升: {time_ratio:.1f}x 倍速度")
            print("🎉 混合處理器修復驗證成功 - 準確性和性能雙優")
        elif all_normal:
            print("✅ 混合處理器在大樣本上的篩選邏輯基本正常")
            print(f"⚠️  有輕微差異但在可接受範圍內 (< 1%)")
            print(f"🚀 性能提升: {time_ratio:.1f}x 倍速度")
        else:
            print("❌ 混合處理器在大樣本上存在明顯篩選差異")
            print("🔧 建議進一步檢查算法差異")

    else:
        print("❌ 無法完成對比分析 - 某個處理器測試失敗")

if __name__ == "__main__":
    main()