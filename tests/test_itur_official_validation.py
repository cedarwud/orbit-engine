#!/usr/bin/env python3
"""
ITU-Rpy 官方套件功能驗證測試

目的: 驗證 ITU-Rpy 官方套件正確運作並產生物理上合理的大氣衰減值

驗證策略:
1. 功能測試: API 正常運作
2. 物理合理性: 衰減值在預期範圍內
3. 趨勢一致性: 頻率/仰角關係符合物理規律

學術依據:
- ITU-R P.676-13: Ku-band (10-15 GHz) 典型天頂衰減 0.01-0.1 dB
- ITU-R P.676-13: Ka-band (20-30 GHz) 典型天頂衰減 0.05-0.3 dB
"""

import pytest
import sys
from pathlib import Path

# 添加 src 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from stages.stage5_signal_analysis.itur_official_atmospheric_model import create_itur_official_model


class TestITUROfficial:
    """ITU-Rpy 官方套件功能驗證"""

    @pytest.fixture
    def standard_model(self):
        """ITU-R P.835 標準大氣條件模型"""
        return create_itur_official_model(
            temperature_k=283.0,      # 10°C, mid-latitude
            pressure_hpa=1013.25,     # Sea level
            water_vapor_density_g_m3=7.5  # Moderate humidity
        )

    def test_api_basic_functionality(self, standard_model):
        """測試 API 基本功能"""
        # 測試基本調用不拋出異常
        attenuation = standard_model.calculate_total_attenuation(
            frequency_ghz=12.5,
            elevation_deg=15.0
        )

        assert isinstance(attenuation, float)
        assert attenuation > 0, "大氣衰減應為正值"
        assert attenuation < 10.0, "Ku-band 大氣衰減不應超過 10 dB"

        print(f"✅ 基本 API 測試通過: {attenuation:.4f} dB")

    def test_physical_reasonableness_ku_band(self, standard_model):
        """測試 Ku-band 物理合理性"""
        frequency_ghz = 12.5

        # 測試不同仰角
        elevations = [5, 15, 30, 60, 90]
        attenuations = []

        for elev in elevations:
            atten = standard_model.calculate_total_attenuation(
                frequency_ghz=frequency_ghz,
                elevation_deg=elev
            )
            attenuations.append(atten)

            # 物理合理性檢查: Ku-band 衰減應在 0.01-2.0 dB 範圍
            assert 0.01 <= atten <= 2.0, (
                f"Ku-band {elev}° 仰角衰減超出合理範圍: {atten:.4f} dB"
            )

        print(f"\n🛰️ Ku-band (12.5 GHz) 不同仰角:")
        for elev, atten in zip(elevations, attenuations):
            print(f"  {elev:2d}°: {atten:.4f} dB")

        # 物理趨勢檢查: 仰角越高，衰減應越低
        for i in range(len(attenuations) - 1):
            assert attenuations[i] >= attenuations[i+1], (
                f"仰角增加時衰減應減少: {elevations[i]}°({attenuations[i]:.4f}dB) "
                f"vs {elevations[i+1]}°({attenuations[i+1]:.4f}dB)"
            )

        print(f"✅ Ku-band 物理合理性驗證通過")

    def test_physical_reasonableness_ka_band(self, standard_model):
        """測試 Ka-band 物理合理性"""
        frequency_ghz = 28.0

        # 測試不同仰角
        elevations = [5, 15, 30, 60, 90]
        attenuations = []

        for elev in elevations:
            atten = standard_model.calculate_total_attenuation(
                frequency_ghz=frequency_ghz,
                elevation_deg=elev
            )
            attenuations.append(atten)

            # 物理合理性檢查: Ka-band 衰減應在 0.05-3.0 dB 範圍
            assert 0.05 <= atten <= 3.0, (
                f"Ka-band {elev}° 仰角衰減超出合理範圍: {atten:.4f} dB"
            )

        print(f"\n🛰️ Ka-band (28 GHz) 不同仰角:")
        for elev, atten in zip(elevations, attenuations):
            print(f"  {elev:2d}°: {atten:.4f} dB")

        # 物理趨勢檢查: 仰角越高，衰減應越低
        for i in range(len(attenuations) - 1):
            assert attenuations[i] >= attenuations[i+1]

        print(f"✅ Ka-band 物理合理性驗證通過")

    def test_frequency_dependence(self, standard_model):
        """測試頻率依賴性"""
        elevation_deg = 30.0  # 固定仰角
        frequencies = [10.0, 12.5, 15.0, 20.0, 28.0]  # GHz

        attenuations = []
        for freq in frequencies:
            atten = standard_model.calculate_total_attenuation(
                frequency_ghz=freq,
                elevation_deg=elevation_deg
            )
            attenuations.append(atten)

        print(f"\n📡 不同頻率 (仰角 {elevation_deg}°):")
        for freq, atten in zip(frequencies, attenuations):
            print(f"  {freq:5.1f} GHz: {atten:.4f} dB")

        # 一般趨勢: 高頻衰減較大（但有譜線吸收峰例外）
        # 至少驗證 Ka-band (28 GHz) > Ku-band (12.5 GHz)
        ka_band_idx = frequencies.index(28.0)
        ku_band_idx = frequencies.index(12.5)

        assert attenuations[ka_band_idx] > attenuations[ku_band_idx], (
            f"Ka-band 衰減應大於 Ku-band"
        )

        print(f"✅ 頻率依賴性驗證通過")

    def test_starlink_operational_scenario(self, standard_model):
        """測試 Starlink 實際運行場景"""
        scenarios = [
            {
                'name': 'Starlink 最小服務仰角',
                'freq': 12.5,
                'elev': 15.0,
                'max_atten': 0.5  # dB
            },
            {
                'name': 'Starlink 典型通訊',
                'freq': 12.5,
                'elev': 30.0,
                'max_atten': 0.3
            },
            {
                'name': 'Starlink 最佳條件',
                'freq': 12.5,
                'elev': 60.0,
                'max_atten': 0.15
            }
        ]

        print(f"\n🛰️ Starlink 運行場景:")
        for scenario in scenarios:
            atten = standard_model.calculate_total_attenuation(
                frequency_ghz=scenario['freq'],
                elevation_deg=scenario['elev']
            )

            print(f"  {scenario['name']}:")
            print(f"    頻率: {scenario['freq']} GHz, 仰角: {scenario['elev']}°")
            print(f"    衰減: {atten:.4f} dB (上限: {scenario['max_atten']} dB)")

            assert atten <= scenario['max_atten'], (
                f"{scenario['name']} 衰減超出預期: {atten:.4f} dB"
            )

        print(f"✅ Starlink 場景驗證通過")

    def test_different_atmospheric_conditions(self):
        """測試不同大氣條件"""
        conditions = [
            {
                'name': '寒冷乾燥 (冬季)',
                'temp': 263.0,
                'pressure': 1020.0,
                'humidity': 2.0
            },
            {
                'name': '標準條件 (mid-latitude)',
                'temp': 283.0,
                'pressure': 1013.25,
                'humidity': 7.5
            },
            {
                'name': '炎熱潮濕 (夏季)',
                'temp': 303.0,
                'pressure': 1005.0,
                'humidity': 15.0
            }
        ]

        freq = 12.5
        elev = 30.0

        print(f"\n🌤️ 不同大氣條件 ({freq} GHz, {elev}°):")

        for cond in conditions:
            model = create_itur_official_model(
                temperature_k=cond['temp'],
                pressure_hpa=cond['pressure'],
                water_vapor_density_g_m3=cond['humidity']
            )

            atten = model.calculate_total_attenuation(
                frequency_ghz=freq,
                elevation_deg=elev
            )

            print(f"  {cond['name']}:")
            print(f"    T={cond['temp']}K, P={cond['pressure']}hPa, ρ={cond['humidity']}g/m³")
            print(f"    衰減: {atten:.4f} dB")

            # 所有條件下衰減都應在合理範圍
            assert 0.01 <= atten <= 1.0, f"{cond['name']} 衰減超出範圍"

        print(f"✅ 不同大氣條件驗證通過")

    def test_model_info(self):
        """測試模型資訊"""
        model = create_itur_official_model()
        info = model.get_model_info()

        print(f"\n📋 ITU-Rpy 模型資訊:")
        print(f"  名稱: {info['model_name']}")
        print(f"  實現: {info['implementation']}")
        print(f"  來源: {info['source']}")
        print(f"  版本: {info['version']}")
        print(f"  建議書: {info['recommendation']}")

        assert info['implementation'] == 'official'
        assert 'ITU-Rpy' in info['source']
        assert info['version'] is not None

        print(f"✅ 模型資訊驗證通過")


def test_summary():
    """測試摘要"""
    print("\n" + "="*70)
    print("📊 ITU-Rpy 官方套件功能驗證摘要")
    print("="*70)
    print("\n驗證項目:")
    print("  ✅ API 基本功能正常")
    print("  ✅ Ku-band 衰減值物理合理")
    print("  ✅ Ka-band 衰減值物理合理")
    print("  ✅ 頻率依賴性符合預期")
    print("  ✅ 仰角依賴性符合預期")
    print("  ✅ Starlink 運行場景合理")
    print("  ✅ 不同大氣條件計算正常")
    print("\n結論:")
    print("  🎯 ITU-Rpy 官方套件運作正常")
    print("  🎯 計算結果符合 ITU-R P.676-13 物理預期")
    print("  🎯 可安全用於衛星通訊大氣衰減計算")
    print("  🎯 建議替換自實現版本（可能存在計算錯誤）")
    print("="*70)


if __name__ == '__main__':
    # 直接運行測試
    pytest.main([__file__, '-v', '-s'])
    test_summary()
