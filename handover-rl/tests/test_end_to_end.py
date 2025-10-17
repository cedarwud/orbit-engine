#!/usr/bin/env python3
"""
端到端測試腳本

功能:
1. 驗證所有 Phase 可以順利運行
2. 檢查數據流完整性
3. 快速發現潛在問題

執行:
    python tests/test_end_to_end.py

預期結果:
    ✅ Phase 1: Data Loading PASSED
    ✅ Phase 2: Baseline Methods PASSED
    ✅ Phase 3: RL Environment PASSED
    ✅ All tests PASSED!
"""

import subprocess
import sys
from pathlib import Path


def test_phase(phase_name: str, script_path: str) -> bool:
    """
    運行單個 Phase 並檢查結果

    Args:
        phase_name: Phase 名稱
        script_path: Python 腳本路徑

    Returns:
        success: 是否成功
    """
    print(f"\n{'='*70}")
    print(f"Testing {phase_name}")
    print(f"{'='*70}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘超時
        )

        if result.returncode != 0:
            print(f"❌ {phase_name} FAILED")
            print("\n--- STDERR ---")
            print(result.stderr)
            print("\n--- STDOUT ---")
            print(result.stdout)
            return False

        print(f"✅ {phase_name} PASSED")

        # 顯示關鍵輸出
        if "✅" in result.stdout:
            for line in result.stdout.split('\n'):
                if "✅" in line:
                    print(f"   {line.strip()}")

        return True

    except subprocess.TimeoutExpired:
        print(f"❌ {phase_name} TIMEOUT (超過5分鐘)")
        return False
    except Exception as e:
        print(f"❌ {phase_name} ERROR: {e}")
        return False


def verify_outputs() -> bool:
    """驗證關鍵輸出文件是否存在"""
    print(f"\n{'='*70}")
    print("Verifying Output Files")
    print(f"{'='*70}")

    required_files = [
        "data/train_episodes.pkl",
        "data/val_episodes.pkl",
        "data/test_episodes.pkl",
        "data/data_statistics.json",
        "results/baseline_results.json",
        "results/baseline_comparison.txt"
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"   ✅ {file_path} ({size_kb:.1f} KB)")
        else:
            print(f"   ❌ {file_path} NOT FOUND")
            all_exist = False

    return all_exist


def verify_data_integrity() -> bool:
    """驗證數據完整性（深度檢查）"""
    print(f"\n{'='*70}")
    print("Verifying Data Integrity")
    print(f"{'='*70}")

    try:
        import pickle
        import json

        # 檢查 Episodes 數據
        print("\n📊 檢查 Episode 數據...")
        with open("data/train_episodes.pkl", 'rb') as f:
            train_eps = pickle.load(f)

        with open("data/val_episodes.pkl", 'rb') as f:
            val_eps = pickle.load(f)

        with open("data/test_episodes.pkl", 'rb') as f:
            test_eps = pickle.load(f)

        total_eps = len(train_eps) + len(val_eps) + len(test_eps)
        print(f"   ✅ 總 Episodes: {total_eps}")
        print(f"   ✅ 訓練集: {len(train_eps)} ({len(train_eps)/total_eps*100:.1f}%)")
        print(f"   ✅ 驗證集: {len(val_eps)} ({len(val_eps)/total_eps*100:.1f}%)")
        print(f"   ✅ 測試集: {len(test_eps)} ({len(test_eps)/total_eps*100:.1f}%)")

        # 檢查第一個 Episode 的結構
        if len(train_eps) > 0:
            first_ep = train_eps[0]
            print(f"\n📋 檢查 Episode 結構...")

            # 檢查必要的鍵
            required_keys = ['satellite_id', 'constellation', 'time_series', 'episode_length']
            for key in required_keys:
                if key in first_ep:
                    print(f"   ✅ {key}: 存在")
                else:
                    print(f"   ❌ {key}: 缺失")
                    return False

            # 檢查時間序列長度
            time_series_length = len(first_ep.get('time_series', []))
            print(f"   ✅ 時間序列長度: {time_series_length} 點")

            # 檢查特徵完整性（12 維）
            if time_series_length > 0:
                first_point = first_ep['time_series'][0]
                feature_keys = [
                    'rsrp_dbm', 'rsrq_db', 'rs_sinr_db',  # 信號品質 (3)
                    'distance_km', 'elevation_deg', 'doppler_shift_hz', 'radial_velocity_ms',  # 物理參數 (4/7)
                    'atmospheric_loss_db', 'path_loss_db', 'propagation_delay_ms',  # 物理參數 (3/7)
                    'offset_mo_db', 'cell_offset_db'  # 3GPP 偏移 (2)
                ]

                print(f"\n🔍 檢查特徵完整性（12 維）...")
                missing_features = []
                for key in feature_keys:
                    if key in first_point:
                        print(f"   ✅ {key}")
                    else:
                        print(f"   ❌ {key}: 缺失")
                        missing_features.append(key)

                if missing_features:
                    print(f"\n   ⚠️  缺失特徵: {missing_features}")
                    return False
                else:
                    print(f"\n   ✅ 所有 12 維特徵完整")

        # 檢查統計數據
        print(f"\n📊 檢查統計數據...")
        with open("data/data_statistics.json", 'r') as f:
            stats = json.load(f)

        print(f"   ✅ 總 Episodes: {stats['total_episodes']}")
        print(f"   ✅ 星座分布: {stats['constellation_distribution']}")

        # 檢查特徵統計
        feature_stats = stats.get('feature_statistics', {})
        print(f"   ✅ 特徵統計: {len(feature_stats)} 個特徵")

        # 檢查 Baseline 結果
        print(f"\n📈 檢查 Baseline 結果...")
        with open("results/baseline_results.json", 'r') as f:
            baseline_results = json.load(f)

        methods = baseline_results.get('methods', {})
        print(f"   ✅ Baseline 方法數: {len(methods)}")
        for method_name in methods.keys():
            print(f"   ✅ {method_name}")

        print(f"\n✅ 所有數據完整性檢查通過")
        return True

    except Exception as e:
        print(f"\n❌ 數據完整性檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("=" * 70)
    print("Handover-RL End-to-End Test Suite")
    print("=" * 70)
    print("\n🎯 目標: 驗證所有 Phase 可以順利運行")
    print("⏱️  預計時間: 2-5 分鐘\n")

    # 測試序列
    test_sequence = [
        ("Phase 1: Data Loading", "phase1_data_loader_v2.py"),
        ("Phase 2: Baseline Methods", "phase2_baseline_methods.py"),
        ("Phase 3: RL Environment", "phase3_rl_environment.py"),
    ]

    all_passed = True

    # 運行各 Phase 測試
    for phase_name, script in test_sequence:
        if not test_phase(phase_name, script):
            all_passed = False
            break

    # 驗證輸出文件
    if all_passed:
        if not verify_outputs():
            all_passed = False

        # 深度驗證數據完整性
        if all_passed:
            if not verify_data_integrity():
                all_passed = False

    # 最終結果
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All tests PASSED!")
        print("=" * 70)
        print("\n✅ 所有 Phase 運行正常")
        print("✅ 所有輸出文件已生成")
        print("\n下一步:")
        print("  1. 運行完整訓練: python phase4_rl_training.py")
        print("  2. 或使用一鍵腳本: ./run_all.sh")
        return 0
    else:
        print("❌ Some tests FAILED!")
        print("=" * 70)
        print("\n請檢查上述錯誤信息並修復")
        return 1


if __name__ == "__main__":
    sys.exit(main())
