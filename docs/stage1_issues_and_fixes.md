# 🔧 Stage 1 深度檢查問題與修復計劃

**文檔創建日期**: 2025-09-30
**檢查範圍**: Stage 1 TLE 數據載入層
**檢查標準**: 學術嚴謹性、NORAD/NASA 官方規範、研究目標對齊
**總體評分**: B+ (83/100)

---

## 📊 **檢查摘要**

| 類別 | 評分 | 問題數 | 狀態 |
|------|------|--------|------|
| **數據來源** | A+ | 0 | ✅ 真實 TLE 數據 |
| **核心算法** | A+ | 0 | ✅ 官方標準算法 |
| **時間處理** | A+ | 0 | ✅ 獨立 epoch 時間 |
| **常數管理** | A | 0 | ✅ 集中管理 |
| **硬編碼問題** | C | 3 | ❌ 需修復 |
| **學術合規** | B+ | 1 | ⚠️ 需改進 |

**發現問題總數**: 4 個
**P0 (必須修復)**: 3 個
**P1 (建議修復)**: 1 個

---

## 🚨 **P0 級別問題（必須立即修復）**

### **問題 P0-1: 缺少星座配置元數據**

**嚴重性**: 🔴 **Critical**
**影響範圍**: Stage 2, Stage 4
**學術影響**: 無法支援星座分離計算（違反 final.md 要求）

#### **問題描述**

**當前狀態**:
```python
# src/stages/stage1_orbital_calculation/stage1_main_processor.py Line 149-208
def _integrate_results(self, satellites_data, validation_result, time_metadata, start_time):
    metadata = {
        'total_satellites': len(satellites_data),
        'time_base_source': 'individual_tle_epochs',
        # ❌ 缺少星座配置資訊
    }
```

**違反要求**:
- final.md 要求: "⚠️ 星座特定軌道週期 - 必須分別計算各星座的完整軌道週期"
- Starlink: 90-95分鐘軌道週期
- OneWeb: 109-115分鐘軌道週期
- Stage 2 需要此資訊才能正確執行星座分離計算

#### **修復方案**

**文件**: `src/stages/stage1_orbital_calculation/stage1_main_processor.py`
**位置**: `_integrate_results()` 方法，Line 189 之後

**新增代碼**:
```python
# 添加星座配置元數據（支援 Stage 2/4 星座分離計算）
metadata['constellation_configs'] = {
    'starlink': {
        'orbital_period_range_minutes': [90, 95],
        'typical_altitude_km': 550,
        'service_elevation_threshold_deg': 5.0,
        'expected_visible_satellites': [10, 15],
        'candidate_pool_size': [200, 500],
        'orbital_characteristics': 'LEO_low'
    },
    'oneweb': {
        'orbital_period_range_minutes': [109, 115],
        'typical_altitude_km': 1200,
        'service_elevation_threshold_deg': 10.0,
        'expected_visible_satellites': [3, 6],
        'candidate_pool_size': [50, 100],
        'orbital_characteristics': 'LEO_high'
    }
}

# 添加研究配置（NTPU 位置與研究目標）
metadata['research_configuration'] = {
    'observation_location': {
        'name': 'NTPU',
        'latitude_deg': 24.9442,
        'longitude_deg': 121.3714,
        'altitude_m': 0,
        'coordinates': "24°56'39\"N 121°22'17\"E"
    },
    'analysis_method': 'offline_historical_tle',
    'computation_type': 'full_orbital_period_analysis',
    'research_goals': [
        'dynamic_satellite_pool_planning',
        'time_space_staggered_coverage',
        '3gpp_ntn_handover_events',
        'reinforcement_learning_training'
    ]
}

# 添加星座統計
metadata['constellation_statistics'] = {
    'starlink': {
        'total_loaded': len([s for s in satellites_data if s['constellation'] == 'starlink']),
        'data_source': 'Space-Track.org TLE',
        'latest_epoch': max([s.get('epoch_datetime', '') for s in satellites_data if s['constellation'] == 'starlink']) if any(s['constellation'] == 'starlink' for s in satellites_data) else None
    },
    'oneweb': {
        'total_loaded': len([s for s in satellites_data if s['constellation'] == 'oneweb']),
        'data_source': 'Space-Track.org TLE',
        'latest_epoch': max([s.get('epoch_datetime', '') for s in satellites_data if s['constellation'] == 'oneweb']) if any(s['constellation'] == 'oneweb' for s in satellites_data) else None
    }
}
```

**學術依據**:
- final.md: "星座特定軌道週期" 明確要求
- academic_standards_clarification.md: "星座分離計算"

**驗證方法**:
```python
# 執行後檢查
result = processor.execute()
assert 'constellation_configs' in result.data['metadata']
assert result.data['metadata']['constellation_configs']['starlink']['orbital_period_range_minutes'] == [90, 95]
```

---

### **問題 P0-2: 寬鬆的 TLE 格式驗證**

**嚴重性**: 🔴 **Critical - 學術合規**
**影響範圍**: 數據品質保證
**學術影響**: 違反學術嚴謹性，可能接受無效 TLE 數據

#### **問題描述**

**當前狀態**:
```python
# src/stages/stage1_orbital_calculation/tle_data_loader.py Line 253-270
def _validate_tle_format(self, line1: str, line2: str) -> bool:
    """基本TLE格式驗證 - 寬鬆版本用於開發測試"""  # ❌ 不符合學術標準

    # 檢查最小長度 (允許稍短的測試數據)
    if len(line1) < 60 or len(line2) < 60:  # ❌ 應該是 ==69
        return False

    # 檢查行首
    if line1[0] != '1' or line2[0] != '2':
        return False

    # 檢查NORAD ID一致性 (允許更寬鬆的格式)
    if len(line1) >= 7 and len(line2) >= 7:
        norad_id1 = line1[2:7].strip()
        norad_id2 = line2[2:7].strip()
        return norad_id1 == norad_id2

    return True  # ❌ 如果長度不夠，暫時通過
```

**問題分析**:
1. 允許長度 < 69 的 TLE（標準應該正好 69 字符）
2. 註釋明確說「寬鬆版本」，違反學術嚴謹性
3. 長度不夠時「暫時通過」，不符合 Grade A 標準
4. 沒有執行 checksum 驗證

**違反標準**:
- TLEConstants.TLE_LINE_LENGTH = 69（官方標準）
- final.md: "真實軌道動力學基礎的學術研究數據"

#### **修復方案**

**文件**: `src/stages/stage1_orbital_calculation/tle_data_loader.py`
**位置**: Line 253-270

**完全替換為**:
```python
def _validate_tle_format(self, line1: str, line2: str) -> bool:
    """
    嚴格 TLE 格式驗證 - 符合 NORAD/NASA 官方標準

    基於:
    - NORAD TLE 格式規範（69字符標準）
    - CelesTrak 官方文檔
    - Grade A 學術標準要求

    Returns:
        bool: True 表示完全符合官方標準
    """
    from shared.constants.tle_constants import TLEConstants

    # 1. 嚴格長度檢查（官方標準：必須正好 69 字符）
    if len(line1) != TLEConstants.TLE_LINE_LENGTH or len(line2) != TLEConstants.TLE_LINE_LENGTH:
        self.logger.debug(f"TLE長度不符: line1={len(line1)}, line2={len(line2)} (標準=69)")
        return False

    # 2. 行號檢查（Line 1 開頭必須是 '1'，Line 2 必須是 '2'）
    if line1[0] != '1' or line2[0] != '2':
        self.logger.debug(f"TLE行號錯誤: line1[0]={line1[0]}, line2[0]={line2[0]}")
        return False

    # 3. NORAD ID 一致性檢查（兩行必須有相同的衛星ID）
    try:
        norad_id1 = line1[2:7].strip()
        norad_id2 = line2[2:7].strip()
        if norad_id1 != norad_id2:
            self.logger.debug(f"NORAD ID不一致: {norad_id1} vs {norad_id2}")
            return False
    except (IndexError, ValueError) as e:
        self.logger.debug(f"NORAD ID提取失敗: {e}")
        return False

    # 4. Checksum 驗證（官方 Modulo 10 算法）
    try:
        checksum1_expected = int(line1[68])
        checksum2_expected = int(line2[68])

        checksum1_calculated = self._calculate_checksum(line1[:68])
        checksum2_calculated = self._calculate_checksum(line2[:68])

        if checksum1_calculated != checksum1_expected:
            self.logger.debug(f"Line 1 checksum錯誤: 期望={checksum1_expected}, 計算={checksum1_calculated}")
            return False

        if checksum2_calculated != checksum2_expected:
            self.logger.debug(f"Line 2 checksum錯誤: 期望={checksum2_expected}, 計算={checksum2_calculated}")
            return False

    except (IndexError, ValueError) as e:
        self.logger.debug(f"Checksum驗證失敗: {e}")
        return False

    # 5. 字符有效性檢查（確保可打印 ASCII）
    if not all(32 <= ord(c) <= 126 for c in line1) or not all(32 <= ord(c) <= 126 for c in line2):
        self.logger.debug("TLE包含非ASCII字符")
        return False

    return True

def _calculate_checksum(self, line: str) -> int:
    """
    計算 TLE checksum（官方 Modulo 10 算法）

    官方規範:
    - 數字 0-9: 加上該數字值
    - 正號 '+': 算作 1
    - 負號 '-': 算作 1
    - 其他字符: 忽略（字母、空格、句點等）

    參考: https://celestrak.org/NORAD/documentation/tle-fmt.php
    """
    checksum = 0
    for char in line:
        if char.isdigit():
            checksum += int(char)
        elif char in ('+', '-'):
            checksum += 1
    return checksum % 10
```

**學術依據**:
- NORAD/NASA TLE 格式官方規範
- CelesTrak 官方文檔
- Grade A 學術標準

**驗證方法**:
```bash
# 測試嚴格驗證
python3 -c "
from src.stages.stage1_orbital_calculation.tle_data_loader import TLEDataLoader
loader = TLEDataLoader()

# 測試標準 TLE (應該通過)
line1 = '1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927'
line2 = '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537'
assert loader._validate_tle_format(line1, line2) == True

# 測試錯誤長度 (應該失敗)
assert loader._validate_tle_format(line1[:60], line2[:60]) == False
print('✅ 嚴格驗證測試通過')
"
```

---

### **問題 P0-3: 硬編碼星座列表**

**嚴重性**: 🔴 **Critical - 擴展性**
**影響範圍**: 系統擴展性
**學術影響**: 無法支援多星座研究（違反開放封閉原則）

#### **問題描述**

**當前狀態**:
```python
# src/stages/stage1_orbital_calculation/tle_data_loader.py Line 58
def scan_tle_data(self) -> Dict[str, Any]:
    # 掃描已知的星座目錄
    for constellation in ['starlink', 'oneweb']:  # ❌ 硬編碼
        constellation_result = self._scan_constellation(constellation)
```

**其他硬編碼位置**:
- Line 384: `for constellation in ['starlink', 'oneweb']:`（health_check 方法）
- Line 146: `if constellation.lower() == 'starlink':`（採樣邏輯）

**問題分析**:
1. 不支援動態添加新星座（如 Kuiper, Telesat）
2. 違反開放封閉原則（對擴展開放，對修改封閉）
3. 星座特定配置散落在代碼中

#### **修復方案**

**步驟 1: 創建星座配置常數**

**新建文件**: `src/shared/constants/constellation_constants.py`

```python
"""
星座配置常數
基於研究目標和軌道特性定義
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ConstellationConfig:
    """星座配置數據類"""
    name: str
    display_name: str

    # 軌道特性（基於 final.md 研究需求）
    orbital_period_range_minutes: Tuple[int, int]
    typical_altitude_km: int
    orbital_characteristics: str  # 'LEO_low', 'LEO_high', 'MEO', 'GEO'

    # 服務特性（基於 3GPP NTN 標準）
    service_elevation_threshold_deg: float
    expected_visible_satellites: Tuple[int, int]
    candidate_pool_size: Tuple[int, int]

    # 數據來源
    data_source: str
    tle_directory: str

    # 採樣配置（用於開發/測試）
    sample_ratio: float = 0.1
    sample_max: int = 10


class ConstellationRegistry:
    """星座註冊表 - 集中管理所有支援的星座"""

    # 基於 final.md 的研究星座配置
    STARLINK = ConstellationConfig(
        name='starlink',
        display_name='Starlink',
        orbital_period_range_minutes=(90, 95),
        typical_altitude_km=550,
        orbital_characteristics='LEO_low',
        service_elevation_threshold_deg=5.0,
        expected_visible_satellites=(10, 15),
        candidate_pool_size=(200, 500),
        data_source='Space-Track.org',
        tle_directory='starlink/tle',
        sample_ratio=0.5,
        sample_max=10
    )

    ONEWEB = ConstellationConfig(
        name='oneweb',
        display_name='OneWeb',
        orbital_period_range_minutes=(109, 115),
        typical_altitude_km=1200,
        orbital_characteristics='LEO_high',
        service_elevation_threshold_deg=10.0,
        expected_visible_satellites=(3, 6),
        candidate_pool_size=(50, 100),
        data_source='Space-Track.org',
        tle_directory='oneweb/tle',
        sample_ratio=0.25,
        sample_max=5
    )

    # 支援的星座列表（易於擴展）
    SUPPORTED_CONSTELLATIONS = [STARLINK, ONEWEB]

    @classmethod
    def get_constellation(cls, name: str) -> ConstellationConfig:
        """根據名稱獲取星座配置"""
        for constellation in cls.SUPPORTED_CONSTELLATIONS:
            if constellation.name.lower() == name.lower():
                return constellation
        raise ValueError(f"不支援的星座: {name}")

    @classmethod
    def get_all_names(cls) -> List[str]:
        """獲取所有支援的星座名稱"""
        return [c.name for c in cls.SUPPORTED_CONSTELLATIONS]
```

**步驟 2: 重構 TLE Loader**

**文件**: `src/stages/stage1_orbital_calculation/tle_data_loader.py`

**Line 58 修改為**:
```python
from shared.constants.constellation_constants import ConstellationRegistry

def scan_tle_data(self) -> Dict[str, Any]:
    """掃描所有可用的TLE數據文件"""
    self.logger.info("🔍 掃描TLE數據文件...")

    scan_result = {
        'constellations': {},
        'total_constellations': 0,
        'total_files': 0,
        'total_satellites': 0
    }

    # 動態掃描所有註冊的星座（配置驅動）
    for constellation_name in ConstellationRegistry.get_all_names():
        constellation_result = self._scan_constellation(constellation_name)
        if constellation_result:
            scan_result['constellations'][constellation_name] = constellation_result
            scan_result['total_files'] += constellation_result['files_count']
            scan_result['total_satellites'] += constellation_result['satellite_count']
```

**Line 146-149 修改為**:
```python
# 根據星座配置分配採樣數量（配置驅動）
try:
    constellation_config = ConstellationRegistry.get_constellation(constellation)
    constellation_sample_size = min(
        int(sample_size * constellation_config.sample_ratio),
        constellation_config.sample_max
    )
except ValueError:
    # 未知星座使用默認值
    constellation_sample_size = min(sample_size // 10, 5)
    self.logger.warning(f"未知星座 {constellation}，使用默認採樣配置")
```

**Line 384 修改為**:
```python
# 檢查各星座數據（配置驅動）
for constellation_name in ConstellationRegistry.get_all_names():
    constellation_config = ConstellationRegistry.get_constellation(constellation_name)
    constellation_dir = self.tle_data_dir / constellation_config.tle_directory
```

**學術依據**:
- 軟體工程：開放封閉原則
- final.md：支援多星座研究
- 可擴展性：未來可添加 Kuiper, Telesat 等

**驗證方法**:
```python
# 測試配置驅動
from shared.constants.constellation_constants import ConstellationRegistry

# 獲取星座配置
starlink = ConstellationRegistry.get_constellation('starlink')
assert starlink.orbital_period_range_minutes == (90, 95)

# 獲取所有星座
all_constellations = ConstellationRegistry.get_all_names()
assert 'starlink' in all_constellations
assert 'oneweb' in all_constellations
```

---

## 🟡 **P1 級別問題（建議修復）**

### **問題 P1: 魔術數字採樣比例**

**嚴重性**: 🟡 **Medium**
**影響範圍**: 代碼可讀性
**學術影響**: 低（僅影響測試模式）

#### **問題描述**

已在 P0-3 的修復方案中一併解決（通過 ConstellationConfig.sample_ratio 和 sample_max）。

---

## ✅ **驗證通過的項目**

### **1. TLE Checksum 算法** ✅
- **位置**: tle_data_loader.py Line 319-358
- **狀態**: 使用官方 Modulo 10 算法，100% 正確
- **學術依據**: NORAD/NASA TLE 格式規範

### **2. TLE Epoch 時間解析** ✅
- **位置**: tle_data_loader.py Line 282-317
- **狀態**: 正確實現年份轉換和天數計算
- **學術依據**: TLE 官方格式規範

### **3. 獨立 Epoch 時間基準** ✅
- **位置**: time_reference_manager.py Line 71-154
- **狀態**: 100% 符合學術標準，不創建統一時間基準
- **學術依據**: academic_standards_clarification.md

### **4. 物理常數定義** ✅
- **位置**: shared/constants/tle_constants.py
- **狀態**: 所有常數有明確物理依據
- **學術依據**: 軌道力學和觀測標準

---

## 📋 **修復執行計劃**

### **階段 1: P0 問題修復**（預計 30 分鐘）

1. ✅ 創建問題追蹤文檔（本文件）
2. ⏳ **P0-1**: 添加星座配置元數據（10 分鐘）
3. ⏳ **P0-2**: 嚴格 TLE 格式驗證（10 分鐘）
4. ⏳ **P0-3**: 移除硬編碼星座列表（10 分鐘）

### **階段 2: 測試驗證**（預計 10 分鐘）

5. ⏳ 執行 Stage 1 完整測試
6. ⏳ 驗證 9040 顆衛星載入正常
7. ⏳ 檢查星座配置元數據正確輸出
8. ⏳ 驗證嚴格格式驗證生效

### **階段 3: 文檔更新**（預計 10 分鐘）

9. ⏳ 更新 stage1-specification.md
10. ⏳ 更新 stage1_issues_and_fixes.md 狀態

**總預計時間**: 50 分鐘

---

## 📊 **修復後預期評分**

| 類別 | 修復前 | 修復後 | 改善 |
|------|--------|--------|------|
| **硬編碼問題** | C (60) | A (90) | +50% |
| **學術合規** | B+ (83) | A+ (95) | +14% |
| **擴展性** | C (65) | A (92) | +42% |
| **總體評分** | B+ (83) | A (93) | +12% |

---

## 🎯 **修復完成檢查清單**

### **代碼修復**
- [ ] P0-1: 星座配置元數據已添加
- [ ] P0-2: TLE 格式驗證已嚴格化
- [ ] P0-3: 星座列表已配置化

### **測試驗證**
- [ ] Stage 1 執行成功（9040 顆衛星）
- [ ] 星座配置元數據正確輸出
- [ ] 嚴格驗證拒絕無效 TLE
- [ ] 配置驅動星座掃描正常

### **文檔更新**
- [ ] stage1-specification.md 已更新
- [ ] 本文件狀態已更新為「已完成」

---

**文檔維護**: 每次修復完成後更新對應的檢查清單
**版本控制**: Git commit 附帶此文件的引用
**後續追蹤**: 定期檢查修復效果，確保長期維護