# 📋 Stage 4 重構計劃 A: 核心功能修正

**計劃代號**: STAGE4-REFACTOR-A
**優先級**: P0 - 關鍵 (Critical)
**預估工時**: 4-6 小時
**依賴**: 無
**狀態**: 📝 規劃中

---

## 🎯 重構目標

修正 Stage 4 當前實現中缺失的**關鍵核心功能**，確保符合 `stage4-link-feasibility.md` 文檔的基本要求。

### 核心問題
1. ❌ **缺少鏈路預算距離約束** (200-2000km)
2. ❌ **輸出結構不符合規範** (缺少完整時間序列)
3. ❌ **缺少 `is_connectable` 標記** (每個時間點的可連線狀態)

---

## 📊 問題分析

### 問題 1: 鏈路預算距離約束缺失

**文檔要求** (`stage4-link-feasibility.md:208-213`):
```yaml
鏈路預算約束:
  最小距離: 200km  # 避免多普勒過大和調度複雜性
  最大距離: 2000km # 確保信號強度充足
  地理邊界: NTPU 服務覆蓋區域驗證
```

**當前實現問題**:
```python
# constellation_filter.py - 只有仰角篩選
def filter_by_elevation_threshold(self, satellites, elevation_data):
    for sat_id, sat_data in satellites.items():
        elevation = elevation_data[sat_id]
        if elevation >= threshold:  # ❌ 沒有距離檢查
            filtered_satellites[sat_id] = sat_data
```

**影響**:
- 可能包含距離過近的衛星 (< 200km，多普勒效應過大)
- 可能包含距離過遠的衛星 (> 2000km，信號衰減嚴重)
- 不符合實際通訊鏈路可行性標準

---

### 問題 2: 輸出結構不符合規範

**文檔要求** (`stage4-link-feasibility.md:16-35`):
```python
{
    'starlink': [
        {
            'satellite_id': 'STARLINK-1234',
            'time_series': [  # ← 完整時間序列 (~191 時間點)
                {
                    'timestamp': '2025-09-27T08:00:00Z',
                    'is_connectable': True,
                    'elevation_deg': 15.2,
                    'azimuth_deg': 245.7,
                    'distance_km': 750.2
                },
                # ... 繼續 190+ 時間點
            ]
        }
    ]
}
```

**當前實現問題**:
```python
# stage4_link_feasibility_processor.py:169-205
def _calculate_all_elevations(self, wgs84_data):
    for sat_id, sat_data in wgs84_data.items():
        max_elevation = -90.0
        for point in wgs84_coordinates:
            elevation = calculate_elevation(...)
            max_elevation = max(max_elevation, elevation)  # ❌ 只保留最大值
        elevation_data[sat_id] = max_elevation  # ❌ 丟失時間序列
```

**影響**:
- Stage 5/6 無法進行時間序列信號分析
- 無法驗證「任意時刻維持 10-15 顆可見」目標
- 無法計算服務窗口連續性

---

### 問題 3: 缺少 `is_connectable` 標記

**文檔要求** (`stage4-link-feasibility.md:383-387`):
```python
is_connectable = (
    elevation >= elevation_threshold and
    200 <= distance_km <= 2000
)
```

**當前實現問題**:
- 沒有為每個時間點計算可連線狀態
- 無法區分「幾何可見」vs「實際可連線」
- 後續階段無法正確篩選可用時間點

**影響**:
- Stage 5 可能對不可連線時間點計算信號品質
- Stage 6 無法正確生成 3GPP 事件
- 違反學術標準 (可見性 vs 可連線性概念混淆)

---

## 🛠️ 重構方案

### 任務 A.1: 添加鏈路預算距離檢查

#### 目標檔案
- `src/stages/stage4_link_feasibility/link_budget_analyzer.py` (新建)
- `src/stages/stage4_link_feasibility/constellation_filter.py` (修改)

#### 實現步驟

**步驟 1.1: 創建 LinkBudgetAnalyzer 類**
```python
class LinkBudgetAnalyzer:
    """鏈路預算分析器 - 符合 stage4-link-feasibility.md 規範"""

    # 鏈路預算約束參數
    LINK_BUDGET_CONSTRAINTS = {
        'min_distance_km': 200,   # 最小距離
        'max_distance_km': 2000,  # 最大距離
        'min_elevation_deg': 0,   # 地平線遮擋
    }

    def check_distance_constraint(self, distance_km: float) -> bool:
        """檢查距離是否在有效範圍內"""
        return (self.LINK_BUDGET_CONSTRAINTS['min_distance_km']
                <= distance_km
                <= self.LINK_BUDGET_CONSTRAINTS['max_distance_km'])

    def analyze_link_feasibility(self, elevation_deg: float,
                                 distance_km: float,
                                 constellation: str) -> Dict[str, Any]:
        """綜合分析鏈路可行性"""
        # 獲取星座特定門檻
        elevation_threshold = get_constellation_threshold(constellation)

        # 檢查仰角
        elevation_ok = elevation_deg >= elevation_threshold

        # 檢查距離
        distance_ok = self.check_distance_constraint(distance_km)

        # 判斷可連線性
        is_connectable = elevation_ok and distance_ok

        return {
            'is_connectable': is_connectable,
            'elevation_ok': elevation_ok,
            'distance_ok': distance_ok,
            'elevation_deg': elevation_deg,
            'distance_km': distance_km,
            'elevation_threshold': elevation_threshold
        }
```

**步驟 1.2: 修改 ConstellationFilter 整合距離檢查**
```python
# constellation_filter.py - 修改篩選邏輯
def filter_by_elevation_and_distance(self, satellites: Dict[str, Any],
                                    elevation_data: Dict[str, float],
                                    distance_data: Dict[str, float]) -> Dict[str, Any]:
    """按仰角和距離雙重門檻篩選"""
    filtered_satellites = {}

    for sat_id, sat_data in satellites.items():
        constellation = sat_data.get('constellation', 'unknown').lower()
        threshold = self.get_constellation_threshold(constellation)

        elevation = elevation_data.get(sat_id, -90.0)
        distance = distance_data.get(sat_id, float('inf'))

        # 仰角檢查
        elevation_ok = elevation >= threshold

        # 距離檢查 (新增)
        distance_ok = 200 <= distance <= 2000

        # 綜合判斷
        if elevation_ok and distance_ok:
            filtered_satellites[sat_id] = sat_data
```

---

### 任務 A.2: 修改輸出結構為完整時間序列

#### 目標檔案
- `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py` (修改)

#### 實現步驟

**步驟 2.1: 修改 `_calculate_all_elevations` 為 `_calculate_time_series_metrics`**

```python
def _calculate_time_series_metrics(self, wgs84_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """為所有衛星計算完整時間序列指標"""
    time_series_metrics = {}

    for sat_id, sat_data in wgs84_data.items():
        wgs84_coordinates = sat_data.get('wgs84_coordinates', [])
        constellation = sat_data.get('constellation', 'unknown')

        satellite_time_series = []

        for point in wgs84_coordinates:
            # 提取座標
            lat = point.get('latitude_deg')
            lon = point.get('longitude_deg')
            alt_km = point.get('altitude_m', 0) / 1000.0
            timestamp = point.get('timestamp', '')

            # 計算仰角
            elevation = self.visibility_calculator.calculate_satellite_elevation(
                lat, lon, alt_km
            )

            # 計算距離
            distance_km = self.visibility_calculator.calculate_satellite_distance(
                lat, lon, alt_km
            )

            # 計算方位角 (使用現有方法)
            azimuth = self.visibility_calculator.calculate_azimuth(lat, lon)

            # 獲取星座門檻
            elevation_threshold = self.constellation_filter.get_constellation_threshold(constellation)

            # 判斷可連線性 (仰角 + 距離雙重約束)
            is_connectable = (
                elevation >= elevation_threshold and
                200 <= distance_km <= 2000
            )

            # 構建時間點數據
            time_point = {
                'timestamp': timestamp,
                'latitude_deg': lat,
                'longitude_deg': lon,
                'altitude_km': alt_km,
                'elevation_deg': elevation,
                'azimuth_deg': azimuth,
                'distance_km': distance_km,
                'is_connectable': is_connectable,  # 關鍵標記
                'elevation_threshold': elevation_threshold
            }

            satellite_time_series.append(time_point)

        time_series_metrics[sat_id] = satellite_time_series

    return time_series_metrics
```

**步驟 2.2: 修改 `_build_stage4_output` 使用新結構**

```python
def _build_stage4_output(self, original_data: Dict[str, Any],
                       time_series_metrics: Dict[str, List[Dict[str, Any]]],
                       constellation_result: Dict[str, Any]) -> Dict[str, Any]:
    """構建 Stage 4 標準化輸出 (符合文檔規範)"""

    # 按星座分類
    feasible_satellites_by_constellation = {
        'starlink': [],
        'oneweb': [],
        'other': []
    }

    for sat_id, time_series in time_series_metrics.items():
        # 識別星座
        sat_data = original_data.get(sat_id, {})
        constellation = sat_data.get('constellation', 'unknown').lower()

        if 'starlink' in constellation:
            constellation_key = 'starlink'
        elif 'oneweb' in constellation:
            constellation_key = 'oneweb'
        else:
            constellation_key = 'other'

        # 檢查是否至少有一個時間點可連線
        has_connectable_time = any(point['is_connectable'] for point in time_series)

        if has_connectable_time:
            satellite_entry = {
                'satellite_id': sat_id,
                'name': sat_data.get('name', sat_id),
                'constellation': constellation_key,
                'time_series': time_series,  # 完整時間序列
                'service_window': self._calculate_service_window(time_series)
            }

            feasible_satellites_by_constellation[constellation_key].append(satellite_entry)

    # 構建最終輸出
    stage4_output = {
        'stage': 'stage4_link_feasibility',
        'connectable_satellites': feasible_satellites_by_constellation,
        'feasibility_summary': {
            'total_connectable': sum(len(sats) for sats in feasible_satellites_by_constellation.values()),
            'by_constellation': {
                constellation: len(sats)
                for constellation, sats in feasible_satellites_by_constellation.items()
                if sats  # 只包含非空星座
            }
        },
        'metadata': {
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_input_satellites': len(original_data),
            'link_budget_constraints': {
                'min_distance_km': 200,
                'max_distance_km': 2000
            },
            'constellation_thresholds': self.constellation_filter.CONSTELLATION_THRESHOLDS
        }
    }

    return stage4_output
```

**步驟 2.3: 添加服務窗口計算輔助方法**

```python
def _calculate_service_window(self, time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
    """計算服務窗口摘要"""
    connectable_points = [p for p in time_series if p['is_connectable']]

    if not connectable_points:
        return {
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'time_points_count': 0,
            'max_elevation_deg': 0
        }

    return {
        'start_time': connectable_points[0]['timestamp'],
        'end_time': connectable_points[-1]['timestamp'],
        'duration_minutes': len(connectable_points) * (30 / 60.0),  # 假設30秒間隔
        'time_points_count': len(connectable_points),
        'max_elevation_deg': max(p['elevation_deg'] for p in connectable_points)
    }
```

---

### 任務 A.3: 添加方位角計算

#### 目標檔案
- `src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py` (修改)

#### 實現步驟

```python
def calculate_azimuth(self, sat_lat_deg: float, sat_lon_deg: float) -> float:
    """計算衛星相對於 NTPU 的方位角 (0-360°, 北=0°)"""
    try:
        obs_lat = self.NTPU_COORDINATES['latitude_deg']
        obs_lon = self.NTPU_COORDINATES['longitude_deg']

        # 轉換為弧度
        obs_lat_rad = math.radians(obs_lat)
        obs_lon_rad = math.radians(obs_lon)
        sat_lat_rad = math.radians(sat_lat_deg)
        sat_lon_rad = math.radians(sat_lon_deg)

        # 經度差
        dlon = sat_lon_rad - obs_lon_rad

        # 方位角計算 (球面三角學)
        x = math.sin(dlon) * math.cos(sat_lat_rad)
        y = (math.cos(obs_lat_rad) * math.sin(sat_lat_rad) -
             math.sin(obs_lat_rad) * math.cos(sat_lat_rad) * math.cos(dlon))

        azimuth_rad = math.atan2(x, y)
        azimuth_deg = math.degrees(azimuth_rad)

        # 轉換到 0-360° 範圍
        azimuth_deg = (azimuth_deg + 360) % 360

        return azimuth_deg

    except Exception as e:
        self.logger.error(f"方位角計算失敗: {e}")
        return 0.0
```

---

## 🧪 測試計劃

### 測試 A.1: 鏈路預算距離檢查驗證
```python
# 測試距離約束
def test_link_budget_distance():
    analyzer = LinkBudgetAnalyzer()

    # 測試過近衛星 (< 200km)
    assert not analyzer.check_distance_constraint(150)

    # 測試有效距離
    assert analyzer.check_distance_constraint(500)
    assert analyzer.check_distance_constraint(1500)

    # 測試過遠衛星 (> 2000km)
    assert not analyzer.check_distance_constraint(2500)
```

### 測試 A.2: 時間序列輸出結構驗證
```python
# 測試輸出格式
def test_time_series_output():
    result = processor.execute(stage3_output)

    # 檢查必要字段
    assert 'connectable_satellites' in result
    assert 'starlink' in result['connectable_satellites']

    # 檢查時間序列結構
    starlink_sats = result['connectable_satellites']['starlink']
    if starlink_sats:
        first_sat = starlink_sats[0]
        assert 'time_series' in first_sat
        assert len(first_sat['time_series']) > 0

        # 檢查時間點數據
        first_point = first_sat['time_series'][0]
        assert 'timestamp' in first_point
        assert 'is_connectable' in first_point
        assert 'elevation_deg' in first_point
        assert 'distance_km' in first_point
```

### 測試 A.3: `is_connectable` 邏輯驗證
```python
# 測試可連線性判斷
def test_is_connectable_logic():
    # Starlink 衛星: 仰角 6°, 距離 500km
    result = analyze_link_feasibility(
        elevation_deg=6.0,
        distance_km=500.0,
        constellation='starlink'
    )
    assert result['is_connectable'] == True  # 滿足 5° 門檻和距離範圍

    # Starlink 衛星: 仰角 6°, 距離 2500km
    result = analyze_link_feasibility(
        elevation_deg=6.0,
        distance_km=2500.0,
        constellation='starlink'
    )
    assert result['is_connectable'] == False  # 距離超出範圍

    # Starlink 衛星: 仰角 3°, 距離 500km
    result = analyze_link_feasibility(
        elevation_deg=3.0,
        distance_km=500.0,
        constellation='starlink'
    )
    assert result['is_connectable'] == False  # 仰角不足
```

---

## 📋 驗收標準

### 功能驗收
- [ ] 所有衛星時間點都包含距離檢查 (200-2000km)
- [ ] 輸出結構包含完整 `time_series[]` 數組
- [ ] 每個時間點都有正確的 `is_connectable` 布爾值
- [ ] `is_connectable` 邏輯同時考慮仰角和距離
- [ ] 方位角計算準確 (0-360° 範圍)

### 數據驗收
- [ ] Starlink 可連線衛星數 > 0
- [ ] OneWeb 可連線衛星數 > 0
- [ ] 每顆衛星時間序列點數在 95-220 範圍內
- [ ] `is_connectable=True` 的時間點符合雙重約束

### 性能驗收
- [ ] 處理 9000 顆衛星 < 5 秒
- [ ] 記憶體使用 < 2GB

---

## 📦 交付物

1. **新增檔案**
   - `src/stages/stage4_link_feasibility/link_budget_analyzer.py`

2. **修改檔案**
   - `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`
   - `src/stages/stage4_link_feasibility/constellation_filter.py`
   - `src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py`

3. **測試檔案**
   - `tests/stages/stage4/test_link_budget.py` (新建)
   - `tests/stages/stage4/test_time_series_output.py` (新建)

4. **文檔更新**
   - 更新 `docs/stages/stage4-link-feasibility.md` 實現狀態

---

## 🚀 執行順序

1. **任務 A.1** (2-3小時): 鏈路預算距離檢查
2. **任務 A.2** (1-2小時): 時間序列輸出結構
3. **任務 A.3** (0.5小時): 方位角計算
4. **測試驗證** (1小時): 完整測試和驗收

**總計**: 4-6 小時

---

## ⚠️ 風險與依賴

### 風險
- 時間序列數據量可能導致記憶體壓力 (9000衛星 × 200點 × 數據結構)
- 需要確保 Stage 3 輸出包含完整時間序列數據

### 依賴
- ✅ Stage 3 必須提供完整 WGS84 時間序列
- ✅ 現有 `NTPUVisibilityCalculator` 類可直接使用

### 後續依賴
- 計劃 B (學術標準升級) 依賴本計劃完成
- 計劃 C (動態池規劃) 依賴本計劃的時間序列數據

---

**文檔版本**: v1.0
**創建日期**: 2025-09-30
**負責人**: Orbit Engine Team
**審核狀態**: 待審核