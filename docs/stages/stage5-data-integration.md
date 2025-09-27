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

### 🏗️ v2.0 增強模組化架構

Stage 5 專注於數據格式化、智能融合和學術標準驗證：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Stage 5: 數據整合層 (v2.0增強版)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🔄 核心數據處理模組                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Timeseries   │  │Animation    │  │Layer Data   │  │Format       │    │
│  │Converter    │  │Builder      │  │Generator    │  │Converter Hub│    │
│  │             │  │             │  │             │  │             │    │
│  │ • 時序轉換   │  │ • 軌跡動畫   │  │ • 分層數據   │  │ • JSON/CSV  │    │
│  │ • 插值處理   │  │ • 關鍵幀生成 │  │ • 階層組織   │  │ • GeoJSON   │    │
│  │ • 壓縮優化   │  │ • 平滑處理   │  │ • 索引建立   │  │ • 版本控制   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│ 🧠 智能融合與驗證層                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Intelligent  │  │Handover     │  │Academic     │  │Cross-Stage  │    │
│  │Data Fusion  │  │Scenario     │  │Standards    │  │Validator    │    │
│  │Engine       │  │Engine       │  │Validator    │  │             │    │
│  │             │  │             │  │             │  │             │    │
│  │ • 雙源融合   │  │ • 3GPP A4/A5│  │ • Grade A/B │  │ • 數據一致性 │    │
│  │ • 智能整合   │  │ • RSRP計算  │  │ • 零容忍檢查 │  │ • 格式驗證   │    │
│  │ • 品質保證   │  │ • 換手分析   │  │ • 學術合規   │  │ • 錯誤處理   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                    ▼                                      │
│           ┌─────────────────────────────────────────────┐               │
│           │           Stage5 Data Integration Processor │               │
│           │                                             │               │
│           │ • 統一數據流協調                              │               │
│           │ • 多階段數據融合                              │               │
│           │ • 智能品質檢查                                │               │
│           │ • 學術標準合規                                │               │
│           │ • 性能監控與優化                              │               │
│           └─────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### v2.0 增強核心原則
- **格式標準化**: 提供標準化的數據輸出格式
- **多格式支援**: 支援JSON、時間序列、動畫等9種格式
- **智能數據融合**: 階段三科學數據 + 階段四動畫數據雙源整合
- **學術標準合規**: Grade A/B/C零容忍學術標準驗證
- **3GPP標準**: A4/A5換手場景完全合規
- **性能優化**: 高效的數據轉換和處理（<60秒）
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

## 🧠 進階智能模組

### 6. Intelligent Data Fusion Engine (`intelligent_data_fusion_engine.py`)

#### 功能職責
- 智能融合階段三科學數據與階段四動畫數據
- 提供統一增強時間序列數據結構
- 自適應數據來源選擇和品質保證
- 雙源數據一致性驗證

#### 核心方法
```python
class IntelligentDataFusionEngine:
    def fuse_stage_data(self, stage3_data, stage4_data):
        """智能融合多階段數據"""

    def create_enhanced_timeseries(self, fused_data):
        """創建增強時間序列"""

    def validate_data_consistency(self, data_sources):
        """驗證數據一致性"""
```

### 7. Handover Scenario Engine (`handover_scenario_engine.py`)

#### 功能職責
- 生成3GPP A4/A5換手場景
- 計算動態RSRP閾值（基於3GPP標準）
- 分析換手機會和最佳換手窗口
- 提供換手決策支援數據

#### 核心方法
```python
class HandoverScenarioEngine:
    def generate_a4_scenarios(self, satellite_data):
        """生成A4換手場景"""

    def calculate_dynamic_rsrp_threshold(self, noise_floor):
        """計算動態RSRP閾值"""

    def analyze_handover_opportunities(self, timeseries):
        """分析換手機會"""
```

### 8. Academic Standards Validator (`stage5_academic_standards_validator.py`)

#### 功能職責
- 實施Grade A/B/C學術標準合規檢查
- 零容忍運行時數據驗證
- 跨階段數據整合完整性檢查
- 學術論文級品質保證

#### 核心方法
```python
class Stage5AcademicStandardsValidator:
    def validate_grade_a_compliance(self, data):
        """Grade A合規性檢查"""

    def perform_zero_tolerance_checks(self, integration_result):
        """零容忍運行時檢查"""

    def validate_cross_stage_integrity(self, multi_stage_data):
        """跨階段數據完整性驗證"""
```

### 9. Cross-Stage Validator (`cross_stage_validator.py`)

#### 功能職責
- 跨階段數據一致性驗證
- 數據格式標準化檢查
- 錯誤處理和異常管理
- 數據流完整性監控

## 🔄 數據流程

### 輸入處理
```python
# v2.0 增強輸入：多階段數據源
input_sources = {
    'stage3_data': {
        'source': '/app/data/signal_quality_analysis_output.json',
        'provides': ['position_timeseries', 'elevation_deg', 'signal_quality', '3gpp_events']
    },
    'stage4_data': {
        'source': 'data/outputs/stage4/',
        'provides': ['optimal_pool', 'handover_strategy', 'track_points', 'animation_metadata']
    }
}
```

### v2.0 增強處理流程
1. **多源數據載入**: 同時載入階段三科學數據與階段四優化數據
2. **智能數據融合**: 使用IntelligentDataFusionEngine進行雙源整合
3. **學術標準驗證**: Grade A/B/C合規性檢查與零容忍驗證
4. **換手場景生成**: 3GPP A4/A5標準換手場景分析
5. **時間序列轉換**: 融合數據轉換為標準時序格式
6. **動畫數據建構**: 生成軌跡動畫和關鍵幀
7. **分層數據生成**: 創建多尺度索引和階層結構
8. **跨階段驗證**: 數據一致性與完整性最終檢查
9. **多格式輸出**: 轉換為JSON、GeoJSON、CSV等格式

### v2.0 增強輸出格式
```python
stage5_output = {
    'stage': 'stage5_data_integration',
    'version': '2.0_enhanced',

    # 核心數據產品
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

    # v2.0 增強功能
    'intelligent_fusion_results': {
        'fused_satellite_count': 150,
        'data_sources_integrated': ['stage3', 'stage4'],
        'fusion_quality_score': 0.95,
        'enhanced_timeseries': {...}
    },
    'handover_scenarios': {
        'a4_scenarios': [...],
        'a5_scenarios': [...],
        'total_handover_opportunities': 45,
        '3gpp_compliance_status': 'verified'
    },
    'academic_validation': {
        'grade_a_compliance': True,
        'zero_tolerance_checks': 'passed',
        'validation_timestamp': '2025-09-26T10:00:00Z',
        'quality_metrics': {...}
    },

    # 多格式輸出
    'formatted_outputs': {
        'json': {...},
        'geojson': {...},
        'csv': {...},
        'api_package': {...}
    },

    # 增強元數據
    'metadata': {
        'processing_time': '2025-09-26T10:00:00Z',
        'processed_satellites': 150,
        'output_formats': 4,
        'compression_ratio': 0.72,
        'fusion_duration_seconds': 12.5,
        'validation_duration_seconds': 3.2,
        'total_processing_duration': 58.7
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

## 🎯 v2.0 增強性能指標

### 核心處理效能
- **輸入數據**: 約150-250顆優化後衛星（雙源融合）
- **計算時間**: 50-60秒（包含智能融合12.5s + 驗證3.2s）
- **記憶體使用**: <1GB
- **輸出數據**: 9種格式數據包（原4種 + 5種增強）

### 智能融合效能
- **融合成功率**: >95%
- **數據一致性**: 100%（零容忍檢查）
- **3GPP合規**: A4/A5場景100%標準合規
- **Grade A驗證**: 實時零容忍檢查

### 轉換效率
- **壓縮比**: >70%
- **格式轉換**: 並行處理（9種格式）
- **數據查詢**: <10ms響應
- **動畫幀率**: 30 FPS穩定
- **換手場景生成**: <5秒

## 🔍 v2.0 增強驗證標準

### 多源輸入驗證
- 階段三科學數據完整性（仰角、信號品質）
- 階段四優化數據有效性（動畫軌跡、性能數據）
- 衛星數量合理性與數據來源一致性
- 跨階段時間戳同步驗證

### 智能融合驗證
- 雙源數據對齊精度（<1秒時間差）
- 融合算法正確性（數學模型驗證）
- 數據品質評分（>0.9為合格）
- 增強時間序列完整性

### 學術標準驗證
- **Grade A**: 真實數據源驗證、完整算法實現
- **Grade B**: 標準模型合規性檢查
- **Grade C**: 零簡化、零假設驗證
- **3GPP合規**: A4/A5事件標準合規
- **零容忍檢查**: 6大類別運行時驗證

### 輸出驗證
- 9種格式數據一致性（原4種 + 融合5種）
- 壓縮品質保證（無數據損失）
- API格式標準合規（向後兼容）
- 換手場景數據準確性（3GPP標準驗證）

---
**下一處理器**: [持久化與API層](./stage6-persistence-api.md)
**相關文檔**: [v2.0重構計劃](../refactoring_plan_v2/stage5_data_processing.md)