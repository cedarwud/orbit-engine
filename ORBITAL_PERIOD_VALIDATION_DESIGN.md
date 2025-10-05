# 軌道週期完整性驗證設計

**問題**: 如何驗證 Starlink/OneWeb 在各自完整軌道週期內，真的能平均維持目標數量的可見衛星？

**當前驗證的不足**: 只檢查「所有時間點的平均覆蓋率」，未驗證「時間點是否涵蓋完整軌道週期」

---

## 🔍 當前驗證狀態分析

### 現有數據
- **Starlink**: 224 個時間點，平均 10.4 顆，95.5% 覆蓋率 ✅
- **OneWeb**: 190 個時間點，平均 3.3 顆，95.3% 覆蓋率 ✅

### 關鍵問題
1. **時間跨度驗證缺失**: 224 個點是否涵蓋 90-95 分鐘完整軌道週期？
2. **時間間隔均勻性**: 時間點分佈是否均勻（非集中在某段時間）？
3. **軌道週期定義**: 如何準確定義「完整軌道週期」？

---

## 📐 軌道週期理論依據

### Starlink (550km 軌道)
```python
# 軌道週期計算 (開普勒第三定律)
# T = 2π√(a³/μ)
# a = R_earth + h = 6371 + 550 = 6921 km
# μ = 3.986004418e14 m³/s² (地球引力常數)

import math
R_earth = 6371  # km
h_starlink = 550  # km
a = (R_earth + h_starlink) * 1000  # 轉換為 m
mu = 3.986004418e14  # m³/s²

T_starlink = 2 * math.pi * math.sqrt(a**3 / mu)
# T_starlink ≈ 5700 秒 ≈ 95 分鐘
```

### OneWeb (1200km 軌道)
```python
h_oneweb = 1200  # km
a = (R_earth + h_oneweb) * 1000  # m

T_oneweb = 2 * math.pi * math.sqrt(a**3 / mu)
# T_oneweb ≈ 6600 秒 ≈ 110 分鐘
```

### 標準軌道週期
| 星座 | 軌道高度 | 理論週期 | 實測範圍 |
|------|---------|---------|---------|
| **Starlink** | 550 km | 95 分鐘 | 90-95 分鐘 |
| **OneWeb** | 1200 km | 110 分鐘 | 109-115 分鐘 |

---

## ✅ 完整驗證方法設計

### 方法 1: 時間跨度驗證（推薦）

檢查時間點的時間跨度是否涵蓋完整軌道週期：

```python
def validate_orbital_period_coverage(time_points: List[str], constellation: str) -> Dict:
    """驗證時間點是否涵蓋完整軌道週期

    Args:
        time_points: 時間戳列表
        constellation: 'starlink' or 'oneweb'

    Returns:
        {
            'time_span_minutes': float,  # 時間跨度（分鐘）
            'expected_period_minutes': float,  # 預期軌道週期
            'coverage_ratio': float,  # 覆蓋比率（實際/預期）
            'is_complete_period': bool,  # 是否完整週期
            'validation_passed': bool
        }
    """
    # 理論軌道週期
    ORBITAL_PERIODS = {
        'starlink': 95,  # 分鐘
        'oneweb': 110    # 分鐘
    }

    # 解析時間戳
    timestamps = [datetime.fromisoformat(tp) for tp in time_points]
    timestamps.sort()

    # 計算時間跨度
    time_span = timestamps[-1] - timestamps[0]
    time_span_minutes = time_span.total_seconds() / 60

    # 預期週期
    expected_period = ORBITAL_PERIODS[constellation]

    # 覆蓋比率
    coverage_ratio = time_span_minutes / expected_period

    # 驗證標準: 時間跨度 >= 90% 軌道週期
    MIN_COVERAGE_RATIO = 0.9
    is_complete_period = coverage_ratio >= MIN_COVERAGE_RATIO

    return {
        'time_span_minutes': time_span_minutes,
        'expected_period_minutes': expected_period,
        'coverage_ratio': coverage_ratio,
        'is_complete_period': is_complete_period,
        'validation_passed': is_complete_period,
        'message': (
            f"✅ 時間跨度 {time_span_minutes:.1f} 分鐘 >= {expected_period * MIN_COVERAGE_RATIO:.1f} 分鐘"
            if is_complete_period else
            f"❌ 時間跨度不足: {time_span_minutes:.1f} < {expected_period * MIN_COVERAGE_RATIO:.1f} 分鐘"
        )
    }
```

### 方法 2: 時間間隔均勻性驗證

檢查時間點分佈是否均勻（防止集中在某段時間）：

```python
def validate_time_distribution_uniformity(time_points: List[str]) -> Dict:
    """驗證時間點分佈均勻性

    Returns:
        {
            'avg_interval_seconds': float,  # 平均時間間隔
            'max_gap_seconds': float,       # 最大時間間隔
            'std_deviation': float,         # 標準差
            'is_uniform': bool,             # 是否均勻分佈
            'validation_passed': bool
        }
    """
    timestamps = sorted([datetime.fromisoformat(tp) for tp in time_points])

    # 計算所有時間間隔
    intervals = []
    for i in range(1, len(timestamps)):
        delta = (timestamps[i] - timestamps[i-1]).total_seconds()
        intervals.append(delta)

    # 統計指標
    avg_interval = sum(intervals) / len(intervals) if intervals else 0
    max_gap = max(intervals) if intervals else 0

    # 標準差（衡量均勻性）
    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
    std_dev = math.sqrt(variance)

    # 驗證標準: 最大間隔 <= 3 * 平均間隔（允許部分波動）
    MAX_GAP_RATIO = 3.0
    is_uniform = (max_gap <= avg_interval * MAX_GAP_RATIO) if avg_interval > 0 else False

    return {
        'avg_interval_seconds': avg_interval,
        'max_gap_seconds': max_gap,
        'std_deviation': std_dev,
        'is_uniform': is_uniform,
        'validation_passed': is_uniform,
        'message': (
            f"✅ 時間分佈均勻: 最大間隔 {max_gap:.1f}s <= {avg_interval * MAX_GAP_RATIO:.1f}s"
            if is_uniform else
            f"❌ 時間分佈不均: 最大間隔 {max_gap:.1f}s > {avg_interval * MAX_GAP_RATIO:.1f}s"
        )
    }
```

### 方法 3: 衛星可見性連續性驗證

檢查每顆衛星的可見時間窗口是否符合軌道動力學：

```python
def validate_satellite_visibility_continuity(satellite_time_series: List[Dict]) -> Dict:
    """驗證單顆衛星的可見性連續性

    Args:
        satellite_time_series: 單顆衛星的時間序列數據

    Returns:
        {
            'visibility_windows': List[Dict],  # 可見時間窗口列表
            'longest_window_minutes': float,   # 最長可見窗口
            'total_visible_minutes': float,    # 總可見時間
            'is_continuous': bool,             # 是否有連續可見窗口
            'validation_passed': bool
        }
    """
    # 按時間排序
    sorted_series = sorted(satellite_time_series, key=lambda x: x['timestamp'])

    # 識別可見時間窗口
    windows = []
    current_window = None

    for i, point in enumerate(sorted_series):
        is_visible = point.get('visibility_metrics', {}).get('is_connectable', False)
        timestamp = datetime.fromisoformat(point['timestamp'])

        if is_visible:
            if current_window is None:
                # 開始新窗口
                current_window = {
                    'start': timestamp,
                    'end': timestamp,
                    'duration_minutes': 0
                }
            else:
                # 延續當前窗口
                current_window['end'] = timestamp
                current_window['duration_minutes'] = (
                    (current_window['end'] - current_window['start']).total_seconds() / 60
                )
        else:
            if current_window is not None:
                # 結束當前窗口
                windows.append(current_window)
                current_window = None

    # 處理最後一個窗口
    if current_window is not None:
        windows.append(current_window)

    # 統計
    longest_window = max(windows, key=lambda w: w['duration_minutes']) if windows else None
    longest_duration = longest_window['duration_minutes'] if longest_window else 0
    total_visible_time = sum(w['duration_minutes'] for w in windows)

    # LEO 衛星典型可見窗口: 5-15 分鐘
    MIN_WINDOW_MINUTES = 5
    has_continuous_window = longest_duration >= MIN_WINDOW_MINUTES

    return {
        'visibility_windows': windows,
        'longest_window_minutes': longest_duration,
        'total_visible_minutes': total_visible_time,
        'window_count': len(windows),
        'is_continuous': has_continuous_window,
        'validation_passed': has_continuous_window,
        'message': (
            f"✅ 最長可見窗口 {longest_duration:.1f} 分鐘 >= {MIN_WINDOW_MINUTES} 分鐘"
            if has_continuous_window else
            f"❌ 最長可見窗口不足: {longest_duration:.1f} < {MIN_WINDOW_MINUTES} 分鐘"
        )
    }
```

---

## 🎯 建議的驗證流程

### Stage 6 衛星池驗證增強

在現有 `SatellitePoolVerifier.verify_pool_maintenance()` 中新增：

```python
def verify_pool_maintenance_enhanced(self, ...) -> Dict:
    # ... 現有邏輯 ...

    # 🚨 新增: 軌道週期完整性驗證
    all_timestamps = sorted(list(all_timestamps))

    # 驗證 1: 時間跨度覆蓋完整軌道週期
    period_validation = self._validate_orbital_period_coverage(
        all_timestamps, constellation
    )

    # 驗證 2: 時間分佈均勻性
    distribution_validation = self._validate_time_distribution_uniformity(
        all_timestamps
    )

    # 驗證 3: 衛星可見性連續性（抽樣檢查）
    continuity_validations = []
    for satellite in connectable_satellites[:10]:  # 抽查前 10 顆
        continuity = self._validate_satellite_visibility_continuity(
            satellite['time_series']
        )
        continuity_validations.append(continuity)

    # 綜合評估
    enhanced_validation = {
        'orbital_period_coverage': period_validation,
        'time_distribution': distribution_validation,
        'visibility_continuity': {
            'sampled_satellites': len(continuity_validations),
            'continuous_count': sum(1 for v in continuity_validations if v['is_continuous']),
            'avg_longest_window': sum(v['longest_window_minutes'] for v in continuity_validations) / len(continuity_validations)
        },
        'overall_validation_passed': (
            period_validation['validation_passed'] and
            distribution_validation['validation_passed'] and
            sum(1 for v in continuity_validations if v['is_continuous']) >= len(continuity_validations) * 0.8
        )
    }

    result['enhanced_validation'] = enhanced_validation
    return result
```

---

## 📊 預期驗證結果示例

### Starlink 完整驗證
```json
{
  "starlink_pool": {
    "time_points_analyzed": 224,
    "average_visible_count": 10.4,
    "coverage_rate": 0.955,
    "target_met": true,

    "enhanced_validation": {
      "orbital_period_coverage": {
        "time_span_minutes": 92.5,
        "expected_period_minutes": 95,
        "coverage_ratio": 0.974,
        "is_complete_period": true,
        "message": "✅ 時間跨度 92.5 分鐘 >= 85.5 分鐘"
      },
      "time_distribution": {
        "avg_interval_seconds": 24.8,
        "max_gap_seconds": 68.2,
        "is_uniform": true,
        "message": "✅ 時間分佈均勻: 最大間隔 68.2s <= 74.4s"
      },
      "visibility_continuity": {
        "sampled_satellites": 10,
        "continuous_count": 9,
        "avg_longest_window": 8.3
      },
      "overall_validation_passed": true
    }
  }
}
```

### 驗證失敗示例（時間跨度不足）
```json
{
  "enhanced_validation": {
    "orbital_period_coverage": {
      "time_span_minutes": 45.2,
      "expected_period_minutes": 95,
      "coverage_ratio": 0.476,
      "is_complete_period": false,
      "message": "❌ 時間跨度不足: 45.2 < 85.5 分鐘"
    },
    "overall_validation_passed": false
  }
}
```

---

## ✅ 實作優先級

### 立即實作（必要）
1. **軌道週期時間跨度驗證** - 確保數據涵蓋完整週期
2. **更新驗證快照輸出** - 包含增強驗證結果

### 建議實作（提升可信度）
3. **時間分佈均勻性驗證** - 防止數據集中在某段時間
4. **可見性連續性驗證** - 驗證符合軌道動力學

### 文檔補充
5. **更新 Stage 6 文檔** - 說明增強驗證邏輯
6. **更新 final.md** - 補充軌道週期驗證標準

---

## 📝 驗證標準總結

| 驗證項目 | 標準 | 理由 |
|---------|------|------|
| **時間跨度** | ≥ 90% 軌道週期 | 確保涵蓋完整軌道動態 |
| **時間分佈** | 最大間隔 ≤ 3×平均間隔 | 確保時間點均勻分佈 |
| **可見窗口** | 最長窗口 ≥ 5 分鐘 | 符合 LEO 衛星典型可見時間 |
| **池維持率** | ≥ 95% 時間點達標 | 確保連續服務能力 |

**核心原則**: 不僅驗證「平均值達標」，更要驗證「完整軌道週期覆蓋」和「時間分佈合理性」。
