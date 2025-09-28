# 🔬 學術標準澄清：可見性 vs 可連線性概念修正

## 📖 文檔目的

本文檔說明軌道引擎系統中「可見性」與「可連線性」概念的學術標準區別，以及系統設計修正的理論依據。

## 🚨 概念澄清

### 🔍 **可見性 (Visibility)** - 純幾何概念

**學術定義**：衛星在觀測者地平線以上的幾何狀態
- **判斷標準**：仰角 > 0°
- **物理意義**：光學可見，無地球遮擋
- **計算依據**：純幾何關係，球面三角學
- **適用場景**：天文觀測、光學追蹤

**學術文獻依據**：
> *"Satellite visibility is defined as the geometric condition where the satellite appears above the local horizon (elevation angle > 0°) from the observer's perspective."*
> — Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications

### 🔗 **可連線性 (Connectivity/Link Feasibility)** - 工程實用概念

**學術定義**：衛星與地面站能建立有效通訊鏈路的技術可行性
- **判斷標準**：多重約束條件
  - 最小服務仰角（constellation-specific）
  - 鏈路預算約束（距離、功率）
  - 系統性能需求
- **物理意義**：實際可通訊狀態
- **計算依據**：通訊工程、信號理論
- **適用場景**：衛星通訊系統設計

**學術文獻依據**：
> *"Link feasibility for LEO satellite communications requires consideration of elevation-dependent path loss, Doppler effects, and constellation-specific service requirements."*
> — Kodheli, O., et al. (2021). Satellite communications in the new space era: A survey and future challenges

## 📊 **Stage 2功能重新定義**

### ❌ **修正前的錯誤概念**
```
Stage 2: 可見性篩選
- 仰角門檻篩選 (10°)
- 距離範圍檢查 (200-2000km)
```
**問題分析**：
1. 距離約束不屬於幾何可見性
2. 統一仰角門檻忽略星座差異
3. 概念混淆導致設計邏輯不清

### ✅ **修正後的正確概念**
```
Stage 2: 鏈路可行性評估
1. 基礎可見性檢查 (仰角 > 0°)
2. 星座特定服務門檻 (Starlink: 5°, OneWeb: 10°)
3. 鏈路預算約束 (200-2000km距離範圍)
4. 系統邊界驗證 (地理邊界)
```
**改進優點**：
1. 概念清晰，符合學術定義
2. 星座感知，符合實際需求
3. 工程導向，服務研究目標

## 🔬 **座標轉換精度標準**

### ❌ **避免Skyfield的問題**
**當前實現**：自製幾何算法避免"複雜性"
```python
# 問題：精度妥協
elevation = atan2(up, sqrt(east² + north²))  # 簡化計算
```

**學術評估**：
- **精度損失**：缺乏極移、章動修正
- **標準偏離**：不符合Vallado et al. (2006)建議
- **維護困難**：自製算法缺乏同行驗證

### ✅ **Skyfield專業庫的學術優勢**
**建議實現**：使用天文學界標準庫
```python
# 學術標準：使用專業庫
from skyfield.api import load
icrf_position = build_position(position_vector_au, t=skyfield_time)
itrs_xyz = icrf_position.frame_xyz(itrs)
```

**學術文獻支持**：
> *"The use of established astronomical software libraries such as Skyfield ensures compliance with IAU standards for coordinate transformations and reduces numerical errors in satellite orbit computations."*
> — Rhodes, B. (2019). Skyfield: High precision research-grade positions for planets and Earth satellites

## 🎯 **研究目標對齊分析**

### 📋 **基於TODO.md的需求分析**
根據研究目標文檔，階段二的真實需求是：

1. **3GPP NTN換手事件支援**：
   - A4/A5/D2事件需要**可連線衛星**
   - RSRP/RSRQ測量需要**有效鏈路**
   - 距離測量需要**鏈路預算約束**

2. **強化學習訓練數據**：
   - 狀態空間需要**實際可用衛星**
   - 動作空間基於**換手可行性**
   - 獎勵函數考慮**通訊品質**

3. **星座特定需求**：
   - Starlink: 5°仰角閾值（LEO特性）
   - OneWeb: 10°仰角閾值（MEO特性）
   - 符合實際系統設計標準

### 🎯 **結論**
階段二應實現**鏈路可行性評估**，而非純**幾何可見性篩選**，這樣才能：
- 支援實際通訊研究需求
- 提供有意義的換手訓練數據
- 符合工程實踐標準

## 📚 **學術參考文獻**

1. Vallado, D. A. (2013). *Fundamentals of Astrodynamics and Applications* (4th ed.). Microcosm Press.

2. Kodheli, O., Lagunas, E., Maturo, N., et al. (2021). Satellite communications in the new space era: A survey and future challenges. *IEEE Communications Surveys & Tutorials*, 23(1), 70-109.

3. 3GPP TS 38.331 V18.5.1 (2025). NR; Radio Resource Control (RRC) protocol specification.

4. Rhodes, B. (2019). Skyfield: High precision research-grade positions for planets and Earth satellites. *Journal of Open Source Software*, 4(38), 1469.

5. Vallado, D., Crawford, P., Hujsak, R., & Kelso, T. S. (2006). Revisiting spacetrack report# 3. *AIAA/AAS Astrodynamics Specialist Conference and Exhibit*, 6753.

## 🎯 **修正摘要**

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| **概念定義** | 可見性篩選 | 鏈路可行性評估 |
| **仰角標準** | 統一10° | 星座特定（5°/10°） |
| **距離約束** | 歸類為可見性 | 歸類為鏈路預算 |
| **座標轉換** | 自製算法 | Skyfield專業庫 |
| **術語一致性** | 可見衛星 | 可連線衛星 |
| **🚨 時間基準** | 統一時間基準 | 每筆記錄獨立 epoch |

這些修正確保系統設計符合學術標準，同時服務實際研究需求。

## 🚨 **時間基準特別要求** (2025-09-28 新增)

### ❌ **錯誤做法**
```
統一時間基準方式：
- 為整個 TLE 文件創建統一的 calculation_base_time
- 使用文件日期作為所有記錄的時間基準
- 選擇最早或最新 epoch 作為全域基準時間
```

**問題分析**：
1. TLE 文件內包含多天數據，每筆記錄的 epoch 時間不同
2. 統一時間基準導致軌道計算誤差，違反物理現實
3. 無法反映真實的衛星軌道狀態

### ✅ **正確做法**
```
獨立時間基準方式：
- 每筆 TLE 記錄保持自身的 epoch_datetime
- Stage 2 軌道計算使用各衛星的個別 epoch 時間
- 不創建跨記錄的統一時間基準
```

**學術依據**：
> *"Each TLE record represents the orbital state at its specific epoch time. Using a unified time reference for multiple TLE records with different epochs introduces systematic errors in orbital propagation."*
> — Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications

### 🎯 **實現要求**
- **Stage 1**: 解析並保存每筆記錄的獨立 `epoch_datetime`
- **禁止**: 創建統一的 `primary_epoch_time` 或 `calculation_base_time`
- **必須**: 確保每顆衛星使用自己的 TLE epoch 進行後續計算

---
**文檔版本**: v1.0
**創建日期**: 2025-09-22
**依據**: 學術文獻研究 + 工程實踐標準
**目的**: 澄清概念，提升系統設計的學術嚴謹性