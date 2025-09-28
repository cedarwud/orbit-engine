#!/usr/bin/env python3
"""
詳細比對標準版和混合版的每個處理階段
找出導致結果差異的具體階段
"""

import os
import sys
import json
import time
import yaml
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def load_config():
    """載入配置"""
    config_path = "config/stage2_orbital_computing.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('stage2_orbital_computing', {})
    except Exception as e:
        print(f"⚠️ 配置載入失敗: {e}")
        return {}

def load_input_data():
    """載入階段一輸出"""
    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_stage_results(stage_name, results_dict, processor_name):
    """分析單個階段的結果"""
    print(f"    📊 {stage_name} ({processor_name}):")

    if isinstance(results_dict, dict):
        total_satellites = len(results_dict)
        print(f"        衛星數量: {total_satellites}")

        # 檢查第一個衛星的數據結構
        if total_satellites > 0:
            first_satellite_id = list(results_dict.keys())[0]
            first_satellite_data = results_dict[first_satellite_id]

            if isinstance(first_satellite_data, dict):
                if 'positions' in first_satellite_data:
                    positions = first_satellite_data['positions']
                    print(f"        位置數量: {len(positions)} (每顆衛星)")

                    # 檢查位置數據結構
                    if positions and isinstance(positions[0], dict):
                        sample_pos = positions[0]
                        has_visibility = 'is_visible' in sample_pos
                        has_elevation = 'elevation_deg' in sample_pos
                        has_range = 'range_km' in sample_pos
                        print(f"        包含可見性標記: {has_visibility}")
                        print(f"        包含仰角數據: {has_elevation}")
                        print(f"        包含距離數據: {has_range}")

                        if has_elevation:
                            elevations = [pos.get('elevation_deg', 0) for pos in positions[:10]]
                            min_elev = min(elevations)
                            max_elev = max(elevations)
                            print(f"        仰角範圍 (前10個): {min_elev:.1f}° - {max_elev:.1f}°")

                elif 'is_visible' in first_satellite_data:
                    # VisibilityResult 對象
                    visible_count = sum(1 for result in results_dict.values()
                                      if hasattr(result, 'is_visible') and result.is_visible)
                    print(f"        可見衛星: {visible_count}")

                elif 'is_feasible' in first_satellite_data:
                    # FeasibilityResult 對象
                    feasible_count = sum(1 for result in results_dict.values()
                                       if hasattr(result, 'is_feasible') and result.is_feasible)
                    print(f"        可行衛星: {feasible_count}")
    else:
        print(f"        數據類型: {type(results_dict)}")

def debug_standard_processor(config_dict, input_data):
    """調試標準處理器的每個階段"""
    print("🔬 調試標準處理器 (CPU版本)")
    print("="*60)

    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
    processor = Stage2OrbitalComputingProcessor(config=config_dict)

    # 提取TLE數據
    tle_data = processor._extract_tle_data(input_data)
    print(f"📂 階段0: TLE數據提取")
    print(f"    輸入衛星: {len(input_data.get('satellites', []))}")
    print(f"    提取衛星: {len(tle_data)}")

    # 階段1: SGP4軌道計算
    print(f"\n🚀 階段1: SGP4軌道計算")
    orbital_results = processor._perform_modular_orbital_calculations(tle_data)
    analyze_stage_results("軌道計算結果", orbital_results, "標準版")

    # 階段2: 座標轉換
    print(f"\n🌐 階段2: 座標轉換")
    converted_results = processor._perform_coordinate_conversions(orbital_results)
    analyze_stage_results("座標轉換結果", converted_results, "標準版")

    # 階段3: 可見性分析
    print(f"\n👁️ 階段3: 可見性分析")
    visibility_results = processor._perform_modular_visibility_analysis(converted_results, tle_data)
    analyze_stage_results("可見性分析結果", visibility_results, "標準版")

    # 階段4: 鏈路可行性篩選
    print(f"\n🔗 階段4: 鏈路可行性篩選")
    feasibility_results = processor._perform_link_feasibility_filtering(visibility_results, tle_data)
    analyze_stage_results("可行性篩選結果", feasibility_results, "標準版")

    return {
        'tle_data': len(tle_data),
        'orbital_results': len(orbital_results),
        'converted_results': len(converted_results),
        'visibility_results': len(visibility_results),
        'feasibility_results': len(feasibility_results)
    }

def debug_hybrid_processor(config_dict, input_data):
    """調試混合處理器的每個階段"""
    print("\n🔬 調試混合處理器 (GPU+CPU版本)")
    print("="*60)

    from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
    processor = HybridStage2Processor(config=config_dict)

    # 提取TLE數據
    tle_data = processor._extract_tle_data(input_data)
    print(f"📂 階段0: TLE數據提取")
    print(f"    輸入衛星: {len(input_data.get('satellites', []))}")
    print(f"    提取衛星: {len(tle_data)}")

    # 階段1: SGP4軌道計算 (混合版使用優化方法)
    print(f"\n🚀 階段1: SGP4軌道計算 (混合版)")
    orbital_results = processor._perform_modular_orbital_calculations(tle_data)
    analyze_stage_results("軌道計算結果", orbital_results, "混合版")

    # 階段2: 座標轉換 (混合版使用GPU優化)
    print(f"\n🌐 階段2: 座標轉換 (混合版)")
    converted_results = processor._perform_coordinate_conversions(orbital_results)
    analyze_stage_results("座標轉換結果", converted_results, "混合版")

    # 階段3: 可見性分析 (混合版繼承標準版)
    print(f"\n👁️ 階段3: 可見性分析 (混合版)")
    visibility_results = processor._perform_modular_visibility_analysis(converted_results, tle_data)
    analyze_stage_results("可見性分析結果", visibility_results, "混合版")

    # 階段4: 鏈路可行性篩選 (混合版繼承標準版)
    print(f"\n🔗 階段4: 鏈路可行性篩選 (混合版)")
    feasibility_results = processor._perform_link_feasibility_filtering(visibility_results, tle_data)
    analyze_stage_results("可行性篩選結果", feasibility_results, "混合版")

    return {
        'tle_data': len(tle_data),
        'orbital_results': len(orbital_results),
        'converted_results': len(converted_results),
        'visibility_results': len(visibility_results),
        'feasibility_results': len(feasibility_results)
    }

def compare_results(standard_stats, hybrid_stats):
    """比較兩個版本的統計結果"""
    print(f"\n📊 階段比較結果")
    print("="*80)
    print(f"{'階段':<20} {'標準版':<15} {'混合版':<15} {'差異':<15} {'差異率':<10}")
    print("-" * 80)

    stages = [
        ('TLE數據提取', 'tle_data'),
        ('SGP4軌道計算', 'orbital_results'),
        ('座標轉換', 'converted_results'),
        ('可見性分析', 'visibility_results'),
        ('可行性篩選', 'feasibility_results')
    ]

    for stage_name, key in stages:
        std_count = standard_stats.get(key, 0)
        hyb_count = hybrid_stats.get(key, 0)
        diff = hyb_count - std_count
        diff_rate = (diff / std_count * 100) if std_count > 0 else 0

        print(f"{stage_name:<20} {std_count:<15} {hyb_count:<15} {diff:<15} {diff_rate:>8.1f}%")

        # 標記問題階段
        if abs(diff_rate) > 10:  # 差異超過10%
            print(f"    ⚠️  差異過大！{stage_name}可能有問題")

def main():
    """主函數"""
    print("🔍 階段二處理器逐階段調試比較")
    print("找出標準版和混合版結果差異的根本原因")

    # 載入配置和數據
    config_dict = load_config()
    input_data = load_input_data()

    print(f"📊 輸入數據: {len(input_data.get('satellites', []))} 顆衛星")

    try:
        # 調試標準處理器
        standard_stats = debug_standard_processor(config_dict, input_data)

        # 調試混合處理器
        hybrid_stats = debug_hybrid_processor(config_dict, input_data)

        # 比較結果
        compare_results(standard_stats, hybrid_stats)

    except Exception as e:
        print(f"❌ 調試過程失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()