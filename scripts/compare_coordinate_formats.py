#!/usr/bin/env python3
"""
比較標準版和GPU版座標轉換的輸出格式
找出導致篩選異常的數據格式差異
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

def test_coordinate_conversion_formats(sample_size=200):
    """比較座標轉換格式差異"""
    print(f"🔍 比較座標轉換格式 (樣本: {sample_size} 顆)")
    print("=" * 80)

    # 載入配置和數據
    config_path = "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # 準備測試樣本
    test_sample = input_data.copy()
    test_sample['satellites'] = input_data['satellites'][:sample_size]

    print(f"📊 測試樣本: {len(test_sample['satellites'])} 顆衛星")

    # 測試標準處理器的座標轉換
    print(f"\n🔬 測試標準處理器座標轉換...")
    std_orbital_results, std_converted_results = test_standard_coordinate_conversion(
        stage2_config, test_sample
    )

    # 測試混合處理器的座標轉換
    print(f"\n🔬 測試混合處理器座標轉換...")
    hybrid_orbital_results, hybrid_converted_results = test_hybrid_coordinate_conversion(
        stage2_config, test_sample
    )

    # 比較結果
    if std_converted_results and hybrid_converted_results:
        compare_conversion_formats(std_converted_results, hybrid_converted_results)
    else:
        print("❌ 無法完成格式比較 - 某個轉換失敗")

def test_standard_coordinate_conversion(config_dict, input_data):
    """測試標準處理器的座標轉換"""
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

        processor = Stage2OrbitalComputingProcessor(config=config_dict)

        # 提取TLE數據
        tle_data = processor._extract_tle_data(input_data)
        print(f"   TLE數據: {len(tle_data)} 顆")

        # 步驟1: 軌道計算
        orbital_results = processor._perform_modular_orbital_calculations(tle_data)
        print(f"   軌道計算: {len(orbital_results)} 顆")

        # 步驟2: 座標轉換
        converted_results = processor._perform_coordinate_conversions(orbital_results)
        print(f"   座標轉換: {len(converted_results)} 顆")

        return orbital_results, converted_results

    except Exception as e:
        print(f"❌ 標準處理器座標轉換失敗: {e}")
        return None, None

def test_hybrid_coordinate_conversion(config_dict, input_data):
    """測試混合處理器的座標轉換"""
    try:
        from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor

        processor = HybridStage2Processor(config=config_dict)

        # 提取TLE數據
        tle_data = processor._extract_tle_data(input_data)
        print(f"   TLE數據: {len(tle_data)} 顆")

        # 步驟1: 軌道計算 (混合版)
        orbital_results = processor._perform_modular_orbital_calculations(tle_data)
        print(f"   軌道計算: {len(orbital_results)} 顆")

        # 步驟2: 座標轉換 (混合版 - 會觸發GPU批次處理)
        converted_results = processor._perform_coordinate_conversions(orbital_results)
        print(f"   座標轉換: {len(converted_results)} 顆")

        return orbital_results, converted_results

    except Exception as e:
        print(f"❌ 混合處理器座標轉換失敗: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def compare_conversion_formats(std_results, hybrid_results):
    """比較兩種轉換結果的格式差異"""
    print(f"\n📊 座標轉換格式比較")
    print("=" * 80)

    print(f"標準版衛星數: {len(std_results)}")
    print(f"混合版衛星數: {len(hybrid_results)}")

    # 找到共同的衛星ID進行比較
    std_ids = set(std_results.keys())
    hybrid_ids = set(hybrid_results.keys())
    common_ids = std_ids & hybrid_ids

    print(f"共同衛星數: {len(common_ids)}")

    if len(common_ids) == 0:
        print("❌ 沒有共同的衛星ID可以比較")
        return

    # 選擇前3個衛星進行詳細比較
    sample_ids = list(common_ids)[:3]

    for sat_id in sample_ids:
        print(f"\n🔍 比較衛星 {sat_id}")
        print("-" * 60)

        std_sat = std_results[sat_id]
        hybrid_sat = hybrid_results[sat_id]

        # 比較頂層結構
        print(f"標準版結構鍵: {list(std_sat.keys()) if isinstance(std_sat, dict) else type(std_sat)}")
        print(f"混合版結構鍵: {list(hybrid_sat.keys()) if isinstance(hybrid_sat, dict) else type(hybrid_sat)}")

        # 比較位置數據
        std_positions = std_sat.get('positions', []) if isinstance(std_sat, dict) else []
        hybrid_positions = hybrid_sat.get('positions', []) if isinstance(hybrid_sat, dict) else []

        print(f"標準版位置數: {len(std_positions)}")
        print(f"混合版位置數: {len(hybrid_positions)}")

        if len(std_positions) > 0 and len(hybrid_positions) > 0:
            # 比較第一個位置的格式
            std_pos = std_positions[0]
            hybrid_pos = hybrid_positions[0]

            print(f"\n📋 第一個位置格式比較:")
            print(f"標準版位置鍵: {list(std_pos.keys()) if isinstance(std_pos, dict) else type(std_pos)}")
            print(f"混合版位置鍵: {list(hybrid_pos.keys()) if isinstance(hybrid_pos, dict) else type(hybrid_pos)}")

            # 比較關鍵字段
            key_fields = ['elevation_deg', 'azimuth_deg', 'range_km', 'is_visible']
            print(f"\n🔍 關鍵字段比較:")
            for field in key_fields:
                std_val = std_pos.get(field, "不存在") if isinstance(std_pos, dict) else "不是字典"
                hybrid_val = hybrid_pos.get(field, "不存在") if isinstance(hybrid_pos, dict) else "不是字典"

                print(f"   {field}:")
                print(f"      標準版: {std_val} ({type(std_val)})")
                print(f"      混合版: {hybrid_val} ({type(hybrid_val)})")

                if field == 'elevation_deg' and isinstance(std_val, (int, float)) and isinstance(hybrid_val, (int, float)):
                    diff = abs(float(std_val) - float(hybrid_val))
                    print(f"      差異: {diff:.6f}")

    # 統計總體差異
    print(f"\n📈 總體統計比較:")
    analyze_overall_differences(std_results, hybrid_results, common_ids)

def analyze_overall_differences(std_results, hybrid_results, common_ids):
    """分析總體差異"""
    std_elevations = []
    hybrid_elevations = []
    std_visible_count = 0
    hybrid_visible_count = 0

    for sat_id in list(common_ids)[:20]:  # 分析前20個
        std_sat = std_results[sat_id]
        hybrid_sat = hybrid_results[sat_id]

        std_positions = std_sat.get('positions', []) if isinstance(std_sat, dict) else []
        hybrid_positions = hybrid_sat.get('positions', []) if isinstance(hybrid_sat, dict) else []

        for pos in std_positions[:5]:  # 每個衛星取前5個位置
            if isinstance(pos, dict) and 'elevation_deg' in pos:
                std_elevations.append(pos['elevation_deg'])
                if pos.get('is_visible', False):
                    std_visible_count += 1

        for pos in hybrid_positions[:5]:
            if isinstance(pos, dict) and 'elevation_deg' in pos:
                hybrid_elevations.append(pos['elevation_deg'])
                if pos.get('is_visible', False):
                    hybrid_visible_count += 1

    if std_elevations and hybrid_elevations:
        std_avg = sum(std_elevations) / len(std_elevations)
        hybrid_avg = sum(hybrid_elevations) / len(hybrid_elevations)

        print(f"仰角統計 (前20衛星×5位置):")
        print(f"   標準版平均仰角: {std_avg:.2f}°")
        print(f"   混合版平均仰角: {hybrid_avg:.2f}°")
        print(f"   仰角差異: {abs(std_avg - hybrid_avg):.6f}°")

        print(f"可見性統計:")
        print(f"   標準版可見數: {std_visible_count}")
        print(f"   混合版可見數: {hybrid_visible_count}")
        print(f"   可見數差異: {hybrid_visible_count - std_visible_count}")

        if abs(std_avg - hybrid_avg) > 0.01:
            print("⚠️  仰角差異過大！")

        if abs(hybrid_visible_count - std_visible_count) > 5:
            print("⚠️  可見性統計差異過大！")

def main():
    """主函數"""
    print("🔍 座標轉換格式比較分析")
    print("目標：找出GPU批次處理導致篩選異常的原因")

    # 使用200顆衛星 - 確保觸發GPU批次處理
    test_coordinate_conversion_formats(sample_size=200)

if __name__ == "__main__":
    main()