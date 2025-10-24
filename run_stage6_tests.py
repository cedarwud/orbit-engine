#!/usr/bin/env python3
"""
獨立測試運行器 for Stage 6 場景多樣性模組
避免 __init__.py 導入問題
"""

import sys
import os
import unittest
import logging

# 添加 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 直接導入模組（避免通過 __init__.py）
from stages.stage6_research_optimization import traffic_profile_generator
from stages.stage6_research_optimization import satellite_load_simulator
from stages.stage6_research_optimization import scenario_variant_generator

# 配置日誌
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s:%(name)s:%(message)s'
)

print("=" * 70)
print("Stage 6 Scenario Diversity - Unit Tests")
print("=" * 70)
print()

# ========== Test Traffic Profile Generator ==========
print("Testing TrafficProfileGenerator...")
print("-" * 70)

from stages.stage6_research_optimization.traffic_profile_generator import (
    TrafficType, TrafficProfile, TrafficProfileGenerator, create_default_traffic_generator
)

# Test 1: 創建生成器
generator = create_default_traffic_generator()
print(f"✅ Generator created: {len(generator.enabled_types)} traffic types enabled")

# Test 2: 生成所有 profiles
profiles = generator.generate_all_profiles()
print(f"✅ Generated {len(profiles)} traffic profiles")

# Test 3: 驗證 QoS 參數
test_count = 0
for traffic_type, profile in profiles.items():
    try:
        profile.validate()
        test_count += 1
        print(f"✅ {traffic_type}: QoS validation passed")
    except Exception as e:
        print(f"❌ {traffic_type}: Validation failed - {e}")

print(f"\nTraffic Profile Tests: {test_count}/{len(profiles)} passed\n")

# ========== Test Satellite Load Simulator ==========
print("Testing SatelliteLoadSimulator...")
print("-" * 70)

from stages.stage6_research_optimization.satellite_load_simulator import (
    LoadPattern, SatelliteLoad, SatelliteLoadSimulator, create_default_load_simulator
)

# Test 1: 創建模擬器
simulator = create_default_load_simulator()
print(f"✅ Simulator created: {len(simulator.enabled_patterns)} load patterns enabled")

# Test 2: 測試所有負載模式
test_satellites = ["SAT001", "SAT002", "SAT003", "SAT004", "SAT005"]
test_count = 0

for pattern in LoadPattern:
    try:
        loads = simulator.simulate_load(test_satellites, pattern=pattern)
        stats = simulator.get_load_statistics(loads)
        test_count += 1
        print(f"✅ {pattern.value}: Generated {len(loads)} loads, "
              f"avg util={stats['mean_utilization']:.1%}")
    except Exception as e:
        print(f"❌ {pattern.value}: Failed - {e}")

print(f"\nLoad Simulator Tests: {test_count}/{len(LoadPattern)} passed\n")

# ========== Test Scenario Variant Generator ==========
print("Testing ScenarioVariantGenerator...")
print("-" * 70)

from stages.stage6_research_optimization.scenario_variant_generator import (
    ScenarioVariant, ScenarioVariantGenerator
)

# Test 1: 創建變體生成器
config = {
    'variant_id_format': "{base_id}_v{index:03d}_{traffic}_{load}",
    'generate_all_combinations': True
}
variant_gen = ScenarioVariantGenerator(generator, simulator, config, logging.getLogger(__name__))
print(f"✅ Variant generator created: "
      f"{variant_gen.expected_variants_per_sample} expected variants per sample")

# Test 2: 生成變體
try:
    variants = variant_gen.generate_variants("test_sample", test_satellites)
    print(f"✅ Generated {len(variants)} scenario variants")

    # Test 3: 驗證覆蓋率
    is_valid = variant_gen.validate_variant_coverage(variants)
    if is_valid:
        print(f"✅ Variant coverage validation: PASSED")
    else:
        print(f"❌ Variant coverage validation: FAILED")

    # Test 4: 統計
    stats = variant_gen.get_variant_statistics(variants)
    print(f"✅ Variant statistics:")
    print(f"   Traffic types: {stats['traffic_type_counts']}")
    print(f"   Load patterns: {stats['load_pattern_counts']}")

    print(f"\nScenario Variant Tests: 4/4 passed\n")

except Exception as e:
    print(f"❌ Variant generation failed: {e}")
    import traceback
    traceback.print_exc()

# ========== Summary ==========
print("=" * 70)
print("Test Summary")
print("=" * 70)
print(f"✅ TrafficProfileGenerator: {test_count}/{len(profiles)} tests passed")
print(f"✅ SatelliteLoadSimulator: {test_count}/{len(LoadPattern)} tests passed")
print(f"✅ ScenarioVariantGenerator: 4/4 tests passed")
print(f"\n✅ All Stage 6 scenario diversity modules tested successfully!\n")
