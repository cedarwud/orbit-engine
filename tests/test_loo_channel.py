#!/usr/bin/env python3
"""
單元測試: Loo Channel Model

測試 Proposal 002 的 Loo 通道模型實現
SOURCE: Loo, C. (1985) IEEE Transactions on Vehicular Technology, 34(3), 122-127
"""
import sys
import unittest
import logging
sys.path.insert(0, 'src')

from stages.stage5_signal_analysis.three_state_markov import PropagationState
from stages.stage5_signal_analysis.loo_channel import (
    Environment,
    LooChannelConfig,
    LooChannelModel
)

# 禁用日誌輸出
logging.disable(logging.CRITICAL)


class TestEnvironment(unittest.TestCase):
    """測試 Environment enum"""

    def test_environment_values(self):
        """測試環境值正確"""
        self.assertEqual(Environment.OPEN.value, "open")
        self.assertEqual(Environment.SUBURBAN.value, "suburban")
        self.assertEqual(Environment.URBAN.value, "urban")


class TestLooChannelConfig(unittest.TestCase):
    """測試 LooChannelConfig dataclass"""

    def test_default_config(self):
        """測試預設配置"""
        config = LooChannelConfig()
        self.assertEqual(config.environment, Environment.SUBURBAN)
        self.assertEqual(config.carrier_frequency_ghz, 12.0)
        self.assertEqual(config.random_seed, 42)

    def test_custom_config(self):
        """測試自定義配置"""
        config = LooChannelConfig(
            environment=Environment.URBAN,
            carrier_frequency_ghz=28.0,
            mp_mean_db=-8.0,
            sigma_db=5.0,
            random_seed=123
        )
        self.assertEqual(config.environment, Environment.URBAN)
        self.assertEqual(config.carrier_frequency_ghz, 28.0)
        self.assertEqual(config.mp_mean_db, -8.0)
        self.assertEqual(config.sigma_db, 5.0)
        self.assertEqual(config.random_seed, 123)


class TestLooChannelModel(unittest.TestCase):
    """測試 LooChannelModel 類"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)

    def test_initialization_suburban(self):
        """測試 Suburban 環境初始化"""
        config = LooChannelConfig(environment=Environment.SUBURBAN)
        model = LooChannelModel(config, self.logger)

        # 檢查環境參數（Loo 1985 Table II）
        self.assertEqual(model.mp_mean_db, -15.0)
        self.assertEqual(model.sigma_db, 3.5)

    def test_initialization_open(self):
        """測試 Open 環境初始化"""
        config = LooChannelConfig(environment=Environment.OPEN)
        model = LooChannelModel(config, self.logger)

        # 檢查環境參數（Loo 1985 Table II）
        self.assertEqual(model.mp_mean_db, -20.0)
        self.assertEqual(model.sigma_db, 2.0)

    def test_initialization_urban(self):
        """測試 Urban 環境初始化"""
        config = LooChannelConfig(environment=Environment.URBAN)
        model = LooChannelModel(config, self.logger)

        # 檢查環境參數（Loo 1985 Table II）
        self.assertEqual(model.mp_mean_db, -10.0)
        self.assertEqual(model.sigma_db, 6.0)

    def test_environment_parameters_loaded(self):
        """測試環境參數正確加載"""
        for env in [Environment.OPEN, Environment.SUBURBAN, Environment.URBAN]:
            config = LooChannelConfig(environment=env)
            model = LooChannelModel(config, self.logger)

            # 所有環境都應該有負的多徑平均功率
            self.assertLess(model.mp_mean_db, 0.0,
                          f"{env.value} should have negative multipath mean power")

            # 所有環境都應該有正的陰影標準差
            self.assertGreater(model.sigma_db, 0.0,
                             f"{env.value} should have positive shadow std dev")

    def test_los_component_different_states(self):
        """測試不同狀態的 LOS 分量"""
        config = LooChannelConfig(environment=Environment.SUBURBAN, random_seed=42)
        model = LooChannelModel(config, self.logger)

        los_los = model.compute_los_component_db(PropagationState.LOS)
        los_shadowed = model.compute_los_component_db(PropagationState.SHADOWED)
        los_blocked = model.compute_los_component_db(PropagationState.BLOCKED)

        # LOS 狀態應該有最高的 LOS 分量功率（最小衰減）
        self.assertGreater(los_los, los_shadowed,
                          "LOS state should have higher LOS component than Shadowed")
        self.assertGreater(los_shadowed, los_blocked,
                          "Shadowed state should have higher LOS component than Blocked")

    def test_blocked_state_high_attenuation(self):
        """測試 Blocked 狀態高衰減"""
        config = LooChannelConfig(environment=Environment.SUBURBAN, random_seed=42)
        model = LooChannelModel(config, self.logger)

        los_blocked = model.compute_los_component_db(PropagationState.BLOCKED)

        # Blocked 狀態應該有非常低的 LOS 分量（高衰減）
        # 實現中使用 -60 dB 作為 Blocked 狀態的衰減
        self.assertLess(los_blocked, -50.0,
                       "Blocked state should have very low LOS component (< -50 dB)")

    def test_multipath_component_reproducibility(self):
        """測試多徑分量可重現性"""
        config1 = LooChannelConfig(environment=Environment.SUBURBAN, random_seed=42)
        config2 = LooChannelConfig(environment=Environment.SUBURBAN, random_seed=42)

        model1 = LooChannelModel(config1, self.logger)
        model2 = LooChannelModel(config2, self.logger)

        # 相同種子應該產生相同的多徑分量序列
        mp1 = [model1.compute_multipath_component_db() for _ in range(10)]
        mp2 = [model2.compute_multipath_component_db() for _ in range(10)]

        for i, (v1, v2) in enumerate(zip(mp1, mp2)):
            self.assertAlmostEqual(v1, v2, places=5,
                                  msg=f"Multipath component {i} should match")

    def test_free_space_path_loss(self):
        """測試自由空間路徑損耗計算"""
        config = LooChannelConfig(carrier_frequency_ghz=12.0)
        model = LooChannelModel(config, self.logger)

        # 計算不同距離的路徑損耗
        fspl_near = model.compute_free_space_path_loss_db(500.0, 12.0)  # 500 km
        fspl_far = model.compute_free_space_path_loss_db(1000.0, 12.0)  # 1000 km

        # 距離加倍應該增加約 6 dB 損耗（20*log10(2) ≈ 6 dB）
        loss_increase = fspl_far - fspl_near
        self.assertAlmostEqual(loss_increase, 6.02, places=1,
                              msg="Doubling distance should increase FSPL by ~6 dB")

        # 路徑損耗應該為正且合理範圍
        self.assertGreater(fspl_near, 0.0, "FSPL should be positive")
        self.assertLess(fspl_near, 250.0, "FSPL should be reasonable (< 250 dB)")

    def test_atmospheric_attenuation(self):
        """測試大氣衰減計算"""
        config = LooChannelConfig(carrier_frequency_ghz=12.0)
        model = LooChannelModel(config, self.logger)

        # 計算不同仰角的大氣衰減
        atm_low = model.compute_atmospheric_attenuation_db(10.0)   # 低仰角
        atm_high = model.compute_atmospheric_attenuation_db(80.0)  # 高仰角

        # 低仰角應該有更高的大氣衰減（路徑更長）
        self.assertGreater(atm_low, atm_high,
                          "Lower elevation should have higher atmospheric attenuation")

        # 大氣衰減應該為正且合理範圍
        self.assertGreater(atm_low, 0.0, "Atmospheric attenuation should be positive")
        self.assertLess(atm_low, 10.0, "Atmospheric attenuation should be < 10 dB")

    def test_total_attenuation_calculation(self):
        """測試總衰減計算"""
        config = LooChannelConfig(
            environment=Environment.SUBURBAN,
            carrier_frequency_ghz=12.0,
            random_seed=42
        )
        model = LooChannelModel(config, self.logger)

        # 計算總衰減
        total_atten = model.compute_total_attenuation_db(
            PropagationState.LOS,
            elevation_deg=45.0,
            distance_km=800.0
        )

        # 總衰減應該為正且在合理範圍內
        self.assertGreater(total_atten, 0.0, "Total attenuation should be positive")
        self.assertGreater(total_atten, 100.0, "Total attenuation should be > 100 dB")
        self.assertLess(total_atten, 250.0, "Total attenuation should be < 250 dB")

    def test_distance_effect_on_attenuation(self):
        """測試距離對衰減的影響"""
        config = LooChannelConfig(
            environment=Environment.SUBURBAN,
            carrier_frequency_ghz=12.0,
            random_seed=42
        )
        model = LooChannelModel(config, self.logger)

        atten_near = model.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 500.0
        )
        atten_far = model.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 1000.0
        )

        # 距離增加應該增加衰減
        self.assertGreater(atten_far, atten_near,
                          "Greater distance should increase attenuation")

    def test_elevation_effect_on_attenuation(self):
        """測試仰角對衰減的影響"""
        config = LooChannelConfig(
            environment=Environment.SUBURBAN,
            carrier_frequency_ghz=12.0,
            random_seed=42
        )
        model = LooChannelModel(config, self.logger)

        atten_low = model.compute_total_attenuation_db(
            PropagationState.LOS, 10.0, 800.0
        )
        atten_high = model.compute_total_attenuation_db(
            PropagationState.LOS, 80.0, 800.0
        )

        # 低仰角應該有更高的衰減（大氣路徑更長）
        self.assertGreater(atten_low, atten_high,
                          "Lower elevation should have higher attenuation")

    def test_state_effect_on_attenuation(self):
        """測試傳播狀態對衰減的影響"""
        config = LooChannelConfig(
            environment=Environment.SUBURBAN,
            carrier_frequency_ghz=12.0,
            random_seed=42
        )
        model = LooChannelModel(config, self.logger)

        atten_los = model.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 800.0
        )
        atten_blocked = model.compute_total_attenuation_db(
            PropagationState.BLOCKED, 45.0, 800.0
        )

        # Blocked 狀態應該有更高的衰減
        self.assertGreater(atten_blocked, atten_los,
                          "Blocked state should have higher attenuation than LOS")

        # 差異應該顯著（至少 40 dB）
        self.assertGreater(atten_blocked - atten_los, 40.0,
                          "Attenuation difference should be significant (> 40 dB)")


class TestLooChannelEdgeCases(unittest.TestCase):
    """測試邊界情況"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)

    def test_extreme_low_elevation(self):
        """測試極低仰角"""
        config = LooChannelConfig(carrier_frequency_ghz=12.0)
        model = LooChannelModel(config, self.logger)

        # 應該不會崩潰
        atten = model.compute_total_attenuation_db(
            PropagationState.LOS, 0.1, 800.0
        )
        self.assertGreater(atten, 0.0)

    def test_extreme_high_elevation(self):
        """測試極高仰角"""
        config = LooChannelConfig(carrier_frequency_ghz=12.0)
        model = LooChannelModel(config, self.logger)

        # 應該不會崩潰
        atten = model.compute_total_attenuation_db(
            PropagationState.LOS, 89.9, 800.0
        )
        self.assertGreater(atten, 0.0)

    def test_short_distance(self):
        """測試短距離"""
        config = LooChannelConfig(carrier_frequency_ghz=12.0)
        model = LooChannelModel(config, self.logger)

        # 應該不會崩潰
        atten = model.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 100.0
        )
        self.assertGreater(atten, 0.0)

    def test_long_distance(self):
        """測試長距離"""
        config = LooChannelConfig(carrier_frequency_ghz=12.0)
        model = LooChannelModel(config, self.logger)

        # 應該不會崩潰
        atten = model.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 2000.0
        )
        self.assertGreater(atten, 0.0)


if __name__ == '__main__':
    # 運行測試
    unittest.main(verbosity=2)
