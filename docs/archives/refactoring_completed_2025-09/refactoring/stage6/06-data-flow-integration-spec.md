# 數據流整合規格 - Stage 6 核心組件

**依據**: `docs/stages/stage6-research-optimization.md` Line 216-562
**目標**: 正確整合 Stage 1-5 的數據流

---

## 🎯 核心職責

確保 Stage 6 正確訪問和處理上游階段的數據：
1. **Stage 5 數據訪問**: 信號品質分析數據
2. **Stage 4 數據訪問**: 可連線衛星池數據
3. **Stage 1 數據訪問**: 星座配置和研究參數
4. **數據格式轉換**: 處理 ProcessingResult 和 Dict 格式

---

## 📥 上游依賴數據結構

### 從 Stage 5 接收的數據 (文檔 Line 218-259)

```python
# Stage 5 輸出數據結構
stage5_output = {
    'stage': 'stage5_signal_analysis',
    'signal_analysis': {
        'STARLINK-1234': {
            'satellite_id': 'STARLINK-1234',
            'signal_quality': {                      # ← A4/A5 事件核心
                'rsrp_dbm': -88.5,                   # 參考信號接收功率
                'rsrq_db': -10.2,                    # 參考信號接收品質
                'rs_sinr_db': 12.8,                  # 信號干擾噪聲比
                'calculation_standard': '3GPP_TS_38.214'
            },
            'physical_parameters': {                 # ← D2 事件與 ML 核心
                'path_loss_db': 165.3,
                'atmospheric_loss_db': 2.1,
                'doppler_shift_hz': 15234.5,
                'propagation_delay_ms': 4.5,
                'distance_km': 1350.2                # 斜距 (D2 事件核心)
            },
            'quality_assessment': {                  # ← ML 訓練核心
                'quality_level': 'excellent',        # excellent/good/fair/poor
                'is_usable': True,
                'quality_score': 0.92,               # 0-1 標準化分數
                'link_margin_db': 15.2
            },
            'link_budget_detail': {
                'tx_power_dbm': 30.0,
                'total_gain_db': 45.2,
                'total_loss_db': 167.4
            },
            'visibility_metrics': {
                'elevation_deg': 45.3,
                'azimuth_deg': 123.5,
                'is_visible': True,
                'is_connectable': True
            },
            'current_position': {
                'latitude_deg': 25.1234,
                'longitude_deg': 121.5678,
                'altitude_km': 550.123
            }
        },
        # ... 更多衛星 (2000+)
    },
    'analysis_summary': {
        'total_satellites_analyzed': 2059,
        'signal_quality_distribution': {...},
        'usable_satellites': 1823,
        'average_rsrp_dbm': -92.3,
        'average_sinr_db': 10.5
    },
    'metadata': {...}
}
```

### 從 Stage 4 接收的數據 (透過 Stage 5 傳遞，文檔 Line 256-260)

```python
# Stage 4 輸出數據結構 (含完整時間序列)
stage4_output = {
    'stage': 'stage4_link_feasibility',
    'connectable_satellites': {
        'starlink': [
            {
                'satellite_id': 'STARLINK-1234',
                'time_series': [                     # ← 完整時間序列，非單一時間點
                    {
                        'timestamp': '2025-09-27T08:00:00+00:00',
                        'is_connectable': True,
                        'elevation_deg': 15.3,
                        'distance_km': 750.2,
                        'rsrp_dbm': -88.5,
                        'link_budget_valid': True
                    },
                    {
                        'timestamp': '2025-09-27T08:01:00+00:00',
                        'is_connectable': False,
                        'elevation_deg': 4.8,
                        'distance_km': 1950.3,
                        'rsrp_dbm': -105.2,
                        'link_budget_valid': False
                    },
                    # ... 更多時間點 (120+ 時間點，2小時窗口)
                ]
            },
            # ... 更多衛星 (2000+)
        ],
        'oneweb': [
            # 類似結構
        ]
    },
    'feasibility_summary': {...},
    'metadata': {...}
}
```

### 從 Stage 1 接收的配置 (透過前階段傳遞，文檔 Line 261-265)

```python
# Stage 1 配置數據
stage1_config = {
    'constellation_configs': {
        'starlink': {
            'constellation_name': 'Starlink',
            'expected_visible_satellites': [10, 15],  # ← 池目標驗證
            'elevation_threshold_deg': 5.0,
            'orbit_type': 'LEO',
            'orbit_period_minutes': [90, 95]
        },
        'oneweb': {
            'constellation_name': 'OneWeb',
            'expected_visible_satellites': [3, 6],    # ← 池目標驗證
            'elevation_threshold_deg': 10.0,
            'orbit_type': 'MEO',
            'orbit_period_minutes': [109, 115]
        }
    },
    'research_configuration': {
        'observation_location': {
            'name': 'NTPU',
            'latitude_deg': 24.9442,
            'longitude_deg': 121.3714,
            'altitude_m': 50.0
        }
    }
}
```

---

## 🔄 數據訪問實現

### Stage 6 主處理器數據訪問

```python
class Stage6ResearchOptimizationProcessor(BaseStageProcessor):
    """Stage 6 研究數據生成與優化處理器"""

    def _process_research_optimization(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行主要的研究優化流程"""

        # ========== 數據提取與格式轉換 ==========

        # 1. 提取 Stage 5 信號分析數據
        signal_analysis = self._extract_signal_analysis(input_data)

        # 2. 提取 Stage 4 可連線衛星數據 (含時間序列)
        connectable_satellites = self._extract_connectable_satellites(input_data)

        # 3. 提取 Stage 1 配置數據
        constellation_configs = self._extract_constellation_configs(input_data)

        # ========== 核心處理流程 ==========

        # Step 1: 3GPP 事件檢測 (使用 Stage 5 信號數據)
        gpp_events = self._detect_gpp_events(signal_analysis)

        # Step 2: 動態池優化 (使用 Stage 4 時間序列數據)
        pool_verification = self._verify_satellite_pools(
            connectable_satellites,
            constellation_configs
        )

        # Step 3: ML 訓練數據生成 (使用 Stage 5 信號數據 + 3GPP 事件)
        ml_training_data = self._generate_ml_training_data(
            signal_analysis,
            gpp_events,
            pool_verification
        )

        # Step 4: 實時決策支援 (使用 Stage 5 信號數據 + 3GPP 事件)
        decision_support = self._generate_decision_support(
            signal_analysis,
            gpp_events
        )

        # Step 5: 構建標準化輸出
        return self._build_stage6_output(
            gpp_events,
            pool_verification,
            ml_training_data,
            decision_support
        )

    # ========== 數據提取方法 ==========

    def _extract_signal_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取信號分析數據

        支援格式:
        1. Stage 5 直接輸出: input_data['signal_analysis']
        2. ProcessingResult 包裝: input_data.data['signal_analysis']
        3. 完整 Stage 5 輸出: input_data['signal_analysis']
        """
        # 方式1: 直接包含 signal_analysis
        if 'signal_analysis' in input_data:
            return input_data['signal_analysis']

        # 方式2: ProcessingResult 格式
        if hasattr(input_data, 'data') and 'signal_analysis' in input_data.data:
            return input_data.data['signal_analysis']

        # 方式3: 嵌套在 stage5_output 中
        if 'stage5_output' in input_data:
            stage5_output = input_data['stage5_output']
            if 'signal_analysis' in stage5_output:
                return stage5_output['signal_analysis']

        # 異常處理
        self.logger.error("無法提取 signal_analysis 數據")
        raise ValueError("輸入數據缺少 signal_analysis 字段")

    def _extract_connectable_satellites(self, input_data: Dict[str, Any]) -> Dict[str, List]:
        """提取可連線衛星數據 (含時間序列)

        ⚠️ 重要: Stage 4 數據包含完整時間序列，必須正確解析

        返回格式:
        {
            'starlink': [
                {
                    'satellite_id': 'STARLINK-1234',
                    'time_series': [...]  # 完整時間序列
                }
            ],
            'oneweb': [...]
        }
        """
        # Stage 5 會傳遞 Stage 4 數據
        connectable_satellites = None

        # 嘗試從多個可能位置提取
        if 'connectable_satellites' in input_data:
            connectable_satellites = input_data['connectable_satellites']
        elif 'stage4_output' in input_data:
            connectable_satellites = input_data['stage4_output'].get('connectable_satellites')
        elif 'metadata' in input_data:
            # 有些階段會在 metadata 中傳遞上游數據
            connectable_satellites = input_data['metadata'].get('connectable_satellites')

        if connectable_satellites is None:
            self.logger.warning("無法提取 connectable_satellites 數據，池驗證將跳過")
            return {'starlink': [], 'oneweb': []}

        # 驗證數據結構 (確保包含時間序列)
        if not self._validate_time_series_structure(connectable_satellites):
            self.logger.error("connectable_satellites 數據結構無效 (缺少時間序列)")
            return {'starlink': [], 'oneweb': []}

        return connectable_satellites

    def _validate_time_series_structure(self, connectable_satellites: Dict) -> bool:
        """驗證時間序列數據結構

        確保每顆衛星包含完整的 time_series 字段
        """
        for constellation in ['starlink', 'oneweb']:
            if constellation not in connectable_satellites:
                continue

            satellites = connectable_satellites[constellation]
            if not satellites:
                continue

            # 抽樣檢查第一顆衛星
            sample_sat = satellites[0]
            if 'time_series' not in sample_sat:
                self.logger.error(f"{constellation} 衛星缺少 time_series 字段")
                return False

            if not isinstance(sample_sat['time_series'], list):
                self.logger.error(f"{constellation} time_series 不是列表格式")
                return False

            if len(sample_sat['time_series']) == 0:
                self.logger.warning(f"{constellation} time_series 為空")

        return True

    def _extract_constellation_configs(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取星座配置數據"""
        # 嘗試從 metadata 中提取
        metadata = input_data.get('metadata', {})

        constellation_configs = metadata.get('constellation_configs')

        if constellation_configs is None:
            # 使用預設配置
            self.logger.warning("無法提取 constellation_configs，使用預設配置")
            constellation_configs = {
                'starlink': {
                    'expected_visible_satellites': [10, 15],
                    'elevation_threshold_deg': 5.0
                },
                'oneweb': {
                    'expected_visible_satellites': [3, 6],
                    'elevation_threshold_deg': 10.0
                }
            }

        return constellation_configs
```

---

## 🔍 數據訪問範例

### 3GPP 事件檢測數據訪問

```python
def _detect_gpp_events(self, signal_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """檢測 3GPP 事件"""

    if not self.gpp_detector:
        return {'events': [], 'total_events': 0}

    # 提取服務衛星 (選擇 RSRP 最高的)
    serving_satellite = None
    max_rsrp = float('-inf')

    for sat_id, sat_data in signal_analysis.items():
        rsrp = sat_data['signal_quality']['rsrp_dbm']
        if rsrp > max_rsrp:
            max_rsrp = rsrp
            serving_satellite = sat_data

    if not serving_satellite:
        self.logger.warning("無法確定服務衛星")
        return {'events': [], 'total_events': 0}

    # 提取鄰近衛星 (排除服務衛星)
    neighbor_satellites = [
        sat_data for sat_id, sat_data in signal_analysis.items()
        if sat_id != serving_satellite['satellite_id']
    ]

    # 調用 GPP 檢測器
    a4_events = self.gpp_detector.detect_a4_events(
        serving_satellite,
        neighbor_satellites
    )

    a5_events = self.gpp_detector.detect_a5_events(
        serving_satellite,
        neighbor_satellites
    )

    d2_events = self.gpp_detector.detect_d2_events(
        serving_satellite,
        neighbor_satellites
    )

    return {
        'a4_events': a4_events,
        'a5_events': a5_events,
        'd2_events': d2_events,
        'total_events': len(a4_events) + len(a5_events) + len(d2_events)
    }
```

### 動態池驗證數據訪問

```python
def _verify_satellite_pools(
    self,
    connectable_satellites: Dict[str, List],
    constellation_configs: Dict[str, Any]
) -> Dict[str, Any]:
    """驗證動態衛星池"""

    if not self.pool_verifier:
        return {'verified': False}

    # 提取目標範圍
    starlink_config = constellation_configs.get('starlink', {})
    starlink_target = starlink_config.get('expected_visible_satellites', [10, 15])

    oneweb_config = constellation_configs.get('oneweb', {})
    oneweb_target = oneweb_config.get('expected_visible_satellites', [3, 6])

    # 驗證 Starlink 池
    starlink_verification = self.pool_verifier.verify_pool_maintenance(
        connectable_satellites=connectable_satellites.get('starlink', []),
        constellation='starlink',
        target_min=starlink_target[0],
        target_max=starlink_target[1]
    )

    # 驗證 OneWeb 池
    oneweb_verification = self.pool_verifier.verify_pool_maintenance(
        connectable_satellites=connectable_satellites.get('oneweb', []),
        constellation='oneweb',
        target_min=oneweb_target[0],
        target_max=oneweb_target[1]
    )

    # 分析時空錯置
    time_space_offset = self.pool_verifier.analyze_time_space_offset_optimization(
        starlink_verification,
        oneweb_verification
    )

    return {
        'starlink_pool': starlink_verification,
        'oneweb_pool': oneweb_verification,
        'time_space_offset_optimization': time_space_offset
    }
```

### ML 訓練數據生成數據訪問

```python
def _generate_ml_training_data(
    self,
    signal_analysis: Dict[str, Any],
    gpp_events: Dict[str, Any],
    pool_verification: Dict[str, Any]
) -> Dict[str, Any]:
    """生成 ML 訓練數據"""

    if not self.ml_data_generator:
        return {'training_samples': [], 'total_samples': 0}

    # 調用 ML 數據生成器
    dqn_dataset = self.ml_data_generator.generate_dqn_dataset(
        signal_analysis,
        gpp_events
    )

    a3c_dataset = self.ml_data_generator.generate_a3c_dataset(
        signal_analysis,
        gpp_events
    )

    ppo_dataset = self.ml_data_generator.generate_ppo_dataset(
        signal_analysis,
        gpp_events
    )

    sac_dataset = self.ml_data_generator.generate_sac_dataset(
        signal_analysis,
        gpp_events
    )

    return {
        'dqn_dataset': dqn_dataset,
        'a3c_dataset': a3c_dataset,
        'ppo_dataset': ppo_dataset,
        'sac_dataset': sac_dataset,
        'dataset_summary': {
            'total_samples': (
                dqn_dataset.get('dataset_size', 0) +
                a3c_dataset.get('dataset_size', 0) +
                ppo_dataset.get('dataset_size', 0) +
                sac_dataset.get('dataset_size', 0)
            )
        }
    }
```

---

## ✅ 實現檢查清單

### 數據提取
- [ ] Stage 5 信號分析數據提取
- [ ] Stage 4 時間序列數據提取
- [ ] Stage 1 配置數據提取
- [ ] ProcessingResult 格式處理
- [ ] Dict 格式處理

### 數據驗證
- [ ] 數據格式驗證
- [ ] 時間序列結構驗證
- [ ] 必要字段完整性檢查
- [ ] 數據類型正確性檢查

### 錯誤處理
- [ ] 缺失數據處理
- [ ] 格式錯誤處理
- [ ] 降級處理機制
- [ ] 清晰的錯誤日誌

### 單元測試
- [ ] 數據提取測試
- [ ] 格式轉換測試
- [ ] 錯誤處理測試
- [ ] 邊界條件測試

---

**規格版本**: v1.0
**創建日期**: 2025-09-30
**狀態**: 待實現