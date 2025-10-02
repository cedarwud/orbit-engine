# 3GPP 事件檢測器規格 - Stage 6 核心組件

**檔案**: `src/stages/stage6_research_optimization/gpp_event_detector.py`
**依據**: `docs/stages/stage6-research-optimization.md` Line 115-214
**標準**: 3GPP TS 38.331 v18.5.1

---

## 🎯 核心職責

檢測 LEO 衛星通訊中的 3GPP NTN 標準事件：
1. **A4 事件**: 鄰近衛星變得優於門檻值
2. **A5 事件**: 服務衛星劣於門檻1且鄰近衛星優於門檻2
3. **D2 事件**: 基於距離的換手觸發

---

## 📋 3GPP 標準參數

### A4 事件參數 (3GPP TS 38.331 Section 5.5.4.5)
```python
A4_CONFIG = {
    'threshold_dbm': -100.0,          # A4 門檻值
    'hysteresis_db': 2.0,             # 遲滯
    'offset_frequency': 0.0,          # 頻率偏移 (同頻)
    'offset_cell': 0.0,               # 小區偏移
    'time_to_trigger_ms': 640,        # 觸發延遲
    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
}
```

**觸發條件**:
```
Mn + Ofn + Ocn - Hys > Thresh
```
其中:
- `Mn`: 鄰近衛星測量值 (RSRP)
- `Ofn`: 頻率偏移
- `Ocn`: 小區偏移
- `Hys`: 遲滯
- `Thresh`: A4 門檻值

### A5 事件參數 (3GPP TS 38.331 Section 5.5.4.6)
```python
A5_CONFIG = {
    'threshold1_dbm': -110.0,         # 服務衛星門檻
    'threshold2_dbm': -95.0,          # 鄰近衛星門檻
    'hysteresis_db': 2.0,             # 遲滯
    'time_to_trigger_ms': 640,        # 觸發延遲
    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.6'
}
```

**觸發條件**:
```
條件1: Mp + Hys < Thresh1        (服務衛星劣化)
條件2: Mn + Ofn + Ocn - Hys > Thresh2  (鄰近衛星良好)
```

### D2 事件參數 (3GPP TS 38.331 Section 5.5.4.15a)
```python
D2_CONFIG = {
    'threshold1_km': 1500.0,          # 距離門檻1 (鄰近)
    'threshold2_km': 2000.0,          # 距離門檻2 (服務)
    'hysteresis_km': 50.0,            # 距離遲滯
    'time_to_trigger_ms': 640,        # 觸發延遲
    'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.15a'
}
```

**觸發條件**:
```
條件1: Ml1 - Hys > Thresh1       (鄰近衛星距離優於門檻)
條件2: Ml2 + Hys < Thresh2       (服務衛星距離劣於門檻)
```

---

## 🏗️ 類別設計

```python
class GPPEventDetector:
    """3GPP NTN 事件檢測器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化檢測器

        Args:
            config: 配置參數，包含 A4/A5/D2 門檻值
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 事件統計
        self.event_stats = {
            'a4_events': 0,
            'a5_events': 0,
            'd2_events': 0,
            'total_events': 0
        }

    def detect_all_events(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """檢測所有類型的 3GPP 事件

        Args:
            signal_analysis: Stage 5 的信號分析數據
            serving_satellite_id: 當前服務衛星 ID (可選)

        Returns:
            {
                'a4_events': List[Dict],
                'a5_events': List[Dict],
                'd2_events': List[Dict],
                'total_events': int,
                'event_summary': Dict
            }
        """
        pass

    def detect_a4_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測 A4 事件: 鄰近衛星變得優於門檻值

        Args:
            serving_satellite: 服務衛星數據
            neighbor_satellites: 鄰近衛星列表

        Returns:
            A4 事件列表，每個事件包含:
            {
                'event_type': 'A4',
                'event_id': 'A4_STARLINK-1234_1695024000123',
                'timestamp': '2025-09-27T08:00:00.123456+00:00',
                'serving_satellite': 'STARLINK-5678',
                'neighbor_satellite': 'STARLINK-1234',
                'measurements': {
                    'neighbor_rsrp_dbm': -88.5,
                    'threshold_dbm': -100.0,
                    'hysteresis_db': 2.0,
                    'trigger_margin_db': 11.5
                },
                'gpp_parameters': {
                    'offset_frequency': 0.0,
                    'offset_cell': 0.0,
                    'time_to_trigger_ms': 640
                },
                'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
            }
        """
        pass

    def detect_a5_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測 A5 事件: 服務衛星劣化且鄰近衛星良好

        Args:
            serving_satellite: 服務衛星數據
            neighbor_satellites: 鄰近衛星列表

        Returns:
            A5 事件列表，每個事件包含:
            {
                'event_type': 'A5',
                'event_id': 'A5_STARLINK-1234_1695024000123',
                'timestamp': '2025-09-27T08:00:00.123456+00:00',
                'serving_satellite': 'STARLINK-5678',
                'neighbor_satellite': 'STARLINK-1234',
                'measurements': {
                    'serving_rsrp_dbm': -115.2,
                    'neighbor_rsrp_dbm': -88.5,
                    'threshold1_dbm': -110.0,
                    'threshold2_dbm': -95.0,
                    'serving_margin_db': 5.2,
                    'neighbor_margin_db': 6.5
                },
                'dual_threshold_analysis': {
                    'serving_degraded': True,
                    'neighbor_sufficient': True,
                    'handover_recommended': True
                },
                'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.6'
            }
        """
        pass

    def detect_d2_events(
        self,
        serving_satellite: Dict[str, Any],
        neighbor_satellites: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測 D2 事件: 基於距離的換手觸發

        Args:
            serving_satellite: 服務衛星數據
            neighbor_satellites: 鄰近衛星列表

        Returns:
            D2 事件列表，每個事件包含:
            {
                'event_type': 'D2',
                'event_id': 'D2_STARLINK-1234_1695024000123',
                'timestamp': '2025-09-27T08:00:00.123456+00:00',
                'serving_satellite': 'STARLINK-5678',
                'neighbor_satellite': 'STARLINK-1234',
                'measurements': {
                    'serving_distance_km': 1850.5,
                    'neighbor_distance_km': 1350.2,
                    'threshold1_km': 1500.0,
                    'threshold2_km': 2000.0,
                    'hysteresis_km': 50.0,
                    'distance_improvement_km': 500.3
                },
                'distance_analysis': {
                    'neighbor_closer': True,
                    'serving_far': True,
                    'handover_recommended': True
                },
                'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.15a'
            }
        """
        pass

    def _extract_serving_satellite(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """提取服務衛星數據

        策略:
        1. 如果指定 serving_satellite_id，使用該衛星
        2. 否則選擇 RSRP 最高的衛星作為服務衛星
        """
        pass

    def _extract_neighbor_satellites(
        self,
        signal_analysis: Dict[str, Any],
        serving_satellite_id: str
    ) -> List[Dict[str, Any]]:
        """提取鄰近衛星列表 (排除服務衛星)"""
        pass

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數"""
        default_config = {
            'a4_threshold_dbm': -100.0,
            'a5_threshold1_dbm': -110.0,
            'a5_threshold2_dbm': -95.0,
            'd2_threshold1_km': 1500.0,
            'd2_threshold2_km': 2000.0,
            'hysteresis_db': 2.0,
            'hysteresis_km': 50.0,
            'offset_frequency': 0.0,
            'offset_cell': 0.0,
            'time_to_trigger_ms': 640
        }

        if config:
            default_config.update(config)

        return default_config
```

---

## 📊 輸入數據格式

### 從 Stage 5 接收的數據結構
```python
signal_analysis = {
    'STARLINK-1234': {
        'satellite_id': 'STARLINK-1234',
        'signal_quality': {
            'rsrp_dbm': -88.5,           # ← A4/A5 事件核心
            'rsrq_db': -10.2,
            'rs_sinr_db': 12.8,
            'calculation_standard': '3GPP_TS_38.214'
        },
        'physical_parameters': {
            'distance_km': 1350.2,       # ← D2 事件核心
            'path_loss_db': 165.3,
            'atmospheric_loss_db': 2.1,
            'doppler_shift_hz': 15234.5,
            'propagation_delay_ms': 4.5
        },
        'quality_assessment': {
            'quality_level': 'excellent',
            'is_usable': True,
            'quality_score': 0.92,
            'link_margin_db': 15.2
        },
        'visibility_metrics': {
            'elevation_deg': 45.3,
            'azimuth_deg': 123.5,
            'is_visible': True,
            'is_connectable': True
        },
        'current_position': {
            'latitude_deg': 25.1234,
            'longitude_deg': 121.5678,
            'altitude_km': 550.123
        }
    },
    'STARLINK-5678': {
        # 類似結構
    }
    # ... 更多衛星
}
```

---

## 📤 輸出數據格式

### 完整事件檢測結果
```python
{
    'a4_events': [
        {
            'event_type': 'A4',
            'event_id': 'A4_STARLINK-1234_1695024000123',
            'timestamp': '2025-09-27T08:00:00.123456+00:00',
            'serving_satellite': 'STARLINK-5678',
            'neighbor_satellite': 'STARLINK-1234',
            'measurements': {
                'neighbor_rsrp_dbm': -88.5,
                'threshold_dbm': -100.0,
                'hysteresis_db': 2.0,
                'trigger_margin_db': 11.5
            },
            'gpp_parameters': {
                'offset_frequency': 0.0,
                'offset_cell': 0.0,
                'time_to_trigger_ms': 640
            },
            'standard_reference': '3GPP_TS_38.331_v18.5.1_Section_5.5.4.5'
        }
        # ... 更多 A4 事件
    ],
    'a5_events': [
        # A5 事件列表
    ],
    'd2_events': [
        # D2 事件列表
    ],
    'total_events': 1250,
    'event_summary': {
        'a4_count': 800,
        'a5_count': 350,
        'd2_count': 100,
        'events_per_minute': 52.1,
        'average_trigger_margin_db': 8.3
    }
}
```

---

## ✅ 實現檢查清單

### 功能完整性
- [ ] A4 事件檢測邏輯正確
- [ ] A5 事件檢測邏輯正確
- [ ] D2 事件檢測邏輯正確
- [ ] 服務衛星選擇邏輯
- [ ] 鄰近衛星過濾邏輯
- [ ] 事件去重機制

### 3GPP 標準合規
- [ ] 完整的觸發條件實現
- [ ] 正確的參數引用
- [ ] 標準參考文獻標記
- [ ] 遲滯機制實現
- [ ] Time-to-Trigger 支援

### 錯誤處理
- [ ] 空數據處理
- [ ] 無效 RSRP 處理
- [ ] 無效距離處理
- [ ] 異常捕獲和記錄

### 性能要求
- [ ] 1000+ 事件/小時檢測能力
- [ ] < 10ms 單次檢測延遲
- [ ] 記憶體效率優化

### 單元測試
- [ ] A4 事件檢測測試
- [ ] A5 事件檢測測試
- [ ] D2 事件檢測測試
- [ ] 邊界條件測試
- [ ] 3GPP 標準向量測試

---

## 📚 學術參考

1. 3GPP TS 38.331 V18.5.1 (2025). NR; Radio Resource Control (RRC) protocol specification.
   - Section 5.5.4.5: Event A4 (Neighbour becomes better than threshold)
   - Section 5.5.4.6: Event A5 (PCell becomes worse than threshold1 and neighbour becomes better than threshold2)
   - Section 5.5.4.15a: Event D2 (Distance-based handover trigger)

2. 3GPP TR 38.821 V16.1.0 (2019-12). Solutions for NR to support non-terrestrial networks.

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現