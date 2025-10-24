"""
Unit tests for Traffic Profile Generator

Tests the traffic profile generation module for RL training scenario diversity.

SOURCE: Stage 6 場景多樣性生成 - Proposal 002
"""

import unittest
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stages.stage6_research_optimization.traffic_profile_generator import (
    TrafficType,
    TrafficProfile,
    TrafficProfileGenerator,
    create_default_traffic_generator
)


class TestTrafficType(unittest.TestCase):
    """測試 TrafficType Enum"""

    def test_enum_values(self):
        """測試 enum 值正確"""
        self.assertEqual(TrafficType.VOIP.value, "voip")
        self.assertEqual(TrafficType.VIDEO.value, "video")
        self.assertEqual(TrafficType.IOT.value, "iot")
        self.assertEqual(TrafficType.BEST_EFFORT.value, "best_effort")

    def test_enum_count(self):
        """測試有 4 種流量類型"""
        self.assertEqual(len(TrafficType), 4)


class TestTrafficProfile(unittest.TestCase):
    """測試 TrafficProfile Dataclass"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)

    def test_profile_creation(self):
        """測試建立流量 profile"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=150.0,
            min_bandwidth_kbps=64.0,
            min_reliability=0.99,
            priority=1,
            description="Test VoIP",
            use_cases=["Test"]
        )

        self.assertEqual(profile.type, "voip")
        self.assertEqual(profile.max_delay_ms, 150.0)
        self.assertEqual(profile.min_bandwidth_kbps, 64.0)
        self.assertEqual(profile.min_reliability, 0.99)
        self.assertEqual(profile.priority, 1)

    def test_to_dict(self):
        """測試轉換為字典"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=150.0,
            min_bandwidth_kbps=64.0,
            min_reliability=0.99,
            priority=1,
            description="Test",
            use_cases=[]
        )

        profile_dict = profile.to_dict()
        self.assertIsInstance(profile_dict, dict)
        self.assertEqual(profile_dict['type'], "voip")
        self.assertEqual(profile_dict['max_delay_ms'], 150.0)

    def test_validate_valid_profile(self):
        """測試驗證有效的 profile"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=150.0,
            min_bandwidth_kbps=64.0,
            min_reliability=0.99,
            priority=1,
            description="Test",
            use_cases=[]
        )

        # 應該不拋出異常
        self.assertTrue(profile.validate())

    def test_validate_invalid_delay(self):
        """測試驗證無效延遲"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=-10.0,  # 無效：負數
            min_bandwidth_kbps=64.0,
            min_reliability=0.99,
            priority=1,
            description="Test",
            use_cases=[]
        )

        with self.assertRaises(ValueError):
            profile.validate()

    def test_validate_invalid_bandwidth(self):
        """測試驗證無效頻寬"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=150.0,
            min_bandwidth_kbps=0.0,  # 無效：零
            min_reliability=0.99,
            priority=1,
            description="Test",
            use_cases=[]
        )

        with self.assertRaises(ValueError):
            profile.validate()

    def test_validate_invalid_reliability(self):
        """測試驗證無效可靠性"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=150.0,
            min_bandwidth_kbps=64.0,
            min_reliability=1.5,  # 無效：>1.0
            priority=1,
            description="Test",
            use_cases=[]
        )

        with self.assertRaises(ValueError):
            profile.validate()

    def test_validate_invalid_priority(self):
        """測試驗證無效優先級"""
        profile = TrafficProfile(
            type="voip",
            category="conversational",
            max_delay_ms=150.0,
            min_bandwidth_kbps=64.0,
            min_reliability=0.99,
            priority=10,  # 無效：>5
            description="Test",
            use_cases=[]
        )

        with self.assertRaises(ValueError):
            profile.validate()


class TestTrafficProfileGenerator(unittest.TestCase):
    """測試 TrafficProfileGenerator 類"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)
        self.config = {
            'enabled_types': ['voip', 'video', 'iot', 'best_effort'],
            'custom_parameters': {}
        }
        self.generator = TrafficProfileGenerator(self.config, self.logger)

    def test_initialization(self):
        """測試生成器初始化"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(len(self.generator.enabled_types), 4)

    def test_generate_voip_profile(self):
        """測試生成 VoIP profile（3GPP 標準）"""
        profile = self.generator.generate_profile(TrafficType.VOIP)

        # 驗證類型
        self.assertEqual(profile.type, "voip")
        self.assertEqual(profile.category, "conversational")

        # 驗證 QoS 參數（3GPP TS 22.261 Annex A.1）
        self.assertEqual(profile.max_delay_ms, 150.0)
        self.assertEqual(profile.min_bandwidth_kbps, 64.0)
        self.assertEqual(profile.min_reliability, 0.99)
        self.assertEqual(profile.priority, 1)

        # 驗證可選參數
        self.assertEqual(profile.max_jitter_ms, 30.0)
        self.assertEqual(profile.max_packet_loss_rate, 0.01)

    def test_generate_video_profile(self):
        """測試生成 Video profile（3GPP 標準）"""
        profile = self.generator.generate_profile(TrafficType.VIDEO)

        # 驗證類型
        self.assertEqual(profile.type, "video")
        self.assertEqual(profile.category, "streaming")

        # 驗證 QoS 參數（3GPP TS 22.261 Annex A.2）
        self.assertEqual(profile.max_delay_ms, 400.0)
        self.assertEqual(profile.min_bandwidth_kbps, 5000.0)  # 5 Mbps
        self.assertEqual(profile.min_reliability, 0.95)
        self.assertEqual(profile.priority, 2)

    def test_generate_iot_profile(self):
        """測試生成 IoT profile（3GPP 標準）"""
        profile = self.generator.generate_profile(TrafficType.IOT)

        # 驗證類型
        self.assertEqual(profile.type, "iot")
        self.assertEqual(profile.category, "non_critical_iot")

        # 驗證 QoS 參數（3GPP TS 22.261 Annex A.5）
        self.assertEqual(profile.max_delay_ms, 5000.0)  # 5 seconds
        self.assertEqual(profile.min_bandwidth_kbps, 10.0)
        self.assertEqual(profile.min_reliability, 0.90)
        self.assertEqual(profile.priority, 4)

    def test_generate_best_effort_profile(self):
        """測試生成 BestEffort profile（3GPP 標準）"""
        profile = self.generator.generate_profile(TrafficType.BEST_EFFORT)

        # 驗證類型
        self.assertEqual(profile.type, "best_effort")
        self.assertEqual(profile.category, "background")

        # 驗證 QoS 參數（3GPP TS 22.261 Annex A.6）
        self.assertEqual(profile.max_delay_ms, 10000.0)  # 10 seconds
        self.assertEqual(profile.min_bandwidth_kbps, 100.0)
        self.assertEqual(profile.min_reliability, 0.80)
        self.assertEqual(profile.priority, 5)

    def test_generate_all_profiles(self):
        """測試生成所有 profiles"""
        profiles = self.generator.generate_all_profiles()

        # 驗證數量
        self.assertEqual(len(profiles), 4)

        # 驗證包含所有類型
        self.assertIn('voip', profiles)
        self.assertIn('video', profiles)
        self.assertIn('iot', profiles)
        self.assertIn('best_effort', profiles)

        # 驗證每個都是 TrafficProfile 實例
        for traffic_type, profile in profiles.items():
            self.assertIsInstance(profile, TrafficProfile)
            self.assertEqual(profile.type, traffic_type)

    def test_custom_parameters(self):
        """測試自定義參數覆蓋"""
        custom_config = {
            'enabled_types': ['voip'],
            'custom_parameters': {
                'voip': {
                    'max_delay_ms': 100.0,  # 覆蓋預設 150.0
                    'min_bandwidth_kbps': 128.0  # 覆蓋預設 64.0
                }
            }
        }

        generator = TrafficProfileGenerator(custom_config, self.logger)
        profile = generator.generate_profile(TrafficType.VOIP)

        # 驗證自定義參數生效
        self.assertEqual(profile.max_delay_ms, 100.0)
        self.assertEqual(profile.min_bandwidth_kbps, 128.0)

        # 驗證其他參數仍使用預設值
        self.assertEqual(profile.min_reliability, 0.99)

    def test_disabled_traffic_type(self):
        """測試停用的流量類型"""
        config = {
            'enabled_types': ['voip'],  # 只啟用 VoIP
            'custom_parameters': {}
        }
        generator = TrafficProfileGenerator(config, self.logger)

        # VoIP 應該可以生成
        profile_voip = generator.generate_profile(TrafficType.VOIP)
        self.assertIsNotNone(profile_voip)

        # Video 應該拋出異常
        with self.assertRaises(ValueError):
            generator.generate_profile(TrafficType.VIDEO)

    def test_profile_summary(self):
        """測試 profile 摘要生成"""
        profile = self.generator.generate_profile(TrafficType.VOIP)
        summary = self.generator.get_profile_summary(profile)

        # 驗證摘要包含關鍵信息
        self.assertIn("VOIP", summary)
        self.assertIn("150.0 ms", summary)
        self.assertIn("64.0 kbps", summary)
        self.assertIn("99.0%", summary)


class TestCreateDefaultTrafficGenerator(unittest.TestCase):
    """測試便利函數"""

    def test_create_default_generator(self):
        """測試創建預設生成器"""
        generator = create_default_traffic_generator()

        self.assertIsNotNone(generator)
        self.assertEqual(len(generator.enabled_types), 4)

        # 驗證可以生成所有類型
        profiles = generator.generate_all_profiles()
        self.assertEqual(len(profiles), 4)


class TestTrafficProfileQoSCompliance(unittest.TestCase):
    """測試 QoS 參數符合 3GPP 標準"""

    def setUp(self):
        """每個測試前初始化"""
        self.logger = logging.getLogger(__name__)
        self.generator = create_default_traffic_generator(self.logger)

    def test_voip_qos_compliance(self):
        """測試 VoIP QoS 符合 3GPP TS 22.261 Annex A.1"""
        profile = self.generator.generate_profile(TrafficType.VOIP)

        # 3GPP TS 22.261 Annex A.1 要求
        self.assertLessEqual(profile.max_delay_ms, 150.0)
        self.assertGreaterEqual(profile.min_reliability, 0.99)
        self.assertEqual(profile.priority, 1)  # 最高優先級

    def test_video_qos_compliance(self):
        """測試 Video QoS 符合 3GPP TS 22.261 Annex A.2"""
        profile = self.generator.generate_profile(TrafficType.VIDEO)

        # 3GPP TS 22.261 Annex A.2 要求
        self.assertLessEqual(profile.max_delay_ms, 400.0)
        self.assertGreaterEqual(profile.min_reliability, 0.95)
        self.assertGreaterEqual(profile.min_bandwidth_kbps, 5000.0)  # HD streaming

    def test_iot_qos_compliance(self):
        """測試 IoT QoS 符合 3GPP TS 22.261 Annex A.5"""
        profile = self.generator.generate_profile(TrafficType.IOT)

        # 3GPP TS 22.261 Annex A.5 要求
        self.assertGreaterEqual(profile.min_reliability, 0.90)
        self.assertEqual(profile.priority, 4)  # 低優先級

    def test_priority_ordering(self):
        """測試優先級順序正確（VoIP > Video > IoT > BestEffort）"""
        profiles = self.generator.generate_all_profiles()

        voip_priority = profiles['voip'].priority
        video_priority = profiles['video'].priority
        iot_priority = profiles['iot'].priority
        best_effort_priority = profiles['best_effort'].priority

        # 驗證優先級順序（數字越小優先級越高）
        self.assertLess(voip_priority, video_priority)
        self.assertLess(video_priority, iot_priority)
        self.assertLess(iot_priority, best_effort_priority)


if __name__ == '__main__':
    # 配置日誌
    logging.basicConfig(
        level=logging.WARNING,  # 測試時降低日誌級別
        format='%(levelname)s:%(name)s:%(message)s'
    )

    # 運行測試
    unittest.main(verbosity=2)
