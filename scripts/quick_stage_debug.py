#!/usr/bin/env python3
"""
快速比較標準版和混合版的關鍵階段結果
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

def test_processor_stages(processor_class, processor_name, config_dict, input_data):
    """測試處理器的各個階段"""
    print(f"\n🔬 測試 {processor_name}")
    print("-" * 50)

    try:
        # 初始化處理器
        if processor_name == "標準處理器":
            processor = processor_class(config=config_dict)
        else:
            processor = processor_class(config=config_dict)

        # 提取TLE數據
        tle_data = processor._extract_tle_data(input_data)
        print(f"📂 TLE數據: {len(tle_data)} 顆衛星")

        # 階段1: SGP4軌道計算
        orbital_results = processor._perform_modular_orbital_calculations(tle_data)
        print(f"🚀 軌道計算: {len(orbital_results)} 顆衛星")

        # 階段2: 座標轉換
        converted_results = processor._perform_coordinate_conversions(orbital_results)
        print(f"🌐 座標轉換: {len(converted_results)} 顆衛星")

        # 檢查第一顆衛星的轉換結果
        if converted_results:
            first_sat_id = list(converted_results.keys())[0]
            first_sat_data = converted_results[first_sat_id]
            if 'positions' in first_sat_data:
                positions = first_sat_data['positions']
                print(f"    每顆衛星位置數: {len(positions)}")

                # 檢查前幾個位置的仰角
                if positions:
                    elevations = []
                    visible_count = 0
                    for pos in positions[:20]:  # 檢查前20個位置
                        if 'elevation_deg' in pos:
                            elev = pos['elevation_deg']
                            elevations.append(elev)
                            if pos.get('is_visible', False):
                                visible_count += 1

                    if elevations:
                        avg_elev = sum(elevations) / len(elevations)
                        min_elev = min(elevations)
                        max_elev = max(elevations)
                        print(f"    仰角範圍: {min_elev:.1f}° - {max_elev:.1f}° (平均: {avg_elev:.1f}°)")
                        print(f"    前20個位置中可見: {visible_count}")

        # 階段3: 可見性分析
        visibility_results = processor._perform_modular_visibility_analysis(converted_results, tle_data)
        visible_count = sum(1 for result in visibility_results.values()
                          if hasattr(result, 'is_visible') and result.is_visible)
        print(f"👁️ 可見性分析: {len(visibility_results)} 顆衛星, {visible_count} 顆可見")

        # 階段4: 鏈路可行性篩選
        feasibility_results = processor._perform_link_feasibility_filtering(visibility_results, tle_data)
        feasible_count = sum(1 for result in feasibility_results.values()
                           if hasattr(result, 'is_feasible') and result.is_feasible)
        print(f"🔗 可行性篩選: {len(feasibility_results)} 顆衛星, {feasible_count} 顆可行")

        return {
            'tle_data': len(tle_data),
            'orbital_results': len(orbital_results),
            'converted_results': len(converted_results),
            'visible_count': visible_count,
            'feasible_count': feasible_count
        }

    except Exception as e:
        print(f"❌ {processor_name} 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函數"""
    print("🔍 快速階段比較 - 標準版 vs 混合版")

    # 載入配置和數據
    config_dict = load_config()

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    print(f"📊 輸入數據: {len(input_data.get('satellites', []))} 顆衛星")

    # 測試標準處理器
    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
    standard_results = test_processor_stages(Stage2OrbitalComputingProcessor, "標準處理器", config_dict, input_data)

    # 測試混合處理器
    from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
    hybrid_results = test_processor_stages(HybridStage2Processor, "混合處理器", config_dict, input_data)

    # 比較結果
    if standard_results and hybrid_results:
        print(f"\n📊 比較結果")
        print("=" * 60)
        print(f"{'階段':<15} {'標準版':<12} {'混合版':<12} {'差異':<10}")
        print("-" * 60)

        comparisons = [
            ('TLE數據', 'tle_data'),
            ('軌道計算', 'orbital_results'),
            ('座標轉換', 'converted_results'),
            ('可見衛星', 'visible_count'),
            ('可行衛星', 'feasible_count')
        ]

        for name, key in comparisons:
            std_val = standard_results.get(key, 0)
            hyb_val = hybrid_results.get(key, 0)
            diff = hyb_val - std_val

            print(f"{name:<15} {std_val:<12} {hyb_val:<12} {diff:>+10}")

            if key in ['visible_count', 'feasible_count'] and abs(diff) > std_val * 0.1:
                print(f"    ⚠️  {name}差異過大！")

if __name__ == "__main__":
    main()