# Stage 5 驗證快照 Fail-Fast 審計報告

**審計日期**: 2025-10-04
**審計範圍**: Stage 5 驗證快照系統
**審計目標**: 檢查驗證層的所有回退機制

---

## 執行摘要

### 總體評估
- **當前等級**: D (不合格 - 大量驗證回退)
- **目標等級**: A+ (100% Fail-Fast 驗證)
- **發現違規**: 69 個 `.get()` 回退
- **影響範圍**: 4 個驗證模組

### 關鍵發現

**🚨 驗證系統存在系統性回退問題**

驗證器應該是 **最嚴格** 的 Fail-Fast 執行點，但目前：
- ✅ **正確**: 發現問題時返回 `False` 或拋出錯誤
- ❌ **錯誤**: 使用 `.get()` 提取數據時帶有預設值
- ⚠️ **風險**: 預設值可能導致驗證器 **誤判通過**

### 違規統計

| 模組 | `.get()` 數量 | 嚴重性 | 誤判風險 |
|------|--------------|--------|----------|
| `stage5_validator.py` | 21 | 🔴 CRITICAL | HIGH |
| `stage5_compliance_validator.py` | 28 | 🔴 CRITICAL | HIGH |
| `snapshot_manager.py` | 8 | 🟡 MEDIUM | MEDIUM |
| `stage5_signal_validator.py` | 12 | 🟡 MEDIUM | LOW |
| **總計** | **69** | - | - |

---

## 第一部分：驗證器回退機制詳細分析

### 🔴 P1: Layer 2 驗證器 - stage5_validator.py (CRITICAL)

**位置**: `scripts/stage_validators/stage5_validator.py`
**總計 21 個回退**

#### 關鍵違規清單

| 行號 | 代碼 | 預設值 | 風險分析 |
|------|------|--------|----------|
| 32 | `snapshot_data.get('stage')` | None | 低風險 - 後續有檢查 |
| 36 | `snapshot_data.get('data_summary', {})` | `{}` | ⚠️ **高風險** - 空字典可能導致後續 0 值 |
| 37 | `data_summary.get('total_satellites_analyzed', 0)` | `0` | 🚨 **極高風險** - 可能掩蓋真正的 0 衛星問題 |
| 38 | `data_summary.get('usable_satellites', 0)` | `0` | 🚨 **極高風險** - 0 值有歧義 |
| 44 | `data_summary.get('signal_quality_distribution', {})` | `{}` | ⚠️ 高風險 |
| 45 | `signal_quality_distribution.get('excellent', 0)` | `0` | ⚠️ 高風險 |
| 46 | `signal_quality_distribution.get('good', 0)` | `0` | ⚠️ 高風險 |
| 47 | `signal_quality_distribution.get('fair', 0)` | `0` | ⚠️ 高風險 |
| 48 | `signal_quality_distribution.get('poor', 0)` | `0` | ⚠️ 高風險 |
| 55 | `snapshot_data.get('metadata', {})` | `{}` | ⚠️ 高風險 |
| 58 | `metadata.get('gpp_standard_compliance', False)` | `False` | 🚨 **極高風險** - 錯誤預設為不合規 |
| 63 | `metadata.get('itur_standard_compliance', False)` | `False` | 🚨 **極高風險** |
| 68 | `metadata.get('gpp_config', {})` | `{}` | ⚠️ 高風險 |
| 72 | `gpp_config.get('standard_version', '')` | `''` | ⚠️ 高風險 |
| 77 | `metadata.get('itur_config', {})` | `{}` | ⚠️ 高風險 |
| 81 | `itur_config.get('recommendation', '')` | `''` | ⚠️ 高風險 |
| 86 | `metadata.get('physical_constants', {})` | `{}` | ⚠️ 高風險 |
| 90 | `physical_constants.get('standard_compliance')` | `None` | 中風險 - 後續有檢查 |
| 94 | `data_summary.get('average_rsrp_dbm')` | `None` | 中風險 - 後續有檢查 |
| 95 | `data_summary.get('average_sinr_db')` | `None` | 中風險 - 後續有檢查 |

#### 風險場景示例

**場景 1: 數據缺失但驗證誤判通過**

```python
# 假設快照數據不完整
snapshot_data = {
    'stage': 'stage5_signal_analysis'
    # 缺少 data_summary
}

# 當前代碼行為
data_summary = snapshot_data.get('data_summary', {})  # 返回 {}
total_satellites_analyzed = data_summary.get('total_satellites_analyzed', 0)  # 返回 0

# Line 40 檢查
if total_satellites_analyzed == 0:
    return False, f"❌ Stage 5 未分析任何衛星數據"  # 正確返回 False

# ✅ 這裡雖然返回 False，但錯誤訊息有歧義
# 無法區分：
# 1. 真的處理了 0 顆衛星（處理失敗）
# 2. 快照數據缺失（數據結構問題）
```

**場景 2: metadata 缺失導致合規檢查誤判**

```python
# 快照數據缺少 metadata
snapshot_data = {
    'stage': 'stage5_signal_analysis',
    'data_summary': {
        'total_satellites_analyzed': 10,
        'usable_satellites': 5
    }
    # 缺少 metadata
}

# 當前代碼行為
metadata = snapshot_data.get('metadata', {})  # 返回 {}
gpp_compliance = metadata.get('gpp_standard_compliance', False)  # 返回 False

# Line 59-60
if not gpp_compliance:
    return False, f"❌ Stage 5 3GPP 標準合規標記缺失"  # 正確返回 False

# ✅ 雖然返回 False，但如果 metadata 完全缺失，
# 應該更早失敗並給出更清晰的錯誤訊息
```

#### 建議修復 (Fail-Fast)

```python
# ✅ 修復後代碼
def check_stage5_validation(snapshot_data: dict) -> tuple:
    """Stage 5 驗證 - Fail-Fast 版本"""

    # 第一層：驗證基本結構
    if 'stage' not in snapshot_data:
        return False, "❌ 快照數據缺少 'stage' 字段 - 數據結構錯誤"

    if snapshot_data['stage'] != 'stage5_signal_analysis':
        return False, f"❌ Stage 識別錯誤: {snapshot_data['stage']} (期望: stage5_signal_analysis)"

    # 第二層：驗證 data_summary 存在
    if 'data_summary' not in snapshot_data:
        return False, "❌ 快照數據缺少 'data_summary' - 關鍵摘要數據缺失"

    data_summary = snapshot_data['data_summary']

    # 第三層：驗證必要的摘要字段
    required_summary_fields = [
        'total_satellites_analyzed',
        'usable_satellites',
        'signal_quality_distribution',
        'average_rsrp_dbm',
        'average_sinr_db'
    ]

    missing_fields = [f for f in required_summary_fields if f not in data_summary]
    if missing_fields:
        return False, f"❌ data_summary 缺少必要字段: {missing_fields}"

    # 第四層：驗證業務邏輯
    total_satellites_analyzed = data_summary['total_satellites_analyzed']
    if not isinstance(total_satellites_analyzed, (int, float)):
        return False, f"❌ total_satellites_analyzed 類型錯誤: {type(total_satellites_analyzed)}"

    if total_satellites_analyzed == 0:
        return False, f"❌ Stage 5 處理失敗: 0 顆衛星被分析"

    # 第五層：驗證 metadata 存在
    if 'metadata' not in snapshot_data:
        return False, "❌ 快照數據缺少 'metadata' - 標準合規資訊缺失"

    metadata = snapshot_data['metadata']

    # 第六層：驗證合規標記
    if 'gpp_standard_compliance' not in metadata:
        return False, "❌ metadata 缺少 'gpp_standard_compliance' 字段"

    if metadata['gpp_standard_compliance'] != True:  # 明確檢查 True
        return False, f"❌ 3GPP 標準合規性未通過: {metadata['gpp_standard_compliance']}"

    # ... 繼續其他驗證

    # 最後才返回成功
    return True, "✅ Stage 5 驗證通過"
```

**修復效果**:
- ❌ 移除所有 `.get()` 回退
- ✅ 每一層都有明確的 Fail-Fast 檢查
- ✅ 錯誤訊息精確指出問題位置
- ✅ 無法用預設值掩蓋數據缺失

---

### 🔴 P2: Layer 1 合規驗證器 - stage5_compliance_validator.py (CRITICAL)

**位置**: `src/stages/stage5_signal_analysis/stage5_compliance_validator.py`
**總計 28 個回退**

#### 關鍵違規分析

**違規模式 1: 輸入驗證使用回退**

```python
# Line 59 (❌ 違規)
if input_data.get('stage') not in ['stage4_link_feasibility', 'stage4_optimization']:
    errors.append("輸入階段標識錯誤，需要 Stage 4 可連線衛星輸出")

# Line 62 (❌ 違規)
satellites = input_data.get('satellites', {})
```

**問題**:
- 當 `input_data` 缺少 `stage` 字段時，`.get()` 返回 `None`
- `None not in [...]` 為 `True`，觸發錯誤 ✅
- 但錯誤訊息不準確：應該說 "缺少 stage 字段"，而不是 "階段標識錯誤"

**修復**:
```python
# ✅ Fail-Fast 版本
if 'stage' not in input_data:
    errors.append("缺少必需字段: stage")
elif input_data['stage'] not in ['stage4_link_feasibility', 'stage4_optimization']:
    errors.append(f"輸入階段標識錯誤: {input_data['stage']} (期望: stage4_*)")

if 'satellites' not in input_data:
    errors.append("缺少必需字段: satellites")
else:
    satellites = input_data['satellites']
    if not isinstance(satellites, dict):
        errors.append("satellites 必須是字典格式")
    elif len(satellites) == 0:
        warnings.append("satellites 數據為空")
```

---

**違規模式 2: 驗證檢查中的大量 `.get()` 回退**

```python
# Line 157 (❌ 違規)
time_series = sat_data.get('time_series', [])

# Line 177 (❌ 違規)
signal_quality = first_point.get('signal_quality', {})

# Line 189 (❌ 違規)
rsrp = signal_quality.get('rsrp_dbm')

# Line 197 (❌ 違規)
metadata = results.get('metadata', {})

# Line 210 (❌ 違規)
if not metadata.get('gpp_standard_compliance'):
    validation_results['errors'].append('3GPP 標準合規性未確認')

# Line 214 (❌ 違規)
if not metadata.get('time_series_processing'):
    validation_results['errors'].append('時間序列處理標記缺失')
```

**問題**:
- 使用空字典/列表作為預設值
- 合規標記使用 `.get()` 導致 `None` 被判斷為 `False`
- 無法區分 "字段缺失" 和 "字段值為 False"

**修復**:
```python
# ✅ Fail-Fast 版本
# 檢查 time_series 存在性
if 'time_series' not in sat_data:
    validation_results['errors'].append(f'衛星 {sat_id} 缺少 time_series 字段')
    validation_results['passed'] = False
    continue

time_series = sat_data['time_series']
if not isinstance(time_series, list):
    validation_results['errors'].append(f'衛星 {sat_id} time_series 必須是列表')
    validation_results['passed'] = False
    continue

if len(time_series) == 0:
    validation_results['warnings'].append(f'衛星 {sat_id} time_series 為空')
    continue

# 檢查 signal_quality 存在性
first_point = time_series[0]
if 'signal_quality' not in first_point:
    validation_results['errors'].append(f'衛星 {sat_id} 時間點缺少 signal_quality')
    validation_results['passed'] = False
    continue

signal_quality = first_point['signal_quality']

# 檢查 RSRP 存在性
if 'rsrp_dbm' not in signal_quality:
    validation_results['warnings'].append(f'衛星 {sat_id} 缺少 rsrp_dbm')
else:
    rsrp = signal_quality['rsrp_dbm']
    if rsrp < -140 or rsrp > -44:
        validation_results['warnings'].append(f'衛星 {sat_id} RSRP 超出範圍: {rsrp}')

# 檢查 metadata 存在性
if 'metadata' not in results:
    validation_results['errors'].append('缺少 metadata 字段')
    validation_results['passed'] = False
else:
    metadata = results['metadata']

    # 檢查合規標記（明確區分缺失和 False）
    if 'gpp_standard_compliance' not in metadata:
        validation_results['errors'].append('metadata 缺少 gpp_standard_compliance 字段')
        validation_results['passed'] = False
    elif metadata['gpp_standard_compliance'] != True:
        validation_results['errors'].append(
            f'3GPP 標準合規性未通過: {metadata["gpp_standard_compliance"]}'
        )
        validation_results['passed'] = False
```

---

**違規模式 3: verify_3gpp_compliance 方法**

```python
# Line 287 (❌ 違規)
time_series = sat_data.get('time_series', [])

# Line 294 (❌ 違規)
signal_quality = point.get('signal_quality', {})

# Line 297 (❌ 違規)
calc_standard = signal_quality.get('calculation_standard')
```

**問題**: 同樣的回退模式，應該使用 Fail-Fast

---

### 🟡 P3: 快照管理器 - snapshot_manager.py (MEDIUM)

**位置**: `src/stages/stage5_signal_analysis/output_management/snapshot_manager.py`
**總計 8 個回退**

#### 違規清單

```python
# Line 25 (❌ 違規)
analysis_summary = processing_results.get('analysis_summary', {})

# Line 26 (❌ 違規)
metadata = processing_results.get('metadata', {})

# Line 32-38 (❌ 違規 - 6 個)
'total_satellites_analyzed': analysis_summary.get('total_satellites_analyzed', 0),
'usable_satellites': analysis_summary.get('usable_satellites', 0),
'signal_quality_distribution': analysis_summary.get('signal_quality_distribution', {}),
'average_rsrp_dbm': analysis_summary.get('average_rsrp_dbm'),
'average_sinr_db': analysis_summary.get('average_sinr_db'),
'total_time_points_processed': analysis_summary.get('total_time_points_processed', 0)
```

**風險評估**: MEDIUM
- 快照管理器的職責是保存數據
- 使用預設值可能導致保存不完整的快照
- 但最終驗證器會捕獲這些問題

**建議修復**:
```python
# ✅ Fail-Fast 版本
def save(self, processing_results: Dict[str, Any]) -> bool:
    """保存驗證快照 - Fail-Fast 版本"""
    try:
        # 驗證 processing_results 結構
        required_top_level = ['analysis_summary', 'metadata']
        missing = [f for f in required_top_level if f not in processing_results]
        if missing:
            raise ValueError(f"processing_results 缺少必要字段: {missing}")

        analysis_summary = processing_results['analysis_summary']
        metadata = processing_results['metadata']

        # 驗證 analysis_summary 必要字段
        required_summary = [
            'total_satellites_analyzed',
            'usable_satellites',
            'signal_quality_distribution',
            'average_rsrp_dbm',
            'average_sinr_db',
            'total_time_points_processed'
        ]
        missing_summary = [f for f in required_summary if f not in analysis_summary]
        if missing_summary:
            raise ValueError(f"analysis_summary 缺少必要字段: {missing_summary}")

        # 執行驗證
        validation_results = self.validator.run_validation_checks(processing_results)

        # 構建快照（無需 .get()）
        snapshot_data = {
            'stage': 'stage5_signal_analysis',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_summary': {
                'total_satellites_analyzed': analysis_summary['total_satellites_analyzed'],
                'usable_satellites': analysis_summary['usable_satellites'],
                'signal_quality_distribution': analysis_summary['signal_quality_distribution'],
                'average_rsrp_dbm': analysis_summary['average_rsrp_dbm'],
                'average_sinr_db': analysis_summary['average_sinr_db'],
                'total_time_points_processed': analysis_summary['total_time_points_processed']
            },
            'metadata': metadata,
            'validation_results': validation_results
        }

        # 保存快照
        validation_dir = Path("data/validation_snapshots")
        validation_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = validation_dir / "stage5_validation.json"

        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📋 Stage 5驗證快照已保存: {snapshot_path}")
        return True

    except Exception as e:
        logger.error(f"❌ 快照保存失敗: {e}")
        raise  # Fail-Fast: 不要靜默返回 False
```

---

### 🟡 P4: 舊版驗證框架 - stage5_signal_validator.py (MEDIUM)

**位置**: `src/shared/validation_framework/stage5_signal_validator.py`
**總計 12 個回退**

#### 評估

這個文件似乎是舊版本的驗證框架，可能不再使用。

**建議**:
1. 確認是否仍在使用
2. 如果不再使用，應該刪除
3. 如果仍在使用，應該按照相同的 Fail-Fast 原則修復

---

## 第二部分：修復優先級與計劃

### Phase 1: 關鍵驗證器修復 (CRITICAL)
**預計時間**: 3-4 小時
**優先級**: P0

1. **修復 stage5_validator.py** (21 個回退)
   - 移除所有 `.get()` 預設值
   - 分層驗證：結構 → 字段 → 類型 → 業務邏輯
   - 精確的錯誤訊息

2. **修復 stage5_compliance_validator.py** (28 個回退)
   - 修復 `validate_input()` 方法
   - 修復 `validate_output()` 方法
   - 修復 `run_validation_checks()` 方法
   - 修復 `verify_3gpp_compliance()` 方法

**影響**: 破壞性變更 - 可能導致之前能通過的驗證現在失敗

**緩解措施**:
- 同時修復數據生成代碼，確保輸出完整數據
- 提供清晰的錯誤訊息，指導如何修復

---

### Phase 2: 快照管理修復 (MEDIUM)
**預計時間**: 1 小時
**優先級**: P1

3. **修復 snapshot_manager.py** (8 個回退)
   - 添加結構驗證
   - 移除 `.get()` 預設值
   - 失敗時拋出異常而不是返回 False

---

### Phase 3: 清理舊代碼 (LOW)
**預計時間**: 30 分鐘
**優先級**: P2

4. **處理 stage5_signal_validator.py**
   - 確認使用狀態
   - 如果不使用，刪除文件
   - 如果使用，按相同原則修復

---

## 第三部分：驗證器 Fail-Fast 最佳實踐

### 原則 1: 分層驗證

```python
def validate_data(data: Dict[str, Any]) -> tuple:
    """
    分層驗證策略

    第 1 層: 結構驗證（字段是否存在）
    第 2 層: 類型驗證（字段類型是否正確）
    第 3 層: 範圍驗證（值是否在合理範圍）
    第 4 層: 業務邏輯驗證（業務規則是否滿足）
    """

    # 第 1 層: 結構驗證
    if 'required_field' not in data:
        return False, "❌ 第 1 層失敗: 缺少 required_field"

    # 第 2 層: 類型驗證
    if not isinstance(data['required_field'], int):
        return False, f"❌ 第 2 層失敗: required_field 類型錯誤 ({type(data['required_field'])})"

    # 第 3 層: 範圍驗證
    if data['required_field'] < 0:
        return False, f"❌ 第 3 層失敗: required_field 值非法 ({data['required_field']})"

    # 第 4 層: 業務邏輯
    if data['required_field'] == 0:
        return False, "❌ 第 4 層失敗: 未處理任何數據"

    return True, "✅ 所有驗證通過"
```

### 原則 2: 明確的錯誤訊息

```python
# ❌ 錯誤示例
if not data.get('value'):
    return False, "驗證失敗"

# ✅ 正確示例
if 'value' not in data:
    return False, "❌ 缺少必要字段 'value' - 數據結構不完整"
elif data['value'] is None:
    return False, "❌ 字段 'value' 為 None - 計算可能失敗"
elif data['value'] == 0:
    return False, "❌ 字段 'value' 為 0 - 未處理任何數據"
```

### 原則 3: 永不使用預設值

```python
# ❌ 絕對禁止
metadata = data.get('metadata', {})  # 掩蓋了數據缺失

# ✅ 正確做法
if 'metadata' not in data:
    raise ValueError("metadata 字段缺失")
metadata = data['metadata']
```

### 原則 4: 驗證器應該拋出異常或返回明確的失敗

```python
# ⚠️ 不推薦（靜默返回 False）
def save_snapshot(data):
    try:
        # ... 保存邏輯
        return True
    except Exception as e:
        logger.error(f"保存失敗: {e}")
        return False  # 調用者可能忽略這個 False

# ✅ 推薦（拋出異常）
def save_snapshot(data):
    try:
        # ... 保存邏輯
        return True
    except Exception as e:
        logger.error(f"保存失敗: {e}")
        raise  # Fail-Fast: 強制調用者處理
```

---

## 第四部分：測試計劃

### 測試用例 1: 缺失字段檢測

```python
def test_validator_detects_missing_fields():
    """驗證器必須能檢測到缺失的字段"""

    # 準備不完整的快照數據
    incomplete_snapshot = {
        'stage': 'stage5_signal_analysis'
        # 缺少 data_summary
    }

    # 執行驗證
    passed, message = check_stage5_validation(incomplete_snapshot)

    # 斷言
    assert passed == False
    assert 'data_summary' in message
    assert '缺少' in message or '缺失' in message
```

### 測試用例 2: 錯誤類型檢測

```python
def test_validator_detects_wrong_types():
    """驗證器必須能檢測到錯誤的數據類型"""

    snapshot = {
        'stage': 'stage5_signal_analysis',
        'data_summary': "這應該是字典"  # 錯誤類型
    }

    passed, message = check_stage5_validation(snapshot)

    assert passed == False
    assert '類型' in message or 'type' in message.lower()
```

### 測試用例 3: 零值業務邏輯檢測

```python
def test_validator_detects_zero_satellites():
    """驗證器必須能區分缺失字段和真正的零值"""

    snapshot = {
        'stage': 'stage5_signal_analysis',
        'data_summary': {
            'total_satellites_analyzed': 0,  # 真正的零值
            'usable_satellites': 0,
            # ... 其他必要字段
        },
        'metadata': { ... }
    }

    passed, message = check_stage5_validation(snapshot)

    assert passed == False
    assert '0' in message or '零' in message
    assert '處理失敗' in message or '未分析' in message
```

---

## 總結

### 當前狀態（D 級）
- ✅ 驗證器能發現問題並返回失敗
- ❌ 使用 69 個 `.get()` 回退掩蓋數據結構問題
- ❌ 錯誤訊息有歧義
- ❌ 無法區分 "缺失" vs "零值" vs "False"

### 目標狀態（A+ 級）
- ✅ 零回退機制
- ✅ 分層驗證：結構 → 類型 → 範圍 → 業務
- ✅ 精確的錯誤訊息
- ✅ 明確區分各種失敗情況
- ✅ 失敗時拋出異常或返回詳細的失敗原因

### 建議

**立即開始 Phase 1 修復**：
1. 先修復 `stage5_validator.py`（Layer 2 驗證器）
2. 再修復 `stage5_compliance_validator.py`（Layer 1 驗證器）
3. 同時更新相關的數據生成代碼

**預期效果**：
- 更早發現數據問題
- 更精確的錯誤定位
- 更高的系統可靠性
- 完全符合 Fail-Fast 原則

---

**報告生成**: 2025-10-04
**審計完成**: 驗證快照系統 Fail-Fast 合規性審計
**下一步**: 等待用戶確認後開始修復
