#!/usr/bin/env python3
"""
Stage 5 Data Integration - Integration Tests

測試Stage 5 v2.0模組化架構的完整集成功能：
1. DataIntegrationProcessor主處理器
2. TimeseriesConverter時間序列轉換
3. AnimationBuilder動畫數據建構
4. LayeredDataGenerator分層數據生成
5. FormatConverterHub多格式轉換

⚡ Grade A測試標準：
- 完整的功能測試覆蓋
- 真實數據模擬測試
- 性能基準測試
- 錯誤處理測試
"""

import unittest
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add project root to path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Stage 5模組化組件
from src.stages.stage5_data_integration.data_integration_processor import DataIntegrationProcessor
from src.stages.stage5_data_integration.timeseries_converter import TimeseriesConverter
from src.stages.stage5_data_integration.animation_builder import AnimationBuilder
from src.stages.stage5_data_integration.layered_data_generator import LayeredDataGenerator
from src.stages.stage5_data_integration.format_converter_hub import FormatConverterHub

class TestStage5DataIntegration(unittest.TestCase):
    """Stage 5數據整合完整測試套件"""

    def setUp(self):
        """測試設置"""
        # v2.0測試配置
        self.test_config = {
            'timeseries': {
                'sampling_frequency': '10S',
                'interpolation_method': 'cubic_spline',
                'compression_enabled': True,
                'compression_level': 6
            },
            'animation': {
                'frame_rate': 30,
                'duration_seconds': 300,
                'keyframe_optimization': True,
                'effect_quality': 'high'
            },
            'layers': {
                'spatial_resolution_levels': 5,
                'temporal_granularity': ['1MIN', '10MIN', '1HOUR'],
                'quality_tiers': ['high', 'medium', 'low'],
                'enable_spatial_indexing': True
            },
            'formats': {
                'output_formats': ['json', 'geojson', 'csv', 'api_package'],
                'schema_version': '2.0',
                'api_version': 'v2',
                'compression_enabled': True
            }
        }

        # 創建測試用的Stage 4輸出數據
        self.test_stage4_data = self._create_test_stage4_data()

        # 初始化Stage 5處理器
        self.processor = DataIntegrationProcessor(self.test_config)

    def _create_test_stage4_data(self) -> Dict[str, Any]:
        """創建測試用的Stage 4輸出數據"""
        base_time = datetime.now(timezone.utc)

        # 模擬優化池數據
        optimal_pool = {
            'satellites': [
                {
                    'satellite_id': 'STARLINK-1001',
                    'name': 'Starlink-1001',
                    'constellation': 'Starlink',
                    'stage1_orbital': {
                        'position_velocity': {
                            'position': {'x': 6678.0, 'y': 0.0, 'z': 0.0, 'latitude': 0.0, 'longitude': 0.0, 'altitude': 550.0},
                            'velocity': {'vx': 0.0, 'vy': 7.66, 'vz': 0.0}
                        }
                    },
                    'position_timeseries': [
                        {'x_km': 6678.0, 'y_km': 0.0, 'z_km': 0.0, 'latitude_deg': 0.0, 'longitude_deg': 0.0, 'altitude_km': 550.0}
                    ],
                    'rsrp': -85.0,
                    'snr': 12.5
                },
                {
                    'satellite_id': 'ONEWEB-2001',
                    'name': 'OneWeb-2001',
                    'constellation': 'OneWeb',
                    'stage1_orbital': {
                        'position_velocity': {
                            'position': {'x': 7178.0, 'y': 0.0, 'z': 0.0, 'latitude': 45.0, 'longitude': 90.0, 'altitude': 1200.0},
                            'velocity': {'vx': 0.0, 'vy': 7.35, 'vz': 0.0}
                        }
                    },
                    'position_timeseries': [
                        {'x_km': 7178.0, 'y_km': 0.0, 'z_km': 0.0, 'latitude_deg': 45.0, 'longitude_deg': 90.0, 'altitude_km': 1200.0}
                    ],
                    'rsrp': -90.0,
                    'snr': 10.0
                },
                {
                    'satellite_id': 'KUIPER-3001',
                    'name': 'Kuiper-3001',
                    'constellation': 'Kuiper',
                    'stage1_orbital': {
                        'position_velocity': {
                            'position': {'x': 6928.0, 'y': 0.0, 'z': 0.0, 'latitude': -30.0, 'longitude': 180.0, 'altitude': 630.0},
                            'velocity': {'vx': 0.0, 'vy': 7.55, 'vz': 0.0}
                        }
                    },
                    'position_timeseries': [
                        {'x_km': 6928.0, 'y_km': 0.0, 'z_km': 0.0, 'latitude_deg': -30.0, 'longitude_deg': 180.0, 'altitude_km': 630.0}
                    ],
                    'rsrp': -75.0,
                    'snr': 15.0
                }
            ],
            'metadata': {
                'processing_timestamp': base_time.isoformat(),
                'start_time': base_time.isoformat(),
                'end_time': (base_time + timedelta(minutes=5)).isoformat(),
                'total_satellites': 3
            }
        }

        # 模擬優化結果
        optimization_results = {
            'optimization_summary': {
                'satellites_optimized': 3,
                'optimization_method': 'genetic_algorithm',
                'performance_improvement': 0.85
            }
        }

        return {
            'optimal_pool': optimal_pool,
            'optimization_results': optimization_results,
            'metadata': {
                'processing_timestamp': base_time.isoformat(),
                'stage': 'stage4_optimization',
                'processed_satellites': 3
            }
        }

    def test_complete_data_integration_pipeline(self):
        """測試完整的數據整合流水線"""
        print("\n🚀 測試完整的數據整合流水線...")

        start_time = time.time()

        # 執行完整的Stage 5處理
        result = self.processor.process(self.test_stage4_data)

        processing_time = time.time() - start_time

        # 驗證基本結構
        self.assertIn('stage', result)
        self.assertEqual(result['stage'], 'stage5_data_integration')

        # 驗證數據組件
        self.assertIn('timeseries_data', result)
        self.assertIn('animation_data', result)
        self.assertIn('hierarchical_data', result)
        self.assertIn('formatted_outputs', result)
        self.assertIn('metadata', result)

        # 驗證性能目標
        self.assertLess(processing_time, 60.0, "處理時間應少於60秒")

        # 驗證壓縮比
        metadata = result.get('metadata', {})
        compression_ratio = metadata.get('compression_ratio', 0.0)
        self.assertGreater(compression_ratio, 0.5, "壓縮比應大於50%")

        print(f"✅ 完整流水線測試通過 ({processing_time:.2f}秒)")

    def test_timeseries_converter_functionality(self):
        """測試時間序列轉換器功能"""
        print("\n⏰ 測試時間序列轉換器...")

        converter = TimeseriesConverter(self.test_config['timeseries'])
        optimal_pool = self.test_stage4_data['optimal_pool']

        # 測試基本轉換
        timeseries_data = converter.convert_to_timeseries(optimal_pool)

        self.assertIn('dataset_id', timeseries_data)
        self.assertIn('satellite_count', timeseries_data)
        self.assertIn('time_index', timeseries_data)
        self.assertIn('satellite_timeseries', timeseries_data)

        # 驗證衛星數量
        self.assertEqual(timeseries_data['satellite_count'], 3)

        # 測試時間窗口生成
        window_data = converter.generate_time_windows(timeseries_data, 600)
        self.assertIn('windows', window_data)
        self.assertIn('total_windows', window_data)

        # 測試插值
        interpolated_data = converter.interpolate_missing_data(timeseries_data)
        self.assertIn('metadata', interpolated_data)
        self.assertTrue(interpolated_data['metadata'].get('interpolation_applied', False))

        # 測試壓縮
        compressed_data = converter.compress_timeseries(interpolated_data)
        self.assertIsInstance(compressed_data, bytes)

        # 測試解壓縮
        decompressed_data = converter.decompress_timeseries(compressed_data)
        self.assertIn('dataset_id', decompressed_data)

        print("✅ 時間序列轉換器測試通過")

    def test_animation_builder_functionality(self):
        """測試動畫建構器功能"""
        print("\n🎬 測試動畫建構器...")

        # 先生成時間序列數據
        converter = TimeseriesConverter(self.test_config['timeseries'])
        timeseries_data = converter.convert_to_timeseries(self.test_stage4_data['optimal_pool'])

        # 測試動畫建構
        builder = AnimationBuilder(self.test_config['animation'])
        animation_data = builder.build_satellite_animation(timeseries_data)

        self.assertIn('animation_id', animation_data)
        self.assertIn('duration', animation_data)
        self.assertIn('frame_rate', animation_data)
        self.assertIn('satellite_trajectories', animation_data)
        self.assertIn('coverage_animation', animation_data)

        # 驗證動畫參數
        self.assertEqual(animation_data['frame_rate'], 30)
        self.assertEqual(animation_data['duration'], 300)

        # 測試軌跡關鍵幀生成
        satellite_timeseries = timeseries_data.get('satellite_timeseries', {})
        if satellite_timeseries:
            sat_id = list(satellite_timeseries.keys())[0]
            sat_data = satellite_timeseries[sat_id]

            trajectory = builder.generate_trajectory_keyframes(sat_data)
            self.assertIn('satellite_id', trajectory)
            self.assertIn('keyframes', trajectory)
            self.assertIn('orbital_path', trajectory)

        # 測試覆蓋動畫
        coverage_animation = builder.create_coverage_animation(self.test_stage4_data['optimal_pool'])
        self.assertIn('animation_id', coverage_animation)
        self.assertIn('frames', coverage_animation)

        print("✅ 動畫建構器測試通過")

    def test_layer_data_generator_functionality(self):
        """測試分層數據生成器功能"""
        print("\n🗂️ 測試分層數據生成器...")

        # 生成時間序列數據
        converter = TimeseriesConverter(self.test_config['timeseries'])
        timeseries_data = converter.convert_to_timeseries(self.test_stage4_data['optimal_pool'])

        # 測試分層數據生成
        generator = LayeredDataGenerator(self.test_config['layers'])

        # 測試階層式數據集
        hierarchical_data = generator.generate_hierarchical_data(timeseries_data)
        self.assertIn('dataset_id', hierarchical_data)
        self.assertIn('constellation_hierarchy', hierarchical_data)
        self.assertIn('quality_hierarchy', hierarchical_data)
        self.assertIn('temporal_hierarchy', hierarchical_data)
        self.assertIn('geographic_hierarchy', hierarchical_data)

        # 測試空間分層
        spatial_layers = generator.create_spatial_layers(self.test_stage4_data['optimal_pool'])
        self.assertIsInstance(spatial_layers, dict)
        self.assertGreater(len(spatial_layers), 0)

        # 測試時間分層
        temporal_layers = generator.create_temporal_layers(timeseries_data)
        self.assertIsInstance(temporal_layers, dict)
        self.assertGreater(len(temporal_layers), 0)

        # 測試多尺度索引
        hierarchical_combined = {
            'hierarchical_dataset': hierarchical_data,
            'spatial_layers': spatial_layers,
            'temporal_layers': temporal_layers
        }

        multi_scale_index = generator.build_multi_scale_index(hierarchical_combined)
        self.assertIn('spatial_index', multi_scale_index)
        self.assertIn('temporal_index', multi_scale_index)
        self.assertIn('quality_index', multi_scale_index)
        self.assertIn('composite_index', multi_scale_index)

        print("✅ 分層數據生成器測試通過")

    def test_format_converter_hub_functionality(self):
        """測試格式轉換中心功能"""
        print("\n📦 測試格式轉換中心...")

        converter_hub = FormatConverterHub(self.test_config['formats'])

        # 創建測試數據
        test_data = {
            'timeseries_data': {'satellite_count': 3},
            'animation_data': {'frame_count': 100},
            'hierarchical_data': {'spatial_layers': {}},
            'metadata': {'processed_satellites': 3, 'processing_duration_seconds': 45.5}
        }

        # 測試JSON轉換
        json_result = converter_hub.convert_to_json(test_data)
        self.assertIn('metadata', json_result)
        self.assertIn('data', json_result)
        self.assertIn('schema_version', json_result['metadata'])

        # 測試GeoJSON轉換
        spatial_data = {'test_layer': {'grid_data': {'grid_cells': {}}}}
        geojson_result = converter_hub.convert_to_geojson(spatial_data)
        self.assertEqual(geojson_result['type'], 'FeatureCollection')
        self.assertIn('features', geojson_result)

        # 測試CSV轉換
        tabular_data = [
            {'timestamp': '2025-01-01T00:00:00Z', 'satellite_id': 'TEST-1', 'latitude': 0.0, 'longitude': 0.0},
            {'timestamp': '2025-01-01T00:01:00Z', 'satellite_id': 'TEST-2', 'latitude': 45.0, 'longitude': 90.0}
        ]
        csv_result = converter_hub.convert_to_csv(tabular_data)
        self.assertIn('timestamp', csv_result)
        self.assertIn('satellite_id', csv_result)

        # 測試API包裝
        api_result = converter_hub.package_for_api(test_data)
        self.assertIn('api', api_result)
        self.assertIn('status', api_result)
        self.assertIn('data', api_result)
        self.assertEqual(api_result['status']['code'], 200)

        # 測試批量格式轉換
        batch_result = converter_hub.convert_multiple_formats(test_data, ['json', 'csv'])
        self.assertIn('results', batch_result)
        self.assertIn('statistics', batch_result)

        print("✅ 格式轉換中心測試通過")

    def test_performance_benchmarks(self):
        """測試性能基準"""
        print("\n⚡ 測試性能基準...")

        # 創建較大的測試數據集
        large_test_data = self._create_large_test_dataset(50)  # 50顆衛星

        start_time = time.time()
        result = self.processor.process(large_test_data)
        processing_time = time.time() - start_time

        # 驗證性能目標
        self.assertLess(processing_time, 60.0, f"50顆衛星處理時間應少於60秒，實際: {processing_time:.2f}秒")

        # 驗證記憶體效率（通過數據大小估算）
        result_size = len(str(result))
        self.assertLess(result_size, 100_000_000, "結果數據大小應合理")  # < 100MB字符串

        # 驗證壓縮比
        metadata = result.get('metadata', {})
        compression_ratio = metadata.get('compression_ratio', 0.0)
        self.assertGreater(compression_ratio, 0.7, f"壓縮比應大於70%，實際: {compression_ratio:.2f}")

        print(f"✅ 性能基準測試通過 ({processing_time:.2f}秒, 壓縮比: {compression_ratio:.2f})")

    def test_error_handling(self):
        """測試錯誤處理"""
        print("\n🚨 測試錯誤處理...")

        # 測試空輸入數據
        with self.assertRaises(Exception):
            self.processor.process({})

        # 測試缺少必需欄位
        incomplete_data = {
            'optimal_pool': {'satellites': []},  # 空衛星列表
            # 缺少 optimization_results
        }

        with self.assertRaises(Exception):
            self.processor.process(incomplete_data)

        # 測試格式轉換錯誤處理
        converter_hub = FormatConverterHub(self.test_config['formats'])

        # 測試無效數據的CSV轉換
        csv_result = converter_hub.convert_to_csv([])  # 空列表
        self.assertEqual(csv_result, "")

        print("✅ 錯誤處理測試通過")

    def test_data_quality_validation(self):
        """測試數據品質驗證"""
        print("\n🔍 測試數據品質驗證...")

        result = self.processor.process(self.test_stage4_data)

        # 檢查元數據完整性
        metadata = result.get('metadata', {})
        self.assertIn('processing_timestamp', metadata)
        self.assertIn('processed_satellites', metadata)
        self.assertIn('architecture_version', metadata)

        # 檢查統計資訊
        statistics = result.get('statistics', {})
        self.assertIn('satellites_processed', statistics)
        self.assertIn('timeseries_datapoints', statistics)
        self.assertIn('processing_duration', statistics)

        # 驗證數據一致性
        timeseries_data = result.get('timeseries_data', {})
        animation_data = result.get('animation_data', {})

        if timeseries_data and animation_data:
            # 衛星數量應該一致
            timeseries_satellites = len(timeseries_data.get('satellite_timeseries', {}))
            animation_satellites = len(animation_data.get('satellite_trajectories', {}))

            if timeseries_satellites > 0 and animation_satellites > 0:
                self.assertEqual(timeseries_satellites, animation_satellites,
                               "時間序列和動畫數據中的衛星數量應該一致")

        print("✅ 數據品質驗證測試通過")

    def _create_large_test_dataset(self, satellite_count: int) -> Dict[str, Any]:
        """創建大型測試數據集"""
        base_time = datetime.now(timezone.utc)

        satellites = []
        for i in range(satellite_count):
            satellites.append({
                'satellite_id': f'TEST-SAT-{i+1:04d}',
                'name': f'TestSat-{i+1}',
                'constellation': f'TestConstellation{(i % 5) + 1}',
                'stage1_orbital': {
                    'position_velocity': {
                        'position': {
                            'x': 6500.0 + i * 10,
                            'y': 0.0,
                            'z': 0.0,
                            'latitude': -90.0 + (180.0 * i / satellite_count),
                            'longitude': -180.0 + (360.0 * i / satellite_count),
                            'altitude': 500.0 + i * 10
                        },
                        'velocity': {'vx': 0.0, 'vy': 7.5, 'vz': 0.0}
                    }
                },
                'position_timeseries': [{
                    'x_km': 6500.0 + i * 10,
                    'y_km': 0.0,
                    'z_km': 0.0,
                    'latitude_deg': -90.0 + (180.0 * i / satellite_count),
                    'longitude_deg': -180.0 + (360.0 * i / satellite_count),
                    'altitude_km': 500.0 + i * 10
                }],
                'rsrp': -100.0 + (i % 30),
                'snr': 5.0 + (i % 20)
            })

        return {
            'optimal_pool': {
                'satellites': satellites,
                'metadata': {
                    'processing_timestamp': base_time.isoformat(),
                    'start_time': base_time.isoformat(),
                    'end_time': (base_time + timedelta(minutes=5)).isoformat(),
                    'total_satellites': satellite_count
                }
            },
            'optimization_results': {
                'optimization_summary': {
                    'satellites_optimized': satellite_count,
                    'optimization_method': 'genetic_algorithm',
                    'performance_improvement': 0.85
                }
            },
            'metadata': {
                'processing_timestamp': base_time.isoformat(),
                'stage': 'stage4_optimization',
                'processed_satellites': satellite_count
            }
        }

    def tearDown(self):
        """測試清理"""
        pass

def run_stage5_tests():
    """運行Stage 5測試套件"""
    print("🚀 開始Stage 5數據整合測試套件...")
    print("="*60)

    # 創建測試套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestStage5DataIntegration)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 測試結果摘要
    print("="*60)
    print(f"📊 測試結果摘要:")
    print(f"   總測試: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失敗: {len(result.failures)}")
    print(f"   錯誤: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ 失敗的測試:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")

    if result.errors:
        print(f"\n🚨 錯誤的測試:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ 總體成功率: {success_rate:.1f}%")

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_stage5_tests()
    exit(0 if success else 1)