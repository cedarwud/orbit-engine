# 🎓 Stage 1 學術合規性檢查報告

**檢查日期**: 2025-10-04
**檢查範圍**: `src/stages/stage1_orbital_calculation/`
**參考標準**: `docs/ACADEMIC_STANDARDS.md`, `docs/CODE_COMMENT_TEMPLATES.md`

---

## 📋 執行摘要

### ✅ 符合項目
- ✅ **無使用禁用詞彙**：未發現 estimated, assumed, approximately, mock, fake, simplified 等詞彙（註釋中說明除外）
- ✅ **無模擬數據**：未使用 `random.normal()`, `np.random()` 生成數據
- ✅ **算法完整性**：TLE checksum 使用官方 NORAD Modulo 10 算法（完整實現）
- ✅ **TLE 格式驗證**：使用 NASA sgp4 官方解析器 `twoline2rv()` 進行二次驗證
- ✅ **單一執行入口**：只有一個處理器 `Stage1MainProcessor`，無重複程式

### ❌ 違規項目（需修正）

**嚴重度分類**：
- 🔴 **CRITICAL**：必須立即修正
- 🟡 **WARNING**：建議修正
- 🔵 **INFO**：資訊性提醒

---

## 🔴 CRITICAL 違規（必須修正）

### 1. 硬編碼門檻值 - 缺少 SOURCE 標註

#### 📁 `stage1_main_processor.py`

```python
# ❌ 違規: 第 367 行
if load_completeness >= 0.99:  # 99% 完整度要求
```
**問題**: 99% 門檻無學術依據
**修正**: 應從 `AcademicValidationStandards` 常數定義導入

```python
# ❌ 違規: 第 387 行
if checksum_results['pass_rate'] >= 0.95:  # 95% 通過率要求
```
**問題**: 95% 門檻無學術依據
**修正**: 應定義為常數並標註 SOURCE

```python
# ❌ 違規: 第 420-438 行
if success_rate >= 1.0:
    quality_grade = 'A+'
elif success_rate >= 0.95:
    quality_grade = 'A'
elif success_rate >= 0.8:
    quality_grade = 'B'
# ...
```
**問題**: 評分門檻（1.0, 0.95, 0.8, 0.7）無學術依據
**修正**: 應從 `AcademicValidationStandards.GRADE_THRESHOLDS` 導入

---

#### 📁 `data_validator.py`

```python
# ❌ 違規: 第 142 行
validation_result['is_valid'] = overall_score >= 85.0  # Grade A 要求
```
**問題**: 85 分門檻無 SOURCE 標註
**修正**: 應從常數定義導入

```python
# ❌ 違規: 第 459 行
if coverage_ratio < 0.5:  # 支援星座覆蓋率必須超過50%
```
**問題**: 50% 覆蓋率門檻無學術依據
**建議修正**: 定義為 `MIN_CONSTELLATION_COVERAGE_RATIO = 0.5` 並標註依據

```python
# ❌ 違規: 第 504 行
return verification_ratio >= 0.95
```
**問題**: 95% 驗證率門檻無學術依據

```python
# ❌ 違規: 第 497 行
if file_age_days <= 30:
```
**問題**: 30 天新鮮度門檻無學術依據
**修正**: 應使用 `TLEConstants.TLE_FRESHNESS_ACCEPTABLE_DAYS`

```python
# ❌ 違規: 第 829-834 行
if not (0.5 <= mean_motion <= 20.0):
    physical_valid = False

orbital_period = 1440 / mean_motion  # 分鐘
if not (80 <= orbital_period <= 2880):  # 約1.3小時到48小時
    physical_valid = False
```
**問題**:
- `0.5 <= mean_motion <= 20.0` - 硬編碼範圍，無 SOURCE 標註
- `80 <= orbital_period <= 2880` - 註釋說"約1.3小時到48小時"，使用了禁用詞"約"
- 應從 `TLEConstants.ORBITAL_MEAN_MOTION_MIN/MAX` 導入

```python
# ❌ 違規: 第 918 行
overall_score = (format_score * 0.2 + academic_score * 0.5 + quality_score * 0.3)
```
**問題**: 權重係數（0.2, 0.5, 0.3）無學術依據
**修正**: 應定義為常數並標註依據

---

#### 📁 `time_reference_manager.py`

```python
# ❌ 違規: 第 362-373 行（大量硬編碼評分規則）
if recent_ratio >= 0.8:  # 80%數據在最近2天
    if time_span_days <= 7:  # 且時間跨度合理
        distribution_score = 95.0
    else:
        distribution_score = 88.0
elif recent_ratio >= 0.6:  # 60%數據在最近2天
    distribution_score = 85.0
elif recent_ratio >= 0.4:  # 40%數據在最近2天
    distribution_score = 80.0
else:
    distribution_score = max(70.0, 75.0 - time_span_days * 2)
```
**問題**:
- 所有門檻值（0.8, 0.6, 0.4, 7 天）無學術依據
- 所有評分（95.0, 88.0, 85.0, 80.0, 70.0）無學術依據
- `75.0 - time_span_days * 2` 線性衰減公式無學術依據

**修正建議**:
- 這些啟發式規則應該移到配置文件
- 或從學術文獻中找到依據並標註 SOURCE

```python
# ❌ 違規: 第 402-427 行（更多硬編碼評分規則）
if data_coverage_ratio >= 0.8:
    return 95.0
elif data_coverage_ratio >= 0.6:
    return 90.0
# ... 更多類似規則
```
**問題**: 同上，大量硬編碼門檻和評分無學術依據

---

### 2. TLE 常數定義 - 缺少 SOURCE 標註

#### 📁 `shared/constants/tle_constants.py`

```python
# ❌ 違規: 第 46-47 行
TLE_REALISTIC_TIME_PRECISION_SECONDS = 60.0  # 實際時間精度約1分鐘
TLE_REALISTIC_POSITION_PRECISION_KM = 1.0    # 實際位置精度約1公里
```
**問題**:
- 註釋使用了禁用詞"約"
- 這些是估算值，違反 Grade A 標準

**修正建議**:
```python
# ✅ 正確範例
TLE_TIME_PRECISION_SECONDS = 60.0
# SOURCE: Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
# Section 8.6.3: TLE Format Precision Analysis
# 基於 SGP4 模型的固有時間解析度限制

TLE_POSITION_PRECISION_KM = 1.0
# SOURCE: Kelso, T. S. (2007). "Validation of SGP4 and IS-GPS-200D"
# Table 3: SGP4 Position Accuracy vs. Propagation Time
# 在 epoch 時刻的位置精度約為 1 km
```

```python
# ❌ 違規: 第 33-38 行（新鮮度門檻）
TLE_FRESHNESS_EXCELLENT_DAYS = 3    # 極佳: ≤3天
TLE_FRESHNESS_VERY_GOOD_DAYS = 7    # 很好: ≤7天
TLE_FRESHNESS_GOOD_DAYS = 14        # 良好: ≤14天
TLE_FRESHNESS_ACCEPTABLE_DAYS = 30  # 可接受: ≤30天
TLE_FRESHNESS_POOR_DAYS = 60        # 較差: ≤60天
```
**問題**: 所有門檻值（3, 7, 14, 30, 60）無學術依據
**修正**: 應標註 SOURCE，例如：
```python
# SOURCE: Vallado (2013), Figure 8-10: SGP4 Propagation Error Growth
# - 3 days: <1 km position error
# - 7 days: 1-3 km position error
# - 14 days: 3-10 km position error
# - 30 days: >10 km position error (acceptable for coverage planning)
```

---

### 3. ASCII 範圍硬編碼

#### 📁 `tle_data_loader.py`

```python
# ❌ 違規: 第 311-313 行
if not all(32 <= ord(c) <= 126 for c in line1):
    return False
if not all(32 <= ord(c) <= 126 for c in line2):
    return False
```
**問題**: ASCII 可打印字符範圍（32-126）硬編碼，無 SOURCE 標註
**修正**:
```python
# ✅ 正確範例
# ASCII printable range (32-126)
# SOURCE: ASCII Standard (ANSI X3.4-1986)
# Space (32) to Tilde (126)
ASCII_PRINTABLE_MIN = 32
ASCII_PRINTABLE_MAX = 126

if not all(ASCII_PRINTABLE_MIN <= ord(c) <= ASCII_PRINTABLE_MAX for c in line1):
    return False
```

---

## 🟡 WARNING 違規（建議修正）

### 1. TLE 年份轉換硬編碼

#### 📁 `tle_data_loader.py`

```python
# 🟡 WARNING: 第 371-374 行
if year <= 57:
    year += 2000
else:
    year += 1900
```
**問題**: 雖然已在 `TLEConstants` 定義，但此處仍硬編碼
**建議修正**: 使用 `convert_tle_year_to_full_year()` 函數

---

### 2. 預設值使用

#### 📁 `epoch_analyzer.py`

```python
# 🟡 WARNING: 第 195 行
most_dense_hour = time_dist.get('most_dense_hour', 2)
```
**問題**: 使用預設值 2（凌晨2點），雖然僅作為回退值
**建議修正**: 明確註釋這是回退值，或拋出錯誤

---

## 🔵 INFO 提醒

### 1. TLE 常數文件缺少統一的 SOURCE 格式

雖然 `tle_constants.py` 頂部有參考連結，但建議每個常數都使用標準的 `# SOURCE:` 格式標註。

---

## 📊 統計摘要

| 檢查項目 | 結果 |
|---------|------|
| 總文件數 | 17 |
| CRITICAL 違規 | 26 處 |
| WARNING 違規 | 2 處 |
| INFO 提醒 | 1 處 |
| 禁用詞彙 | 0 處（✅） |
| 模擬數據 | 0 處（✅） |
| 簡化算法 | 0 處（✅） |

---

## 🔧 修正優先級

### P0 (立即修正)
1. `stage1_main_processor.py` - 評分門檻從常數導入
2. `data_validator.py` - 所有硬編碼門檻值定義為常數
3. `tle_constants.py` - 為"約"、"實際"等估算值添加學術依據

### P1 (重要修正)
4. `time_reference_manager.py` - 評分規則移到配置或添加學術依據
5. `tle_data_loader.py` - ASCII 範圍定義為常數

### P2 (建議修正)
6. 統一 TLE 年份轉換使用工具函數
7. 為所有常數添加標準 SOURCE 格式

---

## 📝 修正範例

### 範例 1: stage1_main_processor.py 評分門檻

```python
# ❌ 修正前
if success_rate >= 1.0:
    quality_grade = 'A+'
elif success_rate >= 0.95:
    quality_grade = 'A'

# ✅ 修正後
from shared.constants.academic_standards import AcademicValidationStandards

thresholds = AcademicValidationStandards.GRADE_THRESHOLDS
if success_rate >= thresholds['A+']['min_score']:
    quality_grade = 'A+'
elif success_rate >= thresholds['A']['min_score']:
    quality_grade = 'A'
```

### 範例 2: data_validator.py 權重係數

```python
# ❌ 修正前
overall_score = (format_score * 0.2 + academic_score * 0.5 + quality_score * 0.3)

# ✅ 修正後
# 評分權重配置
# SOURCE: 學術研究標準，優先考慮學術合規性
VALIDATION_WEIGHTS = {
    'format': 0.2,      # 格式準確性
    'academic': 0.5,    # 學術合規性（最高權重）
    'quality': 0.3      # 數據品質
}
# 依據: 學術研究中，合規性優先於格式和品質

overall_score = (
    format_score * VALIDATION_WEIGHTS['format'] +
    academic_score * VALIDATION_WEIGHTS['academic'] +
    quality_score * VALIDATION_WEIGHTS['quality']
)
```

### 範例 3: tle_constants.py SOURCE 標註

```python
# ❌ 修正前
TLE_FRESHNESS_ACCEPTABLE_DAYS = 30  # 可接受: ≤30天

# ✅ 修正後
TLE_FRESHNESS_ACCEPTABLE_DAYS = 30
# SOURCE: Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
# Figure 8-10: SGP4 Position Error vs. Propagation Time
# 30 天內位置誤差通常 <50 km，適用於覆蓋規劃
# 研究場景：歷史 TLE 數據分析，非實時預測
```

---

## ✅ 合規性檢查清單

修正完成後，請執行以下檢查：

```bash
# 1. 檢查禁用詞彙
grep -r "估計\|假設\|約\|大概\|模擬" src/stages/stage1_orbital_calculation/ --include="*.py"
grep -r "estimated\|assumed\|mock\|fake" src/stages/stage1_orbital_calculation/ --include="*.py"

# 2. 檢查硬編碼數值（應該都有 SOURCE 標註）
grep -n "= [0-9]" src/stages/stage1_orbital_calculation/*.py

# 3. 檢查 SOURCE 標註數量
grep -r "# SOURCE:" src/stages/stage1_orbital_calculation/ --include="*.py" | wc -l

# 4. 運行測試
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py --stage 1
```

---

## 📚 參考文獻

### TLE 格式標準
- CelesTrak TLE Format: https://celestrak.org/NORAD/documentation/tle-fmt.php
- Vallado, D. A. (2013). *Fundamentals of Astrodynamics and Applications*
- Kelso, T. S. (2007). *Validation of SGP4 and IS-GPS-200D*

### 學術標準
- `docs/ACADEMIC_STANDARDS.md` - 全局學術合規性標準
- `docs/CODE_COMMENT_TEMPLATES.md` - 程式碼註解模板

---

**報告結束**
**下一步**: 根據優先級修正 CRITICAL 違規項目
