# 🎓 學術合規性標準指南（全局規範）

**適用範圍**：所有六個階段的代碼開發

---

## 📋 核心原則

### ❌ 絕對禁止

1. **估計值/假設值**
   - 禁用詞：估計、假設、約、大概、大約、猜測、模擬
   - 禁用詞（英文）：estimated, assumed, approximately, mock, fake

2. **簡化算法**
   - 不使用簡化版、基礎版、示範版算法
   - 必須使用完整的學術標準算法

3. **模擬數據**
   - 不使用 `random.normal()`, `np.random()` 生成數據
   - 不使用 mock/fake 數據

4. **硬編碼參數**
   - 所有數值必須有明確來源
   - 所有門檻必須有學術依據

### ✅ 必須遵守

1. **官方標準**
   - 使用 ITU-R、3GPP、IEEE、NASA JPL 精確規範
   - 引用具體的標準文檔編號和章節

2. **實測數據**
   - 使用實際測量值（GPS、DGPS、官方數據庫）
   - 記錄測量日期、方法、精度

3. **學術引用**
   - 算法實現必須引用原始論文
   - 標註作者、年份、期刊/會議

4. **可追溯性**
   - 所有參數可追溯到官方來源
   - 能通過同行審查

---

## 🔍 各階段檢查重點

### 階段一：軌道計算
- [ ] TLE 數據來自 Space-Track.org（官方）
- [ ] SGP4 算法符合 Vallado 2013 標準
- [ ] 時間系統轉換使用 IERS 官方數據
- [ ] 無硬編碼軌道參數

### 階段二：軌道運算
- [ ] 使用精確的橢圓軌道方程
- [ ] 攝動計算符合 JPL DE440/DE441
- [ ] 數值積分方法有學術依據
- [ ] 無簡化的二體問題假設

### 階段三：座標轉換
- [ ] ITRF/GCRF 轉換符合 IAU SOFA
- [ ] 使用 Skyfield 官方引擎
- [ ] WGS84 參數來自 NIMA TR8350.2
- [ ] 極移/章動數據來自 IERS

### 階段四：鏈路可行性
- [ ] 地面站座標為實測值（GPS/DGPS）
- [ ] 可見性計算使用精確幾何模型
- [ ] 鏈路預算符合 ITU-R 標準
- [ ] 無硬編碼仰角/距離門檻（需引用依據）

### 階段五：訊號分析
- [ ] 訊號模型符合 3GPP TS 38.214
- [ ] 大氣衰減使用 ITU-R P.676 模型
- [ ] 都卜勒計算基於精確軌道速度
- [ ] 無簡化的自由空間損耗公式

### 階段六：研究優化
- [ ] 優化算法有學術引用（如 Set Cover, Greedy）
- [ ] 權重參數有理論依據
- [ ] GPP 事件定義符合 3GPP 規範
- [ ] 無硬編碼啟發式權重

---

## 📝 標註規範

### 數值來源標註
```python
# ✅ 正確示範
altitude_m = 36.0  # SOURCE: GPS Survey 2025-10-02, WGS84, ±1.0m
freq_hz = 2.4e9    # SOURCE: 3GPP TS 38.104 Table 5.2-1 (n41 band)
```

### 算法引用標註
```python
# ✅ 正確示範
def greedy_set_cover(universe, subsets):
    """
    標準貪心 Set Cover 算法

    依據:
    - Chvátal, V. (1979). "A greedy heuristic for the set-covering problem"
      Mathematical Programming, 4(1), 233-235.
    - 近似比: ln(n) (Johnson 1974)
    """
```

### 門檻/參數依據
```python
# ✅ 正確示範
EPOCH_DIVERSITY_THRESHOLD = 0.3  # 依據: Kelso 2007, NORAD TLE 更新頻率統計
TLE_VALIDITY_DAYS = 7            # 依據: Vallado 2013, SGP4 精度範圍 ±3-7 天
```

---

## 🛠️ 手動檢查工具

### 全局檢查（所有階段）
```bash
# 檢查整個 src/ 目錄
make compliance

# 或直接使用工具
python tools/academic_compliance_checker.py src/
```

### 分階段檢查
```bash
# 階段一
python tools/academic_compliance_checker.py src/stages/stage1_orbital_calculation/

# 階段二
python tools/academic_compliance_checker.py src/stages/stage2_orbital_computing/

# 階段三
python tools/academic_compliance_checker.py src/stages/stage3_coordinate_transformation/

# 階段四
python tools/academic_compliance_checker.py src/stages/stage4_link_feasibility/

# 階段五
python tools/academic_compliance_checker.py src/stages/stage5_signal_analysis/

# 階段六
python tools/academic_compliance_checker.py src/stages/stage6_research_optimization/
```

### 快速關鍵字掃描
```bash
# 搜尋禁用詞
grep -r "估計\|假設\|約\|大概\|模擬" src/ --include="*.py"
grep -r "estimated\|assumed\|mock\|fake" src/ --include="*.py"
```

---

## 📚 常見違規與修正

### 違規類型 1：地理座標估計值
```python
# ❌ 違規
latitude = 25.0  # 台北大約在北緯 25 度

# ✅ 修正
latitude = 24.94388888888889  # SOURCE: GPS Survey 2025-10-02
                               # 24°56'38"N, WGS84, DGPS, ±0.5m
```

### 違規類型 2：硬編碼權重
```python
# ❌ 違規
score = diversity * 10 + coverage * 5 + stability * 1

# ✅ 修正（使用標準算法）
# 依據: Chvátal (1979) Set Cover 貪心算法
contribution = count_uncovered_elements(candidate)
score = contribution  # 標準貢獻度計算
```

### 違規類型 3：假設性門檻
```python
# ❌ 違規
if epoch_diversity < 0.5:  # 假設 50% 是合理門檻
    raise ValueError()

# ✅ 修正
# 依據: Kelso (2007), NORAD TLE 更新頻率統計
DIVERSITY_THRESHOLD = 0.3  # 基於 LEO 星座 TLE 更新率
if epoch_diversity < DIVERSITY_THRESHOLD:
    raise ValueError()
```

### 違規類型 4：簡化模型
```python
# ❌ 違規
def simplified_doppler(velocity):
    return velocity * 1000  # 簡化計算

# ✅ 修正
def doppler_shift(velocity_vector, los_vector, freq_hz):
    """
    精確都卜勒頻移計算

    依據:
    - ITU-R Recommendation SM.1541 (2015)
    - 相對論修正: Einstein (1905)
    """
    v_radial = np.dot(velocity_vector, los_vector)
    doppler_hz = -freq_hz * v_radial / SPEED_OF_LIGHT
    return doppler_hz
```

---

## 🎯 檢查清單（使用前確認）

在提交代碼前，確認以下項目：

### 數據來源
- [ ] 所有地理座標是實測值（GPS/DGPS）
- [ ] 所有軌道數據來自官方 TLE
- [ ] 所有物理常數來自標準文檔
- [ ] 無 random/numpy 生成的數據

### 算法實現
- [ ] 所有算法有學術引用
- [ ] 使用完整實現（非簡化版）
- [ ] 數學模型符合標準規範
- [ ] 無啟發式硬編碼

### ⚠️ **算法完整性專項檢查**（新增）

#### ITU-R P.676 大氣衰減模型
- [ ] **氧氣吸收**: 必須使用 **44條譜線** (ITU-R P.676-13 Table 1)
  - ❌ 禁止: 12條、20條等簡化版本
  - ✅ 正確: 完整44條譜線參數表
- [ ] **水蒸氣吸收**: 必須使用 **35條譜線** (ITU-R P.676-13 Table 2)
  - ❌ 禁止: 28條、30條等簡化版本
  - ✅ 正確: 完整35條譜線參數表
- [ ] 路徑長度計算考慮**地球曲率** (低仰角 <5° 必須使用精確公式)
- [ ] 閃爍效應使用 ITU-R P.618-13 完整模型（非經驗係數）

#### 3GPP TS 38.214 信號品質計算
- [ ] RSRP 計算使用**單 RE 功率**定義 (3GPP TS 38.215 Section 5.1.1)
- [ ] RSRQ 計算使用 **N × RSRP / RSSI** 公式 (不是簡化的 RSRP/RSSI)
- [ ] SINR 計算包含**實際干擾估算** (不是固定值或忽略)
- [ ] 噪聲功率使用 **Johnson-Nyquist 公式** (k×T×B，CODATA 2018)

#### 都卜勒效應計算
- [ ] 必須使用 **Stage 2 實際速度數據** (velocity_km_per_s)
  - ❌ 禁止: 假設速度、平均速度、估算值
  - ✅ 正確: 從 Stage 2 提取的 TEME 速度向量
- [ ] 視線方向速度使用**向量點積**計算 (v · r̂)
- [ ] 高速情況 (v>0.1c) 使用**相對論都卜勒公式**

### 參數設定
- [ ] 所有門檻有理論依據
- [ ] 所有權重有學術來源
- [ ] 所有常數有標註來源
- [ ] 可追溯到官方文檔

### 🚫 **預設值使用限制**（新增）
- [ ] 系統參數（頻寬、噪聲係數等）**禁止使用預設值**
  - ❌ 錯誤: `self.config.get('noise_figure_db', 7.0)`
  - ✅ 正確: 必須在配置中提供，或拋出錯誤
- [ ] 門檻值（RSRP、RSRQ、SINR）必須從 **SignalConstants** 導入
  - ❌ 錯誤: `if rsrp >= -100:`
  - ✅ 正確: `if rsrp >= signal_consts.RSRP_FAIR:`
- [ ] 物理常數必須從 **PhysicsConstants** 導入
  - ❌ 錯誤: `c = 299792458.0  # 光速`
  - ✅ 正確: `c = PhysicsConstants().SPEED_OF_LIGHT`

### 🚨 **嚴禁用詞檢查**（新增）
程式碼中禁止出現以下用詞（註釋除外）：
- ❌ **估計**: estimated, estimate, estimation
- ❌ **假設**: assumed, assumption, suppose
- ❌ **約**: approximately, roughly, around
- ❌ **保守**: conservative estimate, conservative value
- ❌ **簡化**: simplified, basic, demo

**例外情況**（僅限這些場景可使用）：
- ✅ 引用他人論文標題: "Chvátal's approximation algorithm"
- ✅ 標準文檔名稱: "ITU-R approximate method"
- ✅ 錯誤訊息: `raise ValueError("禁止使用估算值")`

### 註釋標記
- [ ] 數值有 SOURCE: 標記
- [ ] 算法有依據: 標記
- [ ] 門檻有說明來源
- [ ] 精度有誤差範圍

---

## 🔄 持續改進

這份標準會隨著專案發展持續更新：

1. **發現新違規模式** → 添加到檢查清單
2. **標準更新** → 更新引用文檔版本
3. **工具改進** → 優化檢查器邏輯
4. **誤報修正** → 調整檢測規則

**最後更新**：2025-10-02
**維護者**：專案團隊
**審查頻率**：每次重大變更

---

## 📖 參考文獻

### 軌道力學
- Vallado, D. A. (2013). *Fundamentals of Astrodynamics and Applications*
- Kelso, T. S. (2007). *Validation of SGP4 and IS-GPS-200D*

### 座標系統
- IAU SOFA (2021). *Standards of Fundamental Astronomy*
- NIMA TR8350.2 (2000). *WGS84 Ellipsoid Parameters*

### 無線通訊
- 3GPP TS 38.104: NR Base Station Radio Transmission
- 3GPP TS 38.214: NR Physical Layer Procedures for Data
- ITU-R P.676: Attenuation by Atmospheric Gases

### 演算法理論
- Chvátal, V. (1979). Set-Covering Problem
- Johnson, D. S. (1974). Approximation Algorithms

---

**記住**：學術研究的嚴謹性不能依賴自覺，要系統化驗證。
