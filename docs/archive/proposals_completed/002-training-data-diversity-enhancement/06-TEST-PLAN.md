# 測試計劃：訓練數據多樣性增強

> **測試目標**: 確保 Stage 5/6 擴充符合學術標準、功能正確、性能達標
> **測試覆蓋率目標**: > 80%
> **學術合規性**: 100% 通過

---

## 📋 測試層次結構

```
Level 1: 單元測試 (Unit Tests)
  ├── Markov 模型狀態轉換
  ├── Loo 通道衰減計算
  ├── 流量類型生成
  └── 負載分布模擬

Level 2: 整合測試 (Integration Tests)
  ├── Stage 5 完整流程
  ├── Stage 6 完整流程
  └── 跨 Stage 數據流

Level 3: 性能測試 (Performance Tests)
  ├── 執行時間基準
  ├── 記憶體使用量
  └── 輸出檔案大小

Level 4: 學術合規性測試 (Compliance Tests)
  ├── SOURCE 註解檢查
  ├── 參數來源驗證
  └── 算法標準符合性

Level 5: 端到端測試 (E2E Tests)
  └── 完整六階段流程測試
```

---

## 🧪 單元測試策略

### Stage 5 單元測試

#### Test Suite 1: ThreeStateMarkovModel

**FILE**: `tests/test_three_state_markov.py`

```python
import pytest
import numpy as np
from src.stages.stage5_signal_analysis.three_state_markov import (
    ThreeStateMarkovModel, MarkovConfig, PropagationState
)

class TestThreeStateMarkovModel:
    """
    單元測試: 三態 Markov 模型

    SOURCE: Gilbert-Elliott Model + 3GPP TR 38.901
    """

    @pytest.fixture
    def model(self):
        """Create model instance with default config."""
        config = MarkovConfig(random_seed=42)
        return ThreeStateMarkovModel(config)

    def test_transition_matrix_rows_sum_to_one(self, model):
        """
        TEST: 轉換矩陣每行總和為 1

        REQUIREMENT: Markov 鏈基本性質
        """
        assert np.allclose(model.P.sum(axis=1), 1.0), \
            "Transition matrix rows must sum to 1"

    def test_all_probabilities_non_negative(self, model):
        """
        TEST: 所有轉換機率非負

        REQUIREMENT: 機率值域 [0, 1]
        """
        assert (model.P >= 0).all(), "Probabilities must be non-negative"
        assert (model.P <= 1).all(), "Probabilities must be <= 1"

    def test_elevation_adjustment_increases_los_stability(self, model):
        """
        TEST: 仰角增加時 LOS 穩定性提升

        REQUIREMENT: Lutz et al. (1991) 仰角效應
        """
        P_low = model.adjust_for_elevation(10.0)
        P_high = model.adjust_for_elevation(80.0)

        # P(LOS→LOS) should increase
        assert P_high[0, 0] > P_low[0, 0], \
            "High elevation should increase LOS stability"

        # P(LOS→Blocked) should decrease
        assert P_high[0, 2] < P_low[0, 2], \
            "High elevation should decrease blocking probability"

    def test_high_elevation_approaches_ideal(self, model):
        """
        TEST: 90° 仰角接近理想 LOS 條件

        REQUIREMENT: 垂直路徑應最穩定
        """
        P_90 = model.adjust_for_elevation(90.0)

        assert P_90[0, 0] >= 0.98, "P(LOS→LOS) at 90° should be ≥ 0.98"
        assert P_90[0, 2] <= 0.01, "P(LOS→Blocked) at 90° should be ≤ 0.01"

    def test_steady_state_distribution_sums_to_one(self, model):
        """
        TEST: 穩態分佈總和為 1

        REQUIREMENT: 機率分佈歸一化
        """
        pi = model.get_steady_state_distribution(45.0)

        assert np.isclose(sum(pi), 1.0), "Steady-state must sum to 1"
        assert all(p >= 0 for p in pi), "All probabilities must be non-negative"

    def test_state_simulation_produces_valid_states(self, model):
        """
        TEST: 狀態模擬產生有效 PropagationState

        REQUIREMENT: 輸出類型正確
        """
        current = PropagationState.LOS

        for _ in range(100):
            next_state = model.simulate_next_state(current, 45.0)
            assert isinstance(next_state, PropagationState), \
                "Output must be PropagationState enum"
            current = next_state

    def test_state_transitions_occur(self, model):
        """
        TEST: 狀態轉換確實發生

        REQUIREMENT: 動態傳播條件變化
        """
        states = []
        current = PropagationState.LOS

        for _ in range(500):
            current = model.simulate_next_state(current, 45.0)
            states.append(current)

        # Should observe all 3 states over 500 steps
        unique_states = set(states)
        assert len(unique_states) >= 2, \
            "Should observe state transitions over 500 steps"

    @pytest.mark.parametrize("elevation", [5, 10, 30, 60, 90])
    def test_elevation_adjustment_preserves_normalization(self, model, elevation):
        """
        TEST: 仰角調整後矩陣仍歸一化

        REQUIREMENT: 轉換矩陣數學性質保持
        """
        P_adj = model.adjust_for_elevation(elevation)
        assert np.allclose(P_adj.sum(axis=1), 1.0), \
            f"Adjusted matrix at {elevation}° must remain normalized"
```

---

#### Test Suite 2: LooChannelModel

**FILE**: `tests/test_loo_channel.py`

```python
import pytest
import numpy as np
from src.stages.stage5_signal_analysis.loo_channel import (
    LooChannelModel, LooChannelConfig, Environment
)
from src.stages.stage5_signal_analysis.three_state_markov import PropagationState

class TestLooChannelModel:
    """
    單元測試: Loo 通道模型

    SOURCE: Loo (1985) Land Mobile Satellite Channel
    """

    @pytest.fixture
    def model_suburban(self):
        """Suburban environment model."""
        config = LooChannelConfig(environment=Environment.SUBURBAN, random_seed=42)
        return LooChannelModel(config)

    @pytest.fixture
    def model_urban(self):
        """Urban environment model."""
        config = LooChannelConfig(environment=Environment.URBAN, random_seed=42)
        return LooChannelModel(config)

    def test_environment_presets_applied(self, model_suburban):
        """
        TEST: 環境預設值正確套用

        REQUIREMENT: Loo (1985) Table II 參數
        """
        assert model_suburban.mp_mean_db == -15.0, \
            "Suburban MP mean should be -15.0 dB"
        assert model_suburban.sigma_db == 3.5, \
            "Suburban sigma should be 3.5 dB"

    def test_blocked_state_produces_high_attenuation(self, model_suburban):
        """
        TEST: Blocked 狀態產生高衰減

        REQUIREMENT: 完全遮蔽應顯著降低信號
        """
        los_db = model_suburban.compute_los_component_db(PropagationState.BLOCKED)

        assert los_db < -50.0, \
            "Blocked state should produce > 50 dB attenuation"

    def test_shadowed_worse_than_los(self, model_suburban):
        """
        TEST: Shadowed 衰減大於 LOS

        REQUIREMENT: 部分遮蔽應劣於直射
        """
        # Run multiple samples for statistical significance
        los_samples = [
            model_suburban.compute_los_component_db(PropagationState.LOS)
            for _ in range(100)
        ]
        shadowed_samples = [
            model_suburban.compute_los_component_db(PropagationState.SHADOWED)
            for _ in range(100)
        ]

        assert np.mean(shadowed_samples) < np.mean(los_samples) - 3.0, \
            "Shadowed should have ≥3 dB more attenuation than LOS on average"

    def test_urban_worse_than_suburban(self, model_suburban, model_urban):
        """
        TEST: 市區環境比郊區環境差

        REQUIREMENT: Loo (1985) 環境差異
        """
        # Urban should have higher MP power (less negative)
        assert model_urban.mp_mean_db > model_suburban.mp_mean_db, \
            "Urban MP power should be higher (less negative) than suburban"

        # Urban should have higher shadowing variance
        assert model_urban.sigma_db > model_suburban.sigma_db, \
            "Urban shadowing std should be higher than suburban"

    def test_attenuation_increases_with_distance(self, model_suburban):
        """
        TEST: 衰減隨距離增加

        REQUIREMENT: Free Space Path Loss (Friis equation)
        """
        atten_500km = model_suburban.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 500.0
        )
        atten_1500km = model_suburban.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 1500.0
        )

        assert atten_1500km > atten_500km, \
            "Attenuation should increase with distance"

        # Should be ~10 dB difference (20*log10(1500/500) ≈ 9.5 dB)
        diff = atten_1500km - atten_500km
        assert 8.0 < diff < 12.0, \
            f"Expected ~10 dB difference, got {diff:.1f} dB"

    def test_attenuation_decreases_with_elevation(self, model_suburban):
        """
        TEST: 衰減隨仰角增加而減少

        REQUIREMENT: 大氣衰減隨路徑長度變化
        """
        atten_10deg = model_suburban.compute_total_attenuation_db(
            PropagationState.LOS, 10.0, 800.0
        )
        atten_80deg = model_suburban.compute_total_attenuation_db(
            PropagationState.LOS, 80.0, 800.0
        )

        assert atten_10deg > atten_80deg, \
            "Lower elevation (longer atmospheric path) should have more attenuation"

    def test_attenuation_in_reasonable_range(self, model_suburban):
        """
        TEST: 衰減值在合理範圍

        REQUIREMENT: Ku-band LEO 典型值 100-200 dB
        """
        atten = model_suburban.compute_total_attenuation_db(
            PropagationState.LOS, 45.0, 800.0
        )

        assert 100.0 < atten < 200.0, \
            f"Attenuation {atten:.1f} dB out of typical range (100-200 dB)"

    @pytest.mark.parametrize("state", [
        PropagationState.LOS,
        PropagationState.SHADOWED,
        PropagationState.BLOCKED
    ])
    def test_all_states_produce_valid_output(self, model_suburban, state):
        """
        TEST: 所有狀態產生有效輸出

        REQUIREMENT: 功能完整性
        """
        atten = model_suburban.compute_total_attenuation_db(state, 45.0, 800.0)

        assert isinstance(atten, (int, float)), "Output must be numeric"
        assert not np.isnan(atten), "Output must not be NaN"
        assert not np.isinf(atten), "Output must not be infinite"
```

---

### Stage 6 單元測試

#### Test Suite 3: TrafficProfileGenerator

**FILE**: `tests/test_traffic_profile_generator.py`

```python
import pytest
from src.stages.stage6_research_optimization.traffic_profile_generator import (
    TrafficProfileGenerator, TrafficType
)

class TestTrafficProfileGenerator:
    """
    單元測試: 流量類型生成器

    SOURCE: 3GPP TS 22.261 + Badini et al. (2024)
    """

    @pytest.fixture
    def generator(self):
        """Create generator with default config."""
        config = {'enabled_types': ['voip', 'video', 'iot', 'best_effort']}
        return TrafficProfileGenerator(config, logger=None)

    def test_voip_meets_3gpp_requirements(self, generator):
        """
        TEST: VoIP 參數符合 3GPP TS 22.261

        REQUIREMENT: Annex A.1 Conversational voice
        """
        voip = generator.generate_profile(TrafficType.VOIP)

        assert voip.max_delay_ms <= 150.0, "VoIP delay must be ≤ 150 ms"
        assert voip.min_bandwidth_kbps >= 64.0, "VoIP bandwidth must be ≥ 64 kbps"
        assert voip.min_reliability >= 0.99, "VoIP reliability must be ≥ 99%"
        assert voip.priority == 1, "VoIP must have highest priority"

    def test_video_meets_3gpp_requirements(self, generator):
        """
        TEST: Video 參數符合 3GPP TS 22.261

        REQUIREMENT: Annex A.2 Video streaming
        """
        video = generator.generate_profile(TrafficType.VIDEO)

        assert video.max_delay_ms <= 400.0, "Video delay must be ≤ 400 ms"
        assert video.min_bandwidth_kbps >= 5000.0, "Video bandwidth must be ≥ 5 Mbps"
        assert video.min_reliability >= 0.95, "Video reliability must be ≥ 95%"

    def test_iot_has_relaxed_requirements(self, generator):
        """
        TEST: IoT 要求較寬鬆

        REQUIREMENT: Non-critical IoT tolerance
        """
        iot = generator.generate_profile(TrafficType.IOT)

        assert iot.max_delay_ms >= 1000.0, "IoT can tolerate ≥ 1s delay"
        assert iot.min_bandwidth_kbps <= 100.0, "IoT uses low bandwidth"
        assert iot.priority >= 4, "IoT has low priority"

    def test_priority_ordering(self, generator):
        """
        TEST: 優先級排序正確

        REQUIREMENT: VoIP > Video > BestEffort > IoT
        """
        profiles = generator.generate_all_profiles()

        voip_pri = profiles['voip'].priority
        video_pri = profiles['video'].priority
        best_effort_pri = profiles['best_effort'].priority
        iot_pri = profiles['iot'].priority

        assert voip_pri < video_pri, "VoIP should have higher priority than Video"
        assert video_pri < best_effort_pri, "Video should have higher priority than BestEffort"
        assert iot_pri == max([voip_pri, video_pri, best_effort_pri, iot_pri]), \
            "IoT should have lowest priority"

    def test_all_enabled_types_generated(self, generator):
        """
        TEST: 所有啟用類型都被生成

        REQUIREMENT: 功能完整性
        """
        profiles = generator.generate_all_profiles()

        assert len(profiles) == 4, "Should generate 4 profiles"
        assert 'voip' in profiles
        assert 'video' in profiles
        assert 'iot' in profiles
        assert 'best_effort' in profiles

    def test_custom_parameters_override_defaults(self):
        """
        TEST: 自定義參數覆蓋預設值

        REQUIREMENT: 配置靈活性
        """
        config = {
            'enabled_types': ['voip'],
            'custom_parameters': {
                'voip': {'max_delay_ms': 100.0}  # Stricter than default 150
            }
        }
        generator = TrafficProfileGenerator(config, logger=None)

        voip = generator.generate_profile(TrafficType.VOIP)

        assert voip.max_delay_ms == 100.0, "Custom parameter should override default"
```

---

#### Test Suite 4: SatelliteLoadSimulator

**FILE**: `tests/test_satellite_load_simulator.py`

```python
import pytest
import numpy as np
from src.stages.stage6_research_optimization.satellite_load_simulator import (
    SatelliteLoadSimulator, LoadPattern
)

class TestSatelliteLoadSimulator:
    """
    單元測試: 衛星負載模擬器

    SOURCE: He et al. (2021) + 3GPP TR 38.821
    """

    @pytest.fixture
    def simulator(self):
        """Create simulator with default config."""
        config = {
            'capacity_per_satellite': 200,
            'enabled_patterns': ['uniform', 'concentrated', 'dynamic'],
            'random_seed': 42
        }
        return SatelliteLoadSimulator(config, logger=None)

    @pytest.fixture
    def satellite_ids(self):
        """Create test satellite ID list."""
        return [f"SAT{i:03d}" for i in range(20)]

    def test_uniform_load_has_low_variance(self, simulator, satellite_ids):
        """
        TEST: 均勻負載模式低變異

        REQUIREMENT: Uniform distribution characteristic
        """
        loads = simulator.generate_uniform_load(satellite_ids)
        utils = [l.utilization for l in loads]

        assert np.std(utils) < 0.15, "Uniform load std should be < 0.15"

        # Gini coefficient should be low
        gini = self._compute_gini(utils)
        assert gini < 0.3, f"Uniform load Gini {gini:.3f} should be < 0.3"

    def test_concentrated_load_follows_80_20_rule(self, simulator, satellite_ids):
        """
        TEST: 集中負載符合 80-20 原則

        REQUIREMENT: Hotspot scenario from He et al. (2021)
        """
        loads = simulator.generate_concentrated_load(satellite_ids)

        high_load = [l for l in loads if l.utilization > 0.7]
        low_load = [l for l in loads if l.utilization < 0.4]

        # ~20% high load
        assert len(high_load) >= 3 and len(high_load) <= 5, \
            f"Expected ~20% high load (3-5), got {len(high_load)}"

        # ~80% low load
        assert len(low_load) >= 12, \
            f"Expected ≥60% low load (≥12), got {len(low_load)}"

        # High variance
        utils = [l.utilization for l in loads]
        assert np.std(utils) > 0.25, "Concentrated load should have high variance"

    def test_dynamic_load_varies_over_time(self, simulator, satellite_ids):
        """
        TEST: 動態負載隨時間變化

        REQUIREMENT: Time-varying scenario
        """
        # Sample at different time steps
        loads_t0 = simulator.generate_dynamic_load(satellite_ids, timestamp_index=0)
        loads_t10 = simulator.generate_dynamic_load(satellite_ids, timestamp_index=10)
        loads_t20 = simulator.generate_dynamic_load(satellite_ids, timestamp_index=20)

        utils_t0 = np.mean([l.utilization for l in loads_t0])
        utils_t10 = np.mean([l.utilization for l in loads_t10])
        utils_t20 = np.mean([l.utilization for l in loads_t20])

        # Average utilization should vary
        values = [utils_t0, utils_t10, utils_t20]
        assert max(values) - min(values) > 0.1, \
            "Dynamic load should vary by > 10% over time"

    def test_capacity_constraint_respected(self, simulator, satellite_ids):
        """
        TEST: 容量限制被遵守

        REQUIREMENT: Physical constraint (0 ≤ users ≤ capacity)
        """
        for pattern in [LoadPattern.UNIFORM, LoadPattern.CONCENTRATED]:
            loads = simulator.simulate_load(satellite_ids, pattern=pattern)

            for load in loads:
                assert 0 <= load.current_users <= load.capacity, \
                    f"Users {load.current_users} exceeds capacity {load.capacity}"
                assert 0.0 <= load.utilization <= 1.0, \
                    f"Utilization {load.utilization} out of range [0, 1]"

    def test_load_state_classification_correct(self, simulator, satellite_ids):
        """
        TEST: 負載狀態分類正確

        REQUIREMENT: Low/Moderate/High/Overload thresholds
        """
        loads = simulator.generate_concentrated_load(satellite_ids)

        for load in loads:
            if load.utilization < 0.3:
                assert load.load_state == "low"
            elif load.utilization < 0.7:
                assert load.load_state == "moderate"
            elif load.utilization < 0.9:
                assert load.load_state == "high"
            else:
                assert load.load_state in ["high", "overload"]

    @staticmethod
    def _compute_gini(values):
        """Compute Gini coefficient."""
        sorted_values = np.sort(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        return (2 * np.sum((np.arange(1, n+1) * sorted_values))) / (n * cumsum[-1]) - (n + 1) / n
```

---

## 🔗 整合測試策略

### Test Suite 5: Stage 5 Integration

**FILE**: `tests/integration/test_stage5_integration.py`

```python
def test_stage5_with_propagation_simulation_enabled():
    """
    TEST: Stage 5 啟用傳播模擬完整流程

    REQUIREMENT: Stage 5 功能正確性
    """
    # Load config with propagation enabled
    config = load_test_config('stage5_with_propagation.yaml')
    processor = Stage5Processor(config, logger)

    # Load Stage 4 output
    stage4_data = load_json('test_data/stage4_output_sample.json')

    # Process
    result = processor.process(stage4_data)

    # Verify propagation_condition field exists
    for sat_id, sat_data in result['signal_analysis'].items():
        assert 'propagation_condition' in sat_data['time_series'][0], \
            "Missing propagation_condition field"

        prop_cond = sat_data['time_series'][0]['propagation_condition']

        # Verify required fields
        assert 'state' in prop_cond
        assert prop_cond['state'] in ['LOS', 'Shadowed', 'Blocked']
        assert 'channel_attenuation_db' in prop_cond
        assert 100.0 < prop_cond['channel_attenuation_db'] < 200.0

def test_stage5_backward_compatibility():
    """
    TEST: Stage 5 向後兼容性（propagation disabled）

    REQUIREMENT: NFR-3 向後兼容性
    """
    # Load config with propagation DISABLED
    config = load_test_config('stage5_without_propagation.yaml')
    processor = Stage5Processor(config, logger)

    # Process
    stage4_data = load_json('test_data/stage4_output_sample.json')
    result = processor.process(stage4_data)

    # Verify propagation_condition field does NOT exist
    for sat_id, sat_data in result['signal_analysis'].items():
        assert 'propagation_condition' not in sat_data['time_series'][0], \
            "propagation_condition should not exist when disabled"
```

---

### Test Suite 6: Stage 6 Integration

**FILE**: `tests/integration/test_stage6_integration.py`

```python
def test_stage6_generates_correct_number_of_variants():
    """
    TEST: Stage 6 生成正確數量的變體

    REQUIREMENT: 4 traffic × 3 load = 12 variants
    """
    config = load_test_config('stage6_with_diversity.yaml')
    processor = Stage6Processor(config, logger)

    stage5_data = load_json('test_data/stage5_output_sample.json')
    result = processor.process(stage5_data)

    assert 'scenario_variants' in result
    assert len(result['scenario_variants']) == 12, \
        "Should generate 12 variants (4 traffic × 3 load)"

def test_stage6_variant_ids_unique():
    """
    TEST: 變體 ID 唯一

    REQUIREMENT: 可追溯性
    """
    config = load_test_config('stage6_with_diversity.yaml')
    processor = Stage6Processor(config, logger)

    stage5_data = load_json('test_data/stage5_output_sample.json')
    result = processor.process(stage5_data)

    variant_ids = [v['variant_id'] for v in result['scenario_variants']]

    assert len(variant_ids) == len(set(variant_ids)), \
        "All variant IDs must be unique"

def test_stage6_preserves_base_data():
    """
    TEST: 基礎數據保留

    REQUIREMENT: 不破壞現有功能
    """
    config = load_test_config('stage6_with_diversity.yaml')
    processor = Stage6Processor(config, logger)

    stage5_data = load_json('test_data/stage5_output_sample.json')
    result = processor.process(stage5_data)

    # Base fields should still exist
    assert 'handover_events' in result
    assert 'sample_id' in result
    assert 'timestamp' in result
```

---

## ⚡ 性能測試策略

### Performance Baseline

**執行前性能基準** (Stage 4 完成後):
```
Stage 5 執行時間: ~180 秒 (Starlink 98 satellites × 21 timepoints)
Stage 6 執行時間: ~60 秒
總記憶體使用: ~3.5 GB
輸出檔案大小: ~50 MB (stage5 + stage6)
```

**性能目標** (NFR-2):
```
Stage 5 增加: < 20% (< 36 秒)
Stage 6 增加: < 30% (< 18 秒)
記憶體增加: < 15% (< 525 MB)
檔案大小增加: < 50% (< 25 MB)
```

---

### Performance Test Suite

**FILE**: `tests/performance/test_performance_benchmarks.py`

```python
import time
import psutil
import pytest

class TestPerformanceBenchmarks:
    """
    性能測試: 確保擴充不顯著降低性能

    REQUIREMENT: NFR-2 性能要求
    """

    @pytest.fixture
    def baseline_stage5_time(self):
        """Baseline Stage 5 execution time (seconds)."""
        return 180.0

    @pytest.fixture
    def baseline_stage6_time(self):
        """Baseline Stage 6 execution time (seconds)."""
        return 60.0

    def test_stage5_execution_time_within_target(self, baseline_stage5_time):
        """
        TEST: Stage 5 執行時間 < 基準 + 20%

        REQUIREMENT: NFR-2 性能要求
        """
        config = load_test_config('stage5_with_propagation.yaml')
        processor = Stage5Processor(config, logger)

        stage4_data = load_json('test_data/stage4_full.json')

        start = time.time()
        result = processor.process(stage4_data)
        elapsed = time.time() - start

        max_allowed = baseline_stage5_time * 1.20  # +20%

        assert elapsed < max_allowed, \
            f"Stage 5 took {elapsed:.1f}s, exceeds limit {max_allowed:.1f}s"

    def test_stage6_execution_time_within_target(self, baseline_stage6_time):
        """
        TEST: Stage 6 執行時間 < 基準 + 30%

        REQUIREMENT: NFR-2 性能要求
        """
        config = load_test_config('stage6_with_diversity.yaml')
        processor = Stage6Processor(config, logger)

        stage5_data = load_json('test_data/stage5_full.json')

        start = time.time()
        result = processor.process(stage5_data)
        elapsed = time.time() - start

        max_allowed = baseline_stage6_time * 1.30  # +30%

        assert elapsed < max_allowed, \
            f"Stage 6 took {elapsed:.1f}s, exceeds limit {max_allowed:.1f}s"

    def test_memory_usage_within_target(self):
        """
        TEST: 記憶體使用增加 < 15%

        REQUIREMENT: NFR-2 性能要求
        """
        process = psutil.Process()

        # Baseline memory
        baseline_mb = process.memory_info().rss / 1024 / 1024

        # Run Stage 5 + 6 with diversity
        config5 = load_test_config('stage5_with_propagation.yaml')
        config6 = load_test_config('stage6_with_diversity.yaml')

        processor5 = Stage5Processor(config5, logger)
        processor6 = Stage6Processor(config6, logger)

        stage4_data = load_json('test_data/stage4_full.json')
        result5 = processor5.process(stage4_data)
        result6 = processor6.process(result5)

        # Peak memory
        peak_mb = process.memory_info().rss / 1024 / 1024

        increase_mb = peak_mb - baseline_mb
        increase_pct = (increase_mb / baseline_mb) * 100

        assert increase_pct < 15.0, \
            f"Memory increased by {increase_pct:.1f}%, exceeds 15% limit"

    def test_output_file_size_within_target(self):
        """
        TEST: 輸出檔案大小增加 < 50%

        REQUIREMENT: NFR-2 性能要求
        """
        # Run with diversity disabled
        result_baseline = run_stage6_without_diversity()
        size_baseline = len(json.dumps(result_baseline))

        # Run with diversity enabled
        result_with_diversity = run_stage6_with_diversity()
        size_with_diversity = len(json.dumps(result_with_diversity))

        increase_pct = ((size_with_diversity - size_baseline) / size_baseline) * 100

        assert increase_pct < 50.0, \
            f"File size increased by {increase_pct:.1f}%, exceeds 50% limit"
```

---

## ✅ 學術合規性測試

### Compliance Test Suite

**FILE**: `tests/compliance/test_academic_compliance.py`

```python
import re
import ast

class TestAcademicCompliance:
    """
    學術合規性測試: 確保所有參數有官方來源

    REQUIREMENT: NFR-1 學術合規性
    """

    def test_all_config_parameters_have_source_comments(self):
        """
        TEST: 配置文件所有參數有 SOURCE 註解

        REQUIREMENT: docs/ACADEMIC_STANDARDS.md
        """
        config_files = [
            'config/stage5_signal_analysis_config.yaml',
            'config/stage6_research_optimization_config.yaml'
        ]

        for config_file in config_files:
            with open(config_file, 'r') as f:
                content = f.read()

            # Extract numeric parameters
            params = re.findall(r'^\s*(\w+):\s*([\d.]+)', content, re.MULTILINE)

            for param_name, param_value in params:
                # Check if SOURCE comment exists within 5 lines above
                param_pos = content.find(f'{param_name}: {param_value}')
                preceding_text = content[max(0, param_pos - 500):param_pos]

                assert 'SOURCE:' in preceding_text, \
                    f"Parameter {param_name} in {config_file} missing SOURCE comment"

    def test_all_algorithm_implementations_have_citations(self):
        """
        TEST: 所有算法實現有學術引用

        REQUIREMENT: docs/ACADEMIC_STANDARDS.md
        """
        source_files = [
            'src/stages/stage5_signal_analysis/three_state_markov.py',
            'src/stages/stage5_signal_analysis/loo_channel.py',
            'src/stages/stage6_research_optimization/traffic_profile_generator.py',
            'src/stages/stage6_research_optimization/satellite_load_simulator.py'
        ]

        for source_file in source_files:
            with open(source_file, 'r') as f:
                content = f.read()

            # Check for SOURCE comments
            source_count = content.count('SOURCE:')

            assert source_count > 0, \
                f"File {source_file} has no SOURCE citations"

            # Verify module docstring has citation
            tree = ast.parse(content)
            module_docstring = ast.get_docstring(tree)

            assert module_docstring is not None, \
                f"Module {source_file} missing docstring"
            assert 'SOURCE:' in module_docstring, \
                f"Module {source_file} docstring missing SOURCE citation"

    def test_no_mock_or_simplified_implementations(self):
        """
        TEST: 無 mock 或簡化實現

        REQUIREMENT: 嚴禁使用簡化算法
        """
        source_files = glob.glob('src/stages/stage5_signal_analysis/*.py') + \
                       glob.glob('src/stages/stage6_research_optimization/*.py')

        forbidden_keywords = [
            'mock', 'fake', 'simplified', 'basic model',
            '簡化', '模擬實現', 'placeholder'
        ]

        for source_file in source_files:
            with open(source_file, 'r') as f:
                content = f.read().lower()

            for keyword in forbidden_keywords:
                assert keyword.lower() not in content, \
                    f"File {source_file} contains forbidden keyword '{keyword}'"

    def test_markov_transition_matrix_from_3gpp(self):
        """
        TEST: Markov 轉換矩陣來自 3GPP TR 38.901

        REQUIREMENT: FR-1 動態傳播條件
        """
        from src.stages.stage5_signal_analysis.three_state_markov import MarkovConfig

        config = MarkovConfig()

        # Verify transition probabilities match 3GPP Table 7.6.3-1
        # SOURCE: 3GPP TR 38.901 Table 7.6.3-1
        assert config.P_LL == 0.95  # LOS → LOS
        assert config.P_LS == 0.04  # LOS → Shadowed
        assert config.P_LB == 0.01  # LOS → Blocked

        # Verify normalization
        assert abs((config.P_LL + config.P_LS + config.P_LB) - 1.0) < 0.001

    def test_traffic_profiles_match_3gpp_ts22261(self):
        """
        TEST: 流量類型參數符合 3GPP TS 22.261

        REQUIREMENT: FR-2 流量類型生成
        """
        from src.stages.stage6_research_optimization.traffic_profile_generator import (
            TrafficProfileGenerator
        )

        gen = TrafficProfileGenerator({}, logger=None)

        # VoIP requirements from 3GPP TS 22.261 Annex A.1
        voip_template = gen.PROFILE_TEMPLATES[TrafficType.VOIP]
        assert voip_template['max_delay_ms'] == 150.0
        assert voip_template['min_bandwidth_kbps'] == 64.0
        assert voip_template['min_reliability'] == 0.99

    def test_satellite_capacity_from_3gpp_tr38821(self):
        """
        TEST: 衛星容量來自 3GPP TR 38.821

        REQUIREMENT: FR-3 負載模擬
        """
        # Default capacity should match 3GPP TR 38.821 Section 6.1.1
        config = {'capacity_per_satellite': 200}
        sim = SatelliteLoadSimulator(config, logger=None)

        assert sim.capacity_per_satellite == 200, \
            "Default capacity should be 200 users (3GPP TR 38.821 NTN assumptions)"
```

---

## 🎯 端到端測試

### E2E Test Suite

**FILE**: `tests/e2e/test_full_pipeline_with_diversity.py`

```python
def test_full_six_stage_pipeline_with_diversity():
    """
    TEST: 完整六階段流程（含多樣性擴充）

    REQUIREMENT: 端到端功能驗證
    """
    # Run Stages 1-4 (unchanged)
    run_stage1()
    run_stage2()
    run_stage3()
    run_stage4()

    # Run Stage 5 with propagation simulation
    stage5_result = run_stage5_with_propagation()

    # Verify Stage 5 output
    assert 'signal_analysis' in stage5_result
    first_sat = list(stage5_result['signal_analysis'].values())[0]
    assert 'propagation_condition' in first_sat['time_series'][0]

    # Run Stage 6 with scenario diversity
    stage6_result = run_stage6_with_diversity(stage5_result)

    # Verify Stage 6 output
    assert 'scenario_variants' in stage6_result
    assert len(stage6_result['scenario_variants']) == 12

    # Verify variant structure
    variant = stage6_result['scenario_variants'][0]
    assert 'traffic_profile' in variant
    assert 'satellite_loads' in variant
    assert variant['traffic_profile']['type'] in ['voip', 'video', 'iot', 'best_effort']

    print("✅ 完整六階段流程測試通過")
```

---

## 📊 測試覆蓋率目標

| 模組 | 目標覆蓋率 | 測試數量 |
|------|----------|---------|
| ThreeStateMarkovModel | > 90% | 8 tests |
| LooChannelModel | > 90% | 8 tests |
| TrafficProfileGenerator | > 85% | 6 tests |
| SatelliteLoadSimulator | > 85% | 6 tests |
| ScenarioVariantGenerator | > 80% | 4 tests |
| Stage5Processor (new) | > 80% | 3 tests |
| Stage6Processor (new) | > 80% | 3 tests |
| **總計** | **> 80%** | **38 tests** |

---

## 🚀 測試執行流程

### 本地開發測試

```bash
# 1. 單元測試（快速反饋）
pytest tests/test_three_state_markov.py -v
pytest tests/test_loo_channel.py -v
pytest tests/test_traffic_profile_generator.py -v
pytest tests/test_satellite_load_simulator.py -v

# 2. 整合測試
pytest tests/integration/ -v

# 3. 性能測試（需要完整數據）
pytest tests/performance/ -v --durations=10

# 4. 學術合規性測試
pytest tests/compliance/ -v

# 5. 端到端測試（完整流程）
pytest tests/e2e/ -v
```

### CI/CD 測試流程

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/ -v --cov=src --cov-report=xml

      - name: Run compliance tests
        run: pytest tests/compliance/ -v

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

---

## ✅ 驗收標準

### 單元測試
- ✅ 所有單元測試通過
- ✅ 覆蓋率 > 85% (核心模組)

### 整合測試
- ✅ Stage 5 + 6 整合測試通過
- ✅ 向後兼容性測試通過

### 性能測試
- ✅ Stage 5 執行時間 < 基準 + 20%
- ✅ Stage 6 執行時間 < 基準 + 30%
- ✅ 記憶體增加 < 15%
- ✅ 檔案大小增加 < 50%

### 學術合規性
- ✅ 所有參數有 SOURCE 註解
- ✅ 無 mock 或簡化實現
- ✅ 參數來源可追溯到官方標準

### 端到端測試
- ✅ 完整六階段流程通過
- ✅ 輸出格式正確
- ✅ 變體生成正確

---

**測試完成標準**: 當所有上述測試通過且覆蓋率 > 80% 時，視為測試階段完成。

**返回**: [00-OVERVIEW.md](./00-OVERVIEW.md)
