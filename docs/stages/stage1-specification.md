# 📥 Stage 1: TLE 數據載入層 - 完整規格文檔

**最後更新**: 2025-09-27
**程式狀態**: ✅ 重構完成，Grade A 合規
**接口標準**: 100% BaseStageProcessor 合規

## 📖 概述與目標

**核心職責**: TLE 數據載入、驗證、時間基準建立
**輸入**: TLE 檔案（約 2.2MB）
**輸出**: 標準化 ProcessingResult → 記憶體傳遞至 Stage 2
**處理時間**: ~0.5秒 (8,995顆衛星)
**當前狀態**: ✅ 重構完成，Grade A 學術合規

### 🎯 Stage 1 核心價值
- **數據品質保證**: 嚴格的 TLE 格式驗證與 Checksum 檢查
- **時間基準標準化**: 為後續階段提供統一的計算基準時間
- **接口標準化**: 100% 符合 BaseStageProcessor 接口規範
- **學術級合規**: 符合 Grade A 學術標準，零容忍簡化算法

## 🏗️ 架構設計

### 模組化組件架構
```
┌─────────────────────────────────────────────────────────┐
│               Stage 1: 數據載入層 (重構版)                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │TLE Data     │  │Data         │  │Time Reference│    │
│  │Loader       │  │Validator    │  │Manager      │    │
│  │             │  │             │  │             │    │
│  │• 檔案讀取    │  │• 格式驗證    │  │• Epoch提取   │    │
│  │• 解析TLE    │  │• Checksum   │  │• 基準時間    │    │
│  │• 批次處理    │  │• 完整性檢查  │  │• 標準化     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │              │              │             │
│           └──────────────┼──────────────┘             │
│                          ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │        Stage1MainProcessor                   │    │
│  │        (BaseStageProcessor 合規)             │    │
│  │                                              │    │
│  │ • 協調三個組件                                │    │
│  │ • ProcessingResult 標準輸出                  │    │
│  │ • run_validation_checks() 實現               │    │
│  │ • save_validation_snapshot() 實現            │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 核心處理器實現
```python
class Stage1MainProcessor(BaseStageProcessor):
    """Stage 1 重構處理器 - 100% 接口合規"""

    def process(self, input_data) -> ProcessingResult:
        """返回標準化 ProcessingResult"""

    def run_validation_checks(self, results) -> Dict:
        """5項 Stage 1 專用驗證檢查"""

    def save_validation_snapshot(self, results) -> bool:
        """標準化快照保存"""
```

## 🎯 核心功能與職責

### ✅ **Stage 1 專屬職責**

#### 1. **TLE 數據載入**
- **TLE 檔案讀取**: 支援標準 NORAD TLE 格式
- **批次處理**: 高效處理 8,995+ 顆衛星
- **錯誤處理**: 完整的異常和恢復機制
- **來源追蹤**: 完整的數據血統記錄

#### 2. **數據格式驗證**
- **格式嚴格檢查**: 69字符行長度、行號驗證
- **Checksum 驗證**: 完整的 Modulo 10 算法實現
- **NORAD ID 一致性**: 兩行數據一致性檢查
- **必要字段檢查**: 確保所有關鍵字段存在

#### 3. **時間基準建立**
- **TLE Epoch 提取**: 高精度時間解析
- **時間標準化**: ISO 8601 格式輸出
- **時間基準繼承**: 為 Stage 2 提供 calculation_base_time
- **微秒精度**: 科學級時間精度保證

#### 4. **數據標準化**
- **衛星數據結構**: 標準化衛星記錄格式
- **元數據組織**: 完整的處理元數據
- **品質標記**: A/B/C/F 數據品質評級

### ❌ **明確排除職責** (移至 Stage 2)
- SGP4/SDP4 軌道計算
- 座標系統轉換 (TEME→ITRF→WGS84)
- 可見性分析和篩選
- 仰角、方位角、距離計算

## 🔍 驗證框架

### 5項專用驗證檢查
1. **tle_format_validation** - TLE 格式嚴格驗證
   - 69字符長度檢查
   - 行號正確性 ('1', '2')
   - NORAD ID 一致性

2. **tle_checksum_verification** - Checksum 完整驗證
   - Modulo 10 官方算法完整實作
   - 所有行的校驗和檢查 (Line 1 & Line 2)
   - 要求: 95% 以上通過率
   - 當前實測: 100% 通過率

3. **data_completeness_check** - 數據完整性檢查
   - 必要字段存在性驗證
   - 衛星數據結構完整性
   - 元數據完整性評估

4. **time_base_establishment** - 時間基準建立驗證
   - calculation_base_time 存在檢查
   - tle_epoch_time 正確提取驗證
   - 時間格式標準化檢查

5. **satellite_data_structure** - 衛星數據結構驗證
   - 關鍵字段完整性檢查
   - 數據類型正確性驗證
   - 結構一致性檢查

### 驗證等級標準
- **A+ 級**: 100% 檢查通過，完美數據品質
- **A 級**: 95%+ 檢查通過，優秀數據品質
- **B 級**: 80%+ 檢查通過，良好數據品質
- **C 級**: 70%+ 檢查通過，可用數據品質
- **F 級**: <70% 檢查通過，不可用數據

## 📊 標準化輸出格式

### ProcessingResult 結構
```python
ProcessingResult(
    status=ProcessingStatus.SUCCESS,
    data={
        'stage': 1,
        'stage_name': 'refactored_tle_data_loading',
        'satellites': [...],  # 8,995 顆衛星數據列表
        'metadata': {
            # 時間基準信息 (Stage 2 繼承用)
            'calculation_base_time': '2025-09-27T07:30:24.572437+00:00',
            'tle_epoch_time': '2025-09-27T07:30:24.572437+00:00',
            'time_base_source': 'tle_epoch_derived',
            'tle_epoch_compliance': True,

            # v6.0 時間繼承機制
            'stage1_time_inheritance': {
                'exported_time_base': '2025-09-27T07:30:24.572437+00:00',
                'inheritance_ready': True,
                'calculation_reference': 'tle_epoch_based'
            },

            # 處理統計
            'total_satellites': 8995,
            'processing_duration_seconds': 0.525507,
            'time_reference_established': True,

            # 重構標記
            'refactored_version': True,
            'interface_compliance': True
        },
        'processing_stats': {...}
    },
    metadata={...},
    errors=[],
    warnings=[],
    metrics=ProcessingMetrics(...)
)
```

### 衛星數據格式
```python
satellite = {
    # 基本信息
    'name': 'STARLINK-1234',
    'constellation': 'Starlink',
    'satellite_id': 'STARLINK-1234',
    'norad_id': '25544',

    # TLE 數據
    'tle_line1': '1 25544U 98067A   23001.00000000...',
    'tle_line2': '2 25544  51.6461 339.7939...',
    'line1': '1 25544U 98067A   23001.00000000...',  # 別名
    'line2': '2 25544  51.6461 339.7939...',        # 別名

    # 來源信息
    'source_file': 'tle_data/starlink.txt'
}
```

## ⚡ 性能指標

### 實測性能 (當前狀態)
- **處理時間**: ~0.5秒 (8,995顆衛星)
- **處理速度**: ~17,990顆/秒
- **記憶體使用**: < 200MB
- **驗證成功率**: 100% (A+級品質)
- **快照生成**: < 0.01秒

### 與 Stage 2 集成
- **數據訪問**: `stage1_result.data`
- **兼容性**: 100% 向後兼容
- **傳遞格式**: 標準字典結構
- **時間基準**: 完整繼承機制

## 🚀 使用方式與配置

### 標準調用方式
```python
from stages.stage1_orbital_calculation.stage1_main_processor import Stage1MainProcessor

# 創建處理器
processor = Stage1MainProcessor(config)

# 執行處理
result = processor.execute()  # 返回 ProcessingResult

# 驗證檢查
validation = processor.run_validation_checks(result.data)

# 保存快照
snapshot_saved = processor.save_validation_snapshot(result.data)

# Stage 2 數據訪問
stage2_input = result.data  # 提取數據部分
```

### 配置選項
```python
config = {
    'sample_mode': False,  # 生產模式
    'tle_validation_config': {
        'strict_format_check': True,
        'checksum_verification': True,
        'line_length_check': True,
        'required_fields_check': True
    },
    'time_config': {
        'precision_seconds': 1e-6,
        'output_format': 'iso_8601',
        'timezone': 'UTC'
    }
}
```

## 📋 部署與驗證

### 部署檢驗標準
**成功指標**:
- [ ] ProcessingResult 正確返回
- [ ] 5項驗證檢查全部通過 (100% success_rate)
- [ ] 快照文件正常生成 (`validation_passed: true`)
- [ ] Stage 2 數據接收正常
- [ ] 處理時間 < 1秒
- [ ] 衛星數據數量: 8,995顆

### 測試命令
```bash
# 完整系統測試
python scripts/run_six_stages_with_validation.py --stage 1

# 檢查快照文件
cat data/validation_snapshots/stage1_validation.json | jq '.validation_passed'

# 驗證數據數量
cat data/validation_snapshots/stage1_validation.json | jq '.data_summary.satellite_count'
```

## 🚨 故障排除

### 常見問題
1. **TLE數據過期**
   - 檢查: TLE檔案最後修改時間
   - 解決: 執行增量更新腳本

2. **格式驗證失敗**
   - 檢查: TLE格式完整性
   - 解決: 重新下載TLE數據

3. **時間基準問題**
   - 檢查: metadata中時間基準字段
   - 解決: 確認TLE epoch時間解析正確

### 診斷指令
```bash
# 檢查TLE數據狀態
find data/tle_data -name '*.tle' -exec ls -la {} \;

# 驗證處理器狀態
python -c "
from stages.stage1_orbital_calculation.stage1_main_processor import Stage1MainProcessor
print('✅ Stage 1 處理器載入正常')
"

# 檢查驗證快照
python -c "
import json
with open('data/validation_snapshots/stage1_validation.json', 'r') as f:
    data = json.load(f)
    print(f'驗證狀態: {data.get(\"validation_passed\", False)}')
    print(f'衛星數量: {data.get(\"data_summary\", {}).get(\"satellite_count\", 0)}')
    print(f'重構版本: {data.get(\"refactored_version\", False)}')
"
```

## 🎯 學術標準合規

### Grade A 強制要求
- **✅ 真實數據**: Space-Track.org 官方 TLE 數據
- **✅ 完整驗證**: 5項專用驗證檢查
- **✅ 時間基準**: 100% 使用 TLE epoch 時間
- **✅ 格式標準**: 嚴格遵循 NORAD TLE 格式
- **✅ 精度保證**: 微秒級時間精度

### 零容忍項目
- **❌ 簡化算法**: 絕不允許回退到簡化實現
- **❌ 估算值**: 禁止使用任何估算或假設值
- **❌ 模擬數據**: 必須使用真實 TLE 數據
- **❌ 當前時間**: 禁止使用系統當前時間作為計算基準

---

**文檔版本**: v1.0 (統一版)
**程式版本**: Stage1MainProcessor (重構完成版)
**合規狀態**: ✅ Grade A 學術標準
**維護負責**: Orbit Engine Team