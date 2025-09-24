# 🛰️ 階段二：軌道計算與鏈路可行性評估層

[🔄 返回文檔總覽](../README.md) > 階段二

## 📖 階段概述

**目標**：接收Stage 1的TLE數據，執行SGP4軌道計算和衛星鏈路可行性評估
**輸入**：Stage 1的驗證TLE數據 + 時間基準（記憶體傳遞）
**輸出**：軌道計算結果 + 鏈路可行性分析 → 記憶體傳遞至階段三
**核心工作**：
1. 使用標準SGP4/SDP4算法進行軌道傳播計算
2. TEME→ITRF→WGS84座標系統精確轉換（使用Skyfield專業庫）
3. 計算相對NTPU觀測點的仰角、方位角、距離
4. 多重約束篩選：
   - 基礎可見性檢查（仰角 > 0°）
   - 星座特定服務門檻（Starlink: 5°, OneWeb: 10°）
   - 鏈路預算約束（200-2000km距離範圍）
   - 系統邊界驗證（地理邊界）

**實際結果**：約500-1000顆可建立通訊鏈路的衛星含完整軌道數據
**時間基準**：嚴格使用Stage 1提供的TLE epoch時間
**處理時間**：約2-3分鐘 (完整SGP4軌道計算)

### 🏗️ v2.0 模組化架構

Stage 2 採用8模組設計（4個核心模組 + 4個優化模組），專注於軌道計算核心職責：

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Stage 2: 軌道計算層                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │SGP4 Calculator│  │Coordinate   │  │Link Feasib. │  │Visibility   │        │
│  │             │  │Converter    │  │Filter       │  │Filter       │        │
│  │ • SGP4傳播   │  │ • TEME→ITRF │  │ • 星座門檻   │  │ • 快速篩選   │        │
│  │ • SDP4深空   │  │ • ITRF→WGS84│  │ • 鏈路預算   │  │ • 批次處理   │        │
│  │ • 精度控制   │  │ • 地心轉換   │  │ • 服務窗口   │  │ • 預計算快取 │        │
│  │ • 批次計算   │  │ • 角度計算   │  │ • 可行性評分 │  │ • 幾何檢查   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │               │               │                 │
│           └──────────────┼───────────────┼───────────────┘                 │
│                          │               │                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │Parallel SGP4│  │GPU Coordinate│  │Optimized    │                        │
│  │Calculator   │  │Converter    │  │Stage2       │                        │
│  │             │  │             │  │Processor    │                        │
│  │ • 並行計算   │  │ • GPU加速    │  │ • 性能整合   │                        │
│  │ • 負載分配   │  │ • CUDA支援   │  │ • 資源管理   │                        │
│  │ • 結果聚合   │  │ • 記憶體優化 │  │ • 動態調度   │                        │
│  └─────────────┘  └─────────────┘  └─────────────┘                        │
│           │              │               │                                 │
│           └──────────────┼───────────────┘                                 │
│                          ▼                                                 │
│           ┌─────────────────────────────────────────────┐                 │
│           │        Stage2 Orbital Processor            │                 │
│           │                                             │                 │
│           │ • 計算流程協調 • 優化模組整合                │                 │
│           │ • 時間序列管理 • 性能監控                    │                 │
│           │ • 並行處理控制 • 動態負載平衡                │                 │
│           │ • 結果品質驗證 • 資源使用優化                │                 │
│           └─────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 核心原則
- **計算精度**: 使用標準SGP4/SDP4算法確保軌道計算精度
- **時間基準**: 嚴格使用TLE epoch時間作為計算基準
- **座標標準**: 使用Skyfield專業庫進行精確座標轉換
- **鏈路導向**: 篩選可建立通訊鏈路的衛星，非純幾何可見性
- **星座感知**: 支援不同星座的特定服務門檻標準

## 📦 模組設計

### 1. SGP4 Calculator (`sgp4_calculator.py`)

#### 功能職責
- 實現標準SGP4/SDP4軌道傳播算法
- 處理近地和深空衛星軌道
- 提供高精度位置和速度計算
- 支援批次計算和時間序列生成

#### 核心方法
```python
class SGP4Calculator:
    def calculate_position(self, tle_data, time_since_epoch):
        """計算指定時間的衛星位置"""

    def batch_calculate(self, tle_data_list, time_series):
        """批次計算多顆衛星的軌道"""

    def validate_calculation_accuracy(self, results):
        """驗證計算精度"""
```

### 2. Coordinate Converter (`coordinate_converter.py`)

#### 功能職責
- TEME到ITRF座標系統轉換
- ITRF到WGS84地理座標轉換
- 地心到地平座標系統轉換
- 支援高精度時間和極移參數

#### 核心方法
```python
class CoordinateConverter:
    def teme_to_itrf(self, position, velocity, time):
        """TEME到ITRF轉換"""

    def itrf_to_wgs84(self, position):
        """ITRF到WGS84轉換"""

    def calculate_look_angles(self, sat_pos, observer_pos):
        """計算觀測角度"""
```

### 3. Link Feasibility Filter (`link_feasibility_filter.py`)

#### 功能職責
- 基礎可見性檢查（幾何可見性）
- 星座特定服務門檻篩選（Starlink: 5°, OneWeb: 10°）
- 鏈路預算約束檢查（距離範圍200-2000km）
- 系統邊界驗證（地理邊界）
- 服務窗口計算（可通訊時間段）

> **📖 技術驗證**: 距離計算方法的科學依據和國際標準驗證詳見 [距離計算驗證報告](../technical/distance_calculation_validation.md)

#### 核心方法
```python
class LinkFeasibilityFilter:
    def apply_constellation_elevation_threshold(self, satellites, constellation):
        """應用星座特定仰角門檻篩選"""

    def apply_link_budget_constraints(self, satellites):
        """應用鏈路預算約束"""

    def calculate_service_windows(self, satellite_positions):
        """計算服務時間窗口"""
```

### 4. Stage2 Orbital Processor (`stage2_orbital_computing_processor.py`)

#### 功能職責
- 協調整個軌道計算流程
- 管理時間序列生成
- 控制並行處理
- 驗證結果品質

### 5. 優化模組 (Performance Enhancement Modules)

#### 5.1 Optimized Stage2 Processor (`optimized_stage2_processor.py`)

##### 功能職責
- 提供高性能版本的階段二處理器
- 整合並行計算和GPU加速功能
- 優化大規模衛星處理流程
- 動態資源管理和負載平衡

##### 核心方法
```python
class OptimizedStage2Processor:
    def initialize_performance_optimizations(self):
        """初始化性能優化配置"""

    def process_with_parallel_computing(self, satellite_data):
        """並行處理衛星數據"""

    def optimize_memory_usage(self):
        """優化記憶體使用"""
```

#### 5.2 Parallel SGP4 Calculator (`parallel_sgp4_calculator.py`)

##### 功能職責
- 實現SGP4算法的並行計算版本
- 支援多線程/多進程批次處理
- 優化CPU密集型軌道計算
- 動態工作負載分配

##### 核心方法
```python
class ParallelSGP4Calculator:
    def parallel_batch_calculate(self, tle_data_list, time_series):
        """並行批次計算多顆衛星軌道"""

    def distribute_workload(self, satellites, worker_count):
        """分配工作負載到多個處理器"""

    def aggregate_parallel_results(self, worker_results):
        """聚合並行處理結果"""
```

#### 5.3 GPU Coordinate Converter (`gpu_coordinate_converter.py`)

##### 功能職責
- 利用GPU加速座標轉換計算
- 支援CUDA/OpenCL並行處理
- 優化大規模矩陣運算
- 記憶體轉移優化

##### 核心方法
```python
class GPUCoordinateConverter:
    def gpu_batch_teme_to_itrf(self, positions, times):
        """GPU加速TEME到ITRF批次轉換"""

    def gpu_batch_calculate_look_angles(self, satellite_positions):
        """GPU加速批次計算觀測角度"""

    def optimize_gpu_memory_transfer(self, data):
        """優化GPU記憶體傳輸"""
```

#### 5.4 Visibility Filter (`visibility_filter.py`)

##### 功能職責
- 專用高效可見性篩選引擎
- 幾何可見性快速判斷
- 批次篩選優化
- 預計算和快取機制

##### 核心方法
```python
class VisibilityFilter:
    def fast_elevation_check(self, satellite_positions, observer_location):
        """快速仰角檢查"""

    def batch_visibility_assessment(self, satellites):
        """批次可見性評估"""

    def precompute_visibility_cache(self):
        """預計算可見性快取"""
```

## 🔄 數據流程

### 輸入處理
```python
# 從Stage 1接收數據
stage1_output = {
    'tle_records': [...],  # 驗證過的TLE數據
    'base_time': '2025-09-21T04:00:00Z',  # 時間基準
    'metadata': {...}
}
```

### 處理流程
1. **TLE數據驗證**: 確認從Stage 1接收的數據完整性
2. **SGP4軌道計算**: 使用標準算法計算軌道位置
3. **座標系統轉換**: TEME→ITRF→WGS84→地平座標
4. **可見性分析**: 計算仰角、方位角，應用篩選條件
5. **結果整合**: 組織輸出數據格式

### 輸出格式
```python
stage2_output = {
    'stage': 'stage2_orbital_computing',
    'satellites': {
        'satellite_id': {
            'positions': [...],  # 時間序列位置數據
            'visibility_windows': [...],  # 可見性窗口
            'orbital_parameters': {...}  # 軌道參數
        }
    },
    'metadata': {
        'processing_time': '2025-09-21T04:05:00Z',
        'calculation_base_time': '2025-09-21T04:00:00Z',
        'total_satellites': 8837,
        'visible_satellites': 756
    }
}
```

## ⚙️ 配置參數

### 軌道計算配置
```yaml
orbital_calculation:
  algorithm: "SGP4"           # 使用標準SGP4算法
  time_resolution: 30         # 30秒時間解析度
  prediction_horizon: 24      # 24小時預測窗口
  coordinate_system: "TEME"   # 初始座標系統
```

### 鏈路可行性篩選配置
```yaml
link_feasibility_filter:
  # 星座特定服務門檻
  constellation_elevation_thresholds:
    starlink: 5.0             # Starlink LEO低軌使用5°
    oneweb: 10.0              # OneWeb MEO中軌使用10°
    other: 10.0               # 其他衛星預設10°

  # 鏈路預算約束
  min_distance_km: 200        # 最小距離（避免多普勒過大）
  max_distance_km: 2000       # 最大距離（確保信號強度）

  # 觀測者位置（NTPU精確座標）
  observer_location:
    latitude: 24.9441         # 24°56'39"N
    longitude: 121.3714       # 121°22'17"E
    altitude_km: 0.035        # 35米海拔
```

## 🎯 性能指標

### 處理效能
- **輸入數據**: 8,837顆衛星TLE數據
- **計算時間**: 2-3分鐘
- **記憶體使用**: <1GB
- **輸出數據**: 約500-1000顆可見衛星

### 精度要求
- **位置精度**: <1km誤差
- **時間精度**: <1秒誤差
- **角度精度**: <0.1度誤差

## 🔍 驗證標準

### 輸入驗證
- TLE數據格式完整性
- 時間基準一致性
- 數據血統追蹤

### 計算驗證
- SGP4算法標準合規
- 座標轉換精度檢查
- 可見性邏輯正確性

### 輸出驗證
- 數據結構完整性
- 可見衛星數量合理性
- 處理時間性能達標

---
**下一處理器**: [信號品質分析](./stage3-signal-analysis.md)
**相關文檔**: [v2.0重構計劃](../refactoring_plan_v2/stage2_orbital_computing.md)