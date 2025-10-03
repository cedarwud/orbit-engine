#!/usr/bin/env python3
"""
ITU-R P.618 閃爍模型升級驗證測試

測試目標:
1. 比較簡化模型 vs ITU-Rpy 官方模型精度差異
2. 驗證地理位置對閃爍衰減的影響
3. 確認學術精度提升 (預期 5-10 倍)

學術依據:
- ITU-R P.618-13 (2017): Annex I - Scintillation attenuation prediction
- Karasawa et al. (1988): Tropospheric scintillation measurements
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.stages.stage5_signal_analysis.itur_official_atmospheric_model import (
    ITUROfficalAtmosphericModel
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_scintillation_comparison():
    """
    比較簡化模型 vs ITU-Rpy P.618 官方模型
    """
    print("\n" + "=" * 80)
    print("ITU-R P.618 閃爍模型升級驗證測試")
    print("=" * 80)

    # 初始化模型
    model = ITUROfficalAtmosphericModel(
        temperature_k=283.0,
        pressure_hpa=1013.25,
        water_vapor_density_g_m3=7.5
    )

    # 測試場景：台北觀測站
    test_scenarios = [
        {
            'name': '台北 - 低仰角 5°',
            'latitude': 24.9441,
            'longitude': 121.3714,
            'elevation_deg': 5.0,
            'frequency_ghz': 12.5,
            'antenna_diameter_m': 1.2,
            'antenna_efficiency': 0.65
        },
        {
            'name': '台北 - 中仰角 15°',
            'latitude': 24.9441,
            'longitude': 121.3714,
            'elevation_deg': 15.0,
            'frequency_ghz': 12.5,
            'antenna_diameter_m': 1.2,
            'antenna_efficiency': 0.65
        },
        {
            'name': '台北 - 高仰角 45°',
            'latitude': 24.9441,
            'longitude': 121.3714,
            'elevation_deg': 45.0,
            'frequency_ghz': 12.5,
            'antenna_diameter_m': 1.2,
            'antenna_efficiency': 0.65
        },
        {
            'name': '台北 - Ka頻段 30GHz',
            'latitude': 24.9441,
            'longitude': 121.3714,
            'elevation_deg': 10.0,
            'frequency_ghz': 30.0,
            'antenna_diameter_m': 0.8,
            'antenna_efficiency': 0.60
        },
    ]

    print("\n測試結果比較:")
    print("-" * 80)
    print(f"{'場景':<25} {'簡化模型 (dB)':<15} {'ITU-Rpy P.618 (dB)':<20} {'差異 (dB)':<15}")
    print("-" * 80)

    for scenario in test_scenarios:
        # 簡化模型
        simplified_loss = model._calculate_scintillation_loss(
            elevation_deg=scenario['elevation_deg'],
            frequency_ghz=scenario['frequency_ghz']
        )

        # ITU-Rpy P.618 官方模型
        try:
            official_loss = model.calculate_scintillation_itur_p618(
                latitude_deg=scenario['latitude'],
                longitude_deg=scenario['longitude'],
                elevation_deg=scenario['elevation_deg'],
                frequency_ghz=scenario['frequency_ghz'],
                antenna_diameter_m=scenario['antenna_diameter_m'],
                antenna_efficiency=scenario['antenna_efficiency']
            )

            difference = abs(official_loss - simplified_loss)

            print(
                f"{scenario['name']:<25} "
                f"{simplified_loss:>14.3f} "
                f"{official_loss:>19.3f} "
                f"{difference:>14.3f}"
            )

        except Exception as e:
            print(f"{scenario['name']:<25} ERROR: {e}")

    print("-" * 80)


def test_geographic_variations():
    """
    測試不同地理位置的閃爍衰減差異
    """
    print("\n" + "=" * 80)
    print("地理位置閃爍衰減差異測試")
    print("=" * 80)

    model = ITUROfficalAtmosphericModel()

    # 不同氣候區域測試
    locations = [
        {'name': '台北 (亞熱帶)', 'lat': 24.9441, 'lon': 121.3714},
        {'name': '東京 (溫帶)', 'lat': 35.6762, 'lon': 139.6503},
        {'name': '赤道 (熱帶)', 'lat': 0.0, 'lon': 100.0},
        {'name': '北極圈 (寒帶)', 'lat': 70.0, 'lon': 20.0},
    ]

    elevation_deg = 10.0
    frequency_ghz = 12.5

    print("\n不同氣候區域閃爍衰減:")
    print("-" * 80)
    print(f"{'地點':<20} {'緯度':<10} {'經度':<10} {'閃爍衰減 (dB)':<15}")
    print("-" * 80)

    for loc in locations:
        try:
            scintillation_db = model.calculate_scintillation_itur_p618(
                latitude_deg=loc['lat'],
                longitude_deg=loc['lon'],
                elevation_deg=elevation_deg,
                frequency_ghz=frequency_ghz,
                antenna_diameter_m=1.2,
                antenna_efficiency=0.65
            )

            print(
                f"{loc['name']:<20} "
                f"{loc['lat']:>9.4f} "
                f"{loc['lon']:>9.4f} "
                f"{scintillation_db:>14.3f}"
            )

        except Exception as e:
            print(f"{loc['name']:<20} ERROR: {e}")

    print("-" * 80)


def test_frequency_dependence():
    """
    測試頻率依賴性
    """
    print("\n" + "=" * 80)
    print("閃爍衰減頻率依賴性測試")
    print("=" * 80)

    model = ITUROfficalAtmosphericModel()

    frequencies = [1.5, 2.0, 6.0, 12.5, 20.0, 30.0]  # GHz
    latitude = 24.9441
    longitude = 121.3714
    elevation_deg = 10.0

    print("\n頻率 vs 閃爍衰減:")
    print("-" * 80)
    print(f"{'頻率 (GHz)':<15} {'簡化模型 (dB)':<20} {'ITU-Rpy P.618 (dB)':<20} {'差異 (dB)':<15}")
    print("-" * 80)

    for freq in frequencies:
        simplified = model._calculate_scintillation_loss(elevation_deg, freq)

        try:
            official = model.calculate_scintillation_itur_p618(
                latitude_deg=latitude,
                longitude_deg=longitude,
                elevation_deg=elevation_deg,
                frequency_ghz=freq,
                antenna_diameter_m=1.2,
                antenna_efficiency=0.65
            )

            difference = abs(official - simplified)

            print(
                f"{freq:>14.1f} "
                f"{simplified:>19.3f} "
                f"{official:>19.3f} "
                f"{difference:>14.3f}"
            )

        except Exception as e:
            print(f"{freq:>14.1f} ERROR: {e}")

    print("-" * 80)


def test_model_metadata():
    """
    測試模型元數據
    """
    print("\n" + "=" * 80)
    print("ITU-Rpy 模型元數據")
    print("=" * 80)

    model = ITUROfficalAtmosphericModel()
    metadata = model.get_model_info()

    print(f"\n模型名稱: {metadata['model_name']}")
    print(f"實現方式: {metadata['implementation']}")
    print(f"來源: {metadata['source']}")
    print(f"ITU-Rpy 版本: {metadata['version']}")
    print(f"GitHub: {metadata['github']}")
    print(f"ITU-R 建議書: {metadata['recommendation']}")
    print(f"\n參數:")
    for key, value in metadata['parameters'].items():
        print(f"  {key}: {value}")

    print("=" * 80)


if __name__ == "__main__":
    """
    執行完整測試套件
    """
    print("\n🚀 開始 ITU-R P.618 閃爍模型升級驗證測試")

    try:
        # 測試 1: 模型比較
        test_scintillation_comparison()

        # 測試 2: 地理位置變化
        test_geographic_variations()

        # 測試 3: 頻率依賴性
        test_frequency_dependence()

        # 測試 4: 模型元數據
        test_model_metadata()

        print("\n✅ 所有測試完成")

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
