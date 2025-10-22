# 架構設計：訓練數據多樣性增強

## 🏗️ 總體架構

### 擴充前（現況）

```
Stage 1: TLE Loading
    ↓
Stage 2: Orbital Propagation (SGP4)
    ↓
Stage 3: Coordinate Transformation (TEME → WGS84)
    ↓
Stage 4: Link Feasibility (Pool Optimization)
    ↓
Stage 5: Signal Quality Analysis          ← 靜態計算
    ├── FSPL (Free Space Path Loss)
    ├── Atmospheric Attenuation (ITU-R)
    └── Rain Attenuation
    ↓
Stage 6: Research Optimization            ← 單一場景
    ├── Handover Events (A3/A4/A5/D2)
    └── RL Training Data Generation
```

**限制**:
- Stage 5: 僅靜態幾何可見性，無動態傳播條件
- Stage 6: 單一場景，無流量類型/負載變化

---

### 擴充後（目標）

```
Stage 1-4: 保持不變
    ↓
Stage 5: Signal Quality + **Dynamic Propagation**   ← NEW
    ├── FSPL (Free Space Path Loss)
    ├── Atmospheric Attenuation (ITU-R)
    ├── Rain Attenuation
    ├── **Three-State Markov Model**                 ← NEW
    │   └── LOS / Shadowed / Blocked
    └── **Loo Channel Model**                        ← NEW
        └── Channel Attenuation (Multipath + Shadowing)
    ↓
Stage 6: Research Optimization + **Scenario Diversity**  ← NEW
    ├── Handover Events (A3/A4/A5/D2)
    ├── **Traffic Profile Generator**                ← NEW
    │   └── VoIP / Video / IoT / BestEffort
    ├── **Satellite Load Simulator**                 ← NEW
    │   └── Uniform / Concentrated / Dynamic
    └── **Multi-Scenario Variant Generation**        ← NEW
        └── Same orbit data, different conditions
```

**改進**:
- Stage 5: 動態傳播條件（LOS/Shadowed/Blocked + Loo 通道）
- Stage 6: 場景多樣性（流量類型 + 負載模擬）

---

## 📦 模組架構

### Stage 5 新增模組

```
src/stages/stage5_signal_analysis/
├── (現有模組)
│   ├── stage5_signal_analysis_processor.py
│   ├── gpp_ts38214_signal_calculator.py
│   ├── itur_official_atmospheric_model.py
│   └── ...
└── (新增模組)
    ├── propagation_state_simulator.py          ← NEW
    │   ├── class ThreeStateMarkovModel
    │   ├── class LooChannelModel
    │   └── class PropagationConditionSimulator
    └── propagation_config.py                   ← NEW
        └── Default Markov transition rates
```

### Stage 6 新增模組

```
src/stages/stage6_research_optimization/
├── (現有模組)
│   ├── stage6_research_optimizer.py
│   ├── gpp_event_detector.py
│   └── ...
└── (新增模組)
    ├── traffic_profile_generator.py            ← NEW
    │   ├── @dataclass TrafficProfile
    │   └── class TrafficProfileGenerator
    ├── satellite_load_simulator.py             ← NEW
    │   ├── enum LoadPattern
    │   └── class SatelliteLoadSimulator
    └── scenario_variant_generator.py           ← NEW
        └── class ScenarioVariantGenerator
```

---

## 🔄 數據流設計

### Stage 5 數據流

**輸入** (from Stage 4):
```json
{
  "satellite_id": "46061",
  "timestamp": "2025-10-21T01:53:00+00:00",
  "visibility_metrics": {
    "elevation_deg": 5.62,
    "azimuth_deg": 324.51,
    "distance_km": 2149.75
  }
}
```

**處理流程**:
```
1. FSPL 計算 (現有)
2. 大氣衰減 (現有)
3. 降雨衰減 (現有)
4. **Markov 狀態更新 (NEW)**
   - 輸入: 前一狀態, 仰角, 環境
   - 輸出: 當前傳播狀態 (LOS/Shadowed/Blocked)
5. **Loo 通道計算 (NEW)**
   - 輸入: 傳播狀態, 距離, 仰角
   - 輸出: 通道衰減 (dB)
6. 總路徑損耗合併
```

**輸出** (to Stage 6):
```json
{
  "satellite_id": "46061",
  "timestamp": "2025-10-21T01:53:00+00:00",
  "signal_quality": {
    "rsrp_dbm": -35.2,
    "rsrq_db": -10.5,
    // ... 現有欄位 ...
  },
  "propagation_condition": {                    // NEW
    "state": "LOS",
    "markov_transition_prob": {
      "P_LL": 0.95,
      "P_LS": 0.04,
      "P_LB": 0.01
    },
    "channel_attenuation_db": 2.3,
    "loo_parameters": {
      "mp_db": -15.2,
      "sigma_db": 3.5
    }
  }
}
```

---

### Stage 6 數據流

**輸入** (from Stage 5):
```json
{
  "signal_analysis": {
    "46061": {
      "time_series": [ /* Stage 5 output */ ]
    }
  }
}
```

**處理流程**:
```
1. 換手事件檢測 (現有)
2. **流量類型生成 (NEW)**
   - 為每個基礎軌道數據生成 4 種流量變體
   - VoIP / Video / IoT / BestEffort
3. **負載狀態生成 (NEW)**
   - 模擬 3 種負載模式
   - Uniform / Concentrated / Dynamic
4. **場景變體組合 (NEW)**
   - 組合流量類型 × 負載模式
   - 生成多個訓練樣本變體
5. RL 訓練數據格式化 (現有)
```

**輸出** (final):
```json
{
  "scenario_variants": [
    {
      "variant_id": "voip_uniform_001",
      "base_satellite_id": "46061",
      "base_timestamp": "2025-10-21T01:53:00+00:00",
      "traffic_profile": {                      // NEW
        "type": "voip",
        "qos_requirements": {
          "max_delay_ms": 150,
          "min_bandwidth_kbps": 64,
          "min_reliability": 0.99
        }
      },
      "satellite_loads": [                      // NEW
        {
          "satellite_id": "46061",
          "utilization": 0.45,
          "load_state": "moderate"
        }
      ],
      "handover_events": [ /* existing */ ],
      "rl_training_sample": { /* existing */ }
    },
    // ... more variants ...
  ]
}
```

---

## 🔌 接口設計

### Stage 5 新增 API

#### PropagationConditionSimulator

```python
class PropagationConditionSimulator:
    """
    動態傳播條件模擬器

    職責:
    1. 維護 Markov 狀態機（每個衛星獨立）
    2. 計算 Loo 通道衰減
    3. 整合到 Stage 5 流程
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 包含 Markov 轉換率、Loo 參數
        """
        self.markov_model = ThreeStateMarkovModel(
            transition_matrix=config['markov_transition_matrix']
        )
        self.loo_model = LooChannelModel(
            mp_mean_db=config['loo_mp_mean_db'],
            sigma_db=config['loo_sigma_db']
        )

    def simulate_propagation(
        self,
        satellite_id: str,
        elevation_deg: float,
        distance_km: float,
        prev_state: str = None
    ) -> Dict[str, Any]:
        """
        模擬單個時間點的傳播條件

        Args:
            satellite_id: 衛星 ID
            elevation_deg: 仰角 (degrees)
            distance_km: 距離 (km)
            prev_state: 前一狀態 (LOS/Shadowed/Blocked)

        Returns:
            {
                'state': 'LOS' | 'Shadowed' | 'Blocked',
                'transition_prob': {...},
                'channel_attenuation_db': float,
                'loo_parameters': {...}
            }
        """
        # 1. Markov 狀態轉換
        current_state = self.markov_model.transition(
            prev_state=prev_state,
            elevation_deg=elevation_deg
        )

        # 2. Loo 通道計算
        channel_attenuation = self.loo_model.calculate_attenuation(
            state=current_state,
            distance_km=distance_km,
            elevation_deg=elevation_deg
        )

        return {
            'state': current_state,
            'transition_prob': self.markov_model.get_transition_prob(),
            'channel_attenuation_db': channel_attenuation,
            'loo_parameters': self.loo_model.get_parameters()
        }
```

#### ThreeStateMarkovModel

```python
class ThreeStateMarkovModel:
    """
    三態 Markov 模型

    States: LOS, Shadowed, Blocked

    SOURCE: Gilbert-Elliott Model (1960)
            Lutz et al. (1991) "The land mobile satellite communication channel"
    """

    STATES = ['LOS', 'Shadowed', 'Blocked']

    def __init__(self, transition_matrix: np.ndarray):
        """
        Args:
            transition_matrix: 3x3 轉換矩陣
                [[P_LL, P_LS, P_LB],
                 [P_SL, P_SS, P_SB],
                 [P_BL, P_BS, P_BB]]

        SOURCE: 3GPP TR 38.901 Table 7.6.3.1-1
        """
        self.P = transition_matrix
        self.current_state = 'LOS'  # 初始狀態

    def transition(
        self,
        prev_state: str = None,
        elevation_deg: float = None
    ) -> str:
        """
        執行狀態轉換

        Args:
            prev_state: 前一狀態 (None = 使用內部狀態)
            elevation_deg: 仰角 (影響轉換機率)

        Returns:
            new_state: 新狀態 ('LOS' | 'Shadowed' | 'Blocked')
        """
        if prev_state:
            self.current_state = prev_state

        # 仰角影響轉換率 (高仰角 → 更可能維持 LOS)
        adjusted_P = self._adjust_by_elevation(self.P, elevation_deg)

        # 根據當前狀態選擇轉換機率
        state_idx = self.STATES.index(self.current_state)
        prob_vector = adjusted_P[state_idx, :]

        # 隨機轉換
        new_state_idx = np.random.choice(len(self.STATES), p=prob_vector)
        self.current_state = self.STATES[new_state_idx]

        return self.current_state
```

#### LooChannelModel

```python
class LooChannelModel:
    """
    Loo 通道模型（適用於 Land Mobile Satellite 鏈路）

    SOURCE: Loo, C. (1985). "A statistical model for a land mobile satellite link"
            IEEE Transactions on Vehicular Technology, 34(3), 122-127.
    """

    def __init__(self, mp_mean_db: float, sigma_db: float):
        """
        Args:
            mp_mean_db: Multipath component mean (dB)
            sigma_db: Shadowing standard deviation (dB)

        SOURCE: Loo (1985) Table II - Typical Parameters
                Urban: mp_mean_db=-20, sigma_db=6
                Suburban: mp_mean_db=-15, sigma_db=3
                Rural: mp_mean_db=-10, sigma_db=1
        """
        self.mp_mean_db = mp_mean_db
        self.sigma_db = sigma_db

    def calculate_attenuation(
        self,
        state: str,
        distance_km: float,
        elevation_deg: float
    ) -> float:
        """
        計算通道衰減

        Args:
            state: 傳播狀態 ('LOS' | 'Shadowed' | 'Blocked')
            distance_km: 衛星距離
            elevation_deg: 仰角

        Returns:
            attenuation_db: 通道衰減 (dB)

        SOURCE: Loo (1985) Equation (5)
                A = A_los + A_mp + A_shadow
        """
        if state == 'Blocked':
            return float('inf')  # 完全遮蔽

        # LOS component (always present)
        A_los = 0.0

        # Multipath component (Rayleigh fading)
        A_mp = np.random.exponential(scale=abs(self.mp_mean_db))

        # Shadowing component (Lognormal)
        if state == 'Shadowed':
            A_shadow = np.random.normal(loc=0, scale=self.sigma_db)
        else:  # LOS
            A_shadow = 0.0

        total_attenuation = A_los + A_mp + abs(A_shadow)
        return total_attenuation
```

---

### Stage 6 新增 API

#### TrafficProfileGenerator

```python
@dataclass
class TrafficProfile:
    """
    流量類型定義

    SOURCE: 3GPP TS 22.261 Section 7 - Service requirements
    """
    type: str  # 'voip' | 'video' | 'iot' | 'best_effort'
    max_delay_ms: float
    min_bandwidth_kbps: float
    min_reliability: float
    priority: str  # 'high' | 'medium' | 'low'


class TrafficProfileGenerator:
    """
    流量類型生成器
    """

    # SOURCE: 3GPP TS 22.261 Table 7.2.1-1
    PROFILES = {
        'voip': TrafficProfile(
            type='voip',
            max_delay_ms=150,
            min_bandwidth_kbps=64,
            min_reliability=0.99,
            priority='high'
        ),
        'video': TrafficProfile(
            type='video',
            max_delay_ms=400,
            min_bandwidth_kbps=5000,
            min_reliability=0.95,
            priority='medium'
        ),
        'iot': TrafficProfile(
            type='iot',
            max_delay_ms=5000,
            min_bandwidth_kbps=10,
            min_reliability=0.90,
            priority='low'
        ),
        'best_effort': TrafficProfile(
            type='best_effort',
            max_delay_ms=float('inf'),
            min_bandwidth_kbps=0,
            min_reliability=0.80,
            priority='low'
        )
    }

    def generate_variants(
        self,
        base_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        為基礎數據生成流量類型變體

        Args:
            base_data: Stage 5 輸出的單筆數據

        Returns:
            variants: 4 種流量類型變體
        """
        variants = []
        for profile_name, profile in self.PROFILES.items():
            variant = base_data.copy()
            variant['traffic_profile'] = profile.__dict__
            variant['variant_id'] = f"{profile_name}_{uuid.uuid4().hex[:6]}"
            variants.append(variant)
        return variants
```

#### SatelliteLoadSimulator

```python
class LoadPattern(Enum):
    """負載模式"""
    UNIFORM = "uniform"          # 均勻分布
    CONCENTRATED = "concentrated"  # 集中負載
    DYNAMIC = "dynamic"           # 動態變化


class SatelliteLoadSimulator:
    """
    衛星負載模擬器

    SOURCE: 3GPP TR 38.821 Section 6.1.4 - Capacity assumptions
    """

    # SOURCE: 3GPP TR 38.821 - Starlink ~200 users/satellite
    DEFAULT_CAPACITY = 200

    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self.capacity = capacity

    def generate_loads(
        self,
        satellites: List[str],
        pattern: LoadPattern,
        timestamp: str = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成衛星負載狀態

        Args:
            satellites: 衛星 ID 列表
            pattern: 負載模式
            timestamp: 時間戳（用於 Dynamic 模式）

        Returns:
            loads: {satellite_id: {current_users, utilization, state}}
        """
        if pattern == LoadPattern.UNIFORM:
            return self._generate_uniform(satellites)
        elif pattern == LoadPattern.CONCENTRATED:
            return self._generate_concentrated(satellites)
        else:  # DYNAMIC
            return self._generate_dynamic(satellites, timestamp)

    def _generate_uniform(self, satellites: List[str]) -> Dict:
        """均勻負載 (0.4-0.6)"""
        loads = {}
        for sat_id in satellites:
            util = np.random.uniform(0.4, 0.6)
            loads[sat_id] = {
                'current_users': int(util * self.capacity),
                'capacity': self.capacity,
                'utilization': util,
                'load_state': 'moderate'
            }
        return loads

    # ... _generate_concentrated, _generate_dynamic ...
```

---

## 🧪 配置設計

### Stage 5 配置擴充

**檔案**: `config/stage5_signal_analysis_config.yaml`

```yaml
# ==================== 動態傳播條件配置 (NEW) ====================
enable_propagation_simulation: true  # 啟用/停用動態傳播模擬

# Markov 模型參數
markov_model:
  # SOURCE: 3GPP TR 38.901 Table 7.6.3.1-1
  # Urban LMS Channel Model
  transition_matrix:
    # [LOS, Shadowed, Blocked]
    LOS:       [0.95, 0.04, 0.01]
    Shadowed:  [0.30, 0.60, 0.10]
    Blocked:   [0.10, 0.30, 0.60]

  # 仰角影響係數
  elevation_adjustment:
    enabled: true
    # 高仰角 (>60°) → P_LL += 0.05 (更穩定)
    # 低仰角 (<30°) → P_LB += 0.05 (更易遮蔽)

# Loo 通道參數
loo_channel:
  # SOURCE: Loo (1985) Table II
  # NTPU 環境分類: Suburban
  mp_mean_db: -15.0      # Multipath component mean
  sigma_db: 3.0          # Shadowing std deviation

  # 環境特定調整 (NTPU 台北科大)
  environment: "suburban"
  altitude_m: 36.0
  local_terrain: "urban_fringe"

# 初始狀態
initial_state: "LOS"     # 所有衛星初始為 LOS 狀態

# 日誌設置
logging:
  log_state_transitions: true  # 記錄狀態轉換
  log_channel_stats: true      # 記錄通道統計
```

---

### Stage 6 配置擴充

**檔案**: `config/stage6_research_optimization_config.yaml`

```yaml
# ==================== 場景多樣性配置 (NEW) ====================
enable_traffic_profiles: true  # 啟用流量類型生成
enable_load_simulation: true   # 啟用負載模擬

# 流量類型配置
traffic_profiles:
  # SOURCE: 3GPP TS 22.261 Section 7
  enabled_types:
    - voip
    - video
    - iot
    - best_effort

  # 自定義參數 (覆寫預設值)
  custom_parameters:
    voip:
      max_delay_ms: 150
      min_bandwidth_kbps: 64
    video:
      max_delay_ms: 400
      min_bandwidth_kbps: 5000

# 負載模擬配置
satellite_load_simulation:
  # SOURCE: 3GPP TR 38.821 Section 6.1.4
  capacity_per_satellite: 200  # Starlink capacity assumption

  enabled_patterns:
    - uniform
    - concentrated
    - dynamic

  pattern_distribution:
    uniform: 0.4        # 40% 機率
    concentrated: 0.3   # 30% 機率
    dynamic: 0.3        # 30% 機率

# 場景變體生成
scenario_generation:
  variants_per_sample: 12  # 每個基礎樣本生成 12 個變體
  # 12 = 4 traffic types × 3 load patterns

  variant_id_format: "{traffic}_{load}_{timestamp}_{uuid}"

# 輸出控制
output:
  include_base_data: true      # 包含原始數據
  include_variants: true       # 包含變體數據
  separate_variant_files: false  # 是否分離變體檔案
```

---

## 🔒 錯誤處理

### Stage 5 錯誤處理

```python
class PropagationSimulationError(Exception):
    """傳播模擬錯誤基類"""
    pass

class MarkovStateError(PropagationSimulationError):
    """Markov 狀態錯誤"""
    pass

class LooChannelError(PropagationSimulationError):
    """Loo 通道計算錯誤"""
    pass

# 降級策略
def simulate_with_fallback(satellite_data):
    try:
        return propagation_simulator.simulate(satellite_data)
    except PropagationSimulationError as e:
        logger.warning(f"傳播模擬失敗: {e}, 降級為靜態模式")
        return {
            'state': 'LOS',  # 預設 LOS
            'channel_attenuation_db': 0.0
        }
```

### Stage 6 錯誤處理

```python
class ScenarioGenerationError(Exception):
    """場景生成錯誤基類"""
    pass

# 驗證機制
def validate_traffic_profile(profile: TrafficProfile):
    """驗證流量類型參數合理性"""
    assert profile.max_delay_ms > 0, "Delay must be positive"
    assert profile.min_bandwidth_kbps >= 0, "Bandwidth must be non-negative"
    assert 0 <= profile.min_reliability <= 1, "Reliability must be in [0, 1]"

def validate_load_state(load: Dict):
    """驗證負載狀態合理性"""
    assert 0 <= load['utilization'] <= 1, "Utilization must be in [0, 1]"
    assert load['current_users'] <= load['capacity'], "Users exceed capacity"
```

---

## 📊 性能優化

### Stage 5 優化策略

1. **Markov 狀態緩存**
   - 維護每個衛星的當前狀態，避免重複初始化

2. **Vectorized 計算**
   - 使用 NumPy vectorization 批次計算 Loo 通道

3. **條件執行**
   - 僅在 `enable_propagation_simulation: true` 時執行

### Stage 6 優化策略

1. **Template 複用**
   - 流量類型 profile 使用 immutable dataclass

2. **並行生成**
   - 場景變體生成使用 `concurrent.futures`

3. **增量輸出**
   - 避免在記憶體中累積所有變體

---

**下一步**: 詳細設計 Stage 5 實現（03-STAGE5-PROPAGATION.md）
