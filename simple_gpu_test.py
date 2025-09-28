#!/usr/bin/env python3
"""
簡單的GPU座標轉換測試
"""

import sys
from pathlib import Path
import time
import numpy as np

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_gpu_availability():
    """測試GPU可用性"""
    print("🔬 GPU環境檢測")
    print("=" * 40)

    # 檢查CuPy
    try:
        import cupy as cp
        print("✅ CuPy: 已安裝")
        try:
            device = cp.cuda.Device()
            device_name = cp.cuda.runtime.getDeviceProperties(device.id)['name'].decode()
            mem_info = cp.cuda.runtime.memGetInfo()
            print(f"✅ GPU設備: {device.id} - {device_name}")
            print(f"✅ GPU記憶體: {mem_info[1] / 1024**3:.1f} GB (總量)")
            print(f"✅ GPU可用記憶體: {mem_info[0] / 1024**3:.1f} GB")
            cupy_available = True
        except Exception as e:
            print(f"⚠️ GPU設備無法訪問: {e}")
            cupy_available = False
    except ImportError:
        print("❌ CuPy: 未安裝")
        cupy_available = False

    # 檢查PyOpenCL
    try:
        import pyopencl as cl
        print("✅ PyOpenCL: 已安裝")
        try:
            platforms = cl.get_platforms()
            print(f"✅ OpenCL平台: {len(platforms)}個")
            opencl_available = True
        except Exception as e:
            print(f"⚠️ OpenCL平台無法訪問: {e}")
            opencl_available = False
    except ImportError:
        print("❌ PyOpenCL: 未安裝")
        opencl_available = False

    return cupy_available, opencl_available

def test_gpu_coordinate_converter():
    """測試GPU座標轉換器"""
    try:
        from stages.stage2_orbital_computing.gpu_coordinate_converter import GPUCoordinateConverter
        print("\n🔬 GPU座標轉換器測試")
        print("=" * 40)

        # 檢查GPU可用性
        cupy_available, opencl_available = test_gpu_availability()

        # 初始化GPU座標轉換器
        observer_location = {
            'latitude': 25.0,
            'longitude': 121.0,
            'altitude': 100.0
        }
        gpu_converter = GPUCoordinateConverter(
            observer_location=observer_location,
            enable_gpu=cupy_available
        )

        # 生成測試數據
        print(f"\n📊 生成測試數據...")
        n_positions = 1000

        # 模擬ECI座標 (地球周圍典型衛星位置，單位：公里)
        from stages.stage2_orbital_computing.coordinate_converter import Position3D

        positions = []
        timestamps = []

        base_time = "2025-09-28T12:00:00Z"

        for i in range(n_positions):
            # 生成典型LEO衛星軌道位置 (約400-800km高度)
            radius = 6371 + 400 + (i % 400)  # 地球半徑 + 高度
            angle1 = (i * 2.5) % 360  # 經度變化
            angle2 = 45 + (i * 0.1) % 90  # 緯度變化

            x = radius * np.cos(np.radians(angle1)) * np.cos(np.radians(angle2))
            y = radius * np.sin(np.radians(angle1)) * np.cos(np.radians(angle2))
            z = radius * np.sin(np.radians(angle2))

            # 創建Position3D對象
            position = Position3D(x=x, y=y, z=z)
            positions.append(position)

            # 時間序列 (每30秒一個點)
            time_offset = i * 30
            hour = 12 + (time_offset // 3600)
            minute = (time_offset % 3600) // 60
            second = time_offset % 60
            timestamp = f"2025-09-28T{hour:02d}:{minute:02d}:{second:02d}Z"
            timestamps.append(timestamp)

        print(f"✅ 測試數據: {len(positions)} 個位置")
        print(f"   位置範圍: {min([p.x for p in positions]):.1f} 到 {max([p.x for p in positions]):.1f} km")

        # 執行GPU批次轉換
        print(f"\n🚀 執行GPU批次視角計算...")
        start_time = time.time()

        try:
            batch_result = gpu_converter.gpu_batch_calculate_look_angles(positions)
            execution_time = time.time() - start_time

            print(f"✅ 轉換完成!")
            print(f"   執行時間: {execution_time:.3f} 秒")
            print(f"   處理速度: {len(positions)/execution_time:.0f} 位置/秒")
            print(f"   GPU使用: {'是' if batch_result.gpu_used else '否'}")
            print(f"   設備資訊: {batch_result.device_info}")

            # 檢查結果
            if hasattr(batch_result, 'look_angles') and len(batch_result.look_angles) > 0:
                print(f"   輸出結果: {len(batch_result.look_angles)} 個角度")
                print(f"   範例仰角: {batch_result.look_angles[0][1]:.2f}°")
                print(f"   範例方位角: {batch_result.look_angles[0][0]:.2f}°")

            # 比較CPU性能
            print(f"\n📊 CPU對照測試...")
            cpu_converter = GPUCoordinateConverter(
                observer_location=observer_location,
                enable_gpu=False
            )

            cpu_start = time.time()
            cpu_result = cpu_converter.gpu_batch_calculate_look_angles(positions[:100])  # 少量測試避免太慢
            cpu_time = time.time() - cpu_start

            # 外推CPU完整時間
            estimated_cpu_time = cpu_time * (len(positions) / 100)

            print(f"   CPU時間 (100位置): {cpu_time:.3f} 秒")
            print(f"   CPU預估 ({len(positions)}位置): {estimated_cpu_time:.3f} 秒")

            if batch_result.gpu_used:
                speedup = estimated_cpu_time / execution_time
                print(f"   GPU加速比: {speedup:.1f}x")

                if speedup > 3.0:
                    print("🚀 GPU顯著加速座標轉換!")
                elif speedup > 1.5:
                    print("⚡ GPU有效加速座標轉換")
                else:
                    print("⚠️ GPU加速效果有限")
            else:
                print("❌ GPU未啟用，無法計算加速比")

        except Exception as e:
            print(f"❌ GPU轉換失敗: {e}")
            import traceback
            traceback.print_exc()

    except ImportError as e:
        print(f"❌ 無法導入GPU座標轉換器: {e}")

def main():
    """主函數"""
    print("🔍 GPU座標轉換加速測試")
    print("目標：評估GPU在座標轉換中的加速潛力")

    # 步驟1: 檢測GPU環境
    test_gpu_availability()

    # 步驟2: 測試座標轉換性能
    test_gpu_coordinate_converter()

if __name__ == "__main__":
    main()