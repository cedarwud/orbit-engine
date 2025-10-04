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

    def __init__(self, max_workers: int, config: Dict[str, Any], signal_thresholds: Dict[str, float]):
        """
        初始化工作器管理器

        Args:
            max_workers: 最大工作器數量
            config: 配置字典
            signal_thresholds: 信號門檻配置
        """
        self.max_workers = max_workers
        self.config = config
        self.signal_thresholds = signal_thresholds
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
            satellite_id = satellite.get('satellite_id')
            time_series = satellite.get('time_series', [])

            if not time_series:
                self.logger.warning(f"衛星 {satellite_id} 缺少時間序列數據，跳過")
                continue

            stats['total_satellites_analyzed'] += 1

            try:
                # 分析時間序列
                time_series_analysis = time_series_analyzer.analyze_time_series(
                    satellite_id=satellite_id,
                    time_series=time_series,
                    system_config=system_config
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
            # 提交所有衛星處理任務
            future_to_satellite = {
                executor.submit(
                    _process_single_satellite_worker,
                    satellite,
                    constellation,
                    system_config,
                    self.signal_thresholds,
                    self.config
                ): satellite for satellite in satellites if satellite.get('time_series')
            }

            # 收集結果
            completed = 0
            total = len(future_to_satellite)

            for future in as_completed(future_to_satellite):
                satellite = future_to_satellite[future]
                satellite_id = satellite.get('satellite_id')
                completed += 1

                try:
                    result = future.result()
                    if result and 'satellite_id' in result:
                        analyzed_satellites[result['satellite_id']] = result
                        stats['total_satellites_analyzed'] += 1

                        # 更新統計
                        avg_quality = result.get('summary', {}).get('average_quality_level', 'poor')
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
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Worker 函數：處理單顆衛星（用於並行處理）

    注意：這個函數必須在類外部定義，以便 ProcessPoolExecutor 可以序列化它
    """
    try:
        # 在 worker 進程中重新創建分析器
        from ..time_series_analyzer import create_time_series_analyzer
        time_series_analyzer = create_time_series_analyzer(config, signal_thresholds)

        satellite_id = satellite.get('satellite_id')
        time_series = satellite.get('time_series', [])

        if not time_series:
            return None

        # 分析時間序列
        time_series_analysis = time_series_analyzer.analyze_time_series(
            satellite_id=satellite_id,
            time_series=time_series,
            system_config=system_config
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
        logger.error(f"❌ Worker 處理衛星 {satellite.get('satellite_id')} 失敗: {e}")
        return None
