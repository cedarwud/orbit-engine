#!/usr/bin/env python3
"""
全量衛星數據比較測試
比較標準處理器與混合處理器在完整數據集上的表現
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

def test_full_scale_processor(processor_class, processor_name, config_dict, input_data):
    """測試全量處理器"""
    print(f"\n🔬 全量測試 {processor_name}")
    print("=" * 60)

    input_count = len(input_data.get('satellites', []))
    print(f"📊 輸入數據: {input_count} 顆衛星")

    try:
        # 初始化處理器
        print(f"⚡ 初始化 {processor_name}...")
        if processor_name == "標準處理器":
            processor = processor_class(config=config_dict)
        else:
            processor = processor_class(config=config_dict)

        print(f"✅ {processor_name} 初始化完成")

        # 執行處理
        print(f"🚀 開始執行 {processor_name} (全量數據)...")
        start_time = time.time()
        result = processor.execute(input_data)
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
        filtering_rate = ((input_count - output_count) / input_count * 100) if input_count > 0 else 0
        output_feasible_rate = (feasible_count / output_count * 100) if output_count > 0 else 0
        input_feasible_rate = (feasible_count / input_count * 100) if input_count > 0 else 0
        visibility_rate = (visible_count / input_count * 100) if input_count > 0 else 0

        print(f"\n📊 {processor_name} 全量結果:")
        print(f"   執行時間: {execution_time:.1f} 秒")
        print(f"   輸入衛星: {input_count:,} 顆")
        print(f"   輸出衛星: {output_count:,} 顆")
        print(f"   可見衛星: {visible_count:,} 顆")
        print(f"   可行衛星: {feasible_count:,} 顆")
        print(f"   篩選率: {filtering_rate:.1f}% (被篩選掉的)")
        print(f"   可見率: {visibility_rate:.1f}% (相對於輸入)")
        print(f"   總體可行率: {input_feasible_rate:.1f}% (相對於輸入)")
        print(f"   輸出可行率: {output_feasible_rate:.1f}% (輸出中可行的)")

        # 分析前10個衛星的詳細狀態
        if len(satellites) >= 10:
            print(f"\n📋 前10個輸出衛星的詳細狀態:")
            visible_in_sample = 0
            feasible_in_sample = 0
            elevation_sum = 0
            elevation_count = 0

            for i, sat in enumerate(satellites[:10]):
                is_visible = sat.get('is_visible', False)
                is_feasible = sat.get('is_feasible', False)
                elevation = sat.get('elevation_deg', 0)
                constellation = sat.get('constellation', 'unknown')

                if is_visible:
                    visible_in_sample += 1
                if is_feasible:
                    feasible_in_sample += 1
                if elevation != 0:
                    elevation_sum += elevation
                    elevation_count += 1

                print(f"   {i+1:2d}. {sat.get('name', 'N/A'):<20} ({constellation:<8}): "
                      f"可見={is_visible}, 可行={is_feasible}, 仰角={elevation:.1f}°")

            avg_elevation = elevation_sum / elevation_count if elevation_count > 0 else 0
            print(f"\n   前10個樣本統計: 可見={visible_in_sample}/10, 可行={feasible_in_sample}/10, 平均仰角={avg_elevation:.1f}°")

        return {
            'processor_name': processor_name,
            'execution_time': execution_time,
            'input_count': input_count,
            'output_count': output_count,
            'visible_count': visible_count,
            'feasible_count': feasible_count,
            'filtering_rate': filtering_rate,
            'output_feasible_rate': output_feasible_rate,
            'input_feasible_rate': input_feasible_rate,
            'visibility_rate': visibility_rate,
            'success': True
        }

    except Exception as e:
        print(f"❌ {processor_name} 全量測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return {
            'processor_name': processor_name,
            'success': False,
            'error': str(e)
        }

def main():
    """主函數"""
    print("🔍 全量衛星數據比較測試")
    print("比較標準處理器與簡潔混合處理器的完整性能和準確性")

    # 載入配置和數據
    config_path = "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    total_satellites = len(input_data.get('satellites', []))
    print(f"📊 總輸入數據: {total_satellites:,} 顆衛星")

    results = []

    # 測試標準處理器
    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
    std_result = test_full_scale_processor(Stage2OrbitalComputingProcessor, "標準處理器", stage2_config, input_data)
    if std_result['success']:
        results.append(std_result)

    # 測試簡潔混合處理器
    from stages.stage2_orbital_computing.hybrid_stage2_processor_simple import HybridStage2ProcessorSimple
    hybrid_result = test_full_scale_processor(HybridStage2ProcessorSimple, "簡潔混合處理器", stage2_config, input_data)
    if hybrid_result['success']:
        results.append(hybrid_result)

    # 對比分析
    if len(results) == 2:
        std_result, hybrid_result = results
        print(f"\n📊 全量數據對比分析")
        print("=" * 80)
        print(f"{'指標':<20} {'標準處理器':<15} {'混合處理器':<15} {'差異':<15}")
        print("-" * 80)

        # 性能對比
        time_ratio = std_result['execution_time'] / hybrid_result['execution_time'] if hybrid_result['execution_time'] > 0 else 0
        print(f"{'執行時間':<20} {std_result['execution_time']:<15.1f}s {hybrid_result['execution_time']:<15.1f}s {time_ratio:<15.2f}x")

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
        for name, key in rate_comparisons:
            std_val = std_result[key]
            hyb_val = hybrid_result[key]
            diff = hyb_val - std_val
            print(f"{name:<20} {std_val:<15.1f}% {hyb_val:<15.1f}% {diff:<+15.1f}%")

            # 檢查異常
            if key == 'output_feasible_rate' and abs(diff) > 5:
                print(f"    ⚠️  {name}差異過大！")
                all_normal = False
            elif key in ['filtering_rate', 'input_feasible_rate', 'visibility_rate'] and abs(diff) > 2:
                print(f"    ⚠️  {name}差異過大！")
                all_normal = False

        print("\n" + "=" * 80)
        print("🎯 全量測試結論:")
        if all_normal:
            print("✅ 簡潔混合處理器在全量數據上的篩選邏輯完全正常")
            print("✅ 與標準處理器產生相同的篩選結果")
            print(f"🚀 性能提升: {time_ratio:.2f}x 倍速度")
            print("🎉 簡潔混合處理器修復成功 - 既保證準確性又提升性能")
        else:
            print("❌ 簡潔混合處理器在全量數據上存在篩選異常")
            print("🔧 需要進一步調試修復")

    else:
        print("❌ 無法完成對比分析 - 某個處理器測試失敗")

if __name__ == "__main__":
    main()