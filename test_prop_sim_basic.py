#!/usr/bin/env python3
"""
基本測試：Propagation Simulator 模組功能

不依賴其他 Stage 5 模組，僅測試 propagation_simulator 本身
"""
import sys
sys.path.insert(0, 'src')

print("=" * 70)
print("✅ 測試 Propagation Simulator 基本功能")
print("=" * 70)

# Test 1: Import propagation simulator modules
print("\n📦 測試 1: 導入 propagation simulator 模組...")
try:
    from stages.stage5_signal_analysis.three_state_markov import (
        PropagationState, MarkovConfig, ThreeStateMarkovModel
    )
    from stages.stage5_signal_analysis.loo_channel import (
        Environment, LooChannelConfig, LooChannelModel
    )
    from stages.stage5_signal_analysis.propagation_simulator import (
        PropagationConditionSimulator, PropagationResult, create_default_simulator
    )
    print("   ✅ 所有 propagation 模組導入成功")
except Exception as e:
    print(f"   ❌ 模組導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create propagation simulator with config
print("\n🔬 測試 2: 創建 PropagationConditionSimulator...")
try:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = {
        'markov_model': {
            'P_LL': 0.95, 'P_LS': 0.04, 'P_LB': 0.01,
            'P_SL': 0.10, 'P_SS': 0.80, 'P_SB': 0.10,
            'P_BL': 0.05, 'P_BS': 0.15, 'P_BB': 0.80,
            'elevation_adjustment_enabled': True,
            'random_seed': 42
        },
        'loo_channel': {
            'environment': 'suburban',
            'carrier_frequency_ghz': 12.0,
            'random_seed': 42
        },
        'initial_state': 'LOS'
    }

    prop_sim = PropagationConditionSimulator(config, logger)
    print(f"   ✅ PropagationConditionSimulator 創建成功")
    print(f"   環境: {prop_sim.loo_model.config.environment.value}")
    print(f"   初始狀態: {prop_sim.initial_state.name}")
    print(f"   Markov seed: {prop_sim.markov_model.config.random_seed}")
    print(f"   Loo seed: {prop_sim.loo_model.config.random_seed}")
except Exception as e:
    print(f"   ❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Single simulation
print("\n🛰️  測試 3: 執行單次傳播條件模擬...")
try:
    result = prop_sim.simulate(
        satellite_id="46061",
        timestamp="2025-10-22T01:53:00+00:00",
        elevation_deg=45.0,
        distance_km=800.0
    )
    print(f"   ✅ 模擬執行成功")
    print(f"   衛星 ID: {result.satellite_id}")
    print(f"   時間戳: {result.timestamp}")
    print(f"   傳播狀態: {result.propagation_state}")
    print(f"   通道衰減: {result.channel_attenuation_db:.1f} dB")
    print(f"   LOS 分量: {result.los_component_db:.2f} dB")
    print(f"   多徑分量: {result.multipath_component_db:.2f} dB")
    print(f"   仰角: {result.elevation_deg}°")
    print(f"   距離: {result.distance_km} km")
    print(f"   環境: {result.environment}")
except Exception as e:
    print(f"   ❌ 模擬失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Multiple simulations with state tracking
print("\n🔄 測試 4: 多次模擬（狀態追蹤）...")
try:
    sat_id = "46061"
    results = []
    for i in range(10):
        result = prop_sim.simulate(
            satellite_id=sat_id,
            timestamp=f"2025-10-22T01:53:{i:02d}+00:00",
            elevation_deg=45.0,
            distance_km=800.0
        )
        results.append(result)

    print(f"   ✅ 執行 10 次模擬成功")

    # 顯示狀態序列
    states = [r.propagation_state for r in results]
    print(f"   狀態序列: {states}")

    # 統計狀態分布
    from collections import Counter
    state_counts = Counter(states)
    print(f"   狀態分布:")
    for state, count in state_counts.items():
        pct = (count / len(states)) * 100
        print(f"      {state}: {count}/10 = {pct:.1f}%")

    # 檢查狀態追蹤
    stats = prop_sim.get_state_statistics()
    print(f"   追蹤的衛星數: {stats['total_satellites']}")
    print(f"   當前狀態: {prop_sim.current_states[sat_id].name}")
except Exception as e:
    print(f"   ❌ 多次模擬失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Multiple satellites
print("\n🛰️🛰️  測試 5: 多顆衛星模擬...")
try:
    satellite_ids = ["46061", "54133", "58179"]
    for sat_id in satellite_ids:
        result = prop_sim.simulate(
            satellite_id=sat_id,
            timestamp="2025-10-22T02:00:00+00:00",
            elevation_deg=40.0 + (int(sat_id) % 20),  # 不同仰角
            distance_km=750.0 + (int(sat_id) % 200)   # 不同距離
        )
        print(f"   衛星 {sat_id}: {result.propagation_state} "
              f"(elevation={result.elevation_deg:.1f}°, "
              f"attenuation={result.channel_attenuation_db:.1f} dB)")

    stats = prop_sim.get_state_statistics()
    print(f"   ✅ 多衛星模擬成功")
    print(f"   追蹤的衛星數: {stats['total_satellites']}")
    print(f"   狀態分布:")
    for state, count in stats['state_counts'].items():
        pct = stats['state_percentages'][state]
        print(f"      {state}: {count} ({pct:.1f}%)")
except Exception as e:
    print(f"   ❌ 多衛星模擬失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: JSON serialization
print("\n📄 測試 6: JSON 序列化...")
try:
    result = prop_sim.simulate(
        satellite_id="TEST_SAT",
        timestamp="2025-10-22T03:00:00+00:00",
        elevation_deg=60.0,
        distance_km=700.0
    )

    result_dict = result.to_dict()
    print(f"   ✅ to_dict() 成功")
    print(f"   輸出鍵: {list(result_dict.keys())}")

    # 驗證關鍵欄位
    assert 'satellite_id' in result_dict
    assert 'timestamp' in result_dict
    assert 'propagation_state' in result_dict
    assert 'state_probabilities' in result_dict
    assert 'channel_attenuation_db' in result_dict
    assert 'environment' in result_dict
    print(f"   ✅ 所有關鍵欄位存在")

    # 測試 JSON 序列化
    import json
    json_str = json.dumps(result_dict, indent=2)
    print(f"   ✅ JSON 序列化成功 ({len(json_str)} 字符)")
except Exception as e:
    print(f"   ❌ JSON 序列化失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: State reset
print("\n🔄 測試 7: 狀態重置...")
try:
    # 重置前
    stats_before = prop_sim.get_state_statistics()
    print(f"   重置前: {stats_before['total_satellites']} 顆衛星")

    # 重置所有衛星
    prop_sim.reset_state()

    # 重置後
    stats_after = prop_sim.get_state_statistics()
    print(f"   重置後: {stats_after['total_satellites']} 顆衛星")

    assert stats_after['total_satellites'] == 0, "重置後應該沒有衛星"
    print(f"   ✅ 狀態重置成功")
except Exception as e:
    print(f"   ❌ 狀態重置失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有測試通過！Propagation Simulator 基本功能驗證完成")
print("=" * 70)
print("\n📝 驗證結果:")
print("   ✅ 模組可以正確導入")
print("   ✅ PropagationConditionSimulator 可以初始化")
print("   ✅ 單次模擬執行正常")
print("   ✅ 多次模擬與狀態追蹤正常")
print("   ✅ 多衛星模擬正常")
print("   ✅ JSON 序列化正常")
print("   ✅ 狀態重置功能正常")
print("\n🎯 下一步: 執行完整的 Stage 5 整合測試")
print("   1. 編譯檢查所有修改的文件:")
print("      python3 -m py_compile src/stages/stage5_signal_analysis/*.py")
print("   2. 啟用 propagation simulation:")
print("      修改 config/stage5_signal_analysis_config.yaml")
print("      設置 enable_propagation_simulation: true")
print("   3. 執行 Stage 5:")
print("      ./run.sh --stage 5")
