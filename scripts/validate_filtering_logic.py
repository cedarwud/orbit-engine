#!/usr/bin/env python3
"""
驗證篩選邏輯的正確性
重點：理解輸出的100%可行率是正常的，關鍵是篩選率
"""

import os
import sys
import json
import yaml
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_small_sample(processor_class, processor_name, config_dict, input_data, sample_size=50):
    """測試小樣本"""
    print(f"\n🔬 測試 {processor_name} (樣本: {sample_size})")
    print("-" * 50)

    # 使用小樣本
    small_sample = input_data.copy()
    small_sample['satellites'] = input_data['satellites'][:sample_size]

    try:
        # 初始化處理器
        if processor_name == "標準處理器":
            processor = processor_class(config=config_dict)
        else:
            processor = processor_class(config=config_dict)

        # 執行處理
        result = processor.execute(small_sample)

        # 提取結果
        if hasattr(result, 'data') and isinstance(result.data, dict):
            satellites = result.data.get('satellites', [])
            metadata = result.data.get('metadata', {})
        else:
            satellites = result.get('satellites', []) if isinstance(result, dict) else []
            metadata = result.get('metadata', {}) if isinstance(result, dict) else {}

        # 統計結果
        input_count = sample_size
        output_count = len(satellites)
        visible_count = metadata.get('visible_satellites_count', 0)
        feasible_count = metadata.get('feasible_satellites_count', 0)

        # 計算率
        filtering_rate = ((input_count - output_count) / input_count * 100) if input_count > 0 else 0
        output_feasible_rate = (feasible_count / output_count * 100) if output_count > 0 else 0
        input_feasible_rate = (feasible_count / input_count * 100) if input_count > 0 else 0

        print(f"📊 {processor_name} 結果:")
        print(f"   輸入衛星: {input_count} 顆")
        print(f"   輸出衛星: {output_count} 顆")
        print(f"   可見衛星: {visible_count} 顆")
        print(f"   可行衛星: {feasible_count} 顆")
        print(f"   篩選率: {filtering_rate:.1f}% (被篩選掉的)")
        print(f"   輸出可行率: {output_feasible_rate:.1f}% (輸出中可行的)")
        print(f"   總體可行率: {input_feasible_rate:.1f}% (相對於輸入)")

        # 檢查前幾個衛星的狀態
        if len(satellites) > 0:
            print(f"\n📋 前5個輸出衛星狀態:")
            for i, sat in enumerate(satellites[:5]):
                is_visible = sat.get('is_visible', False)
                is_feasible = sat.get('is_feasible', False)
                elevation = sat.get('elevation_deg', 0)
                constellation = sat.get('constellation', 'unknown')
                print(f"   {i+1}. {sat.get('name', 'N/A')} ({constellation}): "
                      f"可見={is_visible}, 可行={is_feasible}, 仰角={elevation:.1f}°")

        return {
            'input_count': input_count,
            'output_count': output_count,
            'visible_count': visible_count,
            'feasible_count': feasible_count,
            'filtering_rate': filtering_rate,
            'output_feasible_rate': output_feasible_rate,
            'input_feasible_rate': input_feasible_rate
        }

    except Exception as e:
        print(f"❌ {processor_name} 測試失敗: {e}")
        return None

def main():
    """主函數"""
    print("🔍 驗證篩選邏輯的正確性")
    print("重點：理解100%可行率是否正常")

    # 載入配置和數據
    config_path = "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    print(f"📊 總輸入數據: {len(input_data.get('satellites', []))} 顆衛星")

    # 測試標準處理器
    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
    std_result = test_small_sample(Stage2OrbitalComputingProcessor, "標準處理器", stage2_config, input_data, 50)

    # 測試混合處理器
    from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
    hybrid_result = test_small_sample(HybridStage2Processor, "混合處理器", stage2_config, input_data, 50)

    # 對比分析
    if std_result and hybrid_result:
        print(f"\n📊 對比分析")
        print("=" * 60)
        print(f"{'指標':<20} {'標準版':<12} {'混合版':<12} {'差異':<10}")
        print("-" * 60)

        comparisons = [
            ('篩選率', 'filtering_rate'),
            ('輸出可行率', 'output_feasible_rate'),
            ('總體可行率', 'input_feasible_rate'),
            ('輸出數量', 'output_count'),
            ('可行數量', 'feasible_count')
        ]

        all_normal = True
        for name, key in comparisons:
            std_val = std_result[key]
            hyb_val = hybrid_result[key]

            if key in ['filtering_rate', 'output_feasible_rate', 'input_feasible_rate']:
                diff = hyb_val - std_val
                print(f"{name:<20} {std_val:<12.1f}% {hyb_val:<12.1f}% {diff:>+9.1f}%")

                # 檢查是否異常
                if key == 'output_feasible_rate' and abs(diff) > 10:
                    print(f"    ⚠️  {name}差異過大！")
                    all_normal = False
                elif key in ['filtering_rate', 'input_feasible_rate'] and abs(diff) > 5:
                    print(f"    ⚠️  {name}差異過大！")
                    all_normal = False
            else:
                diff = hyb_val - std_val
                print(f"{name:<20} {std_val:<12} {hyb_val:<12} {diff:>+10}")

        print(f"\n🤔 結論:")
        if all_normal:
            print("✅ 混合處理器的篩選邏輯正常")
            print("💡 100%輸出可行率是正常的，因為不可行的衛星已被篩選掉")
        else:
            print("❌ 混合處理器的篩選邏輯異常")

if __name__ == "__main__":
    main()