# 🛰️ Stage 1: TLE數據管理升級計劃

## 📋 階段概覽

**目標**：將自建TLE解析器替換為專業的TLE數據管理套件

**時程**：第1週前半 (3個工作日)

**優先級**：🔴 P0 (基礎數據層)

**現狀問題**：自建TLE解析器存在複雜包裝層，維護困難

## 🎯 重構目標

### 核心目標
- ❌ **移除自建組件**: 淘汰複雜的自建TLE解析器
- ✅ **導入專業庫**: Spacetrack官方API + 標準TLE處理庫
- ✅ **簡化數據流**: 直接對接Space-Track.org官方數據源
- ✅ **保持時間基準**: 確保每筆TLE記錄獨立epoch時間

### 學術標準要求
- **數據來源**: Space-Track.org官方TLE數據
- **時間處理**: 每筆記錄保持獨立epoch_datetime
- **格式標準**: 完全符合TLE標準格式
- **數據完整性**: 確保歷史數據完整載入

## 🔧 技術實現

### 套件選擇

#### Spacetrack (官方API)
```python
# 核心優勢
✅ Space-Track.org官方API
✅ 自動身份驗證
✅ 批量數據下載
✅ 歷史數據查詢
✅ 標準TLE格式保證
```

#### Beyond (ESA標準支援, 可選)
```python
# 輔助功能
✅ ESA標準TLE處理
✅ 高級TLE驗證
✅ 軌道元素解析
```

### 新架構設計

```python
# TLE數據管理架構
tle_management/
├── spacetrack_client.py         # Spacetrack API客戶端
├── tle_parser.py               # 標準TLE解析器
├── data_validator.py           # 數據完整性驗證
└── epoch_manager.py            # 獨立時間基準管理
```

## 📅 實施計劃 (3天)

### Day 1: Spacetrack整合
```bash
# 安裝核心套件
pip install spacetrack requests

# 替換組件
❌ 移除：自建TLE解析器包裝層
✅ 導入：spacetrack.SpaceTrackClient
```

```python
# spacetrack_client.py 實現
from spacetrack import SpaceTrackClient

class TLEDataManager:
    """TLE數據管理器 - 基於官方API"""

    def __init__(self, username: str, password: str):
        self.st = SpaceTrackClient(identity=username, password=password)

    def get_constellation_tle(self, constellation: str) -> List[Dict]:
        """獲取星座TLE數據"""

        if constellation.lower() == 'starlink':
            # 獲取Starlink TLE數據
            tle_data = self.st.tle_latest(
                norad_cat_id=self._get_starlink_catalog_ids(),
                format='tle'
            )
        elif constellation.lower() == 'oneweb':
            # 獲取OneWeb TLE數據
            tle_data = self.st.tle_latest(
                norad_cat_id=self._get_oneweb_catalog_ids(),
                format='tle'
            )

        return self._parse_tle_data(tle_data)

    def load_historical_tle(self, date_range: Tuple[str, str]) -> List[TLERecord]:
        """載入歷史TLE數據，保持獨立epoch"""

        historical_data = self.st.tle(
            epoch=date_range,
            format='tle'
        )

        # 確保每筆記錄保持獨立 epoch_datetime
        parsed_records = []
        for tle_entry in historical_data:
            record = TLERecord(
                satellite_name=tle_entry['OBJECT_NAME'],
                line1=tle_entry['LINE1'],
                line2=tle_entry['LINE2'],
                epoch_datetime=self._parse_epoch_time(tle_entry['EPOCH']),
                # ⚠️ 重要：不創建統一時間基準
                independent_epoch=True
            )
            parsed_records.append(record)

        return parsed_records
```

### Day 2: 數據驗證與格式化
```python
# tle_parser.py 標準解析器
class StandardTLEParser:
    """標準TLE解析器 - 符合學術規範"""

    def parse_tle_line1(self, line1: str) -> Dict:
        """解析TLE第一行"""
        return {
            'satellite_number': int(line1[2:7]),
            'classification': line1[7],
            'international_designator': line1[9:17].strip(),
            'epoch_year': int(line1[18:20]),
            'epoch_day': float(line1[20:32]),
            'first_derivative_mean_motion': float(line1[33:43]),
            'second_derivative_mean_motion': self._parse_exponential(line1[44:52]),
            'drag_term': self._parse_exponential(line1[53:61]),
            'ephemeris_type': int(line1[62]),
            'element_number': int(line1[64:68]),
            'checksum': int(line1[68])
        }

    def parse_tle_line2(self, line2: str) -> Dict:
        """解析TLE第二行"""
        return {
            'satellite_number': int(line2[2:7]),
            'inclination': float(line2[8:16]),
            'raan': float(line2[17:25]),
            'eccentricity': float('0.' + line2[26:33]),
            'argument_of_perigee': float(line2[34:42]),
            'mean_anomaly': float(line2[43:51]),
            'mean_motion': float(line2[52:63]),
            'revolution_number': int(line2[63:68]),
            'checksum': int(line2[68])
        }

    def validate_tle_format(self, line1: str, line2: str) -> bool:
        """驗證TLE格式正確性"""
        # 長度檢查
        if len(line1) != 69 or len(line2) != 69:
            return False

        # 行號檢查
        if line1[0] != '1' or line2[0] != '2':
            return False

        # 校驗和檢查
        return (
            self._calculate_checksum(line1[:-1]) == int(line1[-1]) and
            self._calculate_checksum(line2[:-1]) == int(line2[-1])
        )
```

### Day 3: 數據完整性驗證
```python
# data_validator.py 數據驗證
class TLEDataValidator:
    """TLE數據完整性驗證器"""

    def validate_epoch_consistency(self, tle_records: List[TLERecord]) -> ValidationResult:
        """驗證epoch時間一致性"""

        issues = []

        for record in tle_records:
            # 檢查epoch時間是否合理
            if not self._is_valid_epoch(record.epoch_datetime):
                issues.append(f"無效epoch時間: {record.satellite_name}")

            # 檢查是否保持獨立時間基準
            if not record.independent_epoch:
                issues.append(f"違反獨立epoch原則: {record.satellite_name}")

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            total_records=len(tle_records)
        )

    def validate_constellation_data(self, constellation: str,
                                  tle_records: List[TLERecord]) -> ConstellationValidation:
        """驗證星座數據完整性"""

        if constellation.lower() == 'starlink':
            expected_min_count = 200  # 至少200顆Starlink候選衛星
        elif constellation.lower() == 'oneweb':
            expected_min_count = 50   # 至少50顆OneWeb候選衛星

        actual_count = len(tle_records)

        return ConstellationValidation(
            constellation=constellation,
            expected_min=expected_min_count,
            actual_count=actual_count,
            sufficient_data=actual_count >= expected_min_count,
            data_quality=self._assess_data_quality(tle_records)
        )
```

## 🧪 驗證測試

### 數據完整性測試
```python
def test_tle_data_integrity():
    """TLE數據完整性測試"""

    manager = TLEDataManager(username, password)

    # 測試Starlink數據載入
    starlink_data = manager.get_constellation_tle('starlink')
    assert len(starlink_data) >= 200, "Starlink數據不足"

    # 測試OneWeb數據載入
    oneweb_data = manager.get_constellation_tle('oneweb')
    assert len(oneweb_data) >= 50, "OneWeb數據不足"

def test_epoch_independence():
    """測試epoch時間獨立性"""

    historical_data = manager.load_historical_tle(('2024-01-01', '2024-01-07'))

    # 確保每筆記錄有獨立的epoch時間
    epochs = [record.epoch_datetime for record in historical_data]
    unique_epochs = set(epochs)

    # 應該有多個不同的epoch時間
    assert len(unique_epochs) > 1, "違反獨立epoch原則"
```

## 📊 成功指標

### 量化指標
- **數據覆蓋**: Starlink ≥200顆, OneWeb ≥50顆候選衛星
- **格式正確性**: 100%符合標準TLE格式
- **時間獨立性**: 每筆記錄保持獨立epoch
- **API穩定性**: 數據獲取成功率 >95%

### 質化指標
- **官方數據源**: 100%基於Space-Track.org官方API
- **維護簡化**: 移除自建包裝層的複雜性
- **標準合規**: 完全符合TLE數據標準
- **學術可信**: 使用權威數據源

## ⚠️ 風險控制

### 技術風險
| 風險 | 影響 | 應對策略 |
|------|------|----------|
| API配額限制 | 中等 | 合理請求頻率控制 |
| 網路連接問題 | 低 | 本地緩存機制 |
| 數據格式變化 | 低 | 標準TLE格式穩定 |

### 時程風險
- **API學習曲線**: 預計1天適應時間
- **數據驗證**: 預計1天測試時間
- **緩衝時間**: 已包含在3天計劃中

---

**文檔版本**: v1.0 (修正版)
**建立日期**: 2024-01-15
**重點**: 學術研究的基礎數據管理，無工業級複雜功能
**下一階段**: Stage 2 - 軌道計算升級