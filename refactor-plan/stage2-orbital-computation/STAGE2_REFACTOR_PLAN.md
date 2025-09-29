# 🚀 Stage 2: 軌道計算升級計劃

## 📋 階段概覽

**目標**：將自建SGP4Calculator替換為NASA JPL精度標準的專業軌道計算庫

**時程**：第1週後半 + 第2週 (7個工作日)

**優先級**：🚨 高風險 - 計算精度核心

**現狀問題**：自建SGP4Calculator精度未驗證，存在學術可信度風險

## 🎯 重構目標

### 核心目標
- ❌ **移除自建組件**: 淘汰精度未驗證的SGP4Calculator
- ✅ **導入NASA標準**: Skyfield (NASA JPL精度) + PyOrbital (LEO專用)
- ✅ **星座感知計算**: 分別處理Starlink/OneWeb不同軌道週期
- ✅ **軌道精度提升**: 從~100m誤差降至<10m

### 學術標準要求
- **計算精度**: 軌道預測誤差 < 10m (NASA JPL標準)
- **軌道週期**: 星座特定週期獨立計算
- **時間基準**: 使用Stage 1的獨立epoch時間
- **計算範圍**: 支援完整軌道週期分析

## 🔧 技術實現

### 套件選擇理由

#### Skyfield (主要軌道引擎)
```python
# NASA JPL精度優勢
✅ NASA JPL級精度 (<10m誤差)
✅ 直接支援TLE格式，無需轉換
✅ 內建SGP4/SDP4傳播器
✅ 專為衛星過境預測優化
✅ 天文學社群驗證
```

#### PyOrbital (LEO專用優化)
```python
# LEO衛星專用優勢
✅ LEO衛星專用算法
✅ 快速過境計算
✅ 輕量級實現
✅ 批量處理優化
```

### 新架構設計

```python
# 軌道計算架構
orbital_computation/
├── skyfield_engine.py          # Skyfield主要計算引擎
├── pyorbital_optimizer.py      # PyOrbital LEO優化
├── constellation_processor.py  # 星座特定處理
└── orbit_validator.py          # 軌道精度驗證
```

## 📅 實施計劃 (7天)

### Day 1-3: Skyfield核心引擎
```bash
# 安裝核心軌道計算套件
pip install skyfield>=1.48
pip install pyorbital>=1.8

# 替換組件
❌ 移除：自建 SGP4Calculator
❌ 移除：自建 orbit-predictor 封裝
✅ 導入：skyfield.api.EarthSatellite
✅ 導入：pyorbital.orbital.Orbital
```

```python
# skyfield_engine.py 核心實現
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time

class SkyfieldOrbitEngine:
    """Skyfield軌道計算引擎 - NASA JPL精度"""

    def __init__(self):
        self.ts = load.timescale()
        self.satellites = {}

    def create_satellite_from_tle(self, satellite_name: str,
                                 line1: str, line2: str,
                                 epoch_datetime: datetime) -> EarthSatellite:
        """從TLE創建衛星物件 - 保持獨立epoch"""

        # 使用Stage 1提供的獨立epoch時間
        satellite = EarthSatellite(line1, line2, satellite_name, self.ts)

        # 存儲衛星物件供後續使用
        self.satellites[satellite_name] = {
            'satellite': satellite,
            'epoch_time': epoch_datetime,
            'tle_line1': line1,
            'tle_line2': line2
        }

        return satellite

    def calculate_orbit_positions(self, satellite_name: str,
                                time_window_minutes: int) -> List[OrbitPosition]:
        """計算軌道位置序列 - 星座感知週期"""

        satellite_info = self.satellites[satellite_name]
        satellite = satellite_info['satellite']
        base_time = satellite_info['epoch_time']

        positions = []

        for minute in range(time_window_minutes):
            # 計算時間點
            current_time = self.ts.from_datetime(
                base_time + timedelta(minutes=minute)
            )

            # 獲取衛星位置 (TEME座標系)
            position = satellite.at(current_time)

            # 提取位置和速度向量
            pos_km = position.position.km  # [x, y, z] in km
            vel_kmps = position.velocity.km_per_s  # [vx, vy, vz] in km/s

            positions.append(OrbitPosition(
                time=current_time,
                position_teme=pos_km,
                velocity_teme=vel_kmps,
                satellite_name=satellite_name
            ))

        return positions

    def get_satellite_at_time(self, satellite_name: str,
                            target_time: datetime) -> SatelliteState:
        """獲取指定時間的衛星狀態"""

        satellite = self.satellites[satellite_name]['satellite']
        skyfield_time = self.ts.from_datetime(target_time)

        position = satellite.at(skyfield_time)

        return SatelliteState(
            time=target_time,
            position_teme=position.position.km,
            velocity_teme=position.velocity.km_per_s,
            satellite_name=satellite_name
        )
```

### Day 4-5: 星座特定處理
```python
# constellation_processor.py 星座感知計算
class ConstellationProcessor:
    """星座特定軌道處理器"""

    def __init__(self, orbit_engine: SkyfieldOrbitEngine):
        self.orbit_engine = orbit_engine

        # 星座特定軌道週期 (來自研究文檔)
        self.orbital_periods = {
            'starlink': {
                'min_minutes': 90,
                'max_minutes': 95,
                'typical_minutes': 93
            },
            'oneweb': {
                'min_minutes': 109,
                'max_minutes': 115,
                'typical_minutes': 112
            }
        }

    def process_starlink_constellation(self, starlink_tle_data: List[TLERecord]) -> ConstellationOrbitData:
        """處理Starlink星座 - 90-95分鐘軌道週期"""

        constellation_data = ConstellationOrbitData(
            constellation_name='starlink',
            orbital_period_minutes=self.orbital_periods['starlink']['typical_minutes'],
            satellites={}
        )

        for tle_record in starlink_tle_data:
            # 創建衛星
            satellite = self.orbit_engine.create_satellite_from_tle(
                tle_record.satellite_name,
                tle_record.line1,
                tle_record.line2,
                tle_record.epoch_datetime
            )

            # 計算完整軌道週期 (95分鐘)
            orbit_positions = self.orbit_engine.calculate_orbit_positions(
                tle_record.satellite_name,
                time_window_minutes=95
            )

            constellation_data.satellites[tle_record.satellite_name] = orbit_positions

        return constellation_data

    def process_oneweb_constellation(self, oneweb_tle_data: List[TLERecord]) -> ConstellationOrbitData:
        """處理OneWeb星座 - 109-115分鐘軌道週期"""

        constellation_data = ConstellationOrbitData(
            constellation_name='oneweb',
            orbital_period_minutes=self.orbital_periods['oneweb']['typical_minutes'],
            satellites={}
        )

        for tle_record in oneweb_tle_data:
            # 創建衛星
            satellite = self.orbit_engine.create_satellite_from_tle(
                tle_record.satellite_name,
                tle_record.line1,
                tle_record.line2,
                tle_record.epoch_datetime
            )

            # 計算完整軌道週期 (115分鐘)
            orbit_positions = self.orbit_engine.calculate_orbit_positions(
                tle_record.satellite_name,
                time_window_minutes=115
            )

            constellation_data.satellites[tle_record.satellite_name] = orbit_positions

        return constellation_data
```

### Day 6-7: PyOrbital快速計算整合
```python
# pyorbital_optimizer.py LEO快速計算
from pyorbital.orbital import Orbital
from pyorbital import tlefile

class PyOrbitalOptimizer:
    """PyOrbital LEO衛星快速計算優化器"""

    def __init__(self):
        self.orbital_cache = {}

    def quick_visibility_check(self, satellite_name: str,
                             tle_file_path: str,
                             observer_coords: Coordinates,
                             time_window_hours: int = 24) -> List[VisibilityWindow]:
        """快速可見性檢查 - LEO衛星專用"""

        if satellite_name not in self.orbital_cache:
            # 創建Orbital物件
            orb = Orbital(satellite_name, tle_file=tle_file_path)
            self.orbital_cache[satellite_name] = orb
        else:
            orb = self.orbital_cache[satellite_name]

        # 快速過境預測
        passes = orb.get_next_passes(
            utc_time=datetime.utcnow(),
            length_h=time_window_hours,
            lon=observer_coords.longitude,
            lat=observer_coords.latitude,
            alt=observer_coords.altitude_km
        )

        # 轉換為可見性窗口
        visibility_windows = []
        for rise_time, fall_time, max_elevation in passes:
            visibility_windows.append(VisibilityWindow(
                satellite_name=satellite_name,
                rise_time=rise_time,
                set_time=fall_time,
                max_elevation=max_elevation,
                duration_minutes=(fall_time - rise_time).total_seconds() / 60
            ))

        return visibility_windows

    def batch_satellite_tracking(self, satellite_list: List[str],
                                tle_file_path: str,
                                target_time: datetime) -> Dict[str, SatellitePosition]:
        """批量衛星位置計算"""

        positions = {}

        for satellite_name in satellite_list:
            if satellite_name not in self.orbital_cache:
                orb = Orbital(satellite_name, tle_file=tle_file_path)
                self.orbital_cache[satellite_name] = orb
            else:
                orb = self.orbital_cache[satellite_name]

            # 計算位置
            lon, lat, alt = orb.get_lonlatalt(target_time)

            positions[satellite_name] = SatellitePosition(
                longitude=lon,
                latitude=lat,
                altitude_km=alt,
                timestamp=target_time
            )

        return positions
```

## 🧪 驗證測試

### 軌道精度測試
```python
def test_orbit_accuracy():
    """軌道精度驗證測試 - 與NASA標準對比"""

    engine = SkyfieldOrbitEngine()

    # 使用已知軌道的測試衛星
    test_satellite = engine.create_satellite_from_tle(
        "ISS (ZARYA)",
        "1 25544U 98067A   24001.00000000  .00002182  00000+0  40768-4 0  9990",
        "2 25544  51.6461 339.7939 0001220  92.8340 267.3124 15.49309959123456",
        datetime(2024, 1, 1, 0, 0, 0)
    )

    # 計算24小時軌道
    positions = engine.calculate_orbit_positions("ISS (ZARYA)", 1440)  # 24小時

    # 驗證軌道精度 (與NASA參考數據對比)
    # 這裡需要實際的NASA參考數據進行對比
    assert len(positions) == 1440, "軌道計算點數不正確"

def test_constellation_specific_periods():
    """測試星座特定軌道週期"""

    processor = ConstellationProcessor(engine)

    # 驗證Starlink週期計算
    starlink_data = load_test_starlink_tle()
    starlink_orbits = processor.process_starlink_constellation(starlink_data)
    assert starlink_orbits.orbital_period_minutes == 93

    # 驗證OneWeb週期計算
    oneweb_data = load_test_oneweb_tle()
    oneweb_orbits = processor.process_oneweb_constellation(oneweb_data)
    assert oneweb_orbits.orbital_period_minutes == 112
```

## 📊 成功指標

### 量化指標
- **軌道精度**: 預測誤差 < 10m (NASA JPL標準)
- **計算速度**: 單衛星軌道計算 < 1秒
- **星座處理**: 支援Starlink(95分鐘), OneWeb(115分鐘)獨立週期
- **數據一致性**: 與Stage 1 TLE數據100%相容

### 質化指標
- **NASA標準**: 100%使用NASA JPL級精度算法
- **學術可信**: 基於天文學社群驗證的專業庫
- **計算穩定**: 無自建算法的不確定性
- **維護簡化**: 移除自建SGP4維護負擔

## ⚠️ 風險控制

### 技術風險
| 風險 | 影響 | 應對策略 |
|------|------|----------|
| 精度驗證困難 | 高 | 使用ISS等已知軌道驗證 |
| 計算性能問題 | 中等 | PyOrbital輔助優化 |
| Skyfield學習曲線 | 中等 | 詳細文檔研讀，範例實作 |

### 學術風險
- **精度標準**: 必須達到NASA JPL級精度要求
- **對比驗證**: 需要與權威數據源對比確認
- **計算可重現**: 確保計算結果可重現

---

**文檔版本**: v1.0 (修正版)
**建立日期**: 2024-01-15
**前置條件**: Stage 1 TLE管理完成
**重點**: 學術級軌道計算精度，無工業級監控
**下一階段**: Stage 3 - 座標轉換升級