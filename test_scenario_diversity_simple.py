#!/usr/bin/env python3
"""
簡化場景多樣性整合測試
直接測試 _generate_scenario_variants() 方法

測試目標:
1. 驗證場景變體生成器正確初始化
2. 驗證變體生成邏輯正常運作
3. 驗證輸出格式符合預期
"""

import sys
import os
import logging
from datetime import datetime, timezone

# 添加 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

print("=" * 80)
print("Stage 6 場景多樣性簡化測試 - Proposal 002 Phase 2")
print("=" * 80)
print()

# 設置測試模式
os.environ['ORBIT_ENGINE_TEST_MODE'] = '1'

# ========== Step 1: 準備配置 ==========
print("📋 Step 1: 準備測試配置...")

config = {
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

print("✅ 配置準備完成")
print()

# ========== Step 2: 創建場景變體生成器 ==========
print("🎲 Step 2: 直接創建場景變體生成器...")

try:
    from stages.stage6_research_optimization.traffic_profile_generator import create_default_traffic_generator
    from stages.stage6_research_optimization.satellite_load_simulator import create_default_load_simulator
    from stages.stage6_research_optimization.scenario_variant_generator import ScenarioVariantGenerator

    logger = logging.getLogger(__name__)

    # 創建組件
    traffic_gen = create_default_traffic_generator(logger)
    load_sim = create_default_load_simulator(logger)

    variant_config = config['scenario_diversity']['scenario_generation']
    variant_generator = ScenarioVariantGenerator(traffic_gen, load_sim, variant_config, logger)

    print(f"✅ 場景變體生成器創建成功")
    print(f"   預期變體數: {variant_generator.expected_variants_per_sample} 個/樣本")

except Exception as e:
    print(f"❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ========== Step 3: 準備測試數據 ==========
print("📦 Step 3: 準備測試數據...")

# 模擬 connectable_satellites 數據
test_satellite_ids = ['54133', '58179', '54146', '47135', '52719']
base_sample_id = "test_sample_001"

print(f"✅ 測試數據準備完成")
print(f"   Base sample ID: {base_sample_id}")
print(f"   Satellite IDs: {test_satellite_ids}")
print()

# ========== Step 4: 生成場景變體 ==========
print("⚙️  Step 4: 生成場景變體...")

try:
    variants = variant_generator.generate_variants(
        base_sample_id=base_sample_id,
        satellite_ids=test_satellite_ids,
        timestamp_index=0
    )

    print(f"✅ 場景變體生成成功")
    print(f"   Total variants: {len(variants)}")

except Exception as e:
    print(f"❌ 變體生成失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ========== Step 5: 驗證變體內容 ==========
print("🔍 Step 5: 驗證變體內容...")

# 獲取統計信息
stats = variant_generator.get_variant_statistics(variants)

print(f"✅ 變體統計:")
print(f"   Total variants: {stats['total_variants']}")
print(f"   Traffic types: {stats['traffic_type_counts']}")
print(f"   Load patterns: {stats['load_pattern_counts']}")
print(f"   Unique base samples: {stats['unique_base_samples']}")

# 驗證覆蓋率
is_valid = variant_generator.validate_variant_coverage(variants)

if is_valid:
    print(f"✅ 覆蓋率驗證: PASSED")
else:
    print(f"❌ 覆蓋率驗證: FAILED")

print()

# ========== Step 6: 顯示變體示例 ==========
print("📝 Step 6: 顯示變體示例 (前 6 個)...")

for i, variant in enumerate(variants[:6], 1):
    print(f"   {i}. {variant.variant_id}")
    print(f"      Traffic: {variant.get_traffic_type()}")
    print(f"      Load: {variant.get_load_pattern()}")
    print(f"      Satellites: {len(variant.satellite_loads)}")

print()

# ========== Step 7: 詳細檢查一個變體 ==========
print("🔬 Step 7: 詳細檢查變體 #1...")

example = variants[0]
variant_dict = example.to_dict()

print(f"   Variant ID: {variant_dict['variant_id']}")
print(f"   Base sample ID: {variant_dict['base_sample_id']}")
print(f"   Variant index: {variant_dict['variant_index']}/{variant_dict['total_variants']}")

# 檢查 traffic profile
traffic_profile = variant_dict['traffic_profile']
print(f"\n   Traffic Profile:")
print(f"     Type: {traffic_profile['type']}")
print(f"     Category: {traffic_profile['category']}")
print(f"     Max delay: {traffic_profile['max_delay_ms']} ms")
print(f"     Min bandwidth: {traffic_profile['min_bandwidth_kbps']} kbps")
print(f"     Min reliability: {traffic_profile['min_reliability']}")
print(f"     Priority: {traffic_profile['priority']}")

# 檢查 satellite loads
satellite_loads = variant_dict['satellite_loads']
print(f"\n   Satellite Loads ({len(satellite_loads)} satellites):")
for i, load in enumerate(satellite_loads[:3], 1):
    print(f"     {i}. {load['satellite_id']}: {load['current_users']}/{load['capacity']} users ({load['utilization']:.1%}) - {load['load_state']}")

print()

# ========== Summary ==========
print("=" * 80)
print("測試總結")
print("=" * 80)

tests_passed = 0
total_tests = 5

# Test 1: 變體數量正確
expected_count = 12  # 4 traffic × 3 load
if len(variants) == expected_count:
    print(f"✅ Test 1: 變體數量正確 ({len(variants)}/{expected_count})")
    tests_passed += 1
else:
    print(f"❌ Test 1: 變體數量錯誤 ({len(variants)}/{expected_count})")

# Test 2: 流量類型覆蓋完整
expected_traffic = 4
actual_traffic = len(stats['traffic_type_counts'])
if actual_traffic == expected_traffic:
    print(f"✅ Test 2: 流量類型覆蓋完整 ({actual_traffic}/{expected_traffic})")
    tests_passed += 1
else:
    print(f"❌ Test 2: 流量類型覆蓋不完整 ({actual_traffic}/{expected_traffic})")

# Test 3: 負載模式覆蓋完整
expected_load = 3
actual_load = len(stats['load_pattern_counts'])
if actual_load == expected_load:
    print(f"✅ Test 3: 負載模式覆蓋完整 ({actual_load}/{expected_load})")
    tests_passed += 1
else:
    print(f"❌ Test 3: 負載模式覆蓋不完整 ({actual_load}/{expected_load})")

# Test 4: 覆蓋率驗證通過
if is_valid:
    print(f"✅ Test 4: 覆蓋率驗證通過")
    tests_passed += 1
else:
    print(f"❌ Test 4: 覆蓋率驗證失敗")

# Test 5: 變體包含必要字段
required_fields = ['variant_id', 'base_sample_id', 'traffic_profile', 'satellite_loads', 'variant_index', 'total_variants']
example_dict = variants[0].to_dict()
has_all_fields = all(field in example_dict for field in required_fields)
if has_all_fields:
    print(f"✅ Test 5: 變體包含所有必要字段")
    tests_passed += 1
else:
    missing = [f for f in required_fields if f not in example_dict]
    print(f"❌ Test 5: 變體缺少字段: {missing}")

print()
print(f"測試結果: {tests_passed}/{total_tests} 通過")

if tests_passed == total_tests:
    print("\n🎉 所有測試通過！場景多樣性模組正常運作！")
    sys.exit(0)
else:
    print(f"\n⚠️  部分測試失敗 ({total_tests - tests_passed} 個)")
    sys.exit(1)
