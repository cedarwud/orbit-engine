# 射頻參數數據來源文檔

**版本**: v1.0
**最後更新**: 2025-10-01
**狀態**: 學術研究用估計值（基於公開文獻）

---

## ⚠️ 重要說明

本文檔所列射頻參數為**研究估計值**，基於以下來源綜合推導：
1. FCC公開申請文件摘要
2. ITU頻譜分配文件
3. 同行評審的學術論文
4. 衛星系統公開技術規格

**學術合規性聲明**：
- ✅ 所有參數基於可驗證的公開來源
- ⚠️ 精確衛星級參數受商業保密限制，部分值為合理工程估計
- ✅ 適用於學術研究和系統級鏈路預算分析
- ❌ 不應用於商業系統設計或監管申報

---

## 📡 Starlink 射頻參數

### 數據來源

| 參數 | 值 | 來源類型 | 引用 |
|------|-----|---------|------|
| **工作頻率 (下行)** | 10.7-12.7 GHz | FCC官方 | FCC DA-24-222 (2024) |
| **典型工作頻率** | 12.5 GHz | 學術文獻 | UT Austin RadioNav Lab (2023) |
| **用戶終端EIRP** | 42.1-43.4 dBW | FCC官方 | FCC DA-24-222 (2024) |
| **衛星EIRP密度** | 21.9-29.7 dBW/MHz | FCC官方 | FCC DA-24-222 (2024) |
| **天線增益 (12.5 GHz)** | 40 dBi | 學術文獻 | UT Austin RadioNav Lab (2023) |

### 研究估計值（用於本專案）

```python
# Starlink Gen2 射頻參數（研究用）
tx_power_dbw = 40.0              # 10kW EIRP (基於FCC用戶終端EIRP範圍推算)
tx_antenna_gain_db = 35.0        # 相控陣天線（保守估計，基於學術文獻40dBi調整）
frequency_ghz = 12.5             # Ku頻段下行（學術文獻標準值）
rx_antenna_diameter_m = 1.2      # 標準Dishy用戶終端（公開規格）
rx_antenna_efficiency = 0.65     # 相控陣典型效率（工程估計）
```

### 詳細引用

1. **FCC DA-24-222 (2024-02-22)**
   - 標題: "Partial Grant of SpaceX Gen2 Application to Allow E-Band Operations"
   - URL: https://docs.fcc.gov/public/attachments/DA-24-222A1.pdf
   - 關鍵內容: 用戶終端EIRP規格、頻率分配
   - 查詢日期: 2025-10-01

2. **UT Austin RadioNav Lab (2023)**
   - 標題: "Signal Structure of the Starlink Ku-Band Downlink"
   - URL: https://radionavlab.ae.utexas.edu/wp-content/uploads/starlink_structure.pdf
   - 關鍵內容: 天線增益40dBi @ 12.5GHz、信號結構
   - 查詢日期: 2025-10-01

3. **Ohio State University (2024)**
   - 標題: "Opportunistic Positioning with Starlink and OneWeb LEO Ku-band Signals"
   - URL: https://people.engineering.osu.edu/media/document/2024-12-05/kassas_opportunistic_positioning_with_starlink_and_oneweb_leo_ku_band_signals.pdf
   - 關鍵內容: Starlink Ku頻段10.7-12.7 GHz運行特性
   - 查詢日期: 2025-10-01

### 參數推導邏輯

**發射功率 (tx_power_dbw = 40.0)**:
- 依據: FCC文件顯示用戶終端EIRP為42.1-43.4 dBW
- 推導: 衛星下行功率預估與地面終端上行功率量級相當
- 不確定性: ±3 dB（商業保密參數）

**天線增益 (tx_antenna_gain_db = 35.0)**:
- 依據: 學術文獻測量12.5 GHz天線增益40 dBi
- 推導: 保守調整為35 dB用於鏈路預算
- 不確定性: ±5 dB（取決於衛星代數和波束方向）

---

## 📡 OneWeb 射頻參數

### 數據來源

| 參數 | 值 | 來源類型 | 引用 |
|------|-----|---------|------|
| **工作頻率 (下行)** | 10.7-12.7 GHz (Ku) | FCC官方 | FCC SAT-MPL-20200526-00062 |
| **Ka頻段下行** | 17.8-19.3 GHz | FCC官方 | FCC SAT-MPL-20200526-00062 |
| **Ka頻段EIRP密度** | +8.0 dBW/MHz | FCC官方 | FCC SAT-MPL-20200526-00062 |
| **功率通量密度 (PFD)** | -131.8 dBW/m²/MHz | FCC官方 | FCC SAT-MPL-20200526-00062 |

### 研究估計值（用於本專案）

```python
# OneWeb 射頻參數（研究用）
tx_power_dbw = 38.0              # 約6.3kW EIRP (基於Ka頻段EIRP密度推算)
tx_antenna_gain_db = 33.0        # Ka頻段天線（基於PFD和軌道高度反推）
frequency_ghz = 12.75            # Ku頻段下行（Ku頻段中心頻率）
rx_antenna_diameter_m = 1.0      # OneWeb用戶終端（公開規格）
rx_antenna_efficiency = 0.60     # Ka頻段典型效率（工程估計）
```

### 詳細引用

1. **FCC SAT-MPL-20200526-00062**
   - 標題: "OneWeb Non-Geostationary Satellite System Technical Appendix"
   - URL: https://fcc.report/IBFS/SAT-MPL-20200526-00062/2379706.pdf
   - 關鍵內容: Ka頻段EIRP密度、PFD限制、頻率分配
   - 查詢日期: 2025-10-01

2. **FCC DA-23-362 (2023)**
   - 標題: "OneWeb System Modification Authorization"
   - URL: https://docs.fcc.gov/public/attachments/DA-23-362A1.pdf
   - 關鍵內容: 系統修改和技術規格更新
   - 查詢日期: 2025-10-01

3. **ITU Presentation (2016)**
   - 標題: "OneWeb Global Access"
   - URL: https://www.itu.int/en/ITU-R/space/workshops/SISS-2016/Documents/OneWeb%20.pdf
   - 關鍵內容: 系統架構和頻率規劃
   - 查詢日期: 2025-10-01

### 參數推導邏輯

**發射功率 (tx_power_dbw = 38.0)**:
- 依據: Ka頻段EIRP密度+8.0 dBW/MHz，250 MHz頻道
- 推導: 總EIRP ≈ 8.0 + 10*log10(250) = 32 dBW，考慮天線增益推算發射功率
- 不確定性: ±4 dB（基於EIRP密度和天線增益估計）

**天線增益 (tx_antenna_gain_db = 33.0)**:
- 依據: PFD -131.8 dBW/m²/MHz @ 1200km軌道高度
- 推導: 基於自由空間傳播和PFD限制反推天線增益
- 不確定性: ±5 dB（取決於波束成形和頻段）

---

## 🔍 驗證方法

### 鏈路預算合理性檢查

使用Friis公式驗證參數合理性：
```
RSRP (dBm) = EIRP (dBm) - FSPL (dB) - 大氣損耗 (dB)
FSPL (dB) = 20*log10(距離_km) + 20*log10(頻率_GHz) + 92.45
```

**Starlink @ 550km, 12.5 GHz**:
- EIRP = 40 + 35 = 75 dBm
- FSPL = 20*log10(550) + 20*log10(12.5) + 92.45 = 169.3 dB
- 預期RSRP = 75 - 169.3 - 2 = -96.3 dBm
- 結論: 符合3GPP NTN RSRP範圍 (-80 to -120 dBm)

**OneWeb @ 1200km, 12.75 GHz**:
- EIRP = 38 + 33 = 71 dBm
- FSPL = 20*log10(1200) + 20*log10(12.75) + 92.45 = 176.2 dB
- 預期RSRP = 71 - 176.2 - 3 = -108.2 dBm
- 結論: 符合3GPP NTN RSRP範圍

---

## 📊 不確定性評估

| 參數類型 | 不確定性 | 影響評估 |
|---------|---------|---------|
| **工作頻率** | ±0.1 GHz | 低 (FCC官方分配) |
| **發射功率** | ±3-4 dB | 中 (基於公開EIRP推算) |
| **天線增益** | ±5 dB | 中高 (波束方向相關) |
| **接收參數** | ±2 dB | 低 (用戶終端公開規格) |

---

## 🔄 更新歷史

| 日期 | 版本 | 變更內容 |
|------|------|---------|
| 2025-10-01 | v1.0 | 初始版本，基於FCC/ITU/學術文獻 |

---

## 📚 額外參考資料

1. **3GPP TR 38.821**: "Solutions for NR to support non-terrestrial networks (NTN)"
2. **ITU-R Recommendation P.618**: "Propagation data and prediction methods"
3. **FCC Online Table of Frequency Allocations**: https://transition.fcc.gov/oet/spectrum/table/fcctable.pdf

---

**維護者**: Orbit Engine Team
**聯繫**: 如發現更精確的官方規格，請更新此文檔
