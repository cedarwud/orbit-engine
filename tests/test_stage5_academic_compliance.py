#!/usr/bin/env python3
"""
Stage 5 學術標準合規性測試

驗證項目:
1. ITU-R P.676-13 完整大氣衰減模型
2. 3GPP TS 38.214 標準信號計算
3. Johnson-Nyquist 噪聲底計算
4. 都卜勒效應（使用實際速度數據）
"""

import sys
import os
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

import math


def test_itur_p676_model():
    """測試 ITU-R P.676-13 大氣衰減模型"""
    print("\n" + "="*60)
    print("TEST 1: ITU-R P.676-13 大氣衰減模型")
    print("="*60)

    from src.stages.stage5_signal_analysis.itur_p676_atmospheric_model import create_itur_p676_model

    # 創建模型
    model = create_itur_p676_model(
        temperature_k=283.0,
        pressure_hpa=1013.25,
        water_vapor_density_g_m3=7.5
    )

    # 測試頻率: Ku頻段
    frequency_ghz = 12.5
    elevation_deg = 30.0

    # 計算特定衰減
    gamma_o, gamma_w = model.calculate_specific_attenuation(frequency_ghz)

    print(f"✅ 頻率: {frequency_ghz} GHz")
    print(f"✅ 氧氣衰減係數: {gamma_o:.6f} dB/km")
    print(f"✅ 水蒸氣衰減係數: {gamma_w:.6f} dB/km")

    # 計算總衰減
    total_attenuation = model.calculate_total_attenuation(frequency_ghz, elevation_deg)
    print(f"✅ 總大氣衰減 ({elevation_deg}°): {total_attenuation:.3f} dB")

    # 驗證合理性
    assert 0.0 < gamma_o < 1.0, f"氧氣衰減異常: {gamma_o}"
    assert 0.0 < gamma_w < 1.0, f"水蒸氣衰減異常: {gamma_w}"
    assert 0.0 < total_attenuation < 10.0, f"總衰減異常: {total_attenuation}"

    print("✅ ITU-R P.676-13 模型測試通過")
    return True


def test_3gpp_signal_calculator():
    """測試 3GPP TS 38.214 信號計算器"""
    print("\n" + "="*60)
    print("TEST 2: 3GPP TS 38.214 信號計算器")
    print("="*60)

    from src.stages.stage5_signal_analysis.gpp_ts38214_signal_calculator import create_3gpp_signal_calculator

    # 創建計算器
    calculator = create_3gpp_signal_calculator({
        'bandwidth_mhz': 100.0,
        'subcarrier_spacing_khz': 30.0,
        'noise_figure_db': 7.0
    })

    # 測試參數
    tx_power_dbm = 70.0  # 40dBW = 70dBm
    tx_gain_db = 35.0
    rx_gain_db = 25.0
    path_loss_db = 165.0
    atmospheric_loss_db = 2.0
    elevation_deg = 30.0

    # 計算完整信號品質
    signal_quality = calculator.calculate_complete_signal_quality(
        tx_power_dbm=tx_power_dbm,
        tx_gain_db=tx_gain_db,
        rx_gain_db=rx_gain_db,
        path_loss_db=path_loss_db,
        atmospheric_loss_db=atmospheric_loss_db,
        elevation_deg=elevation_deg
    )

    print(f"✅ RSRP: {signal_quality['rsrp_dbm']:.2f} dBm")
    print(f"✅ RSRQ: {signal_quality['rsrq_db']:.2f} dB")
    print(f"✅ SINR: {signal_quality['sinr_db']:.2f} dB")
    print(f"✅ RSSI: {signal_quality['rssi_dbm']:.2f} dBm")
    print(f"✅ 噪聲功率: {signal_quality['noise_power_dbm']:.2f} dBm")
    print(f"✅ 干擾功率: {signal_quality['interference_power_dbm']:.2f} dBm")

    # 驗證範圍
    assert -140 <= signal_quality['rsrp_dbm'] <= -44, f"RSRP 超出 3GPP 範圍"
    assert -34 <= signal_quality['rsrq_db'] <= 2.5, f"RSRQ 超出 3GPP 範圍"
    assert -23 <= signal_quality['sinr_db'] <= 40, f"SINR 超出範圍"

    # 驗證標準標記
    assert signal_quality['calculation_standard'] == '3GPP_TS_38.214'
    assert signal_quality['measurement_standard'] == '3GPP_TS_38.215'

    print("✅ 3GPP TS 38.214 信號計算器測試通過")
    return True


def test_johnson_nyquist_noise():
    """測試 Johnson-Nyquist 噪聲底計算"""
    print("\n" + "="*60)
    print("TEST 3: Johnson-Nyquist 噪聲底計算")
    print("="*60)

    from src.stages.stage5_signal_analysis.gpp_ts38214_signal_calculator import create_3gpp_signal_calculator

    calculator = create_3gpp_signal_calculator({
        'bandwidth_mhz': 100.0,
        'noise_figure_db': 7.0
    })

    # 計算熱噪聲功率
    noise_power_dbm = calculator.calculate_thermal_noise_power()

    print(f"✅ 帶寬: 100 MHz")
    print(f"✅ 噪聲係數: 7 dB")
    print(f"✅ 溫度: 290 K")
    print(f"✅ 熱噪聲功率: {noise_power_dbm:.2f} dBm")

    # 理論計算驗證
    # N = k × T × B
    k = 1.380649e-23  # Boltzmann constant
    T = 290.0  # K
    B = 100e6  # Hz
    N_watts = k * T * B
    N_dbm_theoretical = 10 * math.log10(N_watts * 1000) + 7.0  # + noise figure

    print(f"✅ 理論值: {N_dbm_theoretical:.2f} dBm")
    print(f"✅ 誤差: {abs(noise_power_dbm - N_dbm_theoretical):.6f} dB")

    # 驗證精度
    assert abs(noise_power_dbm - N_dbm_theoretical) < 0.01, "噪聲計算誤差過大"

    print("✅ Johnson-Nyquist 噪聲底計算測試通過")
    return True


def test_doppler_calculator():
    """測試都卜勒效應計算器"""
    print("\n" + "="*60)
    print("TEST 4: 都卜勒效應計算（實際速度數據）")
    print("="*60)

    from src.stages.stage5_signal_analysis.doppler_calculator import create_doppler_calculator

    calculator = create_doppler_calculator()

    # 模擬 Stage 2 數據 (TEME 座標系統)
    velocity_km_per_s = [7.5, 0.5, 0.2]  # 典型 LEO 速度
    satellite_position_km = [6800, 1000, 500]
    observer_position_km = [0, 0, 6371]  # 地心觀測點
    frequency_hz = 12.5e9  # 12.5 GHz

    # 計算都卜勒頻移
    doppler_data = calculator.calculate_doppler_shift(
        velocity_km_per_s=velocity_km_per_s,
        satellite_position_km=satellite_position_km,
        observer_position_km=observer_position_km,
        frequency_hz=frequency_hz
    )

    print(f"✅ 速度向量: {velocity_km_per_s} km/s")
    print(f"✅ 速度大小: {doppler_data['velocity_magnitude_ms']:.2f} m/s")
    print(f"✅ 視線速度: {doppler_data['radial_velocity_ms']:.2f} m/s")
    print(f"✅ 都卜勒頻移: {doppler_data['doppler_shift_hz']:.2f} Hz")
    print(f"✅ 數據來源: {doppler_data['data_source']}")

    # 驗證合理性
    assert doppler_data['velocity_magnitude_ms'] > 5000, "速度過小"
    assert doppler_data['velocity_magnitude_ms'] < 10000, "速度過大"
    assert abs(doppler_data['doppler_shift_hz']) < 500000, "都卜勒頻移異常"
    assert doppler_data['data_source'] == 'stage2_teme_velocity'

    print("✅ 都卜勒效應計算測試通過")
    return True


def test_no_hardcoded_values():
    """驗證無硬編碼值"""
    print("\n" + "="*60)
    print("TEST 5: 驗證無硬編碼簡化值")
    print("="*60)

    # 檢查關鍵文件
    files_to_check = [
        'src/stages/stage5_signal_analysis/itur_p676_atmospheric_model.py',
        'src/stages/stage5_signal_analysis/gpp_ts38214_signal_calculator.py',
        'src/stages/stage5_signal_analysis/doppler_calculator.py'
    ]

    forbidden_patterns = [
        ('gamma_o = 0.01', 'ITU-R P.676 簡化氧氣係數'),
        ('gamma_w = 0.005', 'ITU-R P.676 簡化水蒸氣係數'),
        ('typical_velocity_ms = 7500', '假設速度值'),
    ]

    all_passed = True

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern, description in forbidden_patterns:
            if pattern in content and 'test' not in file_path.lower():
                print(f"❌ 發現禁止的硬編碼: {description} in {file_path}")
                all_passed = False

    if all_passed:
        print("✅ 無禁止的硬編碼簡化值")

    return all_passed


def main():
    """主測試函數"""
    print("\n" + "="*80)
    print("Stage 5 學術標準合規性測試")
    print("="*80)

    tests = [
        ("ITU-R P.676-13 大氣衰減", test_itur_p676_model),
        ("3GPP TS 38.214 信號計算", test_3gpp_signal_calculator),
        ("Johnson-Nyquist 噪聲底", test_johnson_nyquist_noise),
        ("都卜勒效應（實際速度）", test_doppler_calculator),
        ("無硬編碼簡化值", test_no_hardcoded_values),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試失敗: {e}")
            results.append((test_name, False))

    # 總結
    print("\n" + "="*80)
    print("測試總結")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("="*80)
    print(f"通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("="*80)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)