# 📡 Stage 5: 3GPP事件檢測優化計劃

## 📋 階段概覽

**目標**：優化3GPP NTN換手事件檢測，確保A4/A5/D2事件符合3GPP標準

**時程**：第4週前半 (2個工作日)

**優先級**：✅ 低風險 - 基本功能正確

**現狀評估**：3GPP事件檢測基本正確，僅需輕微優化和標準合規驗證

## 🎯 重構目標

### 核心目標
- ✅ **標準合規**: 確保A4/A5/D2事件完全符合3GPP TS 38.331標準
- ✅ **參數優化**: 優化觸發門檻和滯後參數
- ✅ **事件整合**: 與Stage 4衛星池分析數據整合
- ✅ **RL數據準備**: 為Stage 6 RL環境提供事件觸發數據

### 學術研究要求 (基於 docs/final.md)
- **A4事件支援**: 鄰近衛星變得優於門檻值 (Neighbour becomes better than threshold)
- **A5事件支援**: 服務衛星劣於門檻1且鄰近衛星優於門檻2
- **D2事件支援**: UE與服務衛星距離超過門檻1且與候選衛星距離低於門檻2

## 🔧 技術實現

### 3GPP NTN事件標準

#### A4事件 (鄰近衛星優於門檻)
```python
# 標準依據: 3GPP TS 38.331 v18.5.1 Section 5.5.4.5
# 觸發條件: Mn + Ofn + Ocn – Hys > Thresh (進入條件)
```

#### A5事件 (雙門檻換手)
```python
# 標準依據: 3GPP TS 38.331 v18.5.1 Section 5.5.4.6
# 觸發條件: (Mp + Hys < Thresh1) AND (Mn + Ofn + Ocn – Hys > Thresh2)
```

#### D2事件 (距離換手)
```python
# 標準依據: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a
# 觸發條件: (Ml1 – Hys > Thresh1) AND (Ml2 + Hys < Thresh2)
```

### 優化架構設計

```python
# 3GPP事件檢測架構
gpp_events/
├── event_detector.py          # 3GPP事件檢測器
├── parameter_optimizer.py     # 觸發參數優化
├── standard_validator.py      # 3GPP標準驗證
└── rl_data_generator.py       # RL訓練數據生成
```

## 📅 實施計劃 (2天)

### Day 1: 3GPP標準事件檢測優化
```python
# event_detector.py 3GPP標準事件檢測器
from dataclasses import dataclass
from typing import List, Optional, Dict
import numpy as np

@dataclass
class GPP3EventParameters:
    """3GPP事件參數配置"""
    # A4事件參數
    a4_threshold: float = -95.0  # dBm
    a4_offset_frequency: float = 0.0  # Ofn
    a4_offset_cell: float = 0.0       # Ocn
    a4_hysteresis: float = 2.0        # dB

    # A5事件參數
    a5_threshold1: float = -100.0  # 服務衛星門檻 (dBm)
    a5_threshold2: float = -95.0   # 鄰近衛星門檻 (dBm)
    a5_hysteresis: float = 2.0     # dB

    # D2事件參數
    d2_threshold1: float = 1500.0  # 服務衛星距離門檻 (km)
    d2_threshold2: float = 800.0   # 候選衛星距離門檻 (km)
    d2_hysteresis: float = 50.0    # km

class GPP3EventDetector:
    """3GPP NTN事件檢測器 - 標準合規版本"""

    def __init__(self, parameters: GPP3EventParameters = None):
        self.params = parameters or GPP3EventParameters()
        self.event_history = []

    def detect_a4_events(self, serving_satellite: SatelliteCoordinates,
                        neighbor_satellites: List[SatelliteCoordinates]) -> List[A4Event]:
        """檢測A4事件: 鄰近衛星變得優於門檻值"""

        a4_events = []

        for neighbor in neighbor_satellites:
            # 計算鄰近衛星RSRP (使用Stage 3的信號處理)
            neighbor_rsrp = self._calculate_rsrp_from_distance(neighbor.distance_km)

            # A4觸發條件檢查
            # Mn + Ofn + Ocn – Hys > Thresh
            trigger_condition = (
                neighbor_rsrp +
                self.params.a4_offset_frequency +
                self.params.a4_offset_cell -
                self.params.a4_hysteresis
            ) > self.params.a4_threshold

            if trigger_condition:
                a4_event = A4Event(
                    event_type="A4",
                    trigger_time=neighbor.time,
                    serving_satellite=serving_satellite.satellite_name,
                    neighbor_satellite=neighbor.satellite_name,
                    neighbor_rsrp=neighbor_rsrp,
                    threshold_value=self.params.a4_threshold,
                    margin=neighbor_rsrp - self.params.a4_threshold,
                    parameters_used=self.params
                )
                a4_events.append(a4_event)

        return a4_events

    def detect_a5_events(self, serving_satellite: SatelliteCoordinates,
                        neighbor_satellites: List[SatelliteCoordinates]) -> List[A5Event]:
        """檢測A5事件: 服務衛星劣於門檻1且鄰近衛星優於門檻2"""

        # 計算服務衛星RSRP
        serving_rsrp = self._calculate_rsrp_from_distance(serving_satellite.distance_km)

        # 檢查服務衛星劣化條件: Mp + Hys < Thresh1
        serving_degraded = (serving_rsrp + self.params.a5_hysteresis) < self.params.a5_threshold1

        if not serving_degraded:
            return []

        a5_events = []
        for neighbor in neighbor_satellites:
            neighbor_rsrp = self._calculate_rsrp_from_distance(neighbor.distance_km)

            # 檢查鄰近衛星改善條件: Mn + Ofn + Ocn – Hys > Thresh2
            neighbor_improved = (neighbor_rsrp - self.params.a5_hysteresis) > self.params.a5_threshold2

            if neighbor_improved:
                a5_event = A5Event(
                    event_type="A5",
                    trigger_time=neighbor.time,
                    serving_satellite=serving_satellite.satellite_name,
                    neighbor_satellite=neighbor.satellite_name,
                    serving_rsrp=serving_rsrp,
                    neighbor_rsrp=neighbor_rsrp,
                    threshold1=self.params.a5_threshold1,
                    threshold2=self.params.a5_threshold2,
                    dual_condition_met=True
                )
                a5_events.append(a5_event)

        return a5_events

    def detect_d2_events(self, serving_satellite: SatelliteCoordinates,
                        candidate_satellites: List[SatelliteCoordinates]) -> List[D2Event]:
        """檢測D2事件: 基於衛星移動軌跡的距離換手"""

        serving_distance = serving_satellite.distance_km

        # 檢查服務衛星距離過遠條件: Ml1 – Hys > Thresh1
        serving_too_far = (serving_distance - self.params.d2_hysteresis) > self.params.d2_threshold1

        if not serving_too_far:
            return []

        d2_events = []
        for candidate in candidate_satellites:
            candidate_distance = candidate.distance_km

            # 檢查候選衛星距離合適條件: Ml2 + Hys < Thresh2
            candidate_close = (candidate_distance + self.params.d2_hysteresis) < self.params.d2_threshold2

            if candidate_close:
                d2_event = D2Event(
                    event_type="D2",
                    trigger_time=candidate.time,
                    serving_satellite=serving_satellite.satellite_name,
                    candidate_satellite=candidate.satellite_name,
                    serving_distance=serving_distance,
                    candidate_distance=candidate_distance,
                    distance_improvement=serving_distance - candidate_distance,
                    threshold1=self.params.d2_threshold1,
                    threshold2=self.params.d2_threshold2
                )
                d2_events.append(d2_event)

        return d2_events

    def _calculate_rsrp_from_distance(self, distance_km: float) -> float:
        """基於距離計算RSRP - 整合Stage 3信號處理"""

        # 使用Stage 3的信號處理器
        # 這裡簡化實現，實際應調用Stage 3的SignalQualityProcessor
        tx_power_dbm = 43.0
        frequency_ghz = 2.0
        antenna_gain = 15.0

        path_loss = (
            20 * np.log10(distance_km) +
            20 * np.log10(frequency_ghz) +
            92.45
        )

        rsrp = tx_power_dbm + antenna_gain - path_loss
        return rsrp
```

### Day 2: 參數優化與RL數據準備
```python
# parameter_optimizer.py 參數優化
class EventParameterOptimizer:
    """3GPP事件參數優化器"""

    def __init__(self):
        self.optimization_history = []

    def optimize_for_constellation(self, constellation: ConstellationType,
                                 historical_events: List[HandoverEvent]) -> GPP3EventParameters:
        """針對星座特性優化事件參數"""

        if constellation == ConstellationType.STARLINK:
            # Starlink特化參數 (LEO特性)
            return GPP3EventParameters(
                a4_threshold=-90.0,      # 較高門檻 (信號較強)
                a4_hysteresis=1.5,       # 較小滯後 (快速變化)
                a5_threshold1=-95.0,     # 較高服務門檻
                a5_threshold2=-85.0,     # 較高鄰近門檻
                d2_threshold1=1200.0,    # 較小距離門檻 (低軌)
                d2_threshold2=600.0,     # 較小候選距離
                d2_hysteresis=30.0       # 較小距離滯後
            )
        else:  # OneWeb
            # OneWeb特化參數 (MEO特性)
            return GPP3EventParameters(
                a4_threshold=-95.0,      # 標準門檻
                a4_hysteresis=2.0,       # 標準滯後
                a5_threshold1=-100.0,    # 標準服務門檻
                a5_threshold2=-90.0,     # 標準鄰近門檻
                d2_threshold1=1500.0,    # 標準距離門檻
                d2_threshold2=800.0,     # 標準候選距離
                d2_hysteresis=50.0       # 標準距離滯後
            )

# rl_data_generator.py RL訓練數據生成
class RLTrainingDataGenerator:
    """RL訓練數據生成器 - 基於3GPP事件"""

    def __init__(self, event_detector: GPP3EventDetector):
        self.event_detector = event_detector

    def generate_handover_scenarios(self, pool_analysis_data: List[ConstellationCoverage]) -> List[HandoverScenario]:
        """基於衛星池分析生成換手訓練場景"""

        scenarios = []

        for coverage_data in pool_analysis_data:
            for time_point in coverage_data.pool_analysis.timeline:
                if len(time_point.visible_satellites) >= 2:
                    # 有多顆衛星可見，可能觸發換手事件

                    serving_satellite = time_point.visible_satellites[0]  # 假設第一顆為服務衛星
                    neighbors = time_point.visible_satellites[1:]

                    # 檢測各類事件
                    a4_events = self.event_detector.detect_a4_events(serving_satellite, neighbors)
                    a5_events = self.event_detector.detect_a5_events(serving_satellite, neighbors)
                    d2_events = self.event_detector.detect_d2_events(serving_satellite, neighbors)

                    # 創建訓練場景
                    if a4_events or a5_events or d2_events:
                        scenario = HandoverScenario(
                            scenario_id=f"{coverage_data.constellation.value}_{time_point.time_minute}",
                            serving_satellite=serving_satellite,
                            candidate_satellites=neighbors,
                            triggered_events=a4_events + a5_events + d2_events,
                            pool_state=time_point,
                            scenario_type=self._classify_scenario_type(a4_events, a5_events, d2_events),
                            constellation=coverage_data.constellation
                        )
                        scenarios.append(scenario)

        return scenarios

    def _classify_scenario_type(self, a4_events: List, a5_events: List, d2_events: List) -> str:
        """分類場景類型"""

        if a4_events and not a5_events and not d2_events:
            return "neighbor_improvement"  # 鄰近改善型
        elif a5_events:
            return "serving_degradation"   # 服務劣化型
        elif d2_events:
            return "distance_based"        # 距離換手型
        else:
            return "mixed_events"          # 混合事件型

    def export_for_rl_training(self, scenarios: List[HandoverScenario], output_path: str):
        """導出RL訓練數據格式"""

        rl_training_data = {
            'scenarios': [],
            'state_features': [],
            'action_labels': [],
            'reward_signals': []
        }

        for scenario in scenarios:
            # 特徵提取
            state_features = self._extract_state_features(scenario)
            action_label = self._determine_optimal_action(scenario)
            reward_signal = self._calculate_reward(scenario)

            rl_training_data['scenarios'].append(scenario.scenario_id)
            rl_training_data['state_features'].append(state_features)
            rl_training_data['action_labels'].append(action_label)
            rl_training_data['reward_signals'].append(reward_signal)

        # 保存為JSON格式供Stage 6使用
        import json
        with open(output_path, 'w') as f:
            json.dump(rl_training_data, f, indent=2, default=str)
```

## 🧪 驗證測試

### 3GPP標準合規測試
```python
def test_3gpp_standard_compliance():
    """3GPP標準合規性測試"""

    detector = GPP3EventDetector()

    # A4事件標準測試
    test_serving = create_test_satellite(-85.0, 500.0)  # RSRP -85dBm, 距離500km
    test_neighbors = [
        create_test_satellite(-80.0, 400.0),  # 更好的鄰近衛星
        create_test_satellite(-90.0, 600.0)   # 較差的鄰近衛星
    ]

    a4_events = detector.detect_a4_events(test_serving, test_neighbors)

    # 驗證A4觸發邏輯
    assert len(a4_events) == 1, "A4事件檢測錯誤"
    assert a4_events[0].neighbor_rsrp == -80.0, "RSRP計算錯誤"

def test_event_parameter_optimization():
    """事件參數優化測試"""

    optimizer = EventParameterOptimizer()

    # Starlink參數優化測試
    starlink_params = optimizer.optimize_for_constellation(
        ConstellationType.STARLINK, []
    )

    assert starlink_params.d2_threshold1 < 1500.0, "Starlink距離門檻應較小"
    assert starlink_params.a4_hysteresis < 2.0, "Starlink滯後應較小"

def test_rl_data_generation():
    """RL數據生成測試"""

    generator = RLTrainingDataGenerator(detector)

    # 測試場景生成
    test_pool_data = create_test_pool_analysis_data()
    scenarios = generator.generate_handover_scenarios(test_pool_data)

    assert len(scenarios) > 0, "未生成RL訓練場景"

    # 測試數據導出
    generator.export_for_rl_training(scenarios, "test_rl_data.json")
    assert os.path.exists("test_rl_data.json"), "RL數據導出失敗"
```

## 📊 成功指標

### 量化指標
- **事件檢測準確率**: A4/A5/D2事件檢測準確率 >95%
- **3GPP合規性**: 100%符合3GPP TS 38.331標準
- **RL數據生成**: 生成50+多樣化換手訓練場景
- **參數優化**: 星座特定參數優化完成

### 質化指標
- **標準合規**: 完全符合3GPP NTN換手事件標準
- **數據質量**: 為Stage 6 RL環境提供高質量訓練數據
- **整合完整**: 與Stage 4衛星池數據無縫整合
- **學術價值**: 支援換手優化研究的事件檢測基礎

## ⚠️ 風險控制

### 技術風險
| 風險 | 影響 | 應對策略 |
|------|------|----------|
| 參數設置不當 | 中等 | 基於星座特性分別優化 |
| 事件觸發過敏/遲鈍 | 中等 | 滯後參數精細調整 |
| RL數據品質問題 | 中等 | 多樣化場景生成驗證 |

### 標準風險
- **3GPP合規**: 必須嚴格遵循3GPP TS 38.331標準
- **參數合理性**: 參數設置需符合實際LEO/MEO衛星特性
- **數據一致性**: 與前面階段數據格式保持一致

---

**文檔版本**: v1.0 (修正版)
**建立日期**: 2024-01-15
**前置條件**: Stage 1-4完成 (TLE/軌道/座標/池分析數據可用)
**重點**: 3GPP標準事件檢測，為RL環境準備訓練數據
**下一階段**: Stage 6 - RL環境標準化