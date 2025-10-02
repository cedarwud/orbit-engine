# 📝 程式碼註解模板 - 防止學術違規

本文檔提供**強制性註解模板**，確保所有階段的程式碼符合 Grade A 學術標準。

---

## 🚨 在撰寫新算法時必讀

### ⚠️ 禁止事項檢查清單（寫在程式碼開頭）

```python
"""
算法模組名稱

⚠️ CRITICAL - 學術合規性檢查:
□ 禁止使用簡化算法 (必須完整實現標準)
□ 禁止使用估計值/假設值 (estimated, assumed, approximately)
□ 禁止使用硬編碼係數 (所有數值必須有 SOURCE 標註)
□ 禁止使用預設值 (系統參數必須從配置獲取或拋出錯誤)
□ 必須使用官方標準 (ITU-R, 3GPP, IEEE, NASA JPL)

學術標準: Grade A
參考文檔: docs/ACADEMIC_STANDARDS.md
"""
```

---

## 1️⃣ 物理常數使用模板

### ✅ 正確範例
```python
# ✅ Grade A 標準: 從 PhysicsConstants 導入
from shared.constants.physics_constants import PhysicsConstants
physics_consts = PhysicsConstants()

# 光速
c = physics_consts.SPEED_OF_LIGHT
# SOURCE: CODATA 2018, exact value (defined constant)

# Boltzmann 常數
k = physics_consts.BOLTZMANN_CONSTANT
# SOURCE: CODATA 2018, k = 1.380649×10⁻²³ J/K
```

### ❌ 錯誤範例
```python
# ❌ 違規: 硬編碼，無 SOURCE 標註
c = 299792458.0  # 光速

# ❌ 違規: 使用預設值
k = 1.38e-23  # Boltzmann constant
```

---

## 2️⃣ 算法實現模板

### ✅ 完整算法 (ITU-R P.676-13 範例)

```python
def calculate_atmospheric_attenuation(self, frequency_ghz: float, elevation_deg: float) -> float:
    """
    計算大氣衰減 (ITU-R P.676-13 完整標準)

    ⚠️ CRITICAL: 必須使用完整譜線參數
    - 氧氣吸收: 44條譜線 (ITU-R P.676-13 Table 1)
    - 水蒸氣吸收: 35條譜線 (ITU-R P.676-13 Table 2)

    ❌ 禁止使用簡化版本 (12條、20條、28條等)

    依據:
    - ITU-R Recommendation P.676-13 (08/2019)
    - Section 2: Attenuation by atmospheric gases

    Args:
        frequency_ghz: 頻率 (GHz)
        elevation_deg: 仰角 (度)

    Returns:
        attenuation_db: 總大氣衰減 (dB)
    """
    # ✅ 使用完整 ITU-R P.676-13 模型
    from .itur_p676_atmospheric_model import create_itur_p676_model

    itur_model = create_itur_p676_model(
        temperature_k=self.config['temperature_k'],      # ❌ 禁止預設值
        pressure_hpa=self.config['pressure_hpa'],        # ❌ 禁止預設值
        water_vapor_density_g_m3=self.config['water_vapor_density']  # ❌ 禁止預設值
    )

    # 完整計算 (44+35條譜線)
    attenuation_db = itur_model.calculate_total_attenuation(
        frequency_ghz=frequency_ghz,
        elevation_deg=elevation_deg
    )

    return attenuation_db
```

### ❌ 簡化算法 (嚴重違規)

```python
# ❌ 違規範例: 簡化的大氣衰減 (禁止使用)
def simplified_atmospheric_loss(elevation_deg: float) -> float:
    """❌ 違規: 使用簡化算法"""
    # ❌ 只用幾條吸收線 (違反 Grade A 標準)
    oxygen_lines = [
        [118.7503, 0.94e-6, 2.83],  # ❌ 只有12條線
        ...
    ]

    # ❌ 使用經驗係數 (無學術依據)
    base_loss = 0.2  # ❌ 硬編碼

    return base_loss * (90.0 - elevation_deg) / 90.0  # ❌ 簡化公式
```

---

## 3️⃣ 參數配置模板

### ✅ 強制配置 (禁止預設值)

```python
class SignalCalculator:
    def __init__(self, config: Dict[str, Any]):
        """
        初始化信號計算器

        ⚠️ CRITICAL: 所有系統參數必須從配置提供
        ❌ 禁止使用預設值 (違反 Grade A 標準)
        """
        # ✅ 正確: 必須配置，否則拋出錯誤
        if 'noise_figure_db' not in config:
            raise ValueError(
                "noise_figure_db 必須在配置中提供\n"
                "Grade A 標準禁止使用預設值\n"
                "請提供實際測量值或設備規格書數值"
            )
        self.noise_figure_db = config['noise_figure_db']

        # ✅ 正確: 從 SignalConstants 導入門檻值
        from shared.constants.physics_constants import SignalConstants
        signal_consts = SignalConstants()

        self.rsrp_threshold = signal_consts.RSRP_FAIR
        # SOURCE: 3GPP TS 38.133 Table 9.2.3.1-1
```

### ❌ 錯誤: 使用預設值

```python
# ❌ 違規: 使用預設值 (禁止)
self.noise_figure_db = self.config.get('noise_figure_db', 7.0)  # ❌ 預設值
self.bandwidth_hz = self.config.get('bandwidth_hz', 20e6)       # ❌ 預設值

# ❌ 違規: 硬編碼門檻值
if rsrp >= -100:  # ❌ 無 SOURCE 標註
    return True
```

---

## 4️⃣ 數值標註模板

### ✅ 完整 SOURCE 標註

```python
# ✅ 正確: 實測值標註
latitude = 24.94388888888889
# SOURCE: GPS Survey 2025-10-02
# Location: National Taipei University Ground Station
# Coordinate: 24°56'38"N, WGS84 (EPSG:4326)
# Method: DGPS (Differential GPS)
# Accuracy: ±0.5m horizontal, ±1.0m vertical
# Measurement duration: 10 minutes averaging

# ✅ 正確: 標準文檔引用
guard_band_khz = 1500.0
# SOURCE: 3GPP TS 38.101-1 V18.4.0 (2023-12) Table 5.3.2-1
# NR Band n258: 100MHz channel, 30kHz SCS, guard band 1.5MHz per side

# ✅ 正確: 官方常數
boltzmann_constant = 1.380649e-23
# SOURCE: CODATA 2018 (NIST)
# Reference: https://physics.nist.gov/cgi-bin/cuu/Value?k
# Unit: J/K (Joules per Kelvin)
```

### ❌ 缺少 SOURCE 標註

```python
# ❌ 違規: 無來源標註
latitude = 25.0  # 台北大約北緯25度 (估計值，違規)

# ❌ 違規: 模糊來源
guard_band = 1500.0  # 典型值 (違規)

# ❌ 違規: 無標註
k = 1.38e-23  # Boltzmann constant (違規)
```

---

## 5️⃣ 禁用詞彙替代方案

### ⚠️ 嚴禁用詞

| ❌ 禁止 | ✅ 替代 |
|---------|---------|
| estimated (估計) | measured (實測), calculated (計算) |
| assumed (假設) | specified (指定), configured (配置) |
| approximately (約) | precise value (精確值), exact (精確) |
| conservative estimate (保守估算) | measured lower bound (實測下限) |
| simplified (簡化) | complete implementation (完整實現) |

### 範例

```python
# ❌ 違規
estimated_rsrp = -95.0  # 保守估算

# ✅ 正確
calculated_rsrp = self._calculate_rsrp_3gpp_standard(...)
# SOURCE: 3GPP TS 38.214 complete calculation

# ❌ 違規
if elevation < 10.0:  # 假設低仰角門檻

# ✅ 正確
if elevation < self.low_elevation_threshold:
    # SOURCE: ITU-R P.618-13 Section 2.2.1
    # Low elevation angle defined as < 10° for scintillation effects
```

---

## 6️⃣ 錯誤恢復模板

### ✅ 正確: Fail-Fast (拋出錯誤)

```python
def calculate_signal_quality(self, satellite_data: Dict) -> Dict:
    """計算信號品質"""
    try:
        rsrp = self._calculate_rsrp_3gpp(satellite_data)
        rsrq = self._calculate_rsrq_3gpp(satellite_data, rsrp)
        sinr = self._calculate_sinr_3gpp(satellite_data, rsrp)

        return {'rsrp': rsrp, 'rsrq': rsrq, 'sinr': sinr}

    except Exception as e:
        # ✅ 正確: Fail-Fast，不使用估算值
        error_msg = (
            f"信號品質計算失敗: {e}\n"
            f"Grade A 標準禁止使用估算值回退\n"
            f"請檢查輸入數據完整性"
        )
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)  # ✅ 拋出錯誤，不返回估算值
```

### ❌ 錯誤: 使用估算值恢復

```python
# ❌ 違規: 錯誤時使用估算值
try:
    rsrp = self._calculate_rsrp(...)
except Exception:
    rsrp = -100.0  # ❌ 使用估算值 (違規)

# ❌ 違規: 使用保守估算
if calculation_failed:
    return {
        'rsrp': -120.0,  # ❌ 保守估算 (違規)
        'rsrq': -15.0,   # ❌ 保守估算 (違規)
    }
```

---

## 7️⃣ 函數文檔字符串模板

```python
def calculate_doppler_shift(
    self,
    velocity_km_per_s: List[float],
    satellite_position_km: List[float],
    observer_position_km: List[float],
    frequency_hz: float
) -> Dict[str, float]:
    """
    計算都卜勒頻移 (使用 Stage 2 實際速度數據)

    ⚠️ CRITICAL 要求:
    - ✅ 必須使用 Stage 2 實際速度數據 (velocity_km_per_s)
    - ❌ 禁止使用假設速度、平均速度、估算值
    - ✅ 視線方向速度使用向量點積計算 (v · r̂)
    - ✅ 高速情況 (v>0.1c) 使用相對論都卜勒公式

    學術依據:
    - Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
    - Einstein, A. (1905). On the Electrodynamics of Moving Bodies
    - 非相對論近似僅適用於 v << c (v < 0.1c)

    Args:
        velocity_km_per_s: 衛星速度向量 [vx, vy, vz] (km/s)
            SOURCE: Stage 2 TEME coordinate system
        satellite_position_km: 衛星位置 [x, y, z] (km)
        observer_position_km: 觀測者位置 [x, y, z] (km)
        frequency_hz: 發射頻率 (Hz)

    Returns:
        doppler_data: 都卜勒效應數據
            - doppler_shift_hz: 都卜勒頻移 (Hz)
            - radial_velocity_ms: 視線方向速度 (m/s)
            - calculation_method: 'relativistic' or 'classical'

    Raises:
        ValueError: 當速度數據缺失時（禁止使用估算值）
    """
```

---

## 8️⃣ 模組開頭強制聲明

### 所有新建算法模組必須包含此聲明

```python
#!/usr/bin/env python3
"""
模組名稱: XXX 計算器

⚠️⚠️⚠️ CRITICAL - Grade A 學術標準強制聲明 ⚠️⚠️⚠️

本模組遵循嚴格的學術合規性標準，禁止以下行為:

❌ 禁止事項:
1. 簡化算法 - 必須使用完整標準實現
2. 估計值/假設值 - 所有數值必須有明確來源
3. 硬編碼係數 - 所有參數必須有 SOURCE 標註
4. 預設值 - 系統參數必須從配置獲取
5. 模擬數據 - 禁止使用 random/numpy 生成數據

✅ 必須遵守:
1. 官方標準 - ITU-R, 3GPP, IEEE, NASA JPL 精確規範
2. 實測數據 - GPS測量、官方數據庫、設備規格
3. 學術引用 - 算法必須引用原始論文
4. SOURCE 標註 - 所有數值必須標註來源

參考文檔:
- docs/ACADEMIC_STANDARDS.md (全局標準)
- docs/stages/stageX-specification.md (階段特定要求)

學術標準: Grade A
審查頻率: 每次 commit 前必須自檢
"""
```

---

## 9️⃣ 快速自檢清單 (註解在測試文件中)

```python
# test_xxx.py

"""
學術合規性測試

自檢清單 (提交前檢查):
□ 所有算法使用完整標準實現 (無簡化)
□ 所有數值有 SOURCE 標註
□ 無使用禁用詞彙 (estimated, assumed, approximately)
□ 無預設值 (系統參數必須配置)
□ 物理常數從 PhysicsConstants 導入
□ 門檻值從 SignalConstants 導入
□ 所有硬編碼係數有學術引用
□ 錯誤時 Fail-Fast (不使用估算值)

參考: docs/ACADEMIC_STANDARDS.md
"""

def test_algorithm_completeness():
    """測試算法完整性 (非簡化版本)"""
    # 範例: 驗證 ITU-R P.676 使用 44+35 條譜線
    assert len(model.OXYGEN_LINES) == 44, "必須使用完整44條氧氣譜線"
    assert len(model.WATER_VAPOR_LINES) == 35, "必須使用完整35條水蒸氣譜線"
```

---

## 🎯 總結

**核心原則**:
1. **文檔先行** - 算法前先看模板
2. **SOURCE 必須** - 所有數值必須標註
3. **禁用詞零容忍** - estimated/assumed 絕對禁止
4. **Fail-Fast** - 錯誤時拋出異常，不用估算值

**檢查順序**:
1. 複製對應模板
2. 填入完整 SOURCE 標註
3. 檢查無禁用詞彙
4. 運行合規性檢查工具
5. 通過測試後提交

**違規後果**:
- CRITICAL 違規: 必須修正才能提交
- WARNING 違規: 建議修正

**最後更新**: 2025-10-02
**維護者**: 專案團隊
