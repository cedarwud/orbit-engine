# 📊 階段五：數據整合層

[🔄 返回文檔總覽](../README.md) > 階段五

## 📖 階段概述

**目標**：將優化決策結果轉換為多種輸出格式，為前端和API服務準備數據
**輸入**：Stage 4優化決策層記憶體傳遞的優化池數據和決策結果
**輸出**：多格式數據包 + 動畫數據 → 記憶體傳遞至階段六
**核心工作**：
1. 時間序列數據轉換和插值處理
2. 動畫軌跡數據建構和關鍵幀生成
3. 分層數據結構和索引建立
4. 多格式輸出（JSON、GeoJSON、CSV等）

**實際處理**：約150-250顆優化後衛星的多格式轉換
**處理時間**：約50-60秒（v2.0優化版本）

### 🏗️ v2.0 模組化架構

Stage 5 專注於數據格式化和前端準備：

```
┌─────────────────────────────────────────────────────────────┐
│                   Stage 5: 數據整合層                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │Timeseries   │  │Animation    │  │Layer Data   │       │
│  │Converter    │  │Builder      │  │Generator    │       │
│  │             │  │             │  │             │       │
│  │ • 時序轉換   │  │ • 軌跡動畫   │  │ • 分層數據   │       │
│  │ • 插值處理   │  │ • 關鍵幀生成 │  │ • 階層組織   │       │
│  │ • 壓縮優化   │  │ • 平滑處理   │  │ • 索引建立   │       │
│  │ • 格式標準   │  │ • 效果數據   │  │ • 查詢優化   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│           │              │               │                │
│           └──────────────┼───────────────┘                │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │     Format Converter Hub        │            │
│           │                                 │            │
│           │ • JSON/XML/CSV轉換              │            │
│           │ • GeoJSON地理格式               │            │
│           │ • 壓縮和打包                     │            │
│           │ • 版本控制                       │            │
│           └─────────────────────────────────┘            │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │  Stage5 Data Processor         │            │
│           │                                 │            │
│           │ • 數據流協調                     │            │
│           │ • 品質檢查                       │            │
│           │ • 性能優化                       │            │
│           │ • 輸出管理                       │            │
│           └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 核心原則
- **格式標準化**: 提供標準化的數據輸出格式
- **多格式支援**: 支援JSON、時間序列、動畫等多種格式
- **性能優化**: 高效的數據轉換和處理
- **前端友好**: 直接可用的前端數據格式

## 📦 模組設計

### 1. Timeseries Converter (`timeseries_converter.py`)

#### 功能職責
- 將衛星池數據轉換為時間序列格式
- 提供時間插值和重採樣功能
- 生成時間窗口數據
- 優化時序數據存儲

#### 核心方法
```python
class TimeseriesConverter:
    def convert_to_timeseries(self, satellite_pool):
        """轉換為時間序列數據集"""

    def generate_time_windows(self, timeseries, window_duration):
        """生成時間窗口數據"""

    def interpolate_missing_data(self, timeseries):
        """插值缺失數據"""

    def compress_timeseries(self, timeseries):
        """壓縮時間序列數據"""
```

### 2. Animation Builder (`animation_builder.py`)

#### 功能職責
- 生成衛星軌跡動畫數據
- 創建關鍵幀和補間數據
- 提供平滑動畫效果
- 優化動畫性能

#### 核心方法
```python
class AnimationBuilder:
    def build_satellite_animation(self, timeseries):
        """建構衛星動畫數據"""

    def generate_trajectory_keyframes(self, satellite_timeseries):
        """生成軌跡關鍵幀"""

    def create_coverage_animation(self, satellite_pool):
        """創建覆蓋範圍動畫"""

    def optimize_animation_performance(self, animation):
        """優化動畫性能"""
```

### 3. Layer Data Generator (`layer_data_generator.py`)

#### 功能職責
- 生成分層數據結構
- 建立數據索引和查詢優化
- 提供階層式數據組織
- 支援多尺度數據訪問

#### 核心方法
```python
class LayerDataGenerator:
    def generate_hierarchical_data(self, timeseries):
        """生成階層式數據集"""

    def create_spatial_layers(self, satellite_data):
        """創建空間分層"""

    def create_temporal_layers(self, timeseries):
        """創建時間分層"""

    def build_multi_scale_index(self, hierarchical_data):
        """建立多尺度索引"""
```

### 4. Format Converter Hub (`format_converter_hub.py`)

#### 功能職責
- 統一格式轉換管理
- 支援多種輸出格式
- 提供版本控制
- 優化轉換性能

#### 核心方法
```python
class FormatConverterHub:
    def convert_to_json(self, data, schema_version):
        """轉換為JSON格式"""

    def convert_to_geojson(self, spatial_data):
        """轉換為GeoJSON格式"""

    def convert_to_csv(self, tabular_data):
        """轉換為CSV格式"""

    def package_for_api(self, data, api_version):
        """打包為API格式"""
```

### 5. Stage5 Data Processor (`data_integration_processor.py`)

#### 功能職責
- 協調數據處理流程
- 管理格式轉換
- 品質檢查和驗證
- 輸出管理和優化

## 🔄 數據流程

### 輸入處理
```python
# 從Stage 4接收數據
stage4_output = {
    'optimal_pool': {...},        # 優化後的衛星池
    'handover_strategy': {...},   # 換手策略
    'optimization_results': {...}, # 優化結果
    'metadata': {...}             # 處理元數據
}
```

### 處理流程
1. **輸入數據驗證**: 確認從Stage 4接收的數據完整性
2. **時間序列轉換**: 將優化池數據轉換為時間序列
3. **動畫數據建構**: 生成軌跡動畫和關鍵幀
4. **分層數據生成**: 創建多尺度索引和階層結構
5. **多格式輸出**: 轉換為JSON、GeoJSON、CSV等格式

### 輸出格式
```python
stage5_output = {
    'stage': 'stage5_data_integration',
    'timeseries_data': {
        'dataset_id': '...',
        'satellite_count': 150,
        'time_range': {...},
        'sampling_frequency': '10S',
        'satellite_timeseries': {...}
    },
    'animation_data': {
        'animation_id': '...',
        'duration': 300,  # seconds
        'frame_rate': 30,
        'satellite_trajectories': {...},
        'coverage_animation': {...}
    },
    'hierarchical_data': {
        'spatial_layers': [...],
        'temporal_layers': [...],
        'quality_layers': [...],
        'multi_scale_index': {...}
    },
    'formatted_outputs': {
        'json': {...},
        'geojson': {...},
        'csv': {...},
        'api_package': {...}
    },
    'metadata': {
        'processing_time': '2025-09-21T04:09:00Z',
        'processed_satellites': 150,
        'output_formats': 4,
        'compression_ratio': 0.72
    }
}
```

## ⚙️ 配置參數

### 時間序列配置
```yaml
timeseries:
  sampling_frequency: "10S"        # 10秒採樣頻率
  interpolation_method: "cubic_spline"  # 三次樣條插值
  compression_enabled: true        # 啟用壓縮
  compression_level: 6             # 壓縮等級
```

### 動畫配置
```yaml
animation:
  frame_rate: 30                   # 30 FPS
  duration_seconds: 300            # 5分鐘動畫
  keyframe_optimization: true      # 關鍵幀優化
  effect_quality: "high"           # 高品質效果
```

### 分層配置
```yaml
layers:
  spatial_resolution_levels: 5     # 5級空間解析度
  temporal_granularity: ["1MIN", "10MIN", "1HOUR"]
  quality_tiers: ["high", "medium", "low"]
  enable_spatial_indexing: true    # 啟用空間索引
```

## 🎯 性能指標

### 處理效能
- **輸入數據**: 約150-250顆優化後衛星
- **計算時間**: 50-60秒
- **記憶體使用**: <1GB
- **輸出數據**: 多格式數據包

### 轉換效率
- **壓縮比**: >70%
- **格式轉換**: 並行處理
- **數據查詢**: <10ms響應
- **動畫幀率**: 30 FPS穩定

## 🔍 驗證標準

### 輸入驗證
- 優化池數據完整性
- 決策結果有效性
- 衛星數量合理性

### 轉換驗證
- 時間序列插值精度
- 動畫關鍵幀準確性
- 分層索引正確性

### 輸出驗證
- 多格式數據一致性
- 壓縮品質保證
- API格式標準合規

---
**下一處理器**: [持久化與API層](./stage6-persistence-api.md)
**相關文檔**: [v2.0重構計劃](../refactoring_plan_v2/stage5_data_processing.md)