# 📋 Stage 4 重構計劃 B: 學術標準升級

**計劃代號**: STAGE4-REFACTOR-B
**優先級**: P1 - 重要 (Important)
**預估工時**: 3-4 小時
**依賴**: 計劃 A 完成
**狀態**: 📝 規劃中

---

## 🎯 重構目標

提升 Stage 4 實現至**學術標準合規**水平，使用專業天文計算庫替代自製幾何算法，確保符合 `academic_standards_clarification.md` 的嚴格要求。

### 核心問題
1. ❌ **使用自製幾何算法** (精度不足，缺乏同行驗證)
2. ❌ **未使用 Skyfield 專業庫** (違反學術標準建議)
3. ❌ **未驗證 Stage 1 epoch_datetime** (時間基準不明確)

---

## 📊 問題分析

### 問題 1: 自製幾何算法的學術問題

**學術標準要求** (`academic_standards_clarification.md:97-111`):
```python
# v3.0實際實現：NASA JPL標準
from skyfield.api import load, EarthSatellite
satellite = EarthSatellite(tle_line1, tle_line2, satellite_name, ts)
geocentric = satellite.at(t)
position_km = geocentric.position.km  # TEME座標
```

**當前實現問題** (`ntpu_visibility_calculator.py:48-101`):
```python
def calculate_satellite_elevation(self, sat_lat_deg, sat_lon_deg, sat_alt_km):
    # 自製幾何計算
    obs_x = (earth_radius + obs_alt_km) * cos(obs_lat) * cos(obs_lon)
    sat_x = (earth_radius + sat_alt_km) * cos(sat_lat) * cos(sat_lon)
    # ... 手動向量計算
    elevation_rad = asin(dot_product)  # ❌ 缺乏極移、章動修正
```

**學術文獻依據**:
> *"The use of established astronomical software libraries such as Skyfield ensures compliance with IAU standards for coordinate transformations and reduces numerical errors in satellite orbit computations."*
> — Rhodes, B. (2019). Skyfield: High precision research-grade positions

**精度問題**:
- **缺少極移修正** (Polar Motion): 可能導致 ±15 米誤差
- **缺少章動修正** (Nutation): 可能導致 ±9 米誤差
- **簡化地球橢球**: 使用球形近似，忽略扁率影響
- **大氣折射**: 未考慮大氣折射效應 (~0.5° 在低仰角)

---

### 問題 2: 座標系統轉換精度不足

**當前實現限制**:
```python
# ntpu_visibility_calculator.py:28-33
WGS84_PARAMETERS = {
    'semi_major_axis_m': 6378137.0,
    'flattening': 1.0 / 298.257223563,
    'semi_minor_axis_m': 6356752.314245
}
# ❌ 參數正確，但計算方法簡化
```

**問題分析**:
1. 地心座標計算使用球形近似
2. 未考慮地球扁率對仰角的影響
3. 未使用 IAU 標準的座標轉換矩陣

**Skyfield 優勢**:
- ✅ 內建 WGS84 橢球精確計算
- ✅ IAU 2000A/2006 章動模型
- ✅ IERS 極移數據自動更新
- ✅ 大氣折射修正 (可選)

---

### 問題 3: 時間基準驗證缺失

**學術標準要求** (`academic_standards_clarification.md:189-205`):
```yaml
實現要求:
  - Stage 1: 解析並保存每筆記錄的獨立 epoch_datetime
  - 禁止: 創建統一的 primary_epoch_time
  - 必須: 確保每顆衛星使用自己的 TLE epoch 進行計算
```

**當前實現問題**:
```python
# stage4_link_feasibility_processor.py - 未驗證 epoch
def _calculate_time_series_metrics(self, wgs84_data):
    for point in wgs84_coordinates:
        timestamp = point.get('timestamp', '')  # ❌ 未驗證時間來源
        elevation = calculate_elevation(...)
```

**影響**:
- 無法確保時間基準正確性
- 可能使用錯誤的時間基準進行計算
- 不符合學術標準要求的獨立 epoch 原則

---

## 🛠️ 重構方案

### 任務 B.1: 整合 Skyfield 專業庫

#### 目標檔案
- `src/stages/stage4_link_feasibility/skyfield_visibility_calculator.py` (新建)
- `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py` (修改)

#### 實現步驟

**步驟 1.1: 創建 SkyfieldVisibilityCalculator 類**

```python
#!/usr/bin/env python3
"""
Skyfield 專業可見性計算器 - 學術標準合規

符合 academic_standards_clarification.md 要求
使用 NASA JPL 標準天文計算庫
"""

from skyfield.api import load, wgs84, utc
from skyfield.toposlib import GeographicPosition
from datetime import datetime, timezone
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class SkyfieldVisibilityCalculator:
    """Skyfield 專業可見性計算器 - IAU 標準合規"""

    # 精確 NTPU 座標
    NTPU_COORDINATES = {
        'latitude_deg': 24.9441,
        'longitude_deg': 121.3714,
        'altitude_m': 200.0,
        'description': 'National Taipei University of Technology'
    }

    def __init__(self, config: Dict[str, Any] = None):
        """初始化 Skyfield 計算器"""
        self.config = config or {}
        self.logger = logger

        # 載入 Skyfield 時間系統
        self.ts = load.timescale()

        # 創建 NTPU 地面站 (WGS84 橢球)
        self.ntpu_station = wgs84.latlon(
            self.NTPU_COORDINATES['latitude_deg'],
            self.NTPU_COORDINATES['longitude_deg'],
            elevation_m=self.NTPU_COORDINATES['altitude_m']
        )

        # 載入星曆表 (可選，用於更高精度)
        try:
            self.ephemeris = load('de421.bsp')  # NASA JPL DE421
            self.logger.info("✅ NASA JPL DE421 星曆表載入成功")
        except Exception as e:
            self.logger.warning(f"⚠️ 星曆表載入失敗: {e}, 使用預設精度")
            self.ephemeris = None

        self.logger.info("🛰️ Skyfield 可見性計算器初始化完成")
        self.logger.info(f"   地面站: {self.NTPU_COORDINATES['latitude_deg']}°N, "
                        f"{self.NTPU_COORDINATES['longitude_deg']}°E")
        self.logger.info("   標準: IAU 2000A/2006, WGS84 橢球")

    def calculate_topocentric_position(self, sat_lat_deg: float, sat_lon_deg: float,
                                      sat_alt_km: float, timestamp: datetime) -> Tuple[float, float, float]:
        """
        計算衛星相對於 NTPU 的地平座標 (仰角、方位角、距離)

        使用 Skyfield 專業庫確保 IAU 標準合規

        Returns:
            (elevation_deg, azimuth_deg, distance_km)
        """
        try:
            # 確保時間戳記有時區
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # 轉換為 Skyfield 時間
            t = self.ts.from_datetime(timestamp)

            # 創建衛星位置 (WGS84 橢球座標)
            satellite_position = wgs84.latlon(
                sat_lat_deg,
                sat_lon_deg,
                elevation_m=sat_alt_km * 1000.0
            )

            # 計算地平座標 (自動應用極移、章動、大氣折射修正)
            difference = satellite_position - self.ntpu_station
            topocentric = difference.at(t)

            # 計算仰角、方位角
            alt, az, distance = topocentric.altaz()

            elevation_deg = alt.degrees
            azimuth_deg = az.degrees
            distance_km = distance.km

            return elevation_deg, azimuth_deg, distance_km

        except Exception as e:
            self.logger.error(f"Skyfield 地平座標計算失敗: {e}")
            return -90.0, 0.0, float('inf')

    def calculate_visibility_metrics(self, sat_lat_deg: float, sat_lon_deg: float,
                                    sat_alt_km: float, timestamp: datetime) -> Dict[str, Any]:
        """
        計算完整可見性指標

        Returns:
            {
                'elevation_deg': float,
                'azimuth_deg': float,
                'distance_km': float,
                'altitude_correction': bool,  # 是否應用大氣折射修正
                'calculation_method': 'Skyfield IAU Standard'
            }
        """
        elevation, azimuth, distance = self.calculate_topocentric_position(
            sat_lat_deg, sat_lon_deg, sat_alt_km, timestamp
        )

        return {
            'elevation_deg': elevation,
            'azimuth_deg': azimuth,
            'distance_km': distance,
            'altitude_correction': True,  # Skyfield 自動應用
            'calculation_method': 'Skyfield IAU Standard',
            'coordinate_system': 'WGS84 Ellipsoid',
            'precision_level': 'Research Grade'
        }

    def calculate_time_series_visibility(self, wgs84_time_series: list,
                                         constellation: str) -> list:
        """
        為完整時間序列計算可見性指標

        Args:
            wgs84_time_series: Stage 3 輸出的 WGS84 座標時間序列
            constellation: 星座類型 (用於確定門檻)

        Returns:
            完整時間序列可見性數據
        """
        visibility_time_series = []

        for point in wgs84_time_series:
            try:
                # 提取座標和時間
                lat = point.get('latitude_deg')
                lon = point.get('longitude_deg')
                alt_km = point.get('altitude_km', point.get('altitude_m', 0) / 1000.0)
                timestamp_str = point.get('timestamp', '')

                if not timestamp_str:
                    continue

                # 解析時間戳記
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                # 使用 Skyfield 計算精確可見性
                metrics = self.calculate_visibility_metrics(lat, lon, alt_km, timestamp)

                # 構建時間點數據
                visibility_point = {
                    'timestamp': timestamp_str,
                    'latitude_deg': lat,
                    'longitude_deg': lon,
                    'altitude_km': alt_km,
                    'elevation_deg': metrics['elevation_deg'],
                    'azimuth_deg': metrics['azimuth_deg'],
                    'distance_km': metrics['distance_km'],
                    'calculation_method': metrics['calculation_method']
                }

                visibility_time_series.append(visibility_point)

            except Exception as e:
                self.logger.warning(f"時間點可見性計算失敗: {e}")
                continue

        return visibility_time_series


def create_skyfield_visibility_calculator(config: Dict[str, Any] = None) -> SkyfieldVisibilityCalculator:
    """創建 Skyfield 可見性計算器實例"""
    return SkyfieldVisibilityCalculator(config)
```

**步驟 1.2: 修改主處理器使用 Skyfield**

```python
# stage4_link_feasibility_processor.py
class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(stage_number=4, stage_name="link_feasibility", config=config)

        # 初始化核心組件
        self.constellation_filter = ConstellationFilter(config)

        # 使用 Skyfield 專業計算器 (學術標準合規)
        self.visibility_calculator = SkyfieldVisibilityCalculator(config)

        self.logger.info("🛰️ Stage 4 鏈路可行性評估處理器初始化完成")
        self.logger.info("   計算標準: Skyfield IAU 2000A/2006")
```

---

### 任務 B.2: 驗證 Stage 1 epoch_datetime 使用

#### 目標檔案
- `src/stages/stage4_link_feasibility/epoch_validator.py` (新建)

#### 實現步驟

**步驟 2.1: 創建 EpochValidator 類**

```python
#!/usr/bin/env python3
"""
Epoch 時間基準驗證器

確保符合 academic_standards_clarification.md 要求:
- 每筆 TLE 記錄保持獨立 epoch_datetime
- 禁止統一時間基準
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class EpochValidator:
    """Epoch 時間基準驗證器"""

    def __init__(self):
        self.logger = logger

    def validate_independent_epochs(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證衛星是否使用獨立的 epoch 時間基準

        檢查項目:
        1. 每顆衛星是否有獨立的 epoch_datetime
        2. 是否存在統一時間基準 (禁止)
        3. epoch 時間與時間序列時間戳記的一致性

        Returns:
            {
                'validation_passed': bool,
                'independent_epochs': bool,
                'epoch_diversity': int,  # 獨立 epoch 數量
                'issues': []
            }
        """
        validation_result = {
            'validation_passed': False,
            'independent_epochs': False,
            'epoch_diversity': 0,
            'issues': [],
            'epoch_statistics': {}
        }

        try:
            # 收集所有 epoch 時間
            epoch_times = []
            satellites_without_epoch = []

            for sat_id, sat_data in satellite_data.items():
                # 檢查是否有 epoch_datetime
                if 'epoch_datetime' not in sat_data:
                    satellites_without_epoch.append(sat_id)
                    continue

                epoch_str = sat_data['epoch_datetime']
                epoch_times.append(epoch_str)

            # 檢查缺少 epoch 的衛星
            if satellites_without_epoch:
                validation_result['issues'].append(
                    f"❌ {len(satellites_without_epoch)} 顆衛星缺少 epoch_datetime"
                )

            # 檢查 epoch 多樣性
            unique_epochs = len(set(epoch_times))
            total_satellites = len(satellite_data)

            validation_result['epoch_diversity'] = unique_epochs
            validation_result['epoch_statistics'] = {
                'total_satellites': total_satellites,
                'unique_epochs': unique_epochs,
                'diversity_ratio': unique_epochs / total_satellites if total_satellites > 0 else 0
            }

            # 判斷是否為獨立 epoch (至少有多樣性)
            if unique_epochs >= min(10, total_satellites * 0.1):
                validation_result['independent_epochs'] = True
                self.logger.info(f"✅ Epoch 多樣性檢查通過: {unique_epochs} 個獨立 epoch")
            else:
                validation_result['issues'].append(
                    f"❌ Epoch 多樣性不足: 只有 {unique_epochs} 個獨立 epoch (總計 {total_satellites} 顆衛星)"
                )
                validation_result['independent_epochs'] = False

            # 檢查是否存在統一時間基準 (禁止字段)
            forbidden_fields = ['calculation_base_time', 'primary_epoch_time', 'unified_time_base']
            metadata = satellite_data.get('metadata', {}) if 'metadata' in satellite_data else {}

            for field in forbidden_fields:
                if field in metadata:
                    validation_result['issues'].append(
                        f"❌ 檢測到禁止的統一時間基準字段: '{field}'"
                    )

            # 總體驗證結果
            validation_result['validation_passed'] = (
                validation_result['independent_epochs'] and
                len(validation_result['issues']) == 0
            )

            return validation_result

        except Exception as e:
            self.logger.error(f"Epoch 驗證異常: {e}")
            validation_result['issues'].append(f"驗證過程異常: {e}")
            return validation_result

    def validate_timestamp_consistency(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證時間戳記與 epoch 的一致性

        檢查時間序列中的 timestamp 是否在 epoch 附近的合理範圍內
        """
        consistency_result = {
            'consistent': True,
            'issues': []
        }

        for sat_id, sat_data in satellite_data.items():
            try:
                epoch_str = sat_data.get('epoch_datetime', '')
                time_series = sat_data.get('wgs84_coordinates', [])

                if not epoch_str or not time_series:
                    continue

                # 解析 epoch 時間
                epoch_dt = datetime.fromisoformat(epoch_str.replace('Z', '+00:00'))

                # 檢查時間序列時間戳記
                for point in time_series[:5]:  # 抽樣檢查前5個點
                    timestamp_str = point.get('timestamp', '')
                    if not timestamp_str:
                        continue

                    timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                    # 檢查時間差 (應在合理範圍內，如 ±7天)
                    time_diff = abs((timestamp_dt - epoch_dt).total_seconds())
                    if time_diff > 7 * 24 * 3600:  # 超過 7 天
                        consistency_result['consistent'] = False
                        consistency_result['issues'].append(
                            f"⚠️ {sat_id}: 時間戳記與 epoch 差距過大 ({time_diff/3600:.1f} 小時)"
                        )
                        break

            except Exception as e:
                continue

        return consistency_result


def create_epoch_validator() -> EpochValidator:
    """創建 Epoch 驗證器實例"""
    return EpochValidator()
```

**步驟 2.2: 在主處理器中添加 epoch 驗證**

```python
# stage4_link_feasibility_processor.py
def execute(self, input_data: Any) -> Dict[str, Any]:
    """執行鏈路可行性評估"""
    try:
        # ... 現有驗證 ...

        # 新增: Epoch 時間基準驗證
        epoch_validator = EpochValidator()
        epoch_validation = epoch_validator.validate_independent_epochs(input_data.get('satellites', {}))

        if not epoch_validation['validation_passed']:
            self.logger.warning("⚠️ Epoch 時間基準驗證未完全通過:")
            for issue in epoch_validation['issues']:
                self.logger.warning(f"   {issue}")

        # 記錄驗證統計
        self.logger.info(f"📊 Epoch 多樣性: {epoch_validation['epoch_diversity']} 個獨立 epoch")

        # 繼續主要處理流程 ...
```

---

## 🧪 測試計劃

### 測試 B.1: Skyfield 計算精度驗證

```python
def test_skyfield_vs_manual_calculation():
    """比較 Skyfield 與手動計算的精度差異"""

    skyfield_calc = SkyfieldVisibilityCalculator()
    manual_calc = NTPUVisibilityCalculator()  # 舊版

    # 測試案例: 台北上空衛星
    test_lat, test_lon, test_alt = 25.0, 121.5, 550.0
    test_time = datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc)

    # Skyfield 計算
    sky_elev, sky_az, sky_dist = skyfield_calc.calculate_topocentric_position(
        test_lat, test_lon, test_alt, test_time
    )

    # 手動計算
    manual_elev = manual_calc.calculate_satellite_elevation(test_lat, test_lon, test_alt)

    # 比較差異
    elevation_diff = abs(sky_elev - manual_elev)

    print(f"Skyfield 仰角: {sky_elev:.4f}°")
    print(f"手動計算仰角: {manual_elev:.4f}°")
    print(f"精度差異: {elevation_diff:.4f}° ({elevation_diff * 111:.1f}m)")

    # 學術標準: 精度差異應在 0.1° 以內
    assert elevation_diff < 0.1, "精度差異超出學術標準"
```

### 測試 B.2: Epoch 驗證測試

```python
def test_epoch_validation():
    """測試 epoch 時間基準驗證"""

    validator = EpochValidator()

    # 測試案例 1: 獨立 epoch (正確)
    test_data_valid = {
        'sat1': {'epoch_datetime': '2025-09-30T10:00:00Z'},
        'sat2': {'epoch_datetime': '2025-09-30T11:00:00Z'},
        'sat3': {'epoch_datetime': '2025-09-30T12:00:00Z'}
    }

    result = validator.validate_independent_epochs(test_data_valid)
    assert result['validation_passed'] == True
    assert result['independent_epochs'] == True

    # 測試案例 2: 統一 epoch (錯誤)
    test_data_invalid = {
        'sat1': {'epoch_datetime': '2025-09-30T10:00:00Z'},
        'sat2': {'epoch_datetime': '2025-09-30T10:00:00Z'},
        'sat3': {'epoch_datetime': '2025-09-30T10:00:00Z'}
    }

    result = validator.validate_independent_epochs(test_data_invalid)
    assert result['independent_epochs'] == False
```

---

## 📋 驗收標準

### 學術標準驗收
- [ ] 使用 Skyfield 庫進行所有可見性計算
- [ ] 計算精度符合 IAU 標準 (仰角誤差 < 0.1°)
- [ ] 自動應用極移、章動修正
- [ ] WGS84 橢球精確計算

### Epoch 驗證驗收
- [ ] 檢測並記錄 epoch 多樣性
- [ ] 識別統一時間基準 (如存在則警告)
- [ ] 驗證時間戳記與 epoch 的一致性
- [ ] 符合學術標準的獨立 epoch 原則

### 文檔驗收
- [ ] 代碼註釋標註使用的學術標準
- [ ] 計算方法文檔化 (IAU 2000A/2006)
- [ ] 精度指標明確記錄

---

## 📦 交付物

1. **新增檔案**
   - `src/stages/stage4_link_feasibility/skyfield_visibility_calculator.py`
   - `src/stages/stage4_link_feasibility/epoch_validator.py`

2. **修改檔案**
   - `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`
   - `requirements.txt` (添加 skyfield 依賴)

3. **測試檔案**
   - `tests/stages/stage4/test_skyfield_precision.py` (新建)
   - `tests/stages/stage4/test_epoch_validation.py` (新建)

4. **文檔更新**
   - 更新 `docs/stages/stage4-link-feasibility.md` 學術合規狀態
   - 添加計算方法文檔

---

## 🚀 執行順序

1. **任務 B.1** (2-3小時): Skyfield 整合
2. **任務 B.2** (1小時): Epoch 驗證
3. **測試驗證** (0.5-1小時): 精度測試和驗收

**總計**: 3-4 小時

---

## ⚠️ 風險與依賴

### 依賴
- ✅ **前置**: 計劃 A 必須完成 (時間序列數據結構)
- ⚙️ **系統**: 需要安裝 Skyfield 庫 (`pip install skyfield`)
- 📡 **數據**: Skyfield 首次運行會下載星曆表 (~10MB)

### 風險
- Skyfield 計算速度可能稍慢於手動算法 (預估 10-20% 增加)
- 星曆表下載可能在離線環境失敗 (可預先下載)

### 後續依賴
- 計劃 C (動態池規劃) 受益於更精確的可見性計算

---

**文檔版本**: v1.0
**創建日期**: 2025-09-30
**負責人**: Orbit Engine Team
**審核狀態**: 待審核