# 🌍 Stage 3 清理計畫 - 移除職責越界功能

**目標**: 將 Stage 3 恢復為純座標轉換層，移除所有可見性評估功能

## 🎯 清理目標

### ✅ **保留功能** (核心座標轉換)
- TEME→GCRS→ITRS→WGS84 轉換鏈
- Skyfield 專業庫調用
- IAU 標準合規實現
- 批次處理優化
- WGS84 地理座標輸出

### ❌ **移除功能** (移至 Stage 4)
- `_first_layer_visibility_filter()` - 第一層可見性篩選
- `_geometric_elevation_calculation()` - 幾何仰角計算
- `_real_elevation_calculation()` - 真實仰角計算
- `_fast_elevation_calculation()` - 快速仰角計算
- 星座感知門檻邏輯 (Starlink 5°, OneWeb 10°)
- NTPU 地面站可見性判斷
- 服務窗口計算相關代碼

## 📂 需要修改的檔案

### 1. **主處理器**
```
src/stages/stage3_coordinate_transformation/
├── stage3_coordinate_transform_processor.py  ← 重點清理
├── __init__.py  ← 更新模組導出
└── stage3_coordinate_transform_processor_old.py  ← 保留備份
```

### 2. **相關配置**
```
config/stage3_coordinate_transformation.yaml  ← 移除可見性配置
docs/stages/stage3-signal-analysis.md  ← 重新命名和更新
```

## 🔧 詳細清理步驟

### Step 1: 備份現有實現
```bash
# 備份當前完整實現
cp src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py \
   archives/stage3_with_visibility_backup_$(date +%Y%m%d).py
```

### Step 2: 移除可見性相關方法
需要從 `stage3_coordinate_transform_processor.py` 中移除：

```python
# 移除這些方法 (保存到 stage4 實現中):
def _first_layer_visibility_filter(self, teme_data):
def _geometric_elevation_calculation(self, sat_lat, sat_lon, sat_alt, ground_lat, ground_lon, ground_alt):
def _real_elevation_calculation(self, sat_lat, sat_lon, sat_alt, ground_lat, ground_lon, ground_alt):
def _fast_elevation_calculation(self, sat_lat, sat_lon, sat_alt, ground_lat, ground_lon, ground_alt):

# 移除星座感知邏輯:
if 'starlink' in constellation:
    min_elevation = 5.0
elif 'oneweb' in constellation:
    min_elevation = 10.0
```

### Step 3: 簡化主處理流程
```python
# 修改後的主流程應該只包含:
def _execute_coordinate_transformation(self, teme_data):
    """純座標轉換流程"""
    # 1. 驗證 TEME 輸入
    validated_data = self._validate_teme_input(teme_data)

    # 2. 執行座標轉換 (TEME→WGS84)
    wgs84_results = self._transform_teme_to_wgs84(validated_data)

    # 3. 格式化輸出
    return self._format_wgs84_output(wgs84_results)
```

### Step 4: 更新輸出格式
```python
# 新的標準輸出 (不包含可見性資料):
output_format = {
    'stage': 'stage3_coordinate_transformation',
    'satellites': {
        'satellite_id': {
            'wgs84_coordinates': [
                {
                    'timestamp': 'ISO8601',
                    'latitude_deg': float,
                    'longitude_deg': float,
                    'altitude_m': float
                }
            ],
            'constellation': str,
            'total_positions': int
        }
    },
    'metadata': {
        'coordinate_system': 'WGS84',
        'transformation_standard': 'IAU_2000_2006',
        'total_satellites': int,
        'processing_time': str
    }
}
```

## ✅ 驗證標準

### 功能驗證
- [ ] 只保留純座標轉換功能
- [ ] 所有可見性邏輯已移除
- [ ] Skyfield 專業庫正常調用
- [ ] WGS84 輸出格式正確

### 性能驗證
- [ ] 處理時間 < 2秒 (8,995顆衛星)
- [ ] 記憶體使用合理
- [ ] 座標轉換精度符合要求

### 接口驗證
- [ ] Stage 2 TEME 輸入正確解析
- [ ] Stage 4 可以正確接收 WGS84 輸出
- [ ] ProcessingResult 格式標準化

## 📋 移除功能的保存

### 保存至 Stage 4 實現參考
將移除的可見性功能保存至：
```
refactor_plan_v3_complete/stage4_new_implementation/
├── visibility_functions_from_stage3.py  ← 保存移除的方法
└── constellation_threshold_logic.py     ← 保存星座感知邏輯
```

## 🚨 注意事項

1. **確保 Stage 2 兼容性**: Stage 3 必須能正確處理 Stage 2 的 TEME 輸出
2. **為 Stage 4 準備輸入**: WGS84 座標必須包含足夠資訊供可見性分析
3. **保持專業標準**: 座標轉換精度不能因簡化而降低
4. **文檔同步更新**: 修正 `stage3-signal-analysis.md` 的命名和內容

## 📊 預期成果

完成後的 Stage 3 將：
- ✅ 職責單一明確 (純座標轉換)
- ✅ 符合 v3.0 架構規範
- ✅ 為 Stage 4 提供正確的 WGS84 基礎數據
- ✅ 消除與後續階段的功能重疊