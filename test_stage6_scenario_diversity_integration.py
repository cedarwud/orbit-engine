#!/usr/bin/env python3
"""
Stage 6 場景多樣性整合測試
測試 Proposal 002 Phase 2 整合到 Stage 6 處理器

此測試驗證:
1. Stage 6 處理器正確初始化場景多樣性模組
2. 場景變體生成器正確調用
3. 輸出包含 scenario_variants 字段
4. 生成的變體數量符合預期（4 traffic × 3 load = 12）
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)

print("=" * 80)
print("Stage 6 場景多樣性整合測試 - Proposal 002 Phase 2")
print("=" * 80)
print()

# ========== Step 1: 創建測試配置 ==========
print("📋 Step 1: 創建測試配置...")

# 讀取完整的 Stage 6 配置
config_path = Path(__file__).parent / "config" / "stage6_research_optimization_config.yaml"

try:
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        stage6_config = yaml.safe_load(f)

    # 啟用場景多樣性
    if 'scenario_diversity' not in stage6_config:
        stage6_config['scenario_diversity'] = {}

    stage6_config['scenario_diversity']['enabled'] = True

    print(f"✅ 配置已載入並啟用場景多樣性")
    print(f"   Traffic types: {stage6_config['scenario_diversity'].get('traffic_profiles', {}).get('enabled_types', [])}")
    print(f"   Load patterns: {stage6_config['scenario_diversity'].get('satellite_load_simulation', {}).get('enabled_patterns', [])}")

except Exception as e:
    print(f"❌ 無法載入配置: {e}")
    print(f"   使用最小配置進行測試")
    stage6_config = {
        'scenario_diversity': {
            'enabled': True,
            'traffic_profiles': {
                'enabled_types': ['voip', 'video', 'iot', 'best_effort'],
                'custom_parameters': {}
            },
            'satellite_load_simulation': {
                'capacity_per_satellite': 200,
                'enabled_patterns': ['uniform', 'concentrated', 'dynamic'],
                'random_seed': 42
            },
            'scenario_generation': {
                'variant_id_format': '{base_id}_v{index:03d}_{traffic}_{load}',
                'generate_all_combinations': True
            }
        }
    }

print()

# ========== Step 2: 創建模擬 Stage 5 輸出 ==========
print("📦 Step 2: 創建模擬 Stage 5 輸出數據...")

# 模擬的 Stage 5 輸出結構
mock_stage5_output = {
    'metadata': {
        'processing_timestamp': datetime.now(timezone.utc).isoformat(),
        'constellation_configs': {
            'starlink': {
                'elevation_threshold': 5.0,
                'target_count': 15
            },
            'oneweb': {
                'elevation_threshold': 10.0,
                'target_count': 6
            }
        },
        'dynamic_d2_thresholds': {
            'starlink': {
                'recommended_thresholds': {
                    'd2_threshold1_km': 1500.0,
                    'd2_threshold2_km': 1800.0
                }
            }
        }
    },
    'signal_analysis': {
        '54133': {
            'constellation': 'starlink',
            'physical_parameters': {
                'distance_km': 1432.5,
                'elevation_deg': 25.3,
                'azimuth_deg': 180.0
            },
            'time_series': [
                {
                    'timestamp': '2025-10-22T00:00:00Z',
                    'signal_quality': {
                        'rsrp_dbm': -35.18,
                        'rsrq_db': -10.5,
                        'sinr_db': 15.2
                    },
                    'physical_parameters': {
                        'distance_km': 1432.5,
                        'elevation_deg': 25.3,
                        'azimuth_deg': 180.0
                    },
                    'is_connectable': True
                }
            ],
            'summary': {
                'average_rsrp_dbm': -35.18,
                'average_quality_level': 'excellent',
                'link_margin_db': 12.5
            }
        },
        '58179': {
            'constellation': 'starlink',
            'physical_parameters': {
                'distance_km': 1205.2,
                'elevation_deg': 35.7,
                'azimuth_deg': 90.0
            },
            'time_series': [
                {
                    'timestamp': '2025-10-22T00:00:00Z',
                    'signal_quality': {
                        'rsrp_dbm': -31.14,
                        'rsrq_db': -9.8,
                        'sinr_db': 18.5
                    },
                    'physical_parameters': {
                        'distance_km': 1205.2,
                        'elevation_deg': 35.7,
                        'azimuth_deg': 90.0
                    },
                    'is_connectable': True
                }
            ],
            'summary': {
                'average_rsrp_dbm': -31.14,
                'average_quality_level': 'excellent',
                'link_margin_db': 15.8
            }
        },
        '54146': {
            'constellation': 'starlink',
            'physical_parameters': {
                'distance_km': 1350.0,
                'elevation_deg': 28.5,
                'azimuth_deg': 270.0
            },
            'time_series': [
                {
                    'timestamp': '2025-10-22T00:00:00Z',
                    'signal_quality': {
                        'rsrp_dbm': -34.43,
                        'rsrq_db': -10.2,
                        'sinr_db': 16.0
                    },
                    'physical_parameters': {
                        'distance_km': 1350.0,
                        'elevation_deg': 28.5,
                        'azimuth_deg': 270.0
                    },
                    'is_connectable': True
                }
            ],
            'summary': {
                'average_rsrp_dbm': -34.43,
                'average_quality_level': 'excellent',
                'link_margin_db': 13.2
            }
        }
    },
    'connectable_satellites': {
        'starlink': {
            'satellites': ['54133', '58179', '54146']
        },
        'oneweb': {
            'satellites': []
        }
    }
}

print(f"✅ 模擬數據已創建")
print(f"   Signal analysis: {len(mock_stage5_output['signal_analysis'])} satellites")
print(f"   Connectable satellites: {len(mock_stage5_output['connectable_satellites']['starlink']['satellites'])} (Starlink)")
print()

# ========== Step 3: 初始化 Stage 6 處理器 ==========
print("🤖 Step 3: 初始化 Stage 6 處理器...")

try:
    from stages.stage6_research_optimization.stage6_research_optimization_processor import (
        Stage6ResearchOptimizationProcessor
    )

    processor = Stage6ResearchOptimizationProcessor(config=stage6_config)

    print(f"✅ Stage 6 處理器初始化成功")
    print(f"   場景多樣性啟用: {processor.scenario_diversity_enabled}")
    if processor.variant_generator:
        print(f"   預期變體數: {processor.variant_generator.expected_variants_per_sample} 個/樣本")

except Exception as e:
    print(f"❌ Stage 6 處理器初始化失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ========== Step 4: 執行處理流程 ==========
print("⚙️  Step 4: 執行 Stage 6 處理流程...")

try:
    result = processor.process(mock_stage5_output)

    print(f"✅ Stage 6 處理完成")
    print(f"   Status: {result.status}")
    # ProcessingResult 的 metadata 中有 message
    msg = result.metadata.get('message', 'No message') if hasattr(result, 'metadata') else str(result.status)
    print(f"   Message: {msg}")

except Exception as e:
    print(f"❌ Stage 6 處理失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ========== Step 5: 驗證輸出包含場景變體 ==========
print("🔍 Step 5: 驗證輸出包含場景變體...")

output_data = result.data

if not output_data:
    print(f"❌ 輸出數據為空")
    sys.exit(1)

# 檢查 scenario_variants 字段
if 'scenario_variants' not in output_data:
    print(f"⚠️  輸出中缺少 scenario_variants 字段")
    print(f"   可用字段: {list(output_data.keys())}")
else:
    scenario_variants = output_data['scenario_variants']

    print(f"✅ scenario_variants 字段存在")
    print(f"   Enabled: {scenario_variants.get('enabled', False)}")
    print(f"   Generated: {scenario_variants.get('generated', False)}")

    if scenario_variants.get('generated'):
        total_variants = scenario_variants.get('total_variants', 0)
        stats = scenario_variants.get('statistics', {})

        print(f"   Total variants: {total_variants}")
        print(f"   Base sample ID: {scenario_variants.get('base_sample_id', 'N/A')}")
        print(f"   Coverage valid: {scenario_variants.get('coverage_valid', False)}")
        print(f"   Traffic types: {stats.get('traffic_type_counts', {})}")
        print(f"   Load patterns: {stats.get('load_pattern_counts', {})}")

        # 驗證變體數量
        expected_variants = 4 * 3  # 4 traffic types × 3 load patterns
        if total_variants == expected_variants:
            print(f"   ✅ 變體數量正確: {total_variants} == {expected_variants}")
        else:
            print(f"   ⚠️  變體數量不符預期: {total_variants} != {expected_variants}")

        # 顯示前3個變體示例
        variants_list = scenario_variants.get('variants', [])
        if variants_list:
            print(f"\n   📝 變體示例 (前3個):")
            for i, variant in enumerate(variants_list[:3], 1):
                print(f"      {i}. {variant['variant_id']}")
                print(f"         Traffic: {variant['traffic_profile']['type']}")
                print(f"         Load: {variant['satellite_loads'][0]['pattern'] if variant['satellite_loads'] else 'N/A'}")
    else:
        error = scenario_variants.get('error', 'Unknown error')
        print(f"   ❌ 變體生成失敗: {error}")

print()

# ========== Step 6: 檢查 metadata 統計 ==========
print("📊 Step 6: 檢查 metadata 統計...")

metadata = output_data.get('metadata', {})

if 'scenario_variants_generated' in metadata:
    print(f"✅ metadata 包含場景變體統計")
    print(f"   scenario_variants_generated: {metadata['scenario_variants_generated']}")
    print(f"   scenario_diversity_enabled: {metadata.get('scenario_diversity_enabled', False)}")
else:
    print(f"⚠️  metadata 缺少場景變體統計")

print()

# ========== Summary ==========
print("=" * 80)
print("測試總結")
print("=" * 80)

# 檢查所有關鍵指標
tests_passed = 0
total_tests = 4

# Test 1: 處理器初始化
if processor.scenario_diversity_enabled:
    print("✅ Test 1: 場景多樣性模組成功初始化")
    tests_passed += 1
else:
    print("❌ Test 1: 場景多樣性模組未初始化")

# Test 2: 輸出包含 scenario_variants
if 'scenario_variants' in output_data:
    print("✅ Test 2: 輸出包含 scenario_variants 字段")
    tests_passed += 1
else:
    print("❌ Test 2: 輸出缺少 scenario_variants 字段")

# Test 3: 變體成功生成
if output_data.get('scenario_variants', {}).get('generated'):
    print("✅ Test 3: 場景變體成功生成")
    tests_passed += 1
else:
    print("❌ Test 3: 場景變體生成失敗")

# Test 4: 變體數量正確
expected_count = 12
actual_count = output_data.get('scenario_variants', {}).get('total_variants', 0)
if actual_count == expected_count:
    print(f"✅ Test 4: 變體數量正確 ({actual_count}/{expected_count})")
    tests_passed += 1
else:
    print(f"❌ Test 4: 變體數量不正確 ({actual_count}/{expected_count})")

print()
print(f"測試結果: {tests_passed}/{total_tests} 通過")

if tests_passed == total_tests:
    print("\n🎉 所有測試通過！場景多樣性整合成功！")
    sys.exit(0)
else:
    print(f"\n⚠️  部分測試失敗 ({total_tests - tests_passed} 個)")
    sys.exit(1)
