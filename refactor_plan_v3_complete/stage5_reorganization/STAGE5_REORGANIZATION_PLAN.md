# 📡 Stage 5 重組計畫 - 信號品質分析層

**目標**: 將現有的信號分析功能重新組織為正確的 Stage 5，符合 v3.0 架構

## 🎯 重組目標

### 核心功能定位 (符合 final.md 需求)
1. **3GPP 標準信號計算**: RSRP/RSRQ/SINR 基於 3GPP TS 38.214
2. **ITU-R 物理模型**: 使用 ITU-R P.618 大氣衰減和傳播模型
3. **高精度信號分析**: 僅對 Stage 4 篩選出的可連線衛星進行分析
4. **為 Stage 6 準備**: 提供高品質的信號數據供 3GPP 事件檢測

## 📂 重組策略

### 方案: 重新命名和整合現有實現
```bash
# 主要重組路徑:
src/stages/stage3_signal_analysis/  →  src/stages/stage5_signal_analysis/

# 保留現有架構，更新接口和配置
```

## 🏗️ 重組後架構

### 新目錄結構
```
src/stages/stage5_signal_analysis/
├── stage5_signal_analysis_processor.py      # 主處理器 (重新命名)
├── signal_quality_calculator.py             # ✅ 保留
├── gpp_event_detector.py                    # → 移至 Stage 6
├── physics_calculator.py                    # ✅ 保留
├── config_manager.py                        # ✅ 新增
├── performance_monitor.py                   # ✅ 新增
└── __init__.py                              # ✅ 更新
```

### 功能重新分配
```
✅ 保留在 Stage 5:
- SignalQualityCalculator (RSRP/RSRQ/SINR)
- PhysicsCalculator (ITU-R P.618 模型)
- 大氣衰減計算
- 都卜勒頻移計算
- 信號品質評級

❌ 移至 Stage 6:
- GPPEventDetector (A4/A5/D2 事件檢測)
- 換手候選管理
- 3GPP 事件報告生成
```

## 🔧 重組步驟

### Step 1: 建立新的 Stage 5 目錄
```bash
# 複製現有實現
cp -r src/stages/stage3_signal_analysis/ src/stages/stage5_signal_analysis/

# 備份原實現
mv src/stages/stage3_signal_analysis/ archives/stage3_signal_analysis_backup_$(date +%Y%m%d)/
```

### Step 2: 更新主處理器
```python
# stage5_signal_analysis_processor.py

class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    """
    Stage 5: 信號品質分析層處理器 (v3.0 重構版本)

    專職責任：
    1. RSRP/RSRQ/SINR 信號品質計算 (3GPP TS 38.214)
    2. ITU-R P.618 物理傳播模型
    3. 信號品質評級和統計分析
    4. 為 Stage 6 提供高品質信號數據
    """

    def __init__(self, config=None):
        super().__init__(stage_number=5, stage_name="signal_analysis", config=config)

        # 移除 GPPEventDetector (移至 Stage 6)
        self.signal_calculator = SignalQualityCalculator()
        self.physics_calculator = PhysicsCalculator()

        # 新增性能監控
        self.performance_monitor = PerformanceMonitor()

    def process(self, stage4_input):
        """
        主處理流程 - 接收 Stage 4 的可連線衛星池

        Args:
            stage4_input: Stage 4 鏈路可行性評估結果

        Returns:
            ProcessingResult: 信號品質分析結果
        """
        # 1. 驗證 Stage 4 輸入
        feasible_satellites = self._validate_stage4_input(stage4_input)

        # 2. 對可連線衛星執行信號分析
        signal_analysis_results = self._analyze_feasible_satellites(feasible_satellites)

        # 3. 計算統計摘要
        signal_statistics = self._calculate_signal_statistics(signal_analysis_results)

        # 4. 構建標準化輸出
        return self._build_output(signal_analysis_results, signal_statistics)

    def _analyze_feasible_satellites(self, feasible_satellites):
        """只對可連線衛星進行信號分析 - 高效率實現"""
        results = {}

        for constellation in ['starlink', 'oneweb']:
            if constellation in feasible_satellites:
                constellation_satellites = feasible_satellites[constellation]['satellites']

                # 對每顆可連線衛星進行詳細信號分析
                for satellite in constellation_satellites:
                    signal_data = self._calculate_comprehensive_signal_quality(satellite)
                    results[satellite['satellite_id']] = signal_data

        return results
```

### Step 3: 移除 3GPP 事件檢測功能
```python
# 從 Stage 5 移除，保存至 Stage 6 實現:
# - gpp_event_detector.py
# - 3GPP A4/A5/D2 事件相關代碼
# - 換手候選管理邏輯

# 保存移除的功能
cp src/stages/stage5_signal_analysis/gpp_event_detector.py \
   refactor_plan_v3_complete/stage6_reorganization/gpp_event_detector_from_stage5.py
```

### Step 4: 更新輸入接口
```python
def _validate_stage4_input(self, stage4_input):
    """驗證 Stage 4 輸入格式"""
    required_fields = [
        'feasible_satellites',
        'ntpu_analysis',
        'orbital_period_analysis'
    ]

    # 確保接收到正確的可連線衛星池
    if 'feasible_satellites' not in stage4_input:
        raise ValueError("Stage 4 未提供可連線衛星池")

    return stage4_input['feasible_satellites']
```

### Step 5: 優化信號計算流程
```python
def _calculate_comprehensive_signal_quality(self, satellite):
    """對單顆可連線衛星進行全面信號品質計算"""

    # 1. 基礎 3GPP 信號計算
    basic_signals = self.signal_calculator.calculate_basic_signals(satellite)

    # 2. ITU-R 物理模型增強
    physics_enhanced = self.physics_calculator.apply_propagation_model(
        basic_signals, satellite
    )

    # 3. 信號品質評級
    quality_grade = self.signal_calculator.assess_signal_quality(physics_enhanced)

    # 4. 時間序列信號預測
    signal_trends = self.signal_calculator.analyze_signal_trends(satellite)

    return {
        'basic_signals': basic_signals,
        'physics_enhanced': physics_enhanced,
        'quality_assessment': quality_grade,
        'signal_trends': signal_trends,
        'calculation_timestamp': datetime.now(timezone.utc).isoformat()
    }
```

## 📊 新的標準化輸出格式

```python
stage5_output = {
    'stage': 'stage5_signal_analysis',
    'signal_quality_data': {
        'satellite_id': {
            'constellation': str,
            'signal_metrics': {
                'rsrp_dbm': float,          # 3GPP TS 38.214
                'rsrq_db': float,           # 3GPP TS 38.214
                'rs_sinr_db': float,        # 3GPP TS 38.214
                'path_loss_db': float,      # ITU-R P.618
                'atmospheric_loss_db': float, # ITU-R P.676
                'doppler_shift_hz': float   # 相對論都卜勒
            },
            'quality_assessment': {
                'overall_grade': str,       # 'excellent'|'good'|'fair'|'poor'
                'availability': bool,       # 是否可用於通信
                'reliability_score': float  # 0-1 可靠性評分
            },
            'signal_trends': {
                'trend_direction': str,     # 'improving'|'stable'|'degrading'
                'predicted_duration_min': float, # 可用時間預測
                'confidence_level': float   # 預測信心度
            },
            'physics_parameters': {
                'elevation_angle_deg': float,
                'azimuth_angle_deg': float,
                'distance_km': float,
                'relative_velocity_kmps': float
            }
        }
    },
    'constellation_statistics': {
        'starlink': {
            'total_analyzed': int,
            'excellent_signals': int,
            'good_signals': int,
            'average_rsrp_dbm': float,
            'coverage_reliability': float
        },
        'oneweb': {
            'total_analyzed': int,
            'excellent_signals': int,
            'good_signals': int,
            'average_rsrp_dbm': float,
            'coverage_reliability': float
        }
    },
    'metadata': {
        'processing_timestamp': str,
        'input_source': 'stage4_link_feasibility',
        'signal_analysis_standard': '3GPP_TS_38_214',
        'propagation_model': 'ITU_R_P_618',
        'total_satellites_analyzed': int,
        'processing_duration_ms': float
    }
}
```

## ✅ 重組驗證標準

### 功能驗證
- [ ] 只接收 Stage 4 的可連線衛星池
- [ ] 3GPP TS 38.214 信號計算準確
- [ ] ITU-R P.618 物理模型正確應用
- [ ] 移除所有 3GPP 事件檢測功能

### 性能驗證
- [ ] 處理時間 < 0.5秒 (僅分析可連線衛星)
- [ ] 記憶體使用優化 (比原 Stage 3 更高效)
- [ ] 信號計算精度符合學術標準

### 接口驗證
- [ ] Stage 4 輸入格式正確解析
- [ ] Stage 6 輸出格式標準化
- [ ] ProcessingResult 接口合規

## 🎯 與 final.md 需求的對應

| final.md 需求 | Stage 5 實現 |
|---------------|-------------|
| "3GPP 標準信號品質" | SignalQualityCalculator (3GPP TS 38.214) |
| "ITU-R 物理模型" | PhysicsCalculator (ITU-R P.618) |
| "高效能信號分析" | 僅對可連線衛星分析 (Stage 4 篩選後) |
| "毫秒級響應" | 優化計算流程，專注信號品質 |

## 📋 配置文件更新

### 新建 config/stage5_signal_analysis.yaml
```yaml
# Stage 5 信號品質分析配置
stage5_signal_analysis:
  signal_calculation:
    frequency_ghz: 12.0           # Ku-band
    tx_power_dbw: 40.0
    antenna_gain_db: 35.0
    noise_floor_dbm: -120.0

  quality_thresholds:
    rsrp_excellent: -80.0         # dBm
    rsrp_good: -90.0              # dBm
    rsrp_fair: -100.0             # dBm
    rsrp_poor: -110.0             # dBm

  performance:
    enable_trend_analysis: true
    prediction_window_minutes: 30
    confidence_threshold: 0.8

  academic_compliance:
    standard: "3GPP_TS_38_214"
    propagation_model: "ITU_R_P_618"
    physics_constants: "CODATA_2018"
```

## 🚨 注意事項

1. **確保 Stage 4 依賴**: Stage 5 必須等待 Stage 4 完成後才能執行
2. **移除事件檢測**: 所有 3GPP 事件檢測功能移至 Stage 6
3. **保持學術標準**: 信號計算精度和標準合規性不能降低
4. **性能優化**: 利用 Stage 4 篩選減少計算量，提高效率

完成重組後的 Stage 5 將專注於高品質的信號分析，為 Stage 6 的 3GPP 事件檢測和強化學習提供精確的信號基礎數據。