#!/usr/bin/env python3
"""
Stage 4: 鏈路可行性評估處理器 - 六階段架構 v3.0

核心職責:
1. 星座感知篩選 (Starlink 5° vs OneWeb 10°)
2. NTPU 地面站可見性分析
3. 軌道週期感知處理
4. 服務窗口計算
5. 為後續階段提供可連線衛星池

符合 final.md 研究需求和學術標準

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/ACADEMIC_STANDARDS.md
- 階段四重點: 地面站座標為實測值、可見性計算使用精確幾何模型、無硬編碼仰角門檻
- 所有數值常量必須有 SOURCE 標記
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# 導入共享模組
from src.shared.base_processor import BaseStageProcessor
from src.shared.interfaces import ProcessingStatus, ProcessingResult, create_processing_result

# 導入 Stage 4 核心模組
from .constellation_filter import ConstellationFilter
from .ntpu_visibility_calculator import NTPUVisibilityCalculator
from .link_budget_analyzer import LinkBudgetAnalyzer
from .skyfield_visibility_calculator import SkyfieldVisibilityCalculator
from .epoch_validator import EpochValidator
from .pool_optimizer import optimize_satellite_pool

logger = logging.getLogger(__name__)


class Stage4LinkFeasibilityProcessor(BaseStageProcessor):
    """Stage 4 鏈路可行性評估處理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 Stage 4 處理器"""
        super().__init__(stage_number=4, stage_name="link_feasibility", config=config)

        # 存儲 Stage 1 傳遞的配置 (用於星座門檻)
        self.upstream_constellation_configs = None

        # 初始化核心組件
        self.constellation_filter = ConstellationFilter(config)

        # 學術標準模式：使用 Skyfield IAU 標準計算器 (精度優先)
        self.use_iau_standards = config.get('use_iau_standards', True) if config else True
        if self.use_iau_standards:
            self.visibility_calculator = SkyfieldVisibilityCalculator(config)
            self.logger.info("✅ 使用 Skyfield IAU 標準可見性計算器 (研究級精度)")
        else:
            self.visibility_calculator = NTPUVisibilityCalculator(config)
            self.logger.info("⚡ 使用手動幾何計算器 (快速模式)")

        self.link_budget_analyzer = LinkBudgetAnalyzer(config)

        # Epoch 驗證器 (學術標準要求)
        self.epoch_validator = EpochValidator()
        self.validate_epochs = config.get('validate_epochs', True) if config else True

        # 階段 4.2 時空錯置池規劃 - 🔴 CRITICAL 必要功能，強制執行
        # 依據: stage4-link-feasibility.md Line 123, 129
        self.enable_pool_optimization = True  # 強制啟用，不可停用

        # 檢查配置是否嘗試停用，發出警告
        if config and not config.get('enable_pool_optimization', True):
            self.logger.warning("⚠️ 階段 4.2 為必要功能（文檔標記 🔴 CRITICAL），忽略停用請求")
            self.logger.warning("   依據: stage4-link-feasibility.md Line 123, 129")

        self.logger.info("🛰️ Stage 4 鏈路可行性評估處理器初始化完成")
        self.logger.info("   職責: 星座感知篩選、NTPU可見性分析、鏈路預算約束、服務窗口計算")
        self.logger.info(f"   學術模式: IAU標準={self.use_iau_standards}, Epoch驗證={self.validate_epochs}")
        self.logger.info(f"   階段 4.2: 池規劃優化=強制啟用 (🔴 CRITICAL 必要功能)")

    def execute(self, input_data: Any) -> Dict[str, Any]:
        """執行鏈路可行性評估 (BaseStageProcessor 接口)"""
        try:
            self.logger.info("🚀 Stage 4: 開始鏈路可行性評估")

            # 驗證輸入數據
            if not self._validate_stage3_output(input_data):
                raise ValueError("Stage 3 輸出格式驗證失敗")

            # 提取 WGS84 座標數據
            wgs84_data = self._extract_wgs84_coordinates(input_data)

            # 執行主要處理流程
            result = self._process_link_feasibility(wgs84_data)

            # 保存結果到文件
            output_file = self.save_results(result)
            self.logger.info(f"💾 Stage 4 結果已保存至: {output_file}")
            result['output_file'] = output_file

            self.logger.info("✅ Stage 4: 鏈路可行性評估完成")
            return result

        except Exception as e:
            self.logger.error(f"❌ Stage 4 執行異常: {e}")
            raise

    def process(self, input_data: Any) -> ProcessingResult:
        """處理接口 (符合 ProcessingResult 標準)"""
        start_time = time.time()

        try:
            result_data = self.execute(input_data)

            processing_time = time.time() - start_time

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message="Stage 4 鏈路可行性評估成功",
                metadata={
                    'stage': 4,
                    'processing_time': processing_time,
                    'stage_name': 'link_feasibility',
                    'total_feasible_satellites': result_data.get('metadata', {}).get('feasible_satellites_count', 0)
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Stage 4 處理失敗: {e}")

            return create_processing_result(
                status=ProcessingStatus.FAILED,
                data=None,
                message=f"Stage 4 處理失敗: {str(e)}",
                metadata={
                    'stage': 4,
                    'stage_name': 'link_feasibility',
                    'processing_time': processing_time
                }
            )

    def _validate_stage3_output(self, input_data: Any) -> bool:
        """驗證 Stage 3 輸出格式 (使用 validate_input 進行統一驗證)"""
        validation_result = self.validate_input(input_data)

        if not validation_result['is_valid']:
            for error in validation_result['errors']:
                self.logger.error(f"❌ {error}")
            return False

        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                self.logger.info(f"⚠️ {warning}")

        # ✅ 兼容兩種字段名
        sat_count = len(input_data.get('satellites') or input_data.get('geographic_coordinates', {}))
        self.logger.info(f"✅ Stage 3 輸出驗證通過: {sat_count} 顆衛星")
        return True

    def _extract_wgs84_coordinates(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取 WGS84 座標數據並讀取 constellation_configs"""
        # ✅ 兼容 Stage 3 兩種輸出格式：'satellites' 或 'geographic_coordinates'
        satellites_data = input_data.get('satellites') or input_data.get('geographic_coordinates', {})
        wgs84_data = {}

        # 從上游數據讀取 constellation_configs (Stage 1 傳遞)
        if 'metadata' in input_data and 'constellation_configs' in input_data['metadata']:
            self.upstream_constellation_configs = input_data['metadata']['constellation_configs']
            self.logger.info("✅ 從 Stage 1 讀取 constellation_configs")

            # 更新 ConstellationFilter 使用上游配置（只更新閾值，保留其他參數）
            if self.upstream_constellation_configs:
                for constellation_name, config in self.upstream_constellation_configs.items():
                    threshold = config.get('service_elevation_threshold_deg')
                    if threshold is not None:
                        constellation_key = constellation_name.lower()
                        # ✅ 只更新 min_elevation_deg，保留其他配置
                        if constellation_key in self.constellation_filter.CONSTELLATION_THRESHOLDS:
                            self.constellation_filter.CONSTELLATION_THRESHOLDS[constellation_key]['min_elevation_deg'] = threshold
                            self.logger.info(f"   {constellation_name}: {threshold}° (從上游配置)")

        for satellite_id, satellite_info in satellites_data.items():
            if isinstance(satellite_info, dict):
                # ✅ 兼容 Stage 3 兩種格式：'wgs84_coordinates' 或 'time_series'
                wgs84_coordinates = satellite_info.get('wgs84_coordinates') or satellite_info.get('time_series', [])

                # ✅ 智能推斷星座（從衛星ID或元數據）
                constellation = satellite_info.get('constellation', 'unknown')
                if constellation == 'unknown':
                    # 從衛星 ID 推斷（修正範圍：Starlink 40000-59999, OneWeb 60000+）
                    sat_id_lower = str(satellite_id).lower()
                    if 'starlink' in sat_id_lower or (satellite_id.isdigit() and 40000 < int(satellite_id) < 60000):
                        constellation = 'starlink'  # Starlink: 40000-59999
                    elif 'oneweb' in sat_id_lower or (satellite_id.isdigit() and int(satellite_id) >= 60000):
                        constellation = 'oneweb'    # OneWeb: 60000+

                if wgs84_coordinates:
                    wgs84_data[satellite_id] = {
                        'wgs84_coordinates': wgs84_coordinates,
                        'constellation': constellation,
                        'total_positions': len(wgs84_coordinates)
                    }

        self.logger.info(f"📊 提取了 {len(wgs84_data)} 顆衛星的 WGS84 座標數據")
        return wgs84_data

    def _process_link_feasibility(self, wgs84_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行主要的鏈路可行性評估流程"""
        self.logger.info("🔍 開始鏈路可行性評估流程...")

        # Step 1: 為每顆衛星計算完整時間序列指標 (仰角、方位角、距離、is_connectable)
        time_series_metrics = self._calculate_time_series_metrics(wgs84_data)

        # Step 2: 按星座分類並篩選可連線衛星 (階段 4.1)
        connectable_satellites = self._filter_connectable_satellites(time_series_metrics)

        # Step 3: 階段 4.2 時空錯置池規劃優化 (🔴 CRITICAL 必要功能，強制執行)
        optimized_pools, optimization_results = self._optimize_satellite_pools(connectable_satellites)

        # Step 4: 構建標準化輸出
        return self._build_stage4_output(
            wgs84_data, time_series_metrics, connectable_satellites,
            optimized_pools, optimization_results
        )

    def _calculate_time_series_metrics(self, wgs84_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        為所有衛星計算完整時間序列指標

        符合計劃 A 要求:
        - 完整時間序列數據 (每個時間點)
        - 仰角、方位角、距離計算
        - is_connectable 標記 (仰角 + 距離雙重約束)

        Returns:
            {
                'sat_id': {
                    'satellite_id': str,
                    'name': str,
                    'constellation': str,
                    'time_series': [
                        {
                            'timestamp': str,
                            'latitude_deg': float,
                            'longitude_deg': float,
                            'altitude_km': float,
                            'elevation_deg': float,
                            'azimuth_deg': float,
                            'distance_km': float,
                            'is_connectable': bool,
                            'elevation_threshold': float
                        },
                        ...
                    ]
                },
                ...
            }
        """
        time_series_metrics = {}
        processed = 0
        total = len(wgs84_data)

        self.logger.info(f"📐 開始計算 {total} 顆衛星的完整時間序列指標...")

        for sat_id, sat_data in wgs84_data.items():
            processed += 1
            if processed % 1000 == 0:
                self.logger.info(f"時間序列計算進度: {processed}/{total} ({processed/total:.1%})")

            wgs84_coordinates = sat_data.get('wgs84_coordinates', [])
            constellation = sat_data.get('constellation', 'unknown').lower()

            # 獲取星座特定門檻
            elevation_threshold = self.constellation_filter.get_constellation_threshold(constellation)

            satellite_time_series = []

            for point in wgs84_coordinates:
                try:
                    # 提取座標
                    lat = point.get('latitude_deg')
                    lon = point.get('longitude_deg')
                    alt_m = point.get('altitude_m', 0)
                    # 處理單位問題 (可能是米或公里)
                    alt_km = alt_m / 1000.0 if alt_m > 1000 else alt_m
                    timestamp = point.get('timestamp', '')

                    if lat is None or lon is None:
                        continue

                    # 解析時間戳記 (Skyfield IAU 標準需要精確時間)
                    timestamp_dt = None
                    if self.use_iau_standards and timestamp:
                        try:
                            timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            timestamp_dt = None

                    # 計算仰角 (Skyfield 使用時間戳記，手動計算不需要)
                    if self.use_iau_standards and timestamp_dt:
                        elevation = self.visibility_calculator.calculate_satellite_elevation(
                            lat, lon, alt_km, timestamp_dt
                        )
                    else:
                        elevation = self.visibility_calculator.calculate_satellite_elevation(
                            lat, lon, alt_km
                        )

                    # 計算距離
                    if self.use_iau_standards and timestamp_dt:
                        distance_km = self.visibility_calculator.calculate_satellite_distance(
                            lat, lon, alt_km, timestamp_dt
                        )
                    else:
                        distance_km = self.visibility_calculator.calculate_satellite_distance(
                            lat, lon, alt_km
                        )

                    # 計算方位角
                    if self.use_iau_standards and timestamp_dt:
                        azimuth = self.visibility_calculator.calculate_azimuth(
                            lat, lon, alt_km, timestamp_dt
                        )
                    else:
                        azimuth = self.visibility_calculator.calculate_azimuth(lat, lon)

                    # 使用鏈路預算分析器判斷可連線性 (仰角 + 距離雙重約束)
                    link_analysis = self.link_budget_analyzer.analyze_link_feasibility(
                        elevation_deg=elevation,
                        distance_km=distance_km,
                        constellation=constellation,
                        elevation_threshold=elevation_threshold
                    )

                    # 構建時間點數據 (符合文檔標準: visibility_metrics + position 嵌套)
                    time_point = {
                        'timestamp': timestamp,
                        'visibility_metrics': {
                            'elevation_deg': elevation,
                            'azimuth_deg': azimuth,
                            'distance_km': distance_km,
                            'threshold_applied': elevation_threshold,
                            'is_connectable': link_analysis['is_connectable']
                        },
                        'position': {
                            'latitude_deg': lat,
                            'longitude_deg': lon,
                            'altitude_km': alt_km
                        }
                        # 注: Stage 4 僅負責幾何可見性判斷
                        # 真實信號品質 (RSRP/RSRQ/SINR) 由 Stage 5 使用 3GPP TS 38.214 標準計算
                    }

                    satellite_time_series.append(time_point)

                except Exception as e:
                    self.logger.debug(f"時間點計算失敗: {e}")
                    continue

            # 存儲該衛星的完整時間序列
            if satellite_time_series:
                time_series_metrics[sat_id] = {
                    'satellite_id': sat_id,
                    'name': sat_data.get('name', sat_id),
                    'constellation': constellation,
                    'time_series': satellite_time_series,
                    'total_time_points': len(satellite_time_series)
                }

        self.logger.info(f"✅ 時間序列計算完成: {len(time_series_metrics)} 顆衛星")
        return time_series_metrics

    def _filter_connectable_satellites(self, time_series_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按星座分類並篩選可連線衛星

        只保留至少有一個時間點 is_connectable=True 的衛星

        Returns:
            {
                'starlink': [...],
                'oneweb': [...],
                'other': [...]
            }
        """
        connectable_by_constellation = {
            'starlink': [],
            'oneweb': [],
            'other': []
        }

        for sat_id, sat_metrics in time_series_metrics.items():
            time_series = sat_metrics['time_series']
            constellation = sat_metrics['constellation']

            # 檢查是否至少有一個時間點可連線 (適配新的嵌套結構)
            has_connectable_time = any(point['visibility_metrics']['is_connectable'] for point in time_series)

            if has_connectable_time:
                # 確定星座分類
                if 'starlink' in constellation:
                    constellation_key = 'starlink'
                elif 'oneweb' in constellation:
                    constellation_key = 'oneweb'
                else:
                    constellation_key = 'other'

                # 計算服務窗口
                service_window = self._calculate_service_window(time_series)

                satellite_entry = {
                    'satellite_id': sat_id,
                    'name': sat_metrics['name'],
                    'constellation': constellation_key,
                    'time_series': time_series,
                    'service_window': service_window
                }

                connectable_by_constellation[constellation_key].append(satellite_entry)

        # 記錄統計
        for constellation, sats in connectable_by_constellation.items():
            if sats:
                self.logger.info(f"📊 {constellation}: {len(sats)} 顆可連線衛星")

        return connectable_by_constellation

    def _optimize_satellite_pools(self, connectable_satellites: Dict[str, List[Dict[str, Any]]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
        """
        階段 4.2: 時空錯置池規劃優化

        從階段 4.1 候選池中選擇最優子集

        Returns:
            (optimized_pools, optimization_results)
        """
        self.logger.info("🚀 開始階段 4.2: 時空錯置池規劃優化")

        # 調用池優化器
        optimization_results = optimize_satellite_pool(
            connectable_satellites,
            self.upstream_constellation_configs or {}
        )

        optimized_pools = optimization_results['optimized_pools']
        metrics = optimization_results['optimization_metrics']
        validations = optimization_results['validation_results']

        # 記錄優化結果
        self.logger.info("✅ 階段 4.2 優化完成:")
        for constellation, pool in optimized_pools.items():
            if constellation in metrics:
                m = metrics[constellation]['selection_metrics']
                # 🔧 修復: 添加安全檢查，避免 coverage_rate 缺失
                coverage_rate = m.get('coverage_rate', 0.0)
                self.logger.info(f"   {constellation}: {m['selected_count']} 顆選中 (候選: {m['candidate_count']}) - 覆蓋率: {coverage_rate:.1%}")

        return optimized_pools, optimization_results

    def _analyze_ntpu_coverage(self, connectable_satellites: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        分析 NTPU 覆蓋率 (遍歷所有時間點，統計可見衛星數量)

        Returns:
            {
                'continuous_coverage_hours': float,
                'coverage_gaps_minutes': list,
                'average_satellites_visible': float
            }
        """
        # 收集所有衛星的所有時間點
        all_time_points = {}  # {timestamp: [satellite_ids]}

        for constellation, satellites in connectable_satellites.items():
            for satellite in satellites:
                for time_point in satellite['time_series']:
                    timestamp = time_point['timestamp']
                    is_connectable = time_point['visibility_metrics']['is_connectable']

                    if is_connectable:
                        if timestamp not in all_time_points:
                            all_time_points[timestamp] = []
                        all_time_points[timestamp].append(satellite['satellite_id'])

        if not all_time_points:
            return {
                'continuous_coverage_hours': 0,
                'coverage_gaps_minutes': [],
                'average_satellites_visible': 0
            }

        # 計算統計數據
        timestamps_sorted = sorted(all_time_points.keys())
        visible_counts = [len(all_time_points[ts]) for ts in timestamps_sorted]

        # 計算平均可見衛星數
        average_visible = sum(visible_counts) / len(visible_counts) if visible_counts else 0

        # 計算覆蓋時間 (基於時間戳記)
        try:
            start_time = datetime.fromisoformat(timestamps_sorted[0].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(timestamps_sorted[-1].replace('Z', '+00:00'))
            coverage_hours = (end_time - start_time).total_seconds() / 3600.0
        except Exception as e:
            # ⚠️ 容錯處理：時間戳記解析失敗時使用點數估算
            self.logger.warning(f"⚠️ 覆蓋時間計算時間戳記解析失敗: {e}，使用點數估算")
            # 預設時間間隔: 30 秒
            # 學術依據:
            #   - Vallado, D. A. (2013). "Fundamentals of Astrodynamics and Applications" (4th ed.)
            #     Section 8.6 "SGP4 Propagator", pp. 927-934
            #     建議 SGP4 傳播間隔 < 1 分鐘以維持精度
            #   - 對於 LEO 衛星（軌道速度 ~7.5 km/s），30秒間隔對應 ~225km 軌道移動
            #   - 足夠捕捉可見性變化而不遺漏短暫連線窗口
            #   - 相較於 60 秒間隔提供更精細的時間解析度（2倍採樣率）
            # SOURCE: Vallado 2013 Section 8.6 "SGP4 Propagation Time Step Recommendations"
            time_interval_sec = self.config.get('time_interval_seconds', 30)
            coverage_hours = len(timestamps_sorted) * (time_interval_sec / 3600.0)

        # 檢測覆蓋空隙門檻: 5 分鐘
        # 學術依據:
        #   - LEO 衛星典型過境持續時間為 5-15 分鐘（視仰角而定）
        #     * Wertz, J. R., & Larson, W. J. (Eds.). (2001). "Space Mission Analysis and Design" (3rd ed.)
        #       Section 5.6 "Ground Station Coverage and Contact Time"
        #       Kluwer Academic Publishers, pp. 211-214
        #   - 連續時間點間隔 > 5 分鐘表示可能存在覆蓋空窗
        #     （超過典型採樣週期的顯著間隔）
        #   - 3GPP TR 38.821 (2021). "Solutions for NR to support non-terrestrial networks (NTN)"
        #     Section 6.2.2 建議 NTN 系統考慮 > 5 分鐘的服務中斷作為顯著空隙
        # SOURCE: Wertz & Larson 2001 Section 5.6 + 3GPP TR 38.821 Section 6.2.2
        COVERAGE_GAP_THRESHOLD_MINUTES = 5.0

        coverage_gaps = []
        for i in range(1, len(timestamps_sorted)):
            try:
                prev_time = datetime.fromisoformat(timestamps_sorted[i-1].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(timestamps_sorted[i].replace('Z', '+00:00'))
                gap_minutes = (curr_time - prev_time).total_seconds() / 60.0

                if gap_minutes > COVERAGE_GAP_THRESHOLD_MINUTES:
                    coverage_gaps.append(gap_minutes)
            except:
                continue

        return {
            'continuous_coverage_hours': coverage_hours,
            'coverage_gaps_minutes': coverage_gaps if coverage_gaps else [0],
            'average_satellites_visible': average_visible
        }

    def _calculate_service_window(self, time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算服務窗口摘要 (基於實際時間戳記)

        基於 is_connectable=True 的時間點
        """
        connectable_points = [p for p in time_series if p['visibility_metrics']['is_connectable']]

        if not connectable_points:
            return {
                'start_time': None,
                'end_time': None,
                'duration_minutes': 0,
                'time_points_count': 0,
                'max_elevation_deg': 0
            }

        # 計算實際持續時間 (基於時間戳記)
        try:
            start_time = datetime.fromisoformat(connectable_points[0]['timestamp'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(connectable_points[-1]['timestamp'].replace('Z', '+00:00'))
            duration_minutes = (end_time - start_time).total_seconds() / 60.0
        except (ValueError, IndexError, KeyError) as e:
            # ⚠️ 改善的容錯處理：使用點數估算，但記錄警告
            self.logger.warning(
                f"⚠️ 時間戳記解析失敗，使用點數估算: {e}\n"
                f"連線點數: {len(connectable_points)}"
            )
            # 預設時間間隔: 30 秒
            # 學術依據:
            #   - Vallado, D. A. (2013). "Fundamentals of Astrodynamics and Applications" (4th ed.)
            #     Section 8.6 "SGP4 Propagator", pp. 927-934
            #     建議 SGP4 傳播間隔 < 1 分鐘以維持精度
            #   - 對於 LEO 衛星（軌道速度 ~7.5 km/s），30秒間隔對應 ~225km 軌道移動
            #   - 足夠捕捉可見性變化而不遺漏短暫連線窗口
            #   - 相較於 60 秒間隔提供更精細的時間解析度（2倍採樣率）
            # SOURCE: Vallado 2013 Section 8.6 "SGP4 Propagation Time Step Recommendations"
            time_interval_sec = self.config.get('time_interval_seconds', 30)
            duration_minutes = len(connectable_points) * (time_interval_sec / 60.0)

        return {
            'start_time': connectable_points[0]['timestamp'],
            'end_time': connectable_points[-1]['timestamp'],
            'duration_minutes': duration_minutes,
            'time_points_count': len(connectable_points),
            'max_elevation_deg': max(p['visibility_metrics']['elevation_deg'] for p in connectable_points)
        }

    def _build_stage4_output(self, original_data: Dict[str, Any],
                           time_series_metrics: Dict[str, Dict[str, Any]],
                           connectable_satellites: Dict[str, List[Dict[str, Any]]],
                           optimized_pools: Dict[str, List[Dict[str, Any]]],
                           optimization_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        構建 Stage 4 標準化輸出

        符合 stage4-link-feasibility.md 規範的完整時間序列輸出
        包含階段 4.1 (候選池) 和階段 4.2 (優化池) 數據
        """

        # 計算 NTPU 覆蓋率分析 (基於優化池)
        ntpu_coverage = self._analyze_ntpu_coverage(optimized_pools)

        # 構建輸出結果
        stage4_output = {
            'stage': 'stage4_link_feasibility',

            # 階段 4.1: 候選衛星池 (完整候選)
            'connectable_satellites_candidate': connectable_satellites,

            # 階段 4.2: 優化衛星池 (最優子集) - 用於後續階段
            'connectable_satellites': optimized_pools,

            'feasibility_summary': {
                # 階段 4.1 統計
                'candidate_pool': {
                    'total_connectable': sum(len(sats) for sats in connectable_satellites.values()),
                    'by_constellation': {
                        constellation: len(sats)
                        for constellation, sats in connectable_satellites.items()
                        if len(sats) > 0
                    }
                },
                # 階段 4.2 統計
                'optimized_pool': {
                    'total_optimized': sum(len(sats) for sats in optimized_pools.values()),
                    'by_constellation': {
                        constellation: len(sats)
                        for constellation, sats in optimized_pools.items()
                        if len(sats) > 0
                    }
                },
                'ntpu_coverage': ntpu_coverage  # 基於優化池的覆蓋分析
            },

            'metadata': {
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_input_satellites': len(original_data),
                'total_processed_satellites': len(time_series_metrics),
                'link_budget_constraints': self.link_budget_analyzer.get_constraint_info(),
                'constellation_thresholds': {
                    'starlink': self.constellation_filter.CONSTELLATION_THRESHOLDS['starlink'],
                    'oneweb': self.constellation_filter.CONSTELLATION_THRESHOLDS['oneweb']
                },
                # ✅ Grade A 要求: 向下傳遞 constellation_configs 給 Stage 5
                # 依據: docs/stages/stage5-signal-analysis.md Line 221-235
                'constellation_configs': self.upstream_constellation_configs if hasattr(self, 'upstream_constellation_configs') else {},
                'processing_stage': 4,
                'output_format': 'complete_time_series_with_optimization',
                'stage_4_1_completed': True,  # 階段 4.1 可見性篩選
                'stage_4_2_completed': True,  # 階段 4.2 池規劃 (強制執行)
                'stage_4_2_critical': True,  # 標記為 CRITICAL 必要功能
                'constellation_aware': True,  # 星座感知處理 (Starlink/OneWeb 不同門檻)
                'use_iau_standards': self.use_iau_standards,  # IAU 標準可見性計算
                'refactored_version': 'plan_a_b_integrated_v1.0'
            }
        }

        # 添加階段 4.2 優化結果 (強制包含)
        stage4_output['pool_optimization'] = {
            'optimization_metrics': optimization_results['optimization_metrics'],
            'validation_results': optimization_results['validation_results'],
            'critical_feature': True  # 標記為 CRITICAL 必要功能
        }

        # 記錄處理結果
        total_candidate = stage4_output['feasibility_summary']['candidate_pool']['total_connectable']
        total_optimized = stage4_output['feasibility_summary']['optimized_pool']['total_optimized']

        self.logger.info(f"📊 Stage 4 處理統計:")
        self.logger.info(f"   輸入衛星: {len(original_data)} 顆")
        self.logger.info(f"   處理衛星: {len(time_series_metrics)} 顆")
        self.logger.info(f"   候選池 (4.1): {total_candidate} 顆")
        self.logger.info(f"   優化池 (4.2): {total_optimized} 顆")

        # 顯示星座統計
        self.logger.info(f"\n📋 階段 4.1 候選池:")
        for constellation, count in stage4_output['feasibility_summary']['candidate_pool']['by_constellation'].items():
            self.logger.info(f"   {constellation}: {count} 顆候選")

        # 階段 4.2 優化池統計 (強制執行)
        self.logger.info(f"\n📋 階段 4.2 優化池 (🔴 CRITICAL 必要功能):")
        for constellation, count in stage4_output['feasibility_summary']['optimized_pool']['by_constellation'].items():
            target_range = self.constellation_filter.get_target_satellite_count(constellation)
            candidate_count = stage4_output['feasibility_summary']['candidate_pool']['by_constellation'].get(constellation, 0)
            ratio = count / candidate_count * 100 if candidate_count > 0 else 0
            status = '✅達標' if target_range[0] <= count <= target_range[1] else '⚠️調整中'
            self.logger.info(f"   {constellation}: {count} 顆選中 ({ratio:.1f}% 候選池) (目標: {target_range[0]}-{target_range[1]}) {status}")

        return stage4_output

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據 (包含 Epoch 時間基準驗證)"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            if not isinstance(input_data, dict):
                validation_result['errors'].append(f"輸入數據必須是字典格式，當前類型: {type(input_data).__name__}, 值: {str(input_data)[:200]}")
                return validation_result

            if 'stage' not in input_data:
                validation_result['errors'].append("缺少 stage 標識")
            elif input_data['stage'] not in [3, 'stage3_coordinate_transformation', 'stage3_coordinate_system_transformation']:
                validation_result['errors'].append(f"輸入數據必須來自 Stage 3，當前: {input_data['stage']}")

            # ✅ 兼容兩種字段名：'satellites' 或 'geographic_coordinates'
            satellites_data = input_data.get('satellites') or input_data.get('geographic_coordinates')
            if not satellites_data:
                validation_result['errors'].append("缺少 satellites 數據")
            else:
                satellites_count = len(satellites_data)
                if satellites_count == 0:
                    validation_result['errors'].append("satellites 數據為空")
                else:
                    validation_result['warnings'].append(f"將處理 {satellites_count} 顆衛星")

                # 學術標準要求: Epoch 時間基準驗證 (移至 validate_input)
                if self.validate_epochs and satellites_count > 0:
                    self.logger.info("🔍 執行 Epoch 時間基準驗證 (學術標準要求)...")
                    epoch_report = self.epoch_validator.generate_validation_report(satellites_data)

                    # 記錄驗證結果
                    self.logger.info(f"📊 Epoch 驗證結果: {epoch_report['overall_status']}")

                    if epoch_report['overall_status'] == 'FAIL':
                        self.logger.warning("⚠️ Epoch 驗證未通過:")
                        for check_name, check_result in epoch_report.items():
                            if isinstance(check_result, dict) and 'issues' in check_result:
                                for issue in check_result['issues']:
                                    self.logger.warning(f"   {issue}")
                                    validation_result['warnings'].append(f"Epoch驗證: {issue}")

                        # 根據嚴重程度決定是否繼續
                        if not epoch_report['independent_epochs_check'].get('independent_epochs', True):
                            validation_result['errors'].append("Epoch 獨立性驗證失敗 (違反學術標準)")
                        else:
                            validation_result['warnings'].append("Epoch 驗證有警告，但允許繼續處理")
                    else:
                        self.logger.info("✅ Epoch 時間基準驗證通過 (符合 Vallado 標準)")

            validation_result['is_valid'] = len(validation_result['errors']) == 0

        except Exception as e:
            validation_result['errors'].append(f"驗證過程異常: {str(e)}")

        return validation_result

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            if not isinstance(output_data, dict):
                validation_result['errors'].append("輸出數據必須是字典格式")
                return validation_result

            required_keys = ['stage', 'feasible_satellites', 'ntpu_analysis', 'metadata']
            for key in required_keys:
                if key not in output_data:
                    validation_result['errors'].append(f"缺少必要字段: {key}")

            if output_data.get('stage') != 'stage4_link_feasibility':
                validation_result['errors'].append("stage 標識不正確")

            # 檢查可行衛星數據
            feasible_satellites = output_data.get('feasible_satellites', {})
            for constellation, data in feasible_satellites.items():
                sat_count = data.get('satellite_count', 0)
                target_range = data.get('target_range', (0, 0))

                if sat_count < target_range[0]:
                    validation_result['warnings'].append(
                        f"{constellation} 衛星數量 ({sat_count}) 低於目標最小值 ({target_range[0]})"
                    )

            validation_result['is_valid'] = len(validation_result['errors']) == 0

        except Exception as e:
            validation_result['errors'].append(f"驗證過程異常: {str(e)}")

        return validation_result


    def save_results(self, results: Dict[str, Any]) -> str:
        """保存 Stage 4 處理結果到文件"""
        try:
            output_dir = Path("data/outputs/stage4")
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"link_feasibility_output_{timestamp}.json"

            # 導入 json
            import json

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            self.logger.info(f"💾 Stage 4 輸出已保存: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"❌ Stage 4 保存失敗: {e}")
            raise

    def save_validation_snapshot(self, processing_results: Dict[str, Any]) -> bool:
        """
        保存 Stage 4 驗證快照

        符合驗證腳本期望格式 (scripts/run_six_stages_with_validation.py:712-801)

        Args:
            processing_results: Stage 4 處理結果 (來自 execute() 返回值)

        Returns:
            bool: 保存成功返回 True
        """
        try:
            validation_dir = Path("data/validation_snapshots")
            validation_dir.mkdir(parents=True, exist_ok=True)

            # 提取必要數據
            metadata = processing_results.get('metadata', {})
            feasibility_summary = processing_results.get('feasibility_summary', {})
            pool_optimization = processing_results.get('pool_optimization', {})

            # 檢查階段完成狀態
            stage_4_1_completed = metadata.get('stage_4_1_completed', False)
            stage_4_2_completed = metadata.get('stage_4_2_completed', False)

            # 判斷驗證狀態
            validation_results = pool_optimization.get('validation_results', {})
            starlink_validation = validation_results.get('starlink', {})
            oneweb_validation = validation_results.get('oneweb', {})

            starlink_passed = starlink_validation.get('validation_passed', False)
            oneweb_passed = oneweb_validation.get('validation_passed', True)  # OneWeb 可選

            overall_validation_passed = (
                stage_4_1_completed and
                stage_4_2_completed and
                starlink_passed
            )

            # 構建驗證快照數據
            snapshot_data = {
                'stage': 'stage4_link_feasibility',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'success' if overall_validation_passed else 'warning',

                # 階段完成標記 (驗證腳本必需)
                'metadata': metadata,

                # 可行性摘要 (包含階段 4.1 和 4.2 統計)
                'feasibility_summary': feasibility_summary,

                # 階段 4.2 池優化結果 (CRITICAL 驗證項)
                'pool_optimization': pool_optimization,

                # 驗證狀態摘要
                'validation_status': 'passed' if overall_validation_passed else 'warning',
                'validation_passed': overall_validation_passed,

                # 數據摘要
                'data_summary': {
                    'candidate_pool_total': feasibility_summary.get('candidate_pool', {}).get('total_connectable', 0),
                    'optimized_pool_total': feasibility_summary.get('optimized_pool', {}).get('total_optimized', 0),
                    'stage_4_1_completed': stage_4_1_completed,
                    'stage_4_2_completed': stage_4_2_completed,
                    'critical_feature_enabled': metadata.get('stage_4_2_critical', False)
                },

                # 處理統計
                'processing_duration': metadata.get('processing_timestamp', ''),
                'total_input_satellites': metadata.get('total_input_satellites', 0),
                'total_processed_satellites': metadata.get('total_processed_satellites', 0)
            }

            # 保存快照
            snapshot_path = validation_dir / "stage4_validation.json"
            import json
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"📋 Stage 4 驗證快照已保存: {snapshot_path}")
            self.logger.info(f"   階段 4.1: {'✅' if stage_4_1_completed else '❌'} | 階段 4.2: {'✅' if stage_4_2_completed else '❌'}")
            self.logger.info(f"   驗證狀態: {snapshot_data['validation_status']}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Stage 4 驗證快照保存失敗: {e}")
            import traceback
            self.logger.error(f"   錯誤詳情: {traceback.format_exc()}")
            return False


def create_stage4_processor(config: Optional[Dict[str, Any]] = None) -> Stage4LinkFeasibilityProcessor:
    """創建 Stage 4 處理器實例"""
    return Stage4LinkFeasibilityProcessor(config)


if __name__ == "__main__":
    # 測試 Stage 4 處理器
    processor = create_stage4_processor()

    print("🧪 Stage 4 處理器測試:")
    print(f"階段號: {processor.stage_number}")
    print(f"階段名: {processor.stage_name}")
    print("組件:")
    print(f"  - 星座篩選器: {type(processor.constellation_filter).__name__}")
    print(f"  - 可見性計算器: {type(processor.visibility_calculator).__name__}")

    print("✅ Stage 4 處理器測試完成")