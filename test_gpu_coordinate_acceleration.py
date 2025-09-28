#!/usr/bin/env python3
"""
測試GPU座標轉換加速效果
"""

import os
import sys
import json
import yaml
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_gpu_coordinate_acceleration(sample_size=1000):
    """測試GPU座標轉換加速效果"""
    print(f"🔬 測試GPU座標轉換加速 (樣本: {sample_size})")
    print("=" * 60)

    # 載入配置和數據
    config_path = project_root / "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stage2_config = config.get('stage2_orbital_computing', {})

    # 檢查可用的文件
    possible_paths = [
        "data/outputs/stage1/tle_data_loading_output_20250928_034102.json",
        "data/outputs/stage1/tle_data_loading_output_20250928_033123.json",
        "data/outputs/stage1/tle_data_loading_output_20250928_030755.json"
    ]

    stage1_output_path = None
    for path in possible_paths:
        full_path = project_root / path
        if full_path.exists():
            stage1_output_path = full_path
            break

    if stage1_output_path is None:
        # 尋找任何可用的stage1輸出文件
        import glob
        stage1_files = glob.glob(str(project_root / "data/outputs/stage1/*.json"))
        if stage1_files:
            stage1_output_path = Path(stage1_files[0])
        else:
            print("❌ 找不到任何stage1輸出文件")
            return
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # 準備測試樣本
    test_sample = input_data.copy()
    test_sample['satellites'] = input_data['satellites'][:sample_size]
    actual_size = len(test_sample['satellites'])
    print(f"📊 測試數據: {actual_size} 顆衛星")

    try:
        # 第一階段：標準軌道計算（兩個方案都相同）
        print(f"\n🔬 步驟1: 標準SGP4軌道計算...")
        orbital_results = perform_sgp4_calculation(stage2_config, test_sample)
        print(f"✅ 軌道計算完成: {len(orbital_results)} 顆衛星")

        if len(orbital_results) == 0:
            print("❌ 軌道計算失敗，無法進行座標轉換測試")
            return

        # 測試標準座標轉換
        print(f"\n🔬 測試標準座標轉換...")
        std_coord_result = test_standard_coordinate_conversion(stage2_config, orbital_results)

        # 測試GPU座標轉換
        print(f"\n🔬 測試GPU座標轉換...")
        gpu_coord_result = test_gpu_coordinate_conversion(stage2_config, orbital_results)

        # 比較結果
        if std_coord_result and gpu_coord_result:
            compare_coordinate_results(std_coord_result, gpu_coord_result)
        else:
            print("❌ 無法完成比較 - 某個座標轉換測試失敗")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def perform_sgp4_calculation(config_dict, input_data):
    """執行標準SGP4計算"""
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

        processor = Stage2OrbitalComputingProcessor(config=config_dict)

        # 提取TLE數據
        tle_data = processor._extract_tle_data(input_data)

        # 執行軌道計算
        orbital_results = processor._perform_modular_orbital_calculations(tle_data)

        return orbital_results

    except Exception as e:
        print(f"❌ SGP4計算失敗: {e}")
        return {}

def test_standard_coordinate_conversion(config_dict, orbital_results):
    """測試標準座標轉換"""
    try:
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

        processor = Stage2OrbitalComputingProcessor(config=config_dict)

        start_time = time.time()
        converted_results = processor._perform_coordinate_conversions(orbital_results)
        execution_time = time.time() - start_time

        conversion_count = len(converted_results)

        print(f"📊 標準座標轉換結果:")
        print(f"   執行時間: {execution_time:.1f} 秒")
        print(f"   轉換衛星: {conversion_count} 顆")
        print(f"   平均每顆: {execution_time/conversion_count*1000:.1f} 毫秒" if conversion_count > 0 else "   平均每顆: N/A")

        return {
            'method': '標準座標轉換',
            'execution_time': execution_time,
            'conversion_count': conversion_count,
            'converted_results': converted_results,
            'success': True
        }

    except Exception as e:
        print(f"❌ 標準座標轉換失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_gpu_coordinate_conversion(config_dict, orbital_results):
    """測試GPU座標轉換"""
    try:
        from stages.stage2_orbital_computing.gpu_coordinate_converter import GPUCoordinateConverter

        # 檢查GPU可用性
        try:
            import cupy as cp
            gpu_available = True
            device_info = f"GPU: {cp.cuda.Device().name.decode()}"
        except ImportError:
            gpu_available = False
            device_info = "GPU: Not available (CuPy not installed)"

        print(f"   {device_info}")

        # 初始化GPU座標轉換器
        gpu_converter = GPUCoordinateConverter(
            ground_station_lat=config_dict.get('ground_station', {}).get('latitude', 25.0),
            ground_station_lon=config_dict.get('ground_station', {}).get('longitude', 121.0),
            ground_station_alt=config_dict.get('ground_station', {}).get('altitude', 100.0),
            enable_gpu=gpu_available
        )

        start_time = time.time()

        # 準備批次數據
        positions_batch = []
        timestamps_batch = []

        for satellite_id, orbit_result in orbital_results.items():
            for position in orbit_result.positions:
                positions_batch.append([position.x, position.y, position.z])
                timestamps_batch.append(position.timestamp)

        # 執行GPU批次轉換
        if len(positions_batch) > 0:
            batch_result = gpu_converter.batch_convert(positions_batch, timestamps_batch)
            conversion_count = len(positions_batch)
        else:
            batch_result = None
            conversion_count = 0

        execution_time = time.time() - start_time

        print(f"📊 GPU座標轉換結果:")
        print(f"   執行時間: {execution_time:.1f} 秒")
        print(f"   轉換位置: {conversion_count} 個")
        print(f"   平均每個: {execution_time/conversion_count*1000:.1f} 毫秒" if conversion_count > 0 else "   平均每個: N/A")
        print(f"   GPU使用: {'是' if batch_result and batch_result.gpu_used else '否'}")

        return {
            'method': 'GPU座標轉換',
            'execution_time': execution_time,
            'conversion_count': conversion_count,
            'batch_result': batch_result,
            'gpu_used': batch_result.gpu_used if batch_result else False,
            'success': True
        }

    except Exception as e:
        print(f"❌ GPU座標轉換失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_coordinate_results(std_result, gpu_result):
    """比較座標轉換結果"""
    print(f"\n📊 座標轉換性能比較")
    print("=" * 60)

    # 性能比較
    time_ratio = std_result['execution_time'] / gpu_result['execution_time'] if gpu_result['execution_time'] > 0 else 0
    time_saved = std_result['execution_time'] - gpu_result['execution_time']

    print(f"標準轉換時間:   {std_result['execution_time']:.1f} 秒")
    print(f"GPU轉換時間:    {gpu_result['execution_time']:.1f} 秒")
    print(f"時間節省:       {time_saved:+.1f} 秒")
    print(f"性能提升:       {time_ratio:.2f}x")

    # 數量比較
    print(f"標準轉換數量:   {std_result['conversion_count']}")
    print(f"GPU轉換數量:    {gpu_result['conversion_count']}")

    # GPU使用情況
    if gpu_result.get('gpu_used', False):
        print(f"GPU加速:        ✅ 成功使用GPU")
        if time_ratio > 2.0:
            print(f"🚀 GPU座標轉換顯著提升性能!")
        elif time_ratio > 1.2:
            print(f"⚡ GPU座標轉換有明顯性能提升")
        else:
            print(f"⚠️ GPU座標轉換性能提升有限")
    else:
        print(f"GPU加速:        ❌ 未使用GPU (回退到CPU)")

    print(f"\n🎯 GPU座標轉換結論:")
    if gpu_result.get('gpu_used', False) and time_ratio > 1.5:
        print("✅ GPU座標轉換成功提升性能!")
        print("💡 建議：在混合處理器中啟用GPU座標轉換")
    elif gpu_result.get('gpu_used', False):
        print("⚡ GPU座標轉換有輕微性能提升")
        print("💡 建議：考慮在大規模數據時啟用GPU座標轉換")
    else:
        print("❌ GPU座標轉換未能啟用")
        print("💡 建議：檢查GPU環境配置（CuPy/CUDA安裝）")

if __name__ == "__main__":
    test_gpu_coordinate_acceleration(sample_size=1000)