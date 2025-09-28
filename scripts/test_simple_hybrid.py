#!/usr/bin/env python3
"""
測試正確設計的簡潔混合處理器
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

def test_simple_hybrid_processor(sample_size=None):
    """測試簡潔混合處理器"""
    if sample_size is None:
        print(f"🔬 測試簡潔混合處理器 (全量數據)")
    else:
        print(f"🔬 測試簡潔混合處理器 (樣本: {sample_size})")
    print("=" * 60)

    # 載入配置和數據
    config_path = project_root / "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    stage1_output_path = project_root / "data/outputs/stage1/tle_data_loading_output_20250928_030755.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # 準備測試樣本
    if sample_size is None:
        # 使用全量數據
        test_sample = input_data
        actual_size = len(input_data['satellites'])
        print(f"📊 全量測試數據: {actual_size} 顆衛星")
    else:
        # 使用指定樣本大小
        test_sample = input_data.copy()
        test_sample['satellites'] = input_data['satellites'][:sample_size]
        actual_size = len(test_sample['satellites'])
        print(f"📊 測試數據: {actual_size} 顆衛星")

    try:
        # 測試標準處理器
        print(f"\n🔬 測試標準處理器...")
        std_result = test_standard_processor(stage2_config, test_sample)

        # 測試簡潔混合處理器
        print(f"\n🔬 測試簡潔混合處理器...")
        hybrid_result = test_hybrid_processor(stage2_config, test_sample)

        # 比較結果
        if std_result and hybrid_result:
            compare_results(std_result, hybrid_result)
        else:
            print("❌ 無法完成比較 - 某個處理器測試失敗")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_standard_processor(config_dict, input_data):
    """測試標準處理器"""
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

        processor = Stage2OrbitalComputingProcessor(config=config_dict)
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

        output_count = len(satellites)
        visible_count = metadata.get('visible_satellites_count', 0)
        feasible_count = metadata.get('feasible_satellites_count', 0)

        print(f"📊 標準處理器結果:")
        print(f"   執行時間: {execution_time:.1f} 秒")
        print(f"   輸出衛星: {output_count} 顆")
        print(f"   可見衛星: {visible_count} 顆")
        print(f"   可行衛星: {feasible_count} 顆")

        return {
            'processor': '標準處理器',
            'execution_time': execution_time,
            'output_count': output_count,
            'visible_count': visible_count,
            'feasible_count': feasible_count,
            'success': True
        }

    except Exception as e:
        print(f"❌ 標準處理器失敗: {e}")
        return None

def test_hybrid_processor(config_dict, input_data):
    """測試簡潔混合處理器"""
    try:
        from stages.stage2_orbital_computing.hybrid_stage2_processor_simple import HybridStage2ProcessorSimple

        processor = HybridStage2ProcessorSimple(config=config_dict)
        start_time = time.time()
        result = processor.execute(input_data)
        execution_time = time.time() - start_time

        # 提取結果
        if isinstance(result, dict) and result.get('success', False):
            data = result.get('data', {})
            satellites = data.get('satellites', [])
            metadata = data.get('metadata', {})
        else:
            print(f"⚠️ 混合處理器結果格式: {type(result)}")
            satellites = result.get('satellites', []) if isinstance(result, dict) else []
            metadata = result.get('metadata', {}) if isinstance(result, dict) else {}

        output_count = len(satellites)
        visible_count = metadata.get('visible_satellites_count', 0)
        feasible_count = metadata.get('feasible_satellites_count', 0)

        print(f"📊 簡潔混合處理器結果:")
        print(f"   執行時間: {execution_time:.1f} 秒")
        print(f"   輸出衛星: {output_count} 顆")
        print(f"   可見衛星: {visible_count} 顆")
        print(f"   可行衛星: {feasible_count} 顆")

        performance_stats = result.get('performance_stats', {})
        if performance_stats.get('parallel_processing_used', False):
            sgp4_time = performance_stats.get('sgp4_calculation_time', 0)
            print(f"   SGP4並行時間: {sgp4_time:.1f} 秒")
            print(f"   ⚡ 使用了並行SGP4優化")

        return {
            'processor': '簡潔混合處理器',
            'execution_time': execution_time,
            'output_count': output_count,
            'visible_count': visible_count,
            'feasible_count': feasible_count,
            'performance_stats': performance_stats,
            'success': True
        }

    except Exception as e:
        print(f"❌ 簡潔混合處理器失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_results(std_result, hybrid_result):
    """比較兩個結果"""
    print(f"\n📊 結果比較")
    print("=" * 60)

    # 性能比較
    time_ratio = std_result['execution_time'] / hybrid_result['execution_time'] if hybrid_result['execution_time'] > 0 else 0
    print(f"性能提升: {time_ratio:.1f}x 倍速度")

    # 數量比較
    metrics = ['output_count', 'visible_count', 'feasible_count']
    all_same = True

    for metric in metrics:
        std_val = std_result[metric]
        hybrid_val = hybrid_result[metric]
        diff = hybrid_val - std_val

        print(f"{metric}: 標準={std_val}, 混合={hybrid_val}, 差異={diff:+d}")

        if diff != 0:
            all_same = False

    print(f"\n🎯 測試結論:")
    if all_same:
        print("✅ 簡潔混合處理器與標準處理器產生完全相同的結果！")
        print("✅ 正確的設計原則：只優化計算，不改變業務邏輯")
        print(f"🚀 性能提升: {time_ratio:.1f}x")
    else:
        print("❌ 結果存在差異，需要進一步檢查")

def main():
    """主函數"""
    print("🔍 測試正確設計的簡潔混合處理器")
    print("設計原則：只優化SGP4計算，其他完全使用標準版邏輯")

    test_simple_hybrid_processor(sample_size=None)  # 使用全量數據

if __name__ == "__main__":
    main()