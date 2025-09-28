#!/usr/bin/env python3
"""
調試並行SGP4計算器 - 找出0顆衛星輸出的問題
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

def test_parallel_sgp4_directly(sample_size=10):
    """直接測試並行SGP4計算器"""
    print(f"🔬 直接測試並行SGP4計算器 (樣本: {sample_size})")
    print("=" * 60)

    # 載入配置和數據
    config_path = "config/stage2_orbital_computing.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    # 準備測試樣本
    test_satellites = input_data['satellites'][:sample_size]
    print(f"📊 測試數據: {len(test_satellites)} 顆衛星")

    try:
        # 導入並行SGP4計算器
        from stages.stage2_orbital_computing.parallel_sgp4_calculator import ParallelSGP4Calculator, ParallelConfig

        # 初始化並行計算器
        config = ParallelConfig(
            enable_gpu=False,  # 先測試CPU版本
            enable_multiprocessing=True,
            cpu_workers=4,
            memory_limit_gb=4.0
        )
        parallel_sgp4 = ParallelSGP4Calculator(config)

        # 準備時間序列
        print(f"\n🔬 準備時間序列...")
        time_series = []
        start_time = datetime.now(timezone.utc)
        for minutes in range(0, 120, 15):  # 每15分鐘一個點，共8個點
            time_point = start_time + timedelta(minutes=minutes)
            time_series.append(time_point)

        print(f"   時間點數: {len(time_series)}")
        print(f"   開始時間: {time_series[0]}")
        print(f"   結束時間: {time_series[-1]}")

        # 執行並行計算
        print(f"\n🚀 執行並行SGP4計算...")
        results = parallel_sgp4.batch_calculate_parallel(test_satellites, time_series)

        # 分析結果
        print(f"\n📊 計算結果分析:")
        print(f"   輸入衛星數: {len(test_satellites)}")
        print(f"   輸出結果數: {len(results)}")
        print(f"   成功率: {len(results)/len(test_satellites)*100:.1f}%")

        if len(results) > 0:
            # 檢查結果結構
            first_result = next(iter(results.values()))
            print(f"\n🔍 結果結構檢查:")
            print(f"   結果鍵: {list(first_result.keys())}")

            if 'sgp4_positions' in first_result:
                positions = first_result['sgp4_positions']
                print(f"   SGP4位置數: {len(positions)}")
                if len(positions) > 0:
                    first_pos = positions[0]
                    print(f"   第一個位置類型: {type(first_pos)}")
                    if hasattr(first_pos, 'x'):
                        print(f"   位置坐標: ({first_pos.x:.2f}, {first_pos.y:.2f}, {first_pos.z:.2f})")

            # 檢查前3個結果
            print(f"\n📋 前3個結果詳情:")
            for i, (sat_id, result) in enumerate(list(results.items())[:3]):
                successful = result.get('calculation_successful', False)
                pos_count = len(result.get('sgp4_positions', []))
                method = result.get('calculation_method', 'unknown')
                print(f"   {i+1}. {sat_id}: 成功={successful}, 位置數={pos_count}, 方法={method}")

        else:
            print("❌ 沒有任何計算結果！")
            print("需要檢查:")
            print("   1. TLE數據格式是否正確")
            print("   2. 時間序列是否有效")
            print("   3. SGP4計算是否有錯誤")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_tle_data_format(sample_size=3):
    """檢查TLE數據格式"""
    print(f"\n🔍 檢查TLE數據格式 (前{sample_size}顆)")
    print("-" * 60)

    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    test_satellites = input_data['satellites'][:sample_size]

    for i, sat in enumerate(test_satellites):
        print(f"\n衛星 {i+1}:")
        print(f"   ID: {sat.get('satellite_id', 'missing')}")
        print(f"   名稱: {sat.get('name', 'missing')}")
        print(f"   TLE Line 1: {sat.get('tle_line1', 'missing')}")
        print(f"   TLE Line 2: {sat.get('tle_line2', 'missing')}")

        # 檢查TLE格式有效性
        line1 = sat.get('tle_line1', '')
        line2 = sat.get('tle_line2', '')

        if len(line1) != 69:
            print(f"   ⚠️ TLE Line 1 長度錯誤: {len(line1)} (應為69)")
        if len(line2) != 69:
            print(f"   ⚠️ TLE Line 2 長度錯誤: {len(line2)} (應為69)")

def test_sgp4_engine_directly(sample_size=3):
    """直接測試SGP4引擎"""
    print(f"\n🔬 直接測試SGP4引擎 (前{sample_size}顆)")
    print("-" * 60)

    try:
        from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine

        # 初始化SGP4引擎
        sgp4_engine = SGP4OrbitalEngine(
            observer_coordinates=None,
            eci_only_mode=True
        )

        stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
        with open(stage1_output_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        test_satellites = input_data['satellites'][:sample_size]
        test_time = datetime.now(timezone.utc)

        for i, sat in enumerate(test_satellites):
            sat_id = sat.get('satellite_id', f'sat_{i}')
            line1 = sat.get('tle_line1', '')
            line2 = sat.get('tle_line2', '')

            print(f"\n測試衛星 {sat_id}:")

            try:
                # 解析TLE epoch時間
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])

                if epoch_year < 57:
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year

                epoch_time = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)

                # 構建SGP4引擎期望的數據格式
                sgp4_data = {
                    'line1': line1,
                    'line2': line2,
                    'satellite_name': sat.get('name', 'Satellite'),
                    'epoch_datetime': epoch_time
                }

                # 計算位置
                result = sgp4_engine.calculate_position(sgp4_data, test_time)

                if result and result.calculation_successful:
                    print(f"   ✅ 計算成功")
                    print(f"   位置: ({result.position.x:.2f}, {result.position.y:.2f}, {result.position.z:.2f})")
                    print(f"   速度: ({result.velocity.x:.2f}, {result.velocity.y:.2f}, {result.velocity.z:.2f})")
                else:
                    print(f"   ❌ 計算失敗")
                    if result:
                        print(f"   錯誤: {result.calculation_error}")

            except Exception as e:
                print(f"   ❌ 處理失敗: {e}")

    except Exception as e:
        print(f"❌ SGP4引擎測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    print("🔍 並行SGP4計算器調試")
    print("目標：找出為什麼產生0顆衛星輸出")

    # 步驟1: 檢查TLE數據格式
    test_tle_data_format(sample_size=3)

    # 步驟2: 直接測試SGP4引擎
    test_sgp4_engine_directly(sample_size=3)

    # 步驟3: 測試並行SGP4計算器
    test_parallel_sgp4_directly(sample_size=10)

if __name__ == "__main__":
    main()