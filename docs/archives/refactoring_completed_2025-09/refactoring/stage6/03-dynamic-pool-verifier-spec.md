# 動態衛星池驗證器規格 - Stage 6 核心組件

**檔案**: `src/stages/stage6_research_optimization/satellite_pool_verifier.py`
**依據**: `docs/stages/stage6-research-optimization.md` Line 97-102, 266-437
**目標**: Starlink 10-15顆, OneWeb 3-6顆池維護驗證

---

## 🎯 核心職責

驗證動態衛星池規劃是否達成「任意時刻維持目標數量可見」的需求：
1. **時間序列遍歷**: 遍歷所有時間點，計算每個時刻的可見衛星數
2. **覆蓋率統計**: 計算目標達成率 (> 95%)
3. **空窗期分析**: 識別覆蓋空隙和持續時間
4. **時空錯置驗證**: 驗證輪替機制有效性

---

## 🚨 關鍵概念澄清

### ❌ **錯誤的池驗證方法**
```python
# 錯誤: 只計算候選衛星總數
connectable_satellites = stage4_result.data['connectable_satellites']
starlink_count = len(connectable_satellites['starlink'])  # 2000 顆候選總數，錯誤！
```

### ✅ **正確的池驗證方法**
```python
# 正確: 遍歷每個時間點，計算該時刻實際可見衛星數
def verify_pool_maintenance_correct(stage4_result):
    """
    正確的動態池驗證方法

    connectable_satellites 包含完整時間序列，結構如下:
    {
        'starlink': [
            {
                'satellite_id': 'STARLINK-1234',
                'time_series': [  # ← 完整時間序列，非單一時間點
                    {'timestamp': '...', 'is_connectable': True, ...},
                    {'timestamp': '...', 'is_connectable': False, ...},
                    ...
                ]
            },
            ...
        ]
    }
    """
    connectable_satellites = stage4_result.data['connectable_satellites']

    # 1. 收集所有時間戳
    all_timestamps = set()
    for sat in connectable_satellites['starlink']:
        for tp in sat['time_series']:
            all_timestamps.add(tp['timestamp'])

    # 2. 逐時間點驗證
    coverage_stats = []
    for timestamp in sorted(all_timestamps):
        visible_count = 0
        for sat in connectable_satellites['starlink']:
            for tp in sat['time_series']:
                if tp['timestamp'] == timestamp and tp['is_connectable']:
                    visible_count += 1
                    break

        coverage_stats.append({
            'timestamp': timestamp,
            'visible_count': visible_count,
            'target_met': 10 <= visible_count <= 15
        })

    return coverage_stats
```

---

## 🏗️ 類別設計

```python
class SatellitePoolVerifier:
    """動態衛星池驗證器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化驗證器

        Args:
            config: 配置參數
                - starlink_pool_target: {'min': 10, 'max': 15}
                - oneweb_pool_target: {'min': 3, 'max': 6}
                - coverage_threshold: 0.95 (95% 時間達標)
        """
        self.config = self._load_config(config)
        self.logger = logging.getLogger(__name__)

        # 驗證統計
        self.verification_stats = {
            'starlink': {
                'total_time_points': 0,
                'target_met_count': 0,
                'coverage_rate': 0.0,
                'gap_periods': []
            },
            'oneweb': {
                'total_time_points': 0,
                'target_met_count': 0,
                'coverage_rate': 0.0,
                'gap_periods': []
            }
        }

    def verify_all_pools(
        self,
        connectable_satellites: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """驗證所有星座的衛星池

        Args:
            connectable_satellites: Stage 4 的可連線衛星數據
                {
                    'starlink': [衛星列表],
                    'oneweb': [衛星列表]
                }

        Returns:
            {
                'starlink_pool': {...},
                'oneweb_pool': {...},
                'time_space_offset_optimization': {...},
                'overall_verification': {...}
            }
        """
        pass

    def verify_pool_maintenance(
        self,
        connectable_satellites: List[Dict[str, Any]],
        constellation: str,
        target_min: int,
        target_max: int
    ) -> Dict[str, Any]:
        """驗證動態衛星池是否達成「任意時刻維持目標數量可見」的需求

        Args:
            connectable_satellites: 可連線衛星列表 (含完整時間序列)
            constellation: 星座名稱 ('starlink' 或 'oneweb')
            target_min: 目標最小可見數
            target_max: 目標最大可見數

        Returns:
            {
                'candidate_satellites_total': int,      # 候選衛星總數
                'time_points_analyzed': int,            # 分析的時間點數
                'coverage_rate': float,                 # 覆蓋率 (0-1)
                'target_met': bool,                     # 是否達標 (>95%)
                'coverage_gaps': List[Dict],            # 覆蓋空隙列表
                'average_visible_count': float,         # 平均可見衛星數
                'min_visible_count': int,               # 最少可見數
                'max_visible_count': int,               # 最多可見數
                'continuous_coverage_hours': float      # 連續覆蓋小時數
            }
        """
        # 1. 收集所有時間點
        all_timestamps = set()
        for satellite in connectable_satellites:
            for time_point in satellite['time_series']:
                all_timestamps.add(time_point['timestamp'])

        # 2. 對每個時間點計算可見衛星數
        time_coverage_check = []
        for timestamp in sorted(all_timestamps):
            visible_count = 0

            # 檢查該時刻有多少顆衛星 is_connectable=True
            for satellite in connectable_satellites:
                time_point = next(
                    (tp for tp in satellite['time_series'] if tp['timestamp'] == timestamp),
                    None
                )
                if time_point and time_point.get('is_connectable', False):
                    visible_count += 1

            time_coverage_check.append({
                'timestamp': timestamp,
                'visible_count': visible_count,
                'target_met': target_min <= visible_count <= target_max
            })

        # 3. 計算覆蓋率
        met_count = sum(1 for check in time_coverage_check if check['target_met'])
        coverage_rate = met_count / len(time_coverage_check) if time_coverage_check else 0.0

        # 4. 識別覆蓋空隙
        coverage_gaps = self._identify_coverage_gaps(time_coverage_check, target_min, target_max)

        # 5. 統計指標
        visible_counts = [c['visible_count'] for c in time_coverage_check]
        average_visible = sum(visible_counts) / len(visible_counts) if visible_counts else 0.0
        min_visible = min(visible_counts) if visible_counts else 0
        max_visible = max(visible_counts) if visible_counts else 0

        # 6. 計算連續覆蓋時間
        continuous_hours = self._calculate_continuous_coverage(time_coverage_check)

        return {
            'candidate_satellites_total': len(connectable_satellites),
            'time_points_analyzed': len(time_coverage_check),
            'coverage_rate': coverage_rate,
            'target_met': coverage_rate >= 0.95,  # 95%+ 覆蓋率要求
            'coverage_gaps': coverage_gaps,
            'coverage_gaps_count': len(coverage_gaps),
            'average_visible_count': average_visible,
            'min_visible_count': min_visible,
            'max_visible_count': max_visible,
            'continuous_coverage_hours': continuous_hours
        }

    def _identify_coverage_gaps(
        self,
        time_coverage_check: List[Dict[str, Any]],
        target_min: int,
        target_max: int
    ) -> List[Dict[str, Any]]:
        """識別覆蓋空隙

        Args:
            time_coverage_check: 時間點覆蓋檢查結果
            target_min: 目標最小值
            target_max: 目標最大值

        Returns:
            覆蓋空隙列表，每個空隙包含:
            {
                'start_timestamp': str,
                'end_timestamp': str,
                'duration_minutes': float,
                'min_visible_count': int,
                'severity': 'critical' | 'warning' | 'minor'
            }
        """
        gaps = []
        in_gap = False
        gap_start = None
        gap_min_visible = float('inf')

        for i, check in enumerate(time_coverage_check):
            if not check['target_met']:
                if not in_gap:
                    # 開始新的空隙
                    in_gap = True
                    gap_start = check['timestamp']
                    gap_min_visible = check['visible_count']
                else:
                    gap_min_visible = min(gap_min_visible, check['visible_count'])
            else:
                if in_gap:
                    # 結束空隙
                    gap_end = time_coverage_check[i - 1]['timestamp']
                    duration_minutes = self._calculate_duration_minutes(gap_start, gap_end)

                    # 評估嚴重程度
                    severity = self._assess_gap_severity(
                        gap_min_visible, target_min, duration_minutes
                    )

                    gaps.append({
                        'start_timestamp': gap_start,
                        'end_timestamp': gap_end,
                        'duration_minutes': duration_minutes,
                        'min_visible_count': gap_min_visible,
                        'severity': severity
                    })

                    in_gap = False
                    gap_min_visible = float('inf')

        # 處理最後一個未結束的空隙
        if in_gap:
            gap_end = time_coverage_check[-1]['timestamp']
            duration_minutes = self._calculate_duration_minutes(gap_start, gap_end)
            severity = self._assess_gap_severity(gap_min_visible, target_min, duration_minutes)

            gaps.append({
                'start_timestamp': gap_start,
                'end_timestamp': gap_end,
                'duration_minutes': duration_minutes,
                'min_visible_count': gap_min_visible,
                'severity': severity
            })

        return gaps

    def _calculate_continuous_coverage(
        self,
        time_coverage_check: List[Dict[str, Any]]
    ) -> float:
        """計算連續覆蓋時間 (小時)"""
        if not time_coverage_check:
            return 0.0

        # 找到最長的連續達標時間段
        max_continuous_count = 0
        current_continuous_count = 0

        for check in time_coverage_check:
            if check['target_met']:
                current_continuous_count += 1
                max_continuous_count = max(max_continuous_count, current_continuous_count)
            else:
                current_continuous_count = 0

        # 假設每個時間點間隔為觀測窗口總時長 / 時間點數
        # 通常是 2小時 / 時間點數
        if len(time_coverage_check) > 1:
            time_step_hours = 2.0 / len(time_coverage_check)
            continuous_hours = max_continuous_count * time_step_hours
        else:
            continuous_hours = 0.0

        return continuous_hours

    def _calculate_duration_minutes(
        self,
        start_timestamp: str,
        end_timestamp: str
    ) -> float:
        """計算時間間隔 (分鐘)"""
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))

        duration_seconds = (end_dt - start_dt).total_seconds()
        return duration_seconds / 60.0

    def _assess_gap_severity(
        self,
        visible_count: int,
        target_min: int,
        duration_minutes: float
    ) -> str:
        """評估覆蓋空隙嚴重程度

        Returns:
            'critical': 完全無覆蓋 (0顆) 或長時間 (>10分鐘)
            'warning': 嚴重不足 (< target_min/2) 或中等時間 (5-10分鐘)
            'minor': 輕微不足
        """
        if visible_count == 0 or duration_minutes > 10:
            return 'critical'
        elif visible_count < target_min / 2 or duration_minutes > 5:
            return 'warning'
        else:
            return 'minor'

    def analyze_time_space_offset_optimization(
        self,
        starlink_verification: Dict[str, Any],
        oneweb_verification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析時空錯置優化效果

        Args:
            starlink_verification: Starlink 池驗證結果
            oneweb_verification: OneWeb 池驗證結果

        Returns:
            {
                'optimal_scheduling': bool,
                'coverage_efficiency': float,
                'handover_frequency_per_hour': float,
                'spatial_diversity': float,
                'temporal_overlap': float
            }
        """
        pass

    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """載入並合併配置參數"""
        default_config = {
            'starlink_pool_target': {'min': 10, 'max': 15},
            'oneweb_pool_target': {'min': 3, 'max': 6},
            'coverage_threshold': 0.95,
            'gap_severity_thresholds': {
                'critical_duration_minutes': 10,
                'warning_duration_minutes': 5,
                'critical_visible_ratio': 0.0,
                'warning_visible_ratio': 0.5
            }
        }

        if config:
            default_config.update(config)

        return default_config
```

---

## 📊 輸出數據格式

### 完整池驗證結果
```python
{
    'starlink_pool': {
        'target_range': {'min': 10, 'max': 15},
        'candidate_satellites_total': 2123,     # 候選衛星總數
        'time_points_analyzed': 120,            # 分析的時間點數 (2小時窗口)
        'coverage_rate': 0.975,                 # 97.5% 覆蓋率
        'average_visible_count': 12.3,          # 平均12.3顆可見
        'min_visible_count': 8,                 # 最少8顆
        'max_visible_count': 16,                # 最多16顆
        'target_met': True,                     # ✅ 達標 (>95%)
        'coverage_gaps_count': 3,               # 3個覆蓋空隙
        'coverage_gaps': [
            {
                'start_timestamp': '2025-09-27T03:15:00+00:00',
                'end_timestamp': '2025-09-27T03:17:30+00:00',
                'duration_minutes': 2.5,
                'min_visible_count': 8,
                'severity': 'minor'
            },
            # ... 更多空隙
        ],
        'continuous_coverage_hours': 23.8       # 連續覆蓋23.8小時
    },
    'oneweb_pool': {
        'target_range': {'min': 3, 'max': 6},
        'candidate_satellites_total': 651,
        'time_points_analyzed': 120,
        'coverage_rate': 1.0,                   # 100% 覆蓋率
        'average_visible_count': 4.2,
        'min_visible_count': 3,
        'max_visible_count': 6,
        'target_met': True,                     # ✅ 達標
        'coverage_gaps_count': 0,               # 無空隙
        'coverage_gaps': [],
        'continuous_coverage_hours': 24.0       # 連續覆蓋24小時
    },
    'time_space_offset_optimization': {
        'optimal_scheduling': True,
        'coverage_efficiency': 0.97,
        'handover_frequency_per_hour': 8.2,
        'spatial_diversity': 0.85,
        'temporal_overlap': 0.92
    }
}
```

---

## 🔍 驗證流程圖

```
┌─────────────────────────────────────────────────────────┐
│  Stage 4: connectable_satellites                        │
│  {                                                      │
│    'starlink': [                                        │
│      {                                                  │
│        'satellite_id': 'STARLINK-1234',                │
│        'time_series': [                                │
│          {'timestamp': 't1', 'is_connectable': True},  │
│          {'timestamp': 't2', 'is_connectable': False}, │
│          ...                                           │
│        ]                                               │
│      }                                                 │
│    ]                                                   │
│  }                                                     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 1: 收集所有時間戳                                  │
│  all_timestamps = {t1, t2, t3, ..., t120}              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: 逐時間點計算可見衛星數                          │
│  for each timestamp:                                    │
│    count = 0                                           │
│    for each satellite:                                 │
│      if satellite.is_connectable(timestamp):           │
│        count += 1                                      │
│    coverage_check[timestamp] = {                       │
│      'visible_count': count,                           │
│      'target_met': 10 <= count <= 15                   │
│    }                                                   │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: 計算覆蓋率                                      │
│  met_count = sum(target_met for all timestamps)        │
│  coverage_rate = met_count / total_timestamps          │
│  target_met = coverage_rate >= 0.95                    │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 4: 識別覆蓋空隙                                    │
│  gaps = []                                             │
│  for each continuous period where target_met=False:    │
│    gaps.append({                                       │
│      'start', 'end', 'duration', 'severity'           │
│    })                                                  │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 5: 輸出驗證結果                                    │
│  {                                                     │
│    'coverage_rate': 0.975,                             │
│    'target_met': True,                                 │
│    'coverage_gaps': [...],                             │
│    'average_visible_count': 12.3                       │
│  }                                                     │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ 實現檢查清單

### 功能完整性
- [ ] 時間序列遍歷邏輯
- [ ] 逐時間點可見數計算
- [ ] 覆蓋率統計
- [ ] 覆蓋空隙識別
- [ ] 嚴重程度評估
- [ ] 連續覆蓋時間計算
- [ ] 時空錯置效果分析

### 數據正確性
- [ ] 正確解析 Stage 4 時間序列數據
- [ ] 正確處理 is_connectable 標記
- [ ] 時間戳格式處理
- [ ] 覆蓋率計算精度

### 研究目標達成
- [ ] Starlink 10-15顆驗證
- [ ] OneWeb 3-6顆驗證
- [ ] > 95% 覆蓋率要求
- [ ] 空窗期詳細分析

### 錯誤處理
- [ ] 空數據處理
- [ ] 時間戳異常處理
- [ ] 數據格式錯誤處理

### 單元測試
- [ ] 池維護驗證測試
- [ ] 覆蓋空隙識別測試
- [ ] 時空錯置分析測試
- [ ] 邊界條件測試

---

## 📚 學術依據

**時空錯置池規劃原理** (academic_standards_clarification.md Line 61-82):
```
Stage 4: 鏈路可行性評估與衛星池分析
3. 動態衛星池狀態分析：
   - Starlink: 維持10-15顆持續可見
   - OneWeb: 維持3-6顆持續可見
4. 時空錯置池規劃驗證
```

**研究目標對齊** (docs/stages/stage6-research-optimization.md Line 540-554):
```
| 需求 | 數據來源 | Stage 6 驗證 |
| 動態衛星池 | Stage 4 池規劃 | ✅ 時空錯置輪替機制驗證 |
| 池維持目標 | Stage 4/6 統計 | ✅ Starlink 10-15顆, OneWeb 3-6顆 |
```

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現