# Stage 6 詳細設計：場景多樣性生成

> **模組名稱**: ScenarioVariantGenerator
> **責任**: 為每個訓練樣本生成多種場景變體
> **學術依據**: 2024_07 論文 (流量類型) + 2021_01 論文 (負載多樣性)

---

## 📐 模組架構

### 類別層次結構

```
ScenarioVariantGenerator (主控制器)
├── TrafficProfileGenerator (流量類型生成)
│   ├── _generate_voip_profile()
│   ├── _generate_video_profile()
│   ├── _generate_iot_profile()
│   └── _generate_best_effort_profile()
├── SatelliteLoadSimulator (負載模擬)
│   ├── _generate_uniform_load()
│   ├── _generate_concentrated_load()
│   └── _generate_dynamic_load()
└── VariantCombiner (組合器)
    ├── _create_variant_matrix()
    ├── _assign_variant_id()
    └── combine_into_training_samples()
```

---

## 📱 流量類型生成器

### 理論基礎

**SOURCE**: Badini, I., et al. (2024). "User-Centric Satellite Handover for Multiple Traffic Profiles Using Deep Q-Learning."
          IEEE Transactions on Aerospace and Electronic Systems, 60(4), 4352-4367.

**SOURCE**: 3GPP TS 22.261 v19.1.0 (2023). "Service requirements for the 5G system."
          Annex A - Performance requirements for different service categories.

**核心論點**:
> "Next-generation communication technologies are intended to support the unprecedented diversity of various emerging applications... Distinguishing UEs with different and varying traffic profiles (TPs), i.e., different performance requirements and generated traffic statistics."

---

### 四種流量類型定義

#### 1. VoIP (Voice over IP) - 即時語音

**SOURCE**: 3GPP TS 22.261 Annex A.1 - Conversational voice

```python
@dataclass
class VoIPProfile:
    type: str = "voip"
    category: str = "conversational"  # 3GPP classification

    # QoS Requirements
    # SOURCE: 3GPP TS 22.261 Table A.1-1
    max_delay_ms: float = 150.0       # One-way packet delay budget
    max_jitter_ms: float = 30.0       # Packet delay variation
    min_bandwidth_kbps: float = 64.0  # G.711 codec
    max_packet_loss_rate: float = 0.01  # 1% loss tolerance
    min_reliability: float = 0.99     # 99% success rate

    # Traffic Characteristics
    # SOURCE: ITU-T G.114 (2003) - Quality of Service
    priority: int = 1                 # Highest priority (critical)
    burstiness: str = "periodic"      # 20ms frame intervals
    flow_type: str = "bidirectional"  # Two-way conversation
```

**典型應用**: 衛星電話、遠程會議、VoLTE over NTN

---

#### 2. Video (HD Streaming) - 高清視訊

**SOURCE**: 3GPP TS 22.261 Annex A.2 - Video streaming

```python
@dataclass
class VideoProfile:
    type: str = "video"
    category: str = "streaming"

    # QoS Requirements
    # SOURCE: 3GPP TS 22.261 Table A.2-1
    max_delay_ms: float = 400.0       # Buffering tolerance
    max_jitter_ms: float = 50.0       # Adaptive bitrate can handle
    min_bandwidth_mbps: float = 5.0   # 1080p HD streaming
    max_bandwidth_mbps: float = 25.0  # 4K streaming
    max_packet_loss_rate: float = 0.05  # 5% loss with FEC
    min_reliability: float = 0.95     # 95% success rate

    # Traffic Characteristics
    priority: int = 2                 # Medium-high priority
    burstiness: str = "bursty"        # I-frame spikes
    flow_type: str = "unidirectional"  # Downlink dominant
```

**典型應用**: Netflix/YouTube over Starlink, 直播服務, 視訊監控

---

#### 3. IoT (Sensor Data) - 物聯網

**SOURCE**: 3GPP TS 22.261 Annex A.5 - IoT and critical communications

```python
@dataclass
class IoTProfile:
    type: str = "iot"
    category: str = "non_critical_iot"

    # QoS Requirements
    # SOURCE: 3GPP TS 22.261 Table A.5-2
    max_delay_s: float = 5.0          # Non-critical, delay tolerant
    min_bandwidth_kbps: float = 10.0  # Small packet size
    max_packet_loss_rate: float = 0.10  # 10% loss acceptable
    min_reliability: float = 0.90     # 90% success rate

    # Traffic Characteristics
    priority: int = 4                 # Low priority
    burstiness: str = "sporadic"      # Infrequent transmissions
    flow_type: str = "unidirectional"  # Uplink only (sensors)

    # IoT-specific
    # SOURCE: 3GPP TR 38.821 NTN IoT considerations
    small_packet_size: bool = True    # Typically < 100 bytes
    duty_cycle_pct: float = 0.1       # Active 0.1% of time
```

**典型應用**: 衛星 IoT (農業感測器, 貨櫃追蹤, 環境監測)

---

#### 4. BestEffort (General Data) - 盡力而為

**SOURCE**: 3GPP TS 23.501 Section 5.7.2 - QoS flows

```python
@dataclass
class BestEffortProfile:
    type: str = "best_effort"
    category: str = "background"

    # QoS Requirements
    # SOURCE: 3GPP TS 22.261 Annex A.6 - Background traffic
    max_delay_s: float = 10.0         # No strict requirement
    min_bandwidth_kbps: float = 100.0  # Variable
    max_packet_loss_rate: float = 0.20  # 20% loss acceptable
    min_reliability: float = 0.80     # 80% success rate

    # Traffic Characteristics
    priority: int = 5                 # Lowest priority
    burstiness: str = "random"        # Unpredictable
    flow_type: str = "bidirectional"  # Web browsing, email
```

**典型應用**: 電子郵件, 檔案下載, Web 瀏覽 (非即時)

---

### Python 實現

```python
# FILE: src/stages/stage6_research_optimization/traffic_profile_generator.py

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
from enum import Enum
import logging

class TrafficType(Enum):
    """
    SOURCE: 3GPP TS 22.261 Annex A - Service categories
    """
    VOIP = "voip"
    VIDEO = "video"
    IOT = "iot"
    BEST_EFFORT = "best_effort"

@dataclass
class TrafficProfile:
    """
    統一的流量類型描述

    SOURCE: Badini et al. (2024) - Traffic profile definitions
    """
    type: str
    category: str

    # QoS Parameters
    max_delay_ms: float
    min_bandwidth_kbps: float
    min_reliability: float

    # Optional parameters
    max_jitter_ms: float = None
    max_packet_loss_rate: float = None
    priority: int = 3  # Default medium priority

    # Metadata
    description: str = ""
    use_cases: List[str] = None

class TrafficProfileGenerator:
    """
    Generate traffic profiles for RL training scenarios.

    SOURCE: 2024_07 - Badini et al. - Multiple Traffic Profiles
    """

    # Profile templates from 3GPP standards
    PROFILE_TEMPLATES = {
        TrafficType.VOIP: {
            "category": "conversational",
            "max_delay_ms": 150.0,
            "max_jitter_ms": 30.0,
            "min_bandwidth_kbps": 64.0,
            "max_packet_loss_rate": 0.01,
            "min_reliability": 0.99,
            "priority": 1,
            "description": "Real-time voice communication",
            "use_cases": ["Satellite phone", "VoLTE over NTN", "Remote conferencing"],
            # SOURCE: 3GPP TS 22.261 Annex A.1
        },
        TrafficType.VIDEO: {
            "category": "streaming",
            "max_delay_ms": 400.0,
            "max_jitter_ms": 50.0,
            "min_bandwidth_kbps": 5000.0,  # 5 Mbps
            "max_packet_loss_rate": 0.05,
            "min_reliability": 0.95,
            "priority": 2,
            "description": "HD video streaming",
            "use_cases": ["Netflix over Starlink", "Live broadcast", "Video surveillance"],
            # SOURCE: 3GPP TS 22.261 Annex A.2
        },
        TrafficType.IOT: {
            "category": "non_critical_iot",
            "max_delay_ms": 5000.0,  # 5 seconds
            "min_bandwidth_kbps": 10.0,
            "max_packet_loss_rate": 0.10,
            "min_reliability": 0.90,
            "priority": 4,
            "description": "IoT sensor data uplink",
            "use_cases": ["Agricultural sensors", "Container tracking", "Environmental monitoring"],
            # SOURCE: 3GPP TS 22.261 Annex A.5
        },
        TrafficType.BEST_EFFORT: {
            "category": "background",
            "max_delay_ms": 10000.0,  # 10 seconds
            "min_bandwidth_kbps": 100.0,
            "max_packet_loss_rate": 0.20,
            "min_reliability": 0.80,
            "priority": 5,
            "description": "General data transfer",
            "use_cases": ["Email", "File download", "Web browsing"],
            # SOURCE: 3GPP TS 22.261 Annex A.6
        }
    }

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger

        # Get enabled traffic types from config
        enabled_types = config.get('enabled_types', list(TrafficType))
        self.enabled_types = [TrafficType(t) for t in enabled_types]

        self.logger.info(
            f"🚦 流量類型生成器初始化: {len(self.enabled_types)} 種類型"
        )

    def generate_profile(self, traffic_type: TrafficType) -> TrafficProfile:
        """
        Generate a traffic profile for the specified type.

        Args:
            traffic_type: Traffic type enum

        Returns:
            TrafficProfile object with QoS parameters
        """
        if traffic_type not in self.enabled_types:
            raise ValueError(f"Traffic type {traffic_type} not enabled")

        template = self.PROFILE_TEMPLATES[traffic_type]

        # Apply custom parameters from config if specified
        custom_params = self.config.get('custom_parameters', {}).get(
            traffic_type.value, {}
        )

        # Merge template with custom params
        params = {**template, **custom_params}

        profile = TrafficProfile(
            type=traffic_type.value,
            category=params['category'],
            max_delay_ms=params['max_delay_ms'],
            min_bandwidth_kbps=params['min_bandwidth_kbps'],
            min_reliability=params['min_reliability'],
            max_jitter_ms=params.get('max_jitter_ms'),
            max_packet_loss_rate=params.get('max_packet_loss_rate'),
            priority=params['priority'],
            description=params['description'],
            use_cases=params['use_cases']
        )

        self.logger.debug(
            f"📱 生成流量類型: {traffic_type.value} "
            f"(delay≤{params['max_delay_ms']}ms, bw≥{params['min_bandwidth_kbps']}kbps)"
        )

        return profile

    def generate_all_profiles(self) -> Dict[str, TrafficProfile]:
        """
        Generate all enabled traffic profiles.

        Returns:
            Dictionary mapping traffic type to profile
        """
        profiles = {}

        for traffic_type in self.enabled_types:
            profiles[traffic_type.value] = self.generate_profile(traffic_type)

        self.logger.info(f"✅ 生成 {len(profiles)} 種流量類型")

        return profiles
```

---

## 🛰️ 衛星負載模擬器

### 理論基礎

**SOURCE**: He, S., et al. (2021). "Load-Aware Satellite Handover Strategy Based on Multi-Agent Reinforcement Learning."
          IEEE International Conference on Communications (ICC), 1-6.

**核心論點**:
> "Distributed satellite handover strategy is required to balance satellite load to avoid network congestion... The competition for satellite channels between users covered by the same satellite may cause highly imbalanced satellite load."

**SOURCE**: 3GPP TR 38.821 v17.0.0 (2022). "Solutions for NR to support non-terrestrial networks (NTN)."
          Section 6.1.1 - NTN capacity assumptions.

**容量假設** (Starlink Ku-band):
- 每衛星容量: ~200 同時用戶 (typical)
- 總頻寬: ~20 Gbps per satellite
- Beam 數量: ~1280 spot beams

---

### 三種負載模式定義

#### 1. Uniform Load - 均勻負載

**定義**: 所有衛星負載狀態相近，網路處於均衡狀態

```python
# Utilization: current_users / capacity
uniform_range = (0.4, 0.6)  # 40%-60% 利用率

# 分布特徵
std_deviation < 0.1  # 低變異
gini_coefficient < 0.2  # 高均勻性
```

**適用場景**: 負載均衡演算法運作良好、用戶分布均勻

---

#### 2. Concentrated Load - 集中負載

**定義**: 少數衛星高負載，多數衛星低負載，模擬熱點現象

```python
# 80-20 原則
high_load_satellites = 20%  # Utilization: 0.8-0.9
low_load_satellites = 80%   # Utilization: 0.1-0.3

# 分布特徵
std_deviation > 0.3  # 高變異
gini_coefficient > 0.5  # 高不均勻性
```

**適用場景**: 城市熱點、活動現場、海上航線

---

#### 3. Dynamic Load - 動態負載

**定義**: 負載隨時間變化，模擬真實網路動態

```python
# Time-varying pattern
utilization(t) = base_load + amplitude * sin(2π * t / period)

# 參數
base_load = 0.5        # 50% 平均負載
amplitude = 0.3        # ±30% 變動
period_minutes = 10    # 10 分鐘週期
```

**適用場景**: 日夜流量變化、移動用戶群體

---

### Python 實現

```python
# FILE: src/stages/stage6_research_optimization/satellite_load_simulator.py

from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum
import numpy as np
import logging

class LoadPattern(Enum):
    """
    SOURCE: He et al. (2021) - Load balancing scenarios
    """
    UNIFORM = "uniform"
    CONCENTRATED = "concentrated"
    DYNAMIC = "dynamic"

@dataclass
class SatelliteLoad:
    """
    單一衛星負載狀態

    SOURCE: 3GPP TR 38.821 Section 6.1.1
    """
    satellite_id: str
    current_users: int
    capacity: int
    utilization: float  # 0.0-1.0
    load_state: str     # "low" | "moderate" | "high" | "overload"

    # Metadata
    pattern: str  # Load pattern type
    timestamp_index: int  # For dynamic patterns

class SatelliteLoadSimulator:
    """
    Simulate satellite load diversity for RL training.

    SOURCE: 2021_01 - He et al. - Load-Aware Handover
    """

    # Load state thresholds
    LOAD_THRESHOLDS = {
        "low": (0.0, 0.3),
        "moderate": (0.3, 0.7),
        "high": (0.7, 0.9),
        "overload": (0.9, 1.0)
    }

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger

        # Satellite capacity
        # SOURCE: 3GPP TR 38.821 Section 6.1.1 - NTN capacity assumptions
        self.capacity_per_satellite = config.get(
            'capacity_per_satellite', 200
        )  # Typical Starlink value

        # Enabled patterns
        enabled_patterns = config.get('enabled_patterns', list(LoadPattern))
        self.enabled_patterns = [LoadPattern(p) for p in enabled_patterns]

        # Pattern distribution (probabilities)
        self.pattern_distribution = config.get('pattern_distribution', {
            'uniform': 0.3,
            'concentrated': 0.4,
            'dynamic': 0.3
        })

        # Random seed for reproducibility
        self.rng = np.random.default_rng(config.get('random_seed', 42))

        self.logger.info(
            f"🛰️  衛星負載模擬器初始化: "
            f"{len(self.enabled_patterns)} 種模式, "
            f"容量={self.capacity_per_satellite} 用戶/衛星"
        )

    def _classify_load_state(self, utilization: float) -> str:
        """Classify load state based on utilization."""
        for state, (min_u, max_u) in self.LOAD_THRESHOLDS.items():
            if min_u <= utilization < max_u:
                return state
        return "overload"

    def generate_uniform_load(
        self,
        satellite_ids: List[str]
    ) -> List[SatelliteLoad]:
        """
        Generate uniform load distribution.

        SOURCE: He et al. (2021) - Baseline scenario
        """
        loads = []

        # Target range: 40-60% utilization
        target_util = self.rng.uniform(0.4, 0.6)

        for sat_id in satellite_ids:
            # Small random variation around target
            util = target_util + self.rng.normal(0, 0.05)
            util = np.clip(util, 0.0, 1.0)

            current_users = int(util * self.capacity_per_satellite)

            loads.append(SatelliteLoad(
                satellite_id=sat_id,
                current_users=current_users,
                capacity=self.capacity_per_satellite,
                utilization=util,
                load_state=self._classify_load_state(util),
                pattern="uniform",
                timestamp_index=0
            ))

        self.logger.debug(
            f"📊 生成均勻負載: {len(loads)} 顆衛星, "
            f"平均利用率={target_util:.1%}"
        )

        return loads

    def generate_concentrated_load(
        self,
        satellite_ids: List[str]
    ) -> List[SatelliteLoad]:
        """
        Generate concentrated load distribution (80-20 rule).

        SOURCE: He et al. (2021) - Hotspot scenario
        """
        loads = []
        n_sats = len(satellite_ids)

        # 20% high load, 80% low load
        n_high = max(1, int(n_sats * 0.2))
        high_load_sats = self.rng.choice(
            satellite_ids, size=n_high, replace=False
        )

        for sat_id in satellite_ids:
            if sat_id in high_load_sats:
                # High load: 80-90% utilization
                util = self.rng.uniform(0.8, 0.9)
            else:
                # Low load: 10-30% utilization
                util = self.rng.uniform(0.1, 0.3)

            current_users = int(util * self.capacity_per_satellite)

            loads.append(SatelliteLoad(
                satellite_id=sat_id,
                current_users=current_users,
                capacity=self.capacity_per_satellite,
                utilization=util,
                load_state=self._classify_load_state(util),
                pattern="concentrated",
                timestamp_index=0
            ))

        self.logger.debug(
            f"🔥 生成集中負載: {n_high} 顆高負載 (80-90%), "
            f"{n_sats - n_high} 顆低負載 (10-30%)"
        )

        return loads

    def generate_dynamic_load(
        self,
        satellite_ids: List[str],
        timestamp_index: int,
        period_minutes: float = 10.0
    ) -> List[SatelliteLoad]:
        """
        Generate dynamic load with time variation.

        SOURCE: He et al. (2021) - Time-varying scenario

        Args:
            timestamp_index: Time step index (0, 1, 2, ...)
            period_minutes: Period of load oscillation
        """
        loads = []

        # Sinusoidal variation
        # Assume 30-second intervals (Stage 2 default)
        period_steps = int(period_minutes * 60 / 30)  # Convert to steps
        phase = 2 * np.pi * timestamp_index / period_steps

        for sat_id in satellite_ids:
            # Base load + sinusoidal variation
            base_load = 0.5
            amplitude = 0.3
            util = base_load + amplitude * np.sin(phase + self.rng.uniform(0, 2*np.pi))
            util = np.clip(util, 0.0, 1.0)

            current_users = int(util * self.capacity_per_satellite)

            loads.append(SatelliteLoad(
                satellite_id=sat_id,
                current_users=current_users,
                capacity=self.capacity_per_satellite,
                utilization=util,
                load_state=self._classify_load_state(util),
                pattern="dynamic",
                timestamp_index=timestamp_index
            ))

        self.logger.debug(
            f"🔄 生成動態負載 (t={timestamp_index}): "
            f"平均利用率={np.mean([l.utilization for l in loads]):.1%}"
        )

        return loads

    def simulate_load(
        self,
        satellite_ids: List[str],
        pattern: LoadPattern = None,
        timestamp_index: int = 0
    ) -> List[SatelliteLoad]:
        """
        Simulate satellite load for given pattern.

        Args:
            satellite_ids: List of satellite IDs
            pattern: Load pattern (if None, randomly choose based on distribution)
            timestamp_index: Time step index (for dynamic pattern)

        Returns:
            List of SatelliteLoad objects
        """
        # Choose pattern if not specified
        if pattern is None:
            pattern = self.rng.choice(
                list(self.enabled_patterns),
                p=[self.pattern_distribution.get(p.value, 0.33) for p in self.enabled_patterns]
            )

        # Generate load based on pattern
        if pattern == LoadPattern.UNIFORM:
            return self.generate_uniform_load(satellite_ids)
        elif pattern == LoadPattern.CONCENTRATED:
            return self.generate_concentrated_load(satellite_ids)
        elif pattern == LoadPattern.DYNAMIC:
            return self.generate_dynamic_load(satellite_ids, timestamp_index)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
```

---

## 🔗 場景變體組合器

### 變體生成策略

**策略**: 笛卡爾積 (Cartesian Product)

```
4 種流量類型 × 3 種負載模式 = 12 種場景變體
```

**變體 ID 格式**:
```
{base_sample_id}_v{variant_index:03d}_{traffic_type}_{load_pattern}

範例:
  starlink_t000_v001_voip_uniform
  starlink_t000_v002_voip_concentrated
  starlink_t000_v003_voip_dynamic
  ...
  starlink_t000_v012_best_effort_dynamic
```

---

### Python 實現

```python
# FILE: src/stages/stage6_research_optimization/scenario_variant_generator.py

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import logging

@dataclass
class ScenarioVariant:
    """
    單一場景變體（訓練樣本）

    SOURCE: 2024_07 + 2021_01 - Multi-profile multi-load scenarios
    """
    variant_id: str
    base_sample_id: str

    # Traffic profile
    traffic_profile: Dict[str, Any]

    # Satellite loads
    satellite_loads: List[Dict[str, Any]]

    # Metadata
    variant_index: int
    total_variants: int

class ScenarioVariantGenerator:
    """
    Generate multiple scenario variants for each training sample.

    Combines traffic profiles and load patterns to create diverse RL training data.
    """

    def __init__(
        self,
        traffic_generator: TrafficProfileGenerator,
        load_simulator: SatelliteLoadSimulator,
        config: Dict[str, Any],
        logger: logging.Logger
    ):
        self.traffic_gen = traffic_generator
        self.load_sim = load_simulator
        self.config = config
        self.logger = logger

        # Variant generation settings
        self.variants_per_sample = config.get('variants_per_sample', 12)
        self.variant_id_format = config.get(
            'variant_id_format',
            "{base_id}_v{index:03d}_{traffic}_{load}"
        )

    def generate_variants(
        self,
        base_sample_id: str,
        satellite_ids: List[str],
        timestamp_index: int = 0
    ) -> List[ScenarioVariant]:
        """
        Generate all scenario variants for a base training sample.

        Args:
            base_sample_id: Base sample identifier
            satellite_ids: List of visible satellite IDs
            timestamp_index: Time index for dynamic patterns

        Returns:
            List of scenario variants
        """
        variants = []
        variant_index = 0

        # Generate all traffic profiles
        traffic_profiles = self.traffic_gen.generate_all_profiles()

        # Get enabled load patterns
        load_patterns = self.load_sim.enabled_patterns

        # Cartesian product: traffic × load
        for traffic_type, traffic_profile in traffic_profiles.items():
            for load_pattern in load_patterns:
                variant_index += 1

                # Generate load distribution
                satellite_loads = self.load_sim.simulate_load(
                    satellite_ids, load_pattern, timestamp_index
                )

                # Create variant ID
                variant_id = self.variant_id_format.format(
                    base_id=base_sample_id,
                    index=variant_index,
                    traffic=traffic_type,
                    load=load_pattern.value
                )

                # Create variant object
                variant = ScenarioVariant(
                    variant_id=variant_id,
                    base_sample_id=base_sample_id,
                    traffic_profile=asdict(traffic_profile),
                    satellite_loads=[asdict(load) for load in satellite_loads],
                    variant_index=variant_index,
                    total_variants=len(traffic_profiles) * len(load_patterns)
                )

                variants.append(variant)

        self.logger.info(
            f"✨ 生成場景變體: {base_sample_id} → {len(variants)} 種變體"
        )

        return variants
```

---

## 🔌 整合到 Stage 6 流程

### 修改現有 Stage 6 模組

**FILE**: `src/stages/stage6_research_optimization/stage6_processor.py`

```python
class Stage6Processor:
    """
    Stage 6: Research Optimization + Scenario Diversity
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger

        # NEW: Initialize scenario variant generator if enabled
        if config.get('enable_scenario_diversity', False):
            # Traffic profile generator
            traffic_config = config.get('traffic_profiles', {})
            self.traffic_gen = TrafficProfileGenerator(traffic_config, logger)

            # Satellite load simulator
            load_config = config.get('satellite_load_simulation', {})
            self.load_sim = SatelliteLoadSimulator(load_config, logger)

            # Variant generator (combines traffic + load)
            variant_config = config.get('scenario_generation', {})
            self.variant_gen = ScenarioVariantGenerator(
                self.traffic_gen, self.load_sim, variant_config, logger
            )
        else:
            self.variant_gen = None

    def process_training_sample(
        self,
        sample_id: str,
        signal_data: Dict[str, Any],
        timestamp_index: int
    ) -> Dict[str, Any]:
        """
        處理單一訓練樣本

        Returns:
            包含基礎數據 + 場景變體的完整訓練數據
        """
        # Existing processing (A3/A5 events, etc.)
        result = {
            "sample_id": sample_id,
            "timestamp": signal_data['timestamp'],
            "handover_events": self._detect_handover_events(signal_data),
            # ... existing fields ...
        }

        # NEW: Generate scenario variants if enabled
        if self.variant_gen:
            satellite_ids = list(signal_data['satellites'].keys())
            variants = self.variant_gen.generate_variants(
                base_sample_id=sample_id,
                satellite_ids=satellite_ids,
                timestamp_index=timestamp_index
            )

            result["scenario_variants"] = [
                asdict(variant) for variant in variants
            ]

            self.logger.debug(
                f"🎲 樣本 {sample_id}: 生成 {len(variants)} 種場景變體"
            )

        return result
```

---

## ⚙️ 配置設計

**FILE**: `config/stage6_research_optimization_config.yaml`

```yaml
stage6:
  # Existing configurations...

  # NEW: Scenario Diversity Generation
  enable_scenario_diversity: true  # 設為 false 可停用

  # Traffic Profile Configuration
  # SOURCE: 3GPP TS 22.261 Annex A
  traffic_profiles:
    enabled_types:
      - voip
      - video
      - iot
      - best_effort

    # Optional: Override default parameters
    custom_parameters:
      voip:
        max_delay_ms: 100  # Stricter than 3GPP default
      # video, iot, best_effort use defaults

  # Satellite Load Simulation
  # SOURCE: 3GPP TR 38.821 + He et al. (2021)
  satellite_load_simulation:
    capacity_per_satellite: 200  # Typical Starlink capacity
    # SOURCE: 3GPP TR 38.821 Section 6.1.1

    enabled_patterns:
      - uniform
      - concentrated
      - dynamic

    # Pattern probability distribution
    pattern_distribution:
      uniform: 0.3        # 30% samples
      concentrated: 0.4   # 40% samples (most interesting for RL)
      dynamic: 0.3        # 30% samples

    random_seed: 42  # For reproducibility

  # Scenario Generation Control
  scenario_generation:
    variants_per_sample: 12  # 4 traffic × 3 load = 12 variants
    variant_id_format: "{base_id}_v{index:03d}_{traffic}_{load}"

    # Output control
    output_all_variants: true  # If false, randomly sample N variants
    sampled_variants_per_sample: 4  # Used if output_all_variants=false
```

---

## ✅ 測試策略

### 單元測試

**FILE**: `tests/test_traffic_profile_generator.py`

```python
def test_voip_profile_qos_parameters():
    """測試 VoIP 流量類型 QoS 參數符合 3GPP 標準"""
    config = {}
    gen = TrafficProfileGenerator(config, logger)

    voip = gen.generate_profile(TrafficType.VOIP)

    assert voip.max_delay_ms <= 150.0
    assert voip.min_bandwidth_kbps >= 64.0
    assert voip.min_reliability >= 0.99
    assert voip.priority == 1  # Highest

def test_all_enabled_profiles_generated():
    """測試所有啟用的流量類型都被生成"""
    config = {'enabled_types': ['voip', 'video']}
    gen = TrafficProfileGenerator(config, logger)

    profiles = gen.generate_all_profiles()

    assert len(profiles) == 2
    assert 'voip' in profiles
    assert 'video' in profiles
```

**FILE**: `tests/test_satellite_load_simulator.py`

```python
def test_uniform_load_low_variance():
    """測試均勻負載模式產生低變異分布"""
    config = {'capacity_per_satellite': 200, 'random_seed': 42}
    sim = SatelliteLoadSimulator(config, logger)

    sat_ids = [f"SAT{i}" for i in range(20)]
    loads = sim.generate_uniform_load(sat_ids)

    utils = [l.utilization for l in loads]
    assert np.std(utils) < 0.1  # Low variance

def test_concentrated_load_80_20_rule():
    """測試集中負載模式符合 80-20 原則"""
    config = {'capacity_per_satellite': 200, 'random_seed': 42}
    sim = SatelliteLoadSimulator(config, logger)

    sat_ids = [f"SAT{i}" for i in range(20)]
    loads = sim.generate_concentrated_load(sat_ids)

    high_load = [l for l in loads if l.utilization > 0.7]
    low_load = [l for l in loads if l.utilization < 0.4]

    assert len(high_load) >= 3  # ~20%
    assert len(low_load) >= 14  # ~80%
```

---

### 整合測試

**FILE**: `tests/test_scenario_variant_integration.py`

```python
def test_full_variant_generation_pipeline():
    """測試完整變體生成流程"""
    config = {
        'traffic_profiles': {'enabled_types': ['voip', 'video']},
        'satellite_load_simulation': {'enabled_patterns': ['uniform', 'concentrated']},
        'scenario_generation': {'variants_per_sample': 4}
    }

    traffic_gen = TrafficProfileGenerator(config['traffic_profiles'], logger)
    load_sim = SatelliteLoadSimulator(config['satellite_load_simulation'], logger)
    variant_gen = ScenarioVariantGenerator(traffic_gen, load_sim, config['scenario_generation'], logger)

    variants = variant_gen.generate_variants(
        base_sample_id="TEST_SAMPLE",
        satellite_ids=["SAT1", "SAT2", "SAT3"],
        timestamp_index=0
    )

    # Should generate 2 traffic × 2 load = 4 variants
    assert len(variants) == 4

    # Verify variant IDs are unique
    variant_ids = [v.variant_id for v in variants]
    assert len(set(variant_ids)) == 4

    # Verify traffic profiles differ
    traffic_types = [v.traffic_profile['type'] for v in variants]
    assert 'voip' in traffic_types
    assert 'video' in traffic_types
```

---

## 📊 預期輸出格式

```json
{
  "sample_id": "starlink_t000",
  "timestamp": "2025-10-22T01:53:00+00:00",

  "scenario_variants": [
    {
      "variant_id": "starlink_t000_v001_voip_uniform",
      "base_sample_id": "starlink_t000",
      "variant_index": 1,
      "total_variants": 12,

      "traffic_profile": {
        "type": "voip",
        "category": "conversational",
        "max_delay_ms": 150.0,
        "min_bandwidth_kbps": 64.0,
        "min_reliability": 0.99,
        "priority": 1,
        "description": "Real-time voice communication"
      },

      "satellite_loads": [
        {
          "satellite_id": "46061",
          "current_users": 105,
          "capacity": 200,
          "utilization": 0.525,
          "load_state": "moderate",
          "pattern": "uniform"
        }
      ]
    },
    {
      "variant_id": "starlink_t000_v002_voip_concentrated",
      ...
    }
  ]
}
```

---

## 🎯 驗收標準

### 學術合規性
- ✅ 流量類型參數來自 3GPP TS 22.261
- ✅ 負載容量來自 3GPP TR 38.821
- ✅ 所有參數有 SOURCE 註解
- ✅ 無簡化算法或估計值

### 功能正確性
- ✅ 生成 4 種流量類型（VoIP/Video/IoT/BestEffort）
- ✅ 生成 3 種負載模式（Uniform/Concentrated/Dynamic）
- ✅ 變體 ID 唯一且可追溯
- ✅ 笛卡爾積組合正確（4×3=12 變體）

### 性能要求
- ✅ 單樣本變體生成 < 10 ms
- ✅ Stage 6 執行時間增加 < 30%
- ✅ 輸出檔案大小增加 < 50%

### 向後兼容性
- ✅ `enable_scenario_diversity: false` 時不影響現有輸出
- ✅ 新欄位為可選（不破壞下游）

---

**下一步**: 進入 [06-TEST-PLAN.md](./06-TEST-PLAN.md) 了解完整測試策略
