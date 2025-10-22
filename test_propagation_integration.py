#!/usr/bin/env python3
"""
測試 Propagation Simulator 整合到 Stage 5 的完整流程

此腳本驗證：
1. PropagationConditionSimulator 可以被正確初始化
2. TimeSeriesAnalyzer 可以接受 propagation_simulator 參數
3. 整個處理流程可以運行（不需要實際數據）
"""
import sys
sys.path.insert(0, 'src')

print("=" * 70)
print("✅ 測試 Propagation Simulator 整合")
print("=" * 70)

# Test 1: Import all modules
print("\n📦 測試 1: 導入所有模組...")
try:
    from stages.stage5_signal_analysis.propagation_simulator import (
        PropagationConditionSimulator, create_default_simulator
    )
    from stages.stage5_signal_analysis.three_state_markov import PropagationState, Environment
    from stages.stage5_signal_analysis.time_series_analyzer import create_time_series_analyzer
    print("   ✅ 所有模組導入成功")
except Exception as e:
    print(f"   ❌ 模組導入失敗: {e}")
    sys.exit(1)

# Test 2: Create propagation simulator
print("\n🔬 測試 2: 創建 PropagationConditionSimulator...")
try:
    import logging
    logging.basicConfig(level=logging.WARNING)  # 減少輸出
    logger = logging.getLogger(__name__)

    config = {
        'markov_model': {
            'random_seed': 42,
            'elevation_adjustment_enabled': True
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
except Exception as e:
    print(f"   ❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test simulation
print("\n🛰️  測試 3: 執行傳播條件模擬...")
try:
    result = prop_sim.simulate(
        satellite_id="TEST_SAT_001",
        timestamp="2025-10-22T12:00:00+00:00",
        elevation_deg=45.0,
        distance_km=800.0
    )
    print(f"   ✅ 模擬執行成功")
    print(f"   傳播狀態: {result.propagation_state}")
    print(f"   通道衰減: {result.channel_attenuation_db:.1f} dB")
    print(f"   LOS 分量: {result.los_component_db:.2f} dB")
    print(f"   多徑分量: {result.multipath_component_db:.2f} dB")
except Exception as e:
    print(f"   ❌ 模擬失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create TimeSeriesAnalyzer with propagation_simulator
print("\n📊 測試 4: 創建 TimeSeriesAnalyzer (含 propagation_simulator)...")
try:
    # 最小配置
    minimal_config = {
        'signal_calculator': {
            'bandwidth_mhz': 100.0,
            'subcarrier_spacing_khz': 30.0,
            'noise_figure_db': 7.0,
            'temperature_k': 290.0
        },
        'atmospheric_model': {
            'temperature_k': 283.0,
            'pressure_hpa': 1013.25,
            'water_vapor_density_g_m3': 7.5
        }
    }

    signal_thresholds = {
        'rsrp_excellent': -80.0,
        'rsrp_good': -90.0,
        'rsrp_fair': -100.0,
        'rsrp_poor': -110.0,
        'rsrp_minimum': -120.0,
        'rsrq_excellent': -10.0,
        'rsrq_good': -15.0,
        'rsrq_fair': -20.0,
        'sinr_excellent': 20.0,
        'sinr_good': 13.0
    }

    # 創建分析器（含 propagation_simulator）
    analyzer = create_time_series_analyzer(
        minimal_config,
        signal_thresholds,
        prop_sim  # 傳入 propagation_simulator
    )

    print(f"   ✅ TimeSeriesAnalyzer 創建成功")
    print(f"   propagation_simulator 已傳入: {analyzer.propagation_simulator is not None}")
except Exception as e:
    print(f"   ❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Verify propagation_simulator attribute
print("\n🔍 測試 5: 驗證 propagation_simulator 屬性...")
try:
    assert hasattr(analyzer, 'propagation_simulator'), "TimeSeriesAnalyzer 缺少 propagation_simulator 屬性"
    assert analyzer.propagation_simulator is not None, "propagation_simulator 應該不為 None"
    assert analyzer.propagation_simulator is prop_sim, "propagation_simulator 應該是同一個實例"
    print(f"   ✅ propagation_simulator 屬性驗證成功")
except AssertionError as e:
    print(f"   ❌ 驗證失敗: {e}")
    sys.exit(1)

# Test 6: Test multiple simulations (state tracking)
print("\n🔄 測試 6: 多次模擬（狀態追蹤）...")
try:
    results = []
    for i in range(5):
        result = prop_sim.simulate(
            satellite_id="TEST_SAT_001",
            timestamp=f"2025-10-22T12:00:{i:02d}+00:00",
            elevation_deg=45.0,
            distance_km=800.0
        )
        results.append(result)

    print(f"   ✅ 執行 5 次模擬成功")
    print(f"   狀態序列: {[r.propagation_state for r in results]}")

    # 檢查狀態追蹤
    stats = prop_sim.get_state_statistics()
    print(f"   追蹤的衛星數: {stats['total_satellites']}")
    print(f"   當前狀態: {prop_sim.current_states.get('TEST_SAT_001', 'N/A')}")
except Exception as e:
    print(f"   ❌ 多次模擬失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有測試通過！Propagation Simulator 整合驗證完成")
print("=" * 70)
print("\n📝 總結:")
print("   ✅ PropagationConditionSimulator 可以正確初始化")
print("   ✅ 傳播條件模擬可以執行")
print("   ✅ TimeSeriesAnalyzer 可以接受 propagation_simulator 參數")
print("   ✅ propagation_simulator 屬性正確設置")
print("   ✅ 狀態追蹤功能正常")
print("\n🎯 下一步: 執行完整的 Stage 5 測試")
print("   設置環境變數: export ORBIT_ENGINE_STAGE5_ENABLE_PROPAGATION_SIMULATION=true")
print("   執行 Stage 5: ./run.sh --stage 5")
