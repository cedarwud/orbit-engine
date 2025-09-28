#!/usr/bin/env python3
"""
比較三個處理器版本的篩選結果
- 標準處理器 (CPU)
- 優化處理器 (GPU)
- 混合處理器 (GPU+CPU)
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

def load_stage2_config(config_path: str) -> dict:
    """載入階段二配置"""
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 提取階段二特定配置
        stage2_config = config.get('stage2_orbital_computing', {})
        return stage2_config
    except Exception as e:
        print(f"配置載入失敗: {e}")
        return {}

def run_processor_test(processor_name: str, processor_class, config_dict: dict, input_data: dict):
    """測試單個處理器"""
    print(f"\n{'='*60}")
    print(f"🔬 測試 {processor_name}")
    print(f"{'='*60}")

    try:
        # 初始化處理器
        print(f"⚡ 初始化 {processor_name}...")
        if processor_name == "標準處理器":
            processor = processor_class(config=config_dict)
        elif processor_name == "優化處理器":
            processor = processor_class(config_path=None, enable_optimization=True, **config_dict)
        else:  # 混合處理器
            processor = processor_class(config=config_dict)

        print(f"✅ {processor_name} 初始化完成")

        # 執行處理
        print(f"🚀 開始執行 {processor_name}...")
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

        visibility_rate = (visible_count / total_satellites * 100) if total_satellites > 0 else 0
        feasibility_rate = (feasible_count / total_satellites * 100) if total_satellites > 0 else 0

        print(f"📊 {processor_name} 結果:")
        print(f"   執行時間: {execution_time:.2f} 秒")
        print(f"   總衛星數: {total_satellites}")
        print(f"   可見衛星: {visible_count} ({visibility_rate:.1f}%)")
        print(f"   可行衛星: {feasible_count} ({feasibility_rate:.1f}%)")

        return {
            'processor_name': processor_name,
            'execution_time': execution_time,
            'total_satellites': total_satellites,
            'visible_count': visible_count,
            'feasible_count': feasible_count,
            'visibility_rate': visibility_rate,
            'feasibility_rate': feasibility_rate,
            'success': True
        }

    except Exception as e:
        print(f"❌ {processor_name} 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return {
            'processor_name': processor_name,
            'success': False,
            'error': str(e)
        }

def main():
    """主函數"""
    print("🔬 階段二處理器比較測試")
    print("比較標準、優化、混合三個版本的篩選結果")

    # 載入配置
    config_path = "config/stage2_orbital_computing.yaml"
    config_dict = load_stage2_config(config_path)
    print(f"📊 配置載入: Starlink={config_dict.get('constellation_elevation_thresholds', {}).get('starlink', 'N/A')}°, OneWeb={config_dict.get('constellation_elevation_thresholds', {}).get('oneweb', 'N/A')}°")

    # 載入階段一輸出
    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    print(f"📂 載入階段一輸出: {stage1_output_path}")

    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    print(f"✅ 階段一數據載入完成: {len(input_data.get('satellites', []))} 顆衛星")

    # 測試三個處理器版本
    results = []

    # 1. 標準處理器 (CPU)
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
        result = run_processor_test("標準處理器", Stage2OrbitalComputingProcessor, config_dict, input_data)
        results.append(result)
    except Exception as e:
        print(f"❌ 無法載入標準處理器: {e}")

    # 2. 優化處理器 (GPU)
    try:
        from stages.stage2_orbital_computing.optimized_stage2_processor import OptimizedStage2Processor
        result = run_processor_test("優化處理器", OptimizedStage2Processor, config_dict, input_data)
        results.append(result)
    except Exception as e:
        print(f"❌ 無法載入優化處理器: {e}")

    # 3. 混合處理器 (GPU+CPU)
    try:
        from stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
        result = run_processor_test("混合處理器", HybridStage2Processor, config_dict, input_data)
        results.append(result)
    except Exception as e:
        print(f"❌ 無法載入混合處理器: {e}")

    # 輸出比較結果
    print(f"\n{'='*80}")
    print("📊 處理器比較結果")
    print(f"{'='*80}")

    successful_results = [r for r in results if r.get('success', False)]

    if not successful_results:
        print("❌ 所有處理器測試都失敗了")
        return

    # 表格輸出
    print(f"{'處理器':<12} {'執行時間':<10} {'總數':<8} {'可見':<12} {'可行':<12} {'可見率':<8} {'可行率':<8}")
    print("-" * 80)

    for result in successful_results:
        if result['success']:
            print(f"{result['processor_name']:<12} "
                  f"{result['execution_time']:<10.1f} "
                  f"{result['total_satellites']:<8} "
                  f"{result['visible_count']:<12} "
                  f"{result['feasible_count']:<12} "
                  f"{result['visibility_rate']:<8.1f}% "
                  f"{result['feasibility_rate']:<8.1f}%")

    # 分析差異
    if len(successful_results) > 1:
        print(f"\n🔍 差異分析:")
        base_result = successful_results[0]

        for result in successful_results[1:]:
            if result['success']:
                vis_diff = result['visibility_rate'] - base_result['visibility_rate']
                feas_diff = result['feasibility_rate'] - base_result['feasibility_rate']
                time_ratio = base_result['execution_time'] / result['execution_time'] if result['execution_time'] > 0 else 0

                print(f"   {result['processor_name']} vs {base_result['processor_name']}:")
                print(f"      可見率差異: {vis_diff:+.1f}%")
                print(f"      可行率差異: {feas_diff:+.1f}%")
                print(f"      性能比例: {time_ratio:.1f}x")

if __name__ == "__main__":
    main()