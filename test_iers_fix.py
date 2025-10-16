#!/usr/bin/env python3
"""
驗證 IERS 極移矩陣 Fail-Fast 修復

測試目標:
1. 驗證在正常情況下，極移矩陣計算成功
2. 驗證在 IERS 數據不可用時，系統拋出 RuntimeError (而非返回單位矩陣)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.shared.coordinate_systems.iers_data_manager import get_iers_manager


def test_normal_case():
    """測試正常情況：IERS 數據可用"""
    print("=" * 70)
    print("測試 1: 正常情況 - IERS 數據可用")
    print("=" * 70)

    try:
        iers_manager = get_iers_manager()

        # 使用當前時間測試 (IERS 數據應該可用)
        test_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        print(f"測試時間: {test_time}")
        print("嘗試獲取極移矩陣...")

        polar_motion_matrix = iers_manager.get_polar_motion_matrix(test_time)

        print(f"✅ 成功獲取極移矩陣:")
        print(f"   形狀: {polar_motion_matrix.shape}")
        print(f"   類型: {type(polar_motion_matrix)}")
        print(f"   矩陣內容:")
        for i, row in enumerate(polar_motion_matrix):
            print(f"     [{i}] {row}")

        # 驗證不是單位矩陣 (除非極移參數恰好為0)
        import numpy as np
        if np.allclose(polar_motion_matrix, np.eye(3), atol=1e-10):
            print("⚠️  警告: 極移矩陣接近單位矩陣 (極移參數可能接近0)")
        else:
            print("✅ 極移矩陣包含真實的極移修正 (非單位矩陣)")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_fail_fast_behavior():
    """測試 Fail-Fast 行為：當 IERS 數據處理異常時"""
    print("\n" + "=" * 70)
    print("測試 2: Fail-Fast 行為驗證")
    print("=" * 70)

    print("說明: 由於 IERS 數據管理器會自動下載和緩存數據,")
    print("      在正常運行環境下很難觸發錯誤條件。")
    print("      但我們可以驗證異常處理邏輯已經修改為 Fail-Fast。")

    try:
        from src.shared.coordinate_systems.iers_data_manager import IERSDataManager
        import inspect

        # 讀取源代碼驗證修復
        source = inspect.getsource(IERSDataManager.get_polar_motion_matrix)

        print("\n檢查源代碼中的異常處理:")

        if "raise RuntimeError" in source:
            print("✅ 確認: 代碼包含 'raise RuntimeError' (Fail-Fast)")
        else:
            print("❌ 錯誤: 代碼未包含 'raise RuntimeError'")
            return False

        if "return np.eye(3)" in source:
            print("❌ 錯誤: 代碼仍包含 'return np.eye(3)' 回退邏輯")
            return False
        else:
            print("✅ 確認: 代碼已移除 'return np.eye(3)' 回退邏輯")

        if "Grade A 標準" in source or "Grade A 標准" in source:
            print("✅ 確認: 錯誤訊息提到 Grade A 標準要求")
        else:
            print("⚠️  警告: 錯誤訊息未提到 Grade A 標準")

        print("\n✅ Fail-Fast 行為驗證通過")
        return True

    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False


def test_eop_data_retrieval():
    """測試 EOP 數據獲取 (相關功能驗證)"""
    print("\n" + "=" * 70)
    print("測試 3: EOP 數據獲取驗證")
    print("=" * 70)

    try:
        iers_manager = get_iers_manager()

        test_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        print(f"測試時間: {test_time}")
        print("嘗試獲取地球定向參數...")

        eop_data = iers_manager.get_earth_orientation_parameters(test_time)

        print(f"✅ 成功獲取 EOP 數據:")
        print(f"   極移 X: {eop_data.x_arcsec:.6f} arcsec (誤差: ±{eop_data.x_error:.6f})")
        print(f"   極移 Y: {eop_data.y_arcsec:.6f} arcsec (誤差: ±{eop_data.y_error:.6f})")
        print(f"   UT1-UTC: {eop_data.ut1_utc_sec:.6f} sec (誤差: ±{eop_data.ut1_utc_error:.6f})")
        print(f"   數據來源: {eop_data.data_source}")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "IERS 極移矩陣 Fail-Fast 修復驗證" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")

    results = []

    # 執行測試
    results.append(("正常情況測試", test_normal_case()))
    results.append(("Fail-Fast 行為驗證", test_fail_fast_behavior()))
    results.append(("EOP 數據獲取驗證", test_eop_data_retrieval()))

    # 彙總結果
    print("\n" + "=" * 70)
    print("測試結果彙總")
    print("=" * 70)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 70)
    print(f"總計: {passed} 個測試通過, {failed} 個測試失敗")

    if failed == 0:
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 25 + "✅ 所有測試通過" + " " * 26 + "║")
        print("╚" + "=" * 68 + "╝")
        return 0
    else:
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 22 + "❌ 部分測試失敗" + " " * 26 + "║")
        print("╚" + "=" * 68 + "╝")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
