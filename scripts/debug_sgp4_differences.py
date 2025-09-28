#!/usr/bin/env python3
"""
調試SGP4計算差異 - 找出標準版和並行版的細微差異
"""

import os
import sys
import json
import yaml
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def compare_sgp4_calculations(sample_size=10):
    """比較標準SGP4和並行SGP4的計算結果"""
    print(f"🔬 比較SGP4計算結果差異 (樣本: {sample_size})")
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

    print(f"📊 測試數據: {len(test_sample['satellites'])} 顆衛星")

    try:
        # 獲取標準版SGP4計算結果
        print(f"\n🔬 測試標準版SGP4計算...")
        std_orbital_results = get_standard_sgp4_results(stage2_config, test_sample)

        # 獲取並行版SGP4計算結果
        print(f"\n🔬 測試並行版SGP4計算...")
        parallel_orbital_results = get_parallel_sgp4_results(test_sample)

        # 比較結果
        if std_orbital_results and parallel_orbital_results:
            compare_orbital_results(std_orbital_results, parallel_orbital_results)
        else:
            print("❌ 無法完成比較 - 某個計算失敗")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def get_standard_sgp4_results(config_dict, input_data):
    """獲取標準版SGP4計算結果"""
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

        processor = Stage2OrbitalComputingProcessor(config=config_dict)

        # 提取TLE數據
        tle_data = processor._extract_tle_data(input_data)
        print(f"   TLE數據: {len(tle_data)} 顆")

        # 執行標準SGP4計算
        orbital_results = processor._perform_modular_orbital_calculations(tle_data)
        print(f"   標準SGP4結果: {len(orbital_results)} 顆")

        return orbital_results

    except Exception as e:
        print(f"❌ 標準版SGP4計算失敗: {e}")
        return None

def get_parallel_sgp4_results(input_data):
    """獲取並行版SGP4計算結果"""
    try:
        from stages.stage2_orbital_computing.parallel_sgp4_calculator import ParallelSGP4Calculator, ParallelConfig

        # 初始化並行計算器（不使用GPU，避免GPU差異）
        config = ParallelConfig(
            enable_gpu=False,
            enable_multiprocessing=True,
            cpu_workers=4,
            memory_limit_gb=4.0
        )
        parallel_sgp4 = ParallelSGP4Calculator(config)

        # 準備測試數據
        satellites = input_data['satellites']

        # 準備時間序列
        time_series = []
        start_time = datetime.now(timezone.utc)
        for minutes in range(0, 120, 15):  # 與簡潔混合處理器使用相同的時間序列
            time_point = start_time + timedelta(minutes=minutes)
            time_series.append(time_point)

        print(f"   時間點數: {len(time_series)}")

        # 執行並行計算
        parallel_results = parallel_sgp4.batch_calculate_parallel(satellites, time_series)
        print(f"   並行SGP4結果: {len(parallel_results)} 顆")

        return parallel_results

    except Exception as e:
        print(f"❌ 並行版SGP4計算失敗: {e}")
        return None

def compare_orbital_results(std_results, parallel_results):
    """比較軌道計算結果"""
    print(f"\n📊 SGP4計算結果比較")
    print("=" * 80)

    # 找到共同的衛星ID
    std_ids = set(std_results.keys())
    parallel_ids = set(parallel_results.keys())
    common_ids = std_ids & parallel_ids

    print(f"標準版衛星數: {len(std_ids)}")
    print(f"並行版衛星數: {len(parallel_ids)}")
    print(f"共同衛星數: {len(common_ids)}")

    if len(common_ids) == 0:
        print("❌ 沒有共同的衛星ID可以比較")
        return

    # 比較前3個共同衛星的計算結果
    sample_ids = list(common_ids)[:3]

    for sat_id in sample_ids:
        print(f"\n🔍 比較衛星 {sat_id}")
        print("-" * 60)

        std_result = std_results[sat_id]
        parallel_result = parallel_results[sat_id]

        # 標準版結果分析
        if hasattr(std_result, 'positions'):
            std_positions = std_result.positions
            std_success = std_result.calculation_successful
            print(f"標準版: 成功={std_success}, 位置數={len(std_positions)}")

            if len(std_positions) > 0:
                first_pos = std_positions[0]
                print(f"   第一個位置: ({first_pos.x:.6f}, {first_pos.y:.6f}, {first_pos.z:.6f})")
        else:
            print(f"標準版: 格式異常 - {type(std_result)}")

        # 並行版結果分析
        if isinstance(parallel_result, dict) and 'sgp4_positions' in parallel_result:
            parallel_positions = parallel_result['sgp4_positions']
            parallel_success = parallel_result.get('calculation_successful', False)
            print(f"並行版: 成功={parallel_success}, 位置數={len(parallel_positions)}")

            if len(parallel_positions) > 0:
                first_pos = parallel_positions[0]
                print(f"   第一個位置: ({first_pos.x:.6f}, {first_pos.y:.6f}, {first_pos.z:.6f})")
        else:
            print(f"並行版: 格式異常 - {type(parallel_result)}")

        # 計算位置差異
        if (hasattr(std_result, 'positions') and len(std_result.positions) > 0 and
            isinstance(parallel_result, dict) and 'sgp4_positions' in parallel_result and
            len(parallel_result['sgp4_positions']) > 0):

            std_pos = std_result.positions[0]
            parallel_pos = parallel_result['sgp4_positions'][0]

            x_diff = abs(std_pos.x - parallel_pos.x)
            y_diff = abs(std_pos.y - parallel_pos.y)
            z_diff = abs(std_pos.z - parallel_pos.z)

            total_diff = (x_diff**2 + y_diff**2 + z_diff**2)**0.5

            print(f"   位置差異: X={x_diff:.6f}, Y={y_diff:.6f}, Z={z_diff:.6f}")
            print(f"   總差異: {total_diff:.6f} km")

            if total_diff > 0.001:  # 超過1米
                print(f"   ⚠️ 位置差異過大！")

def test_time_series_consistency():
    """測試時間序列一致性"""
    print(f"\n🔬 測試時間序列一致性")
    print("-" * 60)

    # 測試標準版如何生成時間序列
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

        config_path = "config/stage2_orbital_computing.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        stage2_config = config.get('stage2_orbital_computing', {})

        processor = Stage2OrbitalComputingProcessor(config=stage2_config)

        # 檢查標準版的時間配置
        print(f"標準版配置:")
        print(f"   時間範圍: {stage2_config.get('time_range_hours', 'unknown')} 小時")
        print(f"   時間間隔: {stage2_config.get('time_step_minutes', 'unknown')} 分鐘")

        # 生成標準版時間序列
        start_time = datetime.now(timezone.utc)
        time_range_hours = stage2_config.get('time_range_hours', 2)
        time_step_minutes = stage2_config.get('time_step_minutes', 1)

        std_time_series = []
        current_time = start_time
        end_time = start_time + timedelta(hours=time_range_hours)

        while current_time <= end_time:
            std_time_series.append(current_time)
            current_time += timedelta(minutes=time_step_minutes)

        print(f"標準版時間序列: {len(std_time_series)} 個點")
        print(f"   開始: {std_time_series[0]}")
        print(f"   結束: {std_time_series[-1]}")

        # 並行版時間序列（來自簡潔混合處理器）
        parallel_time_series = []
        for minutes in range(0, 120, 1):  # 來自 _prepare_time_series
            time_point = start_time + timedelta(minutes=minutes)
            parallel_time_series.append(time_point)

        print(f"並行版時間序列: {len(parallel_time_series)} 個點")
        print(f"   開始: {parallel_time_series[0]}")
        print(f"   結束: {parallel_time_series[-1]}")

        if len(std_time_series) != len(parallel_time_series):
            print(f"⚠️ 時間序列長度不同！這可能是差異的根源")

    except Exception as e:
        print(f"❌ 時間序列測試失敗: {e}")

def main():
    """主函數"""
    print("🔍 SGP4計算差異調試")
    print("目標：找出簡潔混合處理器結果差異的根源")

    # 步驟1: 測試時間序列一致性
    test_time_series_consistency()

    # 步驟2: 比較SGP4計算結果
    compare_sgp4_calculations(sample_size=5)

if __name__ == "__main__":
    main()