# Stage 6 嚴重設計缺陷報告

**日期**: 2025-10-05
**嚴重性**: 🚨 **CRITICAL P0** - 完全不符合核心需求
**影響範圍**: Stage 6 整體架構

---

## 🚨 問題概述

**實際輸出**: 只有 **4 顆衛星** 涉及 3GPP 事件，114 個事件
**需求目標**:
- Starlink: **10-15 顆**連續可見
- OneWeb: **3-6 顆**連續可見
- 候選池: ~500 顆 Starlink + ~100 顆 OneWeb
- 換手事件: **50+ 場景**

**差距**: **實際只達成需求的 <1%**

---

## 🔍 根本原因分析

### 當前錯誤實現

**文件**: `src/stages/stage6_research_optimization/gpp_event_detector.py`

```python
def detect_all_events(signal_analysis, serving_satellite_id=None):
    # 1. 選擇一顆服務衛星 (58179)
    serving_satellite = self._extract_serving_satellite(...)

    # 2. 提取鄰近衛星 (111 顆)
    neighbor_satellites = self._extract_neighbor_satellites(...)

    # 3. 檢測 A3/A4/A5/D2 事件 (一次性)
    a3_events = self.detect_a3_events(serving_satellite, neighbor_satellites)
    a4_events = self.detect_a4_events(serving_satellite, neighbor_satellites)
    # ...

    return result  # 只檢測一次就結束
```

**問題**:
1. ❌ **只選擇一顆服務衛星** (應該是動態輪替的 10-15 顆)
2. ❌ **只檢測一次** (應該遍歷所有時間點)
3. ❌ **沒有時間維度** (應該模擬 95 分鐘 Starlink 軌道週期)
4. ❌ **沒有動態輪替** (應該模擬衛星進入/離開池)

### 數據流分析

**Stage 5 輸出** ✅ 正確:
```json
{
  "signal_analysis": {
    "49287": {
      "time_series": [
        {"timestamp": "t1", "rsrp": -35.2, "elevation": 25.3, ...},
        {"timestamp": "t2", "rsrp": -36.1, "elevation": 23.8, ...},
        ...  // 35 個時間點
      ],
      "summary": {...}
    },
    "49294": { "time_series": [...] },  // 另一顆衛星
    ...  // 共 112 顆衛星
  },
  "connectable_satellites": {
    "starlink": [70 顆衛星],  // ✅ 正確
    "oneweb": [42 顆衛星]     // ✅ 正確
  }
}
```

**Stage 6 當前處理** ❌ 錯誤:
```python
# 錯誤 1: 只處理 summary，忽略 time_series
serving_sat = signal_analysis["58179"]
serving_rsrp = serving_sat["summary"]["average_rsrp_dbm"]  # 只用平均值

# 錯誤 2: 只檢測一次
for neighbor in neighbors:
    check_a4_event(serving_rsrp, neighbor["summary"]["average_rsrp_dbm"])

# 結果: 只有 4 顆衛星參與事件檢測
```

**Stage 6 應有處理** ✅ 正確:
```python
# 正確 1: 遍歷所有時間點
all_time_points = collect_all_timestamps_from_112_satellites()
# 結果: 224 個 Starlink 時間點 + 190 個 OneWeb 時間點

# 正確 2: 每個時間點檢測
for timestamp in all_time_points:
    # 找出該時刻可見的衛星
    visible_sats = get_visible_satellites_at(timestamp)
    # 應有 10-15 顆 Starlink 或 3-6 顆 OneWeb

    # 選擇服務衛星 (可以輪替或基於策略)
    serving_sat = select_serving_satellite(visible_sats)

    # 檢測該時刻的事件
    neighbors = visible_sats - serving_sat
    detect_events_at_timestamp(serving_sat, neighbors, timestamp)

# 結果: 應有數千個事件 (每個時間點可能產生多個事件)
```

---

## 📊 實際 vs 預期對比

| 指標 | 預期 | 實際 | 差距 |
|------|------|------|------|
| **時間點數** | 414 個 (224+190) | 1 個 | **-99.8%** |
| **參與衛星** | 112 顆 | 4 顆 | **-96.4%** |
| **事件數量** | 50+ 場景 × 414 時間點 ≈ **20,000+** | 114 | **-99.4%** |
| **動態池模擬** | ✅ 必須 | ❌ 完全沒有 | **0%** |
| **符合需求** | 100% | **<1%** | **P0 級別缺陷** |

---

## 🎯 核心需求重申 (來自 docs/final.md)

### 動態衛星池核心概念

> **定義**: 通過數百顆衛星的時空錯置軌道運行，確保NTPU上空**任意時刻**都維持指定數量衛星可見的動態覆蓋系統。

**時空錯置原理**:
```
時間軸示意（Starlink 為例）:

t=0分  → 可見：衛星 A1, A2, B1, B2, C1, C2, D1, D2, E1, E2, F1  (11顆)
          候選池其餘 489 顆：不可見（在地平線下或距離過遠）

t=5分  → 可見：衛星 A2, B1, B2, C1, C2, D1, D2, E1, E2, F1, F2  (11顆)
          A1 離開，F2 進入（動態輪替）

t=10分 → 可見：衛星 B1, B2, C1, C2, D1, D2, E1, E2, F1, F2, G1, G2  (12顆)
          A2 離開，G1, G2 進入

... 以此類推，整個軌道週期內 500 顆候選協同輪替，維持 10-15 顆可見
```

### Stage 6 應有職責

**從 docs/stages/stage6-research-optimization.md**:

1. **3GPP NTN 事件檢測** (當前實作)
   - ❌ 但只做了一次，沒有時間維度

2. **動態衛星池驗證** (當前實作)
   - ✅ 有驗證平均可見數 (10.4 顆 Starlink, 3.3 顆 OneWeb)
   - ❌ 但沒有輸出每個時間點的可見衛星列表

3. **換手決策評估** (當前實作)
   - ❌ 只評估了一次，沒有模擬動態換手場景

---

## 🛠️ 必要修正方案

### 修正 1: 重新設計 detect_all_events()

**新架構**:
```python
def detect_all_events_across_time(
    self,
    signal_analysis: Dict[str, Any],
    connectable_satellites: Dict[str, List]
) -> Dict[str, Any]:
    """遍歷所有時間點檢測 3GPP 事件

    新增需求:
    - 必須處理 time_series，不能只用 summary
    - 必須遍歷所有時間點
    - 必須輸出每個時間點的可見衛星和事件
    """

    # Step 1: 收集所有時間點
    all_timestamps = self._collect_all_timestamps(signal_analysis)
    # 應得到 ~414 個時間點 (224 Starlink + 190 OneWeb)

    all_events = {
        'a3_events': [],
        'a4_events': [],
        'a5_events': [],
        'd2_events': [],
        'time_series_events': []  # 新增: 每個時間點的事件
    }

    # Step 2: 遍歷每個時間點
    for timestamp in all_timestamps:
        # 找出該時刻可見的衛星
        visible_satellites = self._get_visible_satellites_at(
            signal_analysis,
            timestamp
        )

        if len(visible_satellites) < 2:
            continue  # 至少需要 2 顆衛星才能檢測事件

        # 選擇服務衛星 (可以是信號最強、或輪替策略)
        serving_sat = self._select_serving_satellite(visible_satellites)
        neighbors = [s for s in visible_satellites if s != serving_sat]

        # 檢測該時刻的事件
        timestamp_events = self._detect_events_at_timestamp(
            serving_sat,
            neighbors,
            timestamp
        )

        # 記錄該時刻的事件和池狀態
        all_events['time_series_events'].append({
            'timestamp': timestamp,
            'visible_satellites': [s['satellite_id'] for s in visible_satellites],
            'serving_satellite': serving_sat['satellite_id'],
            'events': timestamp_events
        })

        # 累加到總事件列表
        all_events['a3_events'].extend(timestamp_events['a3'])
        all_events['a4_events'].extend(timestamp_events['a4'])
        all_events['a5_events'].extend(timestamp_events['a5'])
        all_events['d2_events'].extend(timestamp_events['d2'])

    return all_events
```

### 修正 2: 新增時間點數據提取

```python
def _collect_all_timestamps(self, signal_analysis: Dict) -> List[str]:
    """從所有衛星的 time_series 收集所有時間戳"""
    all_timestamps = set()

    for sat_id, sat_data in signal_analysis.items():
        time_series = sat_data.get('time_series', [])
        for point in time_series:
            all_timestamps.add(point['timestamp'])

    return sorted(list(all_timestamps))

def _get_visible_satellites_at(
    self,
    signal_analysis: Dict,
    timestamp: str
) -> List[Dict]:
    """獲取特定時間點可見的衛星"""
    visible = []

    for sat_id, sat_data in signal_analysis.items():
        time_series = sat_data.get('time_series', [])

        # 找到該時間點的數據
        for point in time_series:
            if point['timestamp'] == timestamp:
                # 檢查是否可見 (elevation > 0, is_connectable = True)
                if point.get('is_connectable', False):
                    visible.append({
                        'satellite_id': sat_id,
                        'timestamp': timestamp,
                        'rsrp': point['rsrp_dbm'],
                        'elevation': point['elevation_deg'],
                        'distance': point['distance_km'],
                        # ... 其他需要的欄位
                    })
                break

    return visible
```

### 修正 3: 驗證框架需加強

**當前驗證** (錯誤通過):
```python
# stage6_validation_framework.py
def validate_event_count(self, data):
    event_count = data.get('total_events', 0)
    if event_count > 0:  # ❌ 只檢查 > 0
        return True
```

**應有驗證**:
```python
def validate_event_count(self, data):
    event_count = data.get('total_events', 0)
    min_expected = 50  # 來自 docs/final.md

    if event_count < min_expected:
        raise ValidationError(
            f"事件數量不足: {event_count} < {min_expected}\n"
            f"需求: 50+ 換手場景 (docs/final.md Line 175)\n"
            f"請檢查是否遍歷所有時間點"
        )
    return True

def validate_satellite_coverage(self, data):
    """驗證是否有足夠的衛星參與"""
    participating_sats = set()

    for event_type in ['a3_events', 'a4_events', 'd2_events']:
        for event in data.get(event_type, []):
            participating_sats.add(event.get('serving_satellite'))
            participating_sats.add(event.get('neighbor_satellite'))

    min_expected = 20  # 至少應有 20 顆衛星參與
    if len(participating_sats) < min_expected:
        raise ValidationError(
            f"參與衛星數不足: {len(participating_sats)} < {min_expected}\n"
            f"Stage 5 輸出了 112 顆衛星，但只有 {len(participating_sats)} 顆參與事件檢測\n"
            f"請檢查事件檢測邏輯是否遍歷所有衛星"
        )
```

---

## ⏱️ 預期修正工作量

| 任務 | 預估時間 | 優先級 |
|------|---------|--------|
| 重新設計 detect_all_events() | 2-3 小時 | **P0** |
| 實作 time_series 處理邏輯 | 1-2 小時 | **P0** |
| 新增時間點數據提取 | 1 小時 | **P0** |
| 加強驗證框架 | 1 小時 | **P0** |
| 測試與驗證 | 2 小時 | **P0** |
| 文檔更新 | 1 小時 | P1 |
| **總計** | **8-10 小時** | **P0** |

---

## 🎯 成功標準

修正完成後，Stage 6 應輸出：

1. **時間序列事件**:
   - ✅ 414 個時間點的完整記錄
   - ✅ 每個時間點標註可見衛星 (10-15 顆或 3-6 顆)

2. **事件統計**:
   - ✅ 至少 50+ 換手場景
   - ✅ 預期 5,000-20,000 個總事件 (取決於門檻設定)
   - ✅ A3/A4/A5/D2 各類事件均有合理分佈

3. **衛星覆蓋**:
   - ✅ 112 顆衛星中至少 80% 參與事件檢測
   - ✅ 動態池輪替清晰可見

4. **學術標準**:
   - ✅ 所有事件符合 3GPP TS 38.331 v18.5.1
   - ✅ 時間序列分析符合真實衛星軌道動力學

---

## 📝 建議

### 立即行動 (P0)
1. **暫停當前驗證框架** - 當前的「✅ 通過」是錯誤的
2. **重新設計 Stage 6 事件檢測** - 按上述方案實作
3. **加強驗證標準** - 必須檢查事件數量、參與衛星數、時間點數

### 中期改進 (P1)
4. **文檔同步** - 更新 Stage 6 文檔說明時間序列處理
5. **性能優化** - 處理 414 時間點可能需要優化

### 長期規劃 (P2)
6. **動態換手策略** - 實作不同的服務衛星選擇策略
7. **池優化算法** - 基於事件檢測結果優化衛星池

---

**總結**: 當前 Stage 6 實現完全不符合核心需求，驗證框架失效，必須立即修正。
