# 🌐 Stage 3: 座標轉換系統升級計劃

## 📋 階段概覽

**目標**：將自建座標轉換引擎替換為IAU標準的Astropy專業庫

**時程**：第2週後半 + 第3週前半 (4個工作日)

**優先級**：🚨 高風險 - IAU標準合規

**現狀問題**：自建座標轉換引擎缺乏IAU標準驗證，存在精度風險

## 🎯 重構目標

### 核心目標
- ❌ **移除自建組件**: 淘汰缺乏標準驗證的座標轉換引擎
- ✅ **導入IAU標準**: Astropy天文學標準庫
- ✅ **高精度轉換**: 座標轉換精度 < 0.5m
- ✅ **信號處理增強**: SciPy專業信號處理算法

### 學術標準要求
- **座標精度**: 轉換誤差 < 0.5m (IAU標準)
- **時間標準**: 支援UTC、TAI、TT等多種時間標準
- **座標系統**: TEME、ITRS、GCRS完整支援
- **信號處理**: 專業級RSRP/RSRQ信號濾波

## 🔧 技術實現

### 套件選擇理由

#### Astropy (IAU標準座標庫)
```python
# IAU標準優勢
✅ IAU官方標準實現
✅ 高精度座標轉換 (<0.5m)
✅ 支援極移、章動修正
✅ 多時間標準支援
✅ 完整的celestial mechanics
✅ 天文學社群驗證
```

#### SciPy (科學計算核心)
```python
# 信號處理優勢
✅ 專業信號處理算法
✅ 濾波器設計工具
✅ 統計分析功能
✅ 優化算法庫
✅ 數值計算標準
```

### 新架構設計

```python
# 座標轉換與信號處理架構
coordinate_transformation/
├── astropy_transformer.py     # Astropy座標轉換核心
├── signal_processor.py        # SciPy信號處理
├── coordinate_validator.py    # IAU標準驗證
└── ntpu_coordinates.py        # NTPU特定座標處理
```

## 📅 實施計劃 (4天)

### Day 1-2: Astropy座標轉換核心
```bash
# 安裝IAU標準座標庫
pip install astropy>=5.3
pip install scipy>=1.10.0

# 替換組件
❌ 移除：自建 SkyfieldCoordinateEngine
❌ 移除：自建 IERS/WGS84 管理器
✅ 導入：astropy.coordinates
✅ 導入：astropy.time
✅ 導入：scipy.signal
```

```python
# astropy_transformer.py IAU標準實現
from astropy.coordinates import TEME, ITRS, GCRS, EarthLocation, AltAz
from astropy.time import Time
from astropy import units as u

class IAUStandardTransformer:
    """IAU標準座標轉換器"""

    def __init__(self):
        # NTPU座標 (來自研究文檔)
        self.ntpu_location = EarthLocation(
            lat=24.944167 * u.deg,    # 24°56'39"N
            lon=121.371944 * u.deg,   # 121°22'17"E
            height=0.1 * u.km         # 海拔約100m
        )

    def teme_to_itrs(self, teme_position: np.ndarray,
                     observation_time: datetime) -> np.ndarray:
        """TEME到ITRS座標轉換 - IAU標準"""

        # 轉換為Astropy時間物件
        astropy_time = Time(observation_time, scale='utc')

        # 創建TEME座標物件
        teme_coord = TEME(
            x=teme_position[0] * u.km,
            y=teme_position[1] * u.km,
            z=teme_position[2] * u.km,
            obstime=astropy_time,
            representation_type='cartesian'
        )

        # 高精度轉換到ITRS (包含極移修正)
        itrs_coord = teme_coord.transform_to(
            ITRS(obstime=astropy_time)
        )

        return itrs_coord.cartesian.xyz.to(u.km).value

    def itrs_to_geographic(self, itrs_position: np.ndarray) -> Tuple[float, float, float]:
        """ITRS到地理座標轉換"""

        # 使用EarthLocation進行精確轉換
        location = EarthLocation.from_geocentric(
            x=itrs_position[0] * u.km,
            y=itrs_position[1] * u.km,
            z=itrs_position[2] * u.km
        )

        return (
            location.lat.to(u.deg).value,    # 緯度
            location.lon.to(u.deg).value,    # 經度
            location.height.to(u.km).value   # 高度
        )

    def calculate_elevation_azimuth(self, satellite_itrs: np.ndarray,
                                  observation_time: datetime) -> Tuple[float, float]:
        """計算衛星仰角方位角 - 天文學標準"""

        astropy_time = Time(observation_time, scale='utc')

        # 創建衛星在ITRS中的座標
        sat_itrs = ITRS(
            x=satellite_itrs[0] * u.km,
            y=satellite_itrs[1] * u.km,
            z=satellite_itrs[2] * u.km,
            obstime=astropy_time
        )

        # 轉換到NTPU的地平座標系
        altaz_frame = AltAz(obstime=astropy_time, location=self.ntpu_location)
        sat_altaz = sat_itrs.transform_to(altaz_frame)

        return (
            sat_altaz.alt.to(u.deg).value,  # 仰角
            sat_altaz.az.to(u.deg).value    # 方位角
        )

    def calculate_distance(self, satellite_itrs: np.ndarray) -> float:
        """計算衛星到NTPU的距離"""

        sat_location = EarthLocation.from_geocentric(
            x=satellite_itrs[0] * u.km,
            y=satellite_itrs[1] * u.km,
            z=satellite_itrs[2] * u.km
        )

        # 計算到NTPU的距離
        distance = self.ntpu_location.separation_3d(sat_location)
        return distance.to(u.km).value

class CoordinateProcessor:
    """座標處理器 - 整合Stage 2軌道數據"""

    def __init__(self):
        self.transformer = IAUStandardTransformer()

    def process_satellite_coordinates(self, orbit_position: OrbitPosition) -> SatelliteCoordinates:
        """處理衛星座標 - 完整轉換鏈"""

        # TEME → ITRS 轉換
        itrs_position = self.transformer.teme_to_itrs(
            orbit_position.position_teme,
            orbit_position.time.datetime
        )

        # ITRS → 地理座標
        lat, lon, alt = self.transformer.itrs_to_geographic(itrs_position)

        # 計算仰角方位角
        elevation, azimuth = self.transformer.calculate_elevation_azimuth(
            itrs_position,
            orbit_position.time.datetime
        )

        # 計算距離
        distance_km = self.transformer.calculate_distance(itrs_position)

        return SatelliteCoordinates(
            time=orbit_position.time,
            satellite_name=orbit_position.satellite_name,
            position_teme=orbit_position.position_teme,
            position_itrs=itrs_position,
            latitude=lat,
            longitude=lon,
            altitude_km=alt,
            elevation=elevation,
            azimuth=azimuth,
            distance_km=distance_km
        )
```

### Day 3: SciPy信號處理整合
```python
# signal_processor.py 信號品質處理
from scipy import signal
from scipy.stats import norm
import numpy as np

class SignalQualityProcessor:
    """信號品質處理器 - 3GPP標準"""

    def __init__(self):
        self.filters = {}

    def calculate_rsrp_from_distance(self, distance_km: float,
                                   tx_power_dbm: float = 43.0) -> float:
        """基於距離計算RSRP - 自由空間路徑損耗模型"""

        # 自由空間路徑損耗 (Friis公式)
        # PL(dB) = 20*log10(d) + 20*log10(f) + 92.45
        frequency_ghz = 2.0  # 典型LEO衛星頻率
        path_loss = (
            20 * np.log10(distance_km) +
            20 * np.log10(frequency_ghz) +
            92.45
        )

        antenna_gain = 15.0  # dBi (典型衛星天線增益)

        # RSRP = Tx_Power + Antenna_Gain - Path_Loss
        rsrp = tx_power_dbm + antenna_gain - path_loss

        return rsrp

    def calculate_rsrq(self, rsrp: float, rssi: float) -> float:
        """計算RSRQ - 符合3GPP標準"""

        # RSRQ = N × RSRP / RSSI (N為RB數量，一般為50)
        n_rb = 50  # 3GPP標準Resource Block數量
        rsrq = n_rb * (10**(rsrp/10)) / (10**(rssi/10))

        return 10 * np.log10(rsrq)

    def filter_rsrp_signal(self, rsrp_data: np.ndarray,
                          sample_rate: float = 1.0,
                          cutoff_freq: float = 0.1) -> np.ndarray:
        """RSRP信號濾波 - 移除高頻雜訊"""

        # 設計Butterworth低通濾波器
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff_freq / nyquist

        b, a = signal.butter(3, normal_cutoff, btype='low', analog=False)

        # 零相位濾波 (避免相位延遲)
        filtered_rsrp = signal.filtfilt(b, a, rsrp_data)

        return filtered_rsrp

    def assess_signal_quality(self, rsrp: float, rsrq: float) -> str:
        """評估信號品質等級"""

        if rsrp > -85 and rsrq > -10:
            return "Excellent"
        elif rsrp > -95 and rsrq > -15:
            return "Good"
        elif rsrp > -105 and rsrq > -20:
            return "Fair"
        else:
            return "Poor"
```

### Day 4: 座標驗證與整合
```python
# coordinate_validator.py IAU標準驗證
class CoordinateValidator:
    """座標轉換IAU標準驗證器"""

    def validate_coordinate_precision(self, test_coordinates: List[TestCoordinate]) -> ValidationResult:
        """驗證座標轉換精度"""

        transformer = IAUStandardTransformer()
        precision_errors = []

        for test_coord in test_coordinates:
            # 執行座標轉換
            itrs_result = transformer.teme_to_itrs(
                test_coord.teme_input,
                test_coord.test_time
            )

            # 計算與標準答案的誤差
            error_km = np.linalg.norm(itrs_result - test_coord.expected_itrs)

            precision_errors.append(error_km)

        # 統計分析
        mean_error = np.mean(precision_errors)
        max_error = np.max(precision_errors)
        error_std = np.std(precision_errors)

        return ValidationResult(
            mean_error_km=mean_error,
            max_error_km=max_error,
            error_std_km=error_std,
            precision_requirement_met=max_error < 0.0005,  # 0.5m要求
            total_tests=len(test_coordinates)
        )

    def validate_iau_compliance(self) -> ComplianceResult:
        """驗證IAU標準合規性"""

        checks = {
            'time_standards': self._check_time_standards(),
            'coordinate_frames': self._check_coordinate_frames(),
            'precision_corrections': self._check_precision_corrections(),
            'reference_systems': self._check_reference_systems()
        }

        return ComplianceResult(
            iau_compliant=all(checks.values()),
            compliance_checks=checks
        )
```

## 🧪 驗證測試

### IAU標準合規測試
```python
def test_iau_coordinate_precision():
    """IAU座標精度測試"""

    transformer = IAUStandardTransformer()

    # 使用ISS已知位置進行測試
    test_teme = np.array([6500.0, 0.0, 0.0])  # km
    test_time = datetime(2024, 1, 15, 12, 0, 0)

    itrs_result = transformer.teme_to_itrs(test_teme, test_time)

    # 驗證精度要求 (< 0.5m)
    # 這裡需要標準參考答案進行對比
    # assert precision_error < 0.0005  # 0.5m

def test_signal_processing_quality():
    """信號處理品質測試"""

    processor = SignalQualityProcessor()

    # 測試距離-RSRP計算
    distance_500km = 500.0
    rsrp_500 = processor.calculate_rsrp_from_distance(distance_500km)
    assert -120 < rsrp_500 < -70, "RSRP計算異常"

    # 測試信號濾波
    noisy_signal = np.random.normal(0, 1, 1000)
    filtered = processor.filter_rsrp_signal(noisy_signal)
    noise_reduction = np.std(noisy_signal) / np.std(filtered)
    assert noise_reduction > 1.5, "濾波效果不足"
```

## 📊 成功指標

### 量化指標
- **座標精度**: 轉換誤差 < 0.5m (IAU標準)
- **時間精度**: 微秒級時間處理
- **信號處理**: SNR改善 > 3dB
- **計算速度**: 座標轉換 < 1ms/點

### 質化指標
- **IAU標準**: 100%符合國際天文學聯合會標準
- **學術認可**: 使用天文學社群驗證的專業庫
- **精度保證**: 消除自建算法的不確定性
- **維護簡化**: 減少座標系統維護複雜度

## ⚠️ 風險控制

### 技術風險
| 風險 | 影響 | 應對策略 |
|------|------|----------|
| Astropy學習曲線 | 中等 | 詳細文檔研讀，範例學習 |
| 精度驗證困難 | 高 | 使用已知標準案例驗證 |
| 時間標準複雜性 | 中等 | 專注UTC標準，逐步擴展 |

### 學術風險
- **IAU合規**: 必須100%符合IAU標準
- **精度達標**: 必須達到0.5m精度要求
- **標準一致**: 與國際學術界保持一致

---

**文檔版本**: v1.0 (修正版)
**建立日期**: 2024-01-15
**前置條件**: Stage 2 軌道計算完成
**重點**: IAU標準座標轉換，無過度複雜功能
**下一階段**: Stage 4 - 衛星池分析優化