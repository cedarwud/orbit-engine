#!/usr/bin/env python3
"""
工作器管理器 - Stage 5 並行處理模組

負責管理衛星信號分析的並行/順序處理
"""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SignalAnalysisWorkerManager:
    """並行處理工作器管理器"""

    def __init__(self, max_workers: int, config: Dict[str, Any], signal_thresholds: Dict[str, float],
                 propagation_simulator=None):
        """
        初始化工作器管理器

        Args:
            max_workers: 最大工作器數量
            config: 配置字典
            signal_thresholds: 信號門檻配置
            propagation_simulator: 動態傳播條件模擬器 (可選, Proposal 002)
        """
        self.max_workers = max_workers
        self.config = config
        self.signal_thresholds = signal_thresholds
        self.propagation_simulator = propagation_simulator
        self.enable_parallel = max_workers > 1
        self.logger = logging.getLogger(__name__)

    def process_satellites(
        self,
        satellites: List[Dict[str, Any]],
        constellation: str,
        system_config: Dict[str, Any],
        time_series_analyzer
    ) -> Dict[str, Any]:
        """
        處理衛星數據（自動選擇並行/順序）

        Args:
            satellites: 衛星列表
            constellation: 星座名稱
            system_config: 系統配置
            time_series_analyzer: 時間序列分析器實例

        Returns:
            Dict: 包含 satellites 和 stats 的結果
        """
        # 根據配置和數據量自動選擇處理模式
        if self.enable_parallel and len(satellites) > 5:
            self.logger.info(f"🚀 使用 {self.max_workers} 個工作器並行處理 {len(satellites)} 顆衛星...")
            return self._process_parallel(satellites, constellation, system_config)
        else:
            self.logger.info(f"使用單核心處理 {len(satellites)} 顆衛星...")
            return self._process_serial(satellites, constellation, system_config, time_series_analyzer)

    def _process_serial(
        self,
        satellites: List[Dict[str, Any]],
        constellation: str,
        system_config: Dict[str, Any],
        time_series_analyzer
    ) -> Dict[str, Any]:
        """順序處理衛星（單核心）"""
        analyzed_satellites = {}
        stats = {
            'total_satellites_analyzed': 0,
            'excellent_signals': 0,
            'good_signals': 0,
            'fair_signals': 0,
            'poor_signals': 0
        }

        for satellite in satellites:
            # ✅ Fail-Fast: 明確檢查 satellite_id
            if 'satellite_id' not in satellite:
                self.logger.warning("衛星數據缺少 satellite_id 字段，跳過此衛星")
                continue
            satellite_id = satellite['satellite_id']

            # ✅ Fail-Fast: 明確檢查 time_series
            if 'time_series' not in satellite:
                self.logger.warning(f"衛星 {satellite_id} 缺少 time_series 字段，跳過")
                continue
            time_series = satellite['time_series']

            if not time_series:
                self.logger.warning(f"衛星 {satellite_id} 的 time_series 為空，跳過")
                continue

            stats['total_satellites_analyzed'] += 1

            try:
                # 分析時間序列
                time_series_analysis = time_series_analyzer.analyze_time_series(
                    satellite_id=satellite_id,
                    time_series=time_series,
                    system_config=system_config,
                    constellation=constellation  # A3 事件需要星座資訊
                )

                # 存儲分析結果
                analyzed_satellites[satellite_id] = {
                    'satellite_id': satellite_id,
                    'constellation': constellation,
                    'time_series': time_series_analysis['time_series'],
                    'summary': time_series_analysis['summary'],
                    'physical_parameters': time_series_analysis['physics_summary']
                }

                # 更新統計
                avg_quality = time_series_analysis['summary']['average_quality_level']
                if avg_quality == 'excellent':
                    stats['excellent_signals'] += 1
                elif avg_quality == 'good':
                    stats['good_signals'] += 1
                elif avg_quality == 'fair':
                    stats['fair_signals'] += 1
                else:
                    stats['poor_signals'] += 1

            except Exception as e:
                self.logger.error(f"❌ 衛星 {satellite_id} 時間序列分析失敗: {e}")
                stats['poor_signals'] += 1
                continue

        return {
            'satellites': analyzed_satellites,
            'stats': stats
        }

    def _process_parallel(
        self,
        satellites: List[Dict[str, Any]],
        constellation: str,
        system_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """並行處理衛星（多核心）"""
        analyzed_satellites = {}
        stats = {
            'total_satellites_analyzed': 0,
            'excellent_signals': 0,
            'good_signals': 0,
            'fair_signals': 0,
            'poor_signals': 0
        }

        # 創建進程池並提交任務
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # ✅ Fail-Fast: 提交所有衛星處理任務（明確檢查 time_series）
            # 🆕 NEW: 傳遞 propagation_simulator 配置（而非實例，因為不能序列化）
            enable_prop_sim = self.propagation_simulator is not None
            prop_sim_config = self.config.get('propagation_simulation', {}) if enable_prop_sim else None

            future_to_satellite = {
                executor.submit(
                    _process_single_satellite_worker,
                    satellite,
                    constellation,
                    system_config,
                    self.signal_thresholds,
                    self.config,
                    enable_prop_sim,  # 🆕 傳遞啟用標誌
                    prop_sim_config   # 🆕 傳遞配置（而非實例）
                ): satellite for satellite in satellites
                if 'time_series' in satellite and satellite['time_series']
            }

            # 收集結果
            completed = 0
            total = len(future_to_satellite)

            for future in as_completed(future_to_satellite):
                satellite = future_to_satellite[future]

                # ✅ Fail-Fast: 明確檢查 satellite_id
                if 'satellite_id' not in satellite:
                    self.logger.warning("結果收集：衛星數據缺少 satellite_id 字段")
                    completed += 1
                    continue
                satellite_id = satellite['satellite_id']
                completed += 1

                try:
                    result = future.result()
                    if result and 'satellite_id' in result:
                        analyzed_satellites[result['satellite_id']] = result
                        stats['total_satellites_analyzed'] += 1

                        # ✅ Fail-Fast: 明確檢查 summary 和 average_quality_level
                        if 'summary' not in result:
                            self.logger.warning(f"衛星 {satellite_id} 結果缺少 summary 字段，標記為 poor")
                            avg_quality = 'poor'
                        else:
                            summary = result['summary']
                            if 'average_quality_level' not in summary:
                                self.logger.warning(f"衛星 {satellite_id} summary 缺少 average_quality_level 字段，標記為 poor")
                                avg_quality = 'poor'
                            else:
                                avg_quality = summary['average_quality_level']

                        # 更新統計
                        if avg_quality == 'excellent':
                            stats['excellent_signals'] += 1
                        elif avg_quality == 'good':
                            stats['good_signals'] += 1
                        elif avg_quality == 'fair':
                            stats['fair_signals'] += 1
                        else:
                            stats['poor_signals'] += 1

                except Exception as e:
                    self.logger.error(f"❌ 衛星 {satellite_id} 並行處理失敗: {e}")
                    stats['poor_signals'] += 1

                # 進度報告（每 10 顆）
                if completed % 10 == 0 or completed == total:
                    self.logger.info(f"   進度: {completed}/{total} 顆衛星已處理 ({completed*100//total}%)")

        return {
            'satellites': analyzed_satellites,
            'stats': stats
        }


def _process_single_satellite_worker(
    satellite: Dict[str, Any],
    constellation: str,
    system_config: Dict[str, Any],
    signal_thresholds: Dict[str, float],
    config: Dict[str, Any],
    enable_propagation_sim: bool = False,
    propagation_sim_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Worker 函數：處理單顆衛星（用於並行處理）

    注意：這個函數必須在類外部定義，以便 ProcessPoolExecutor 可以序列化它

    Args:
        enable_propagation_sim: 是否啟用傳播模擬 (Proposal 002)
        propagation_sim_config: 傳播模擬配置 (如果啟用)
    """
    try:
        # 在 worker 進程中重新創建 propagation_simulator（如果啟用）
        propagation_simulator = None
        if enable_propagation_sim and propagation_sim_config:
            try:
                from ..propagation_simulator import PropagationConditionSimulator
                import logging
                worker_logger = logging.getLogger(__name__)
                propagation_simulator = PropagationConditionSimulator(
                    propagation_sim_config,
                    worker_logger
                )
            except Exception as e:
                logger.warning(f"⚠️ Worker 進程創建 propagation_simulator 失敗: {e}")
                propagation_simulator = None

        # 在 worker 進程中重新創建分析器（傳入 propagation_simulator）
        from ..time_series_analyzer import create_time_series_analyzer
        time_series_analyzer = create_time_series_analyzer(
            config,
            signal_thresholds,
            propagation_simulator  # 🆕 傳遞 propagation_simulator
        )

        # ✅ Fail-Fast: 明確檢查 satellite_id
        if 'satellite_id' not in satellite:
            logger.warning("Worker: 衛星數據缺少 satellite_id 字段")
            return None
        satellite_id = satellite['satellite_id']

        # ✅ Fail-Fast: 明確檢查 time_series
        if 'time_series' not in satellite:
            logger.warning(f"Worker: 衛星 {satellite_id} 缺少 time_series 字段")
            return None
        time_series = satellite['time_series']

        if not time_series:
            logger.debug(f"Worker: 衛星 {satellite_id} 的 time_series 為空")
            return None

        # 分析時間序列
        time_series_analysis = time_series_analyzer.analyze_time_series(
            satellite_id=satellite_id,
            time_series=time_series,
            system_config=system_config,
            constellation=constellation  # A3 事件需要星座資訊
        )

        # 返回分析結果
        return {
            'satellite_id': satellite_id,
            'constellation': constellation,
            'time_series': time_series_analysis['time_series'],
            'summary': time_series_analysis['summary'],
            'physical_parameters': time_series_analysis['physics_summary']
        }

    except Exception as e:
        # ✅ Fail-Fast: 明確檢查 satellite_id（用於錯誤日誌）
        sat_id = satellite.get('satellite_id', 'UNKNOWN')  # ✅ Exception 處理中可使用預設值
        logger.error(f"❌ Worker 處理衛星 {sat_id} 失敗: {e}")
        return None
