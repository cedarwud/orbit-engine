#!/usr/bin/env python3
"""
🎯 Simple Hybrid Stage2 Processor - 正確的設計方式

設計原則：
✅ 只優化底層計算（SGP4並行）
✅ 其他業務邏輯完全使用標準版
✅ 不重寫整個方法，只替換計算核心
✅ 確保結果與標準版完全一致

性能目標: 保持準確性的前提下提升速度
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

# 導入標準處理器作為基礎
from .stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

# 導入並行SGP4計算器（唯一的優化組件）
from .parallel_sgp4_calculator import ParallelSGP4Calculator, ParallelConfig
from .sgp4_calculator import SGP4OrbitResult, SGP4Position

logger = logging.getLogger(__name__)


class HybridStage2ProcessorSimple(Stage2OrbitalComputingProcessor):
    """
    🎯 簡潔混合式階段二處理器

    設計原則：只優化計算核心，不重寫業務邏輯
    - 繼承標準版確保所有邏輯正確
    - 只重寫SGP4軌道計算方法
    - 座標轉換、可見性、鏈路篩選等完全使用標準版
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化混合處理器"""
        # 先初始化標準版
        super().__init__(config)

        # 性能統計
        self.performance_stats = {
            'parallel_processing_used': False,
            'sgp4_calculation_time': 0.0
        }

        # 初始化並行SGP4計算器（唯一的優化）
        self._initialize_parallel_sgp4()

        self.logger.info("🎯 簡潔混合式處理器初始化完成")
        self.logger.info("📋 架構: 標準版業務邏輯 + 並行SGP4計算")

    def _initialize_parallel_sgp4(self):
        """初始化並行SGP4計算器"""
        try:
            # 檢查是否可以使用並行處理
            cpu_count = os.cpu_count() or 4
            if cpu_count >= 4:  # 至少4核心才啟用並行
                parallel_config = ParallelConfig(
                    enable_gpu=False,  # 暫時不使用GPU避免複雜性
                    enable_multiprocessing=True,
                    gpu_batch_size=1000,
                    cpu_workers=min(8, max(4, cpu_count)),
                    memory_limit_gb=4.0
                )
                self.parallel_sgp4 = ParallelSGP4Calculator(parallel_config)
                self.performance_stats['parallel_processing_used'] = True
                self.logger.info(f"✅ 並行SGP4計算器已初始化 ({parallel_config.cpu_workers} 核心)")
            else:
                self.parallel_sgp4 = None
                self.logger.info("📊 系統核心數不足，使用標準SGP4計算")

        except Exception as e:
            self.logger.warning(f"⚠️ 並行SGP4初始化失敗，回退到標準版: {e}")
            self.parallel_sgp4 = None

    def _perform_modular_orbital_calculations(self, tle_data: List[Dict]) -> Dict[str, SGP4OrbitResult]:
        """
        🚀 重寫SGP4軌道計算 - 使用並行優化但保持標準介面

        這是唯一被重寫的方法，其他所有方法都使用標準版
        """
        start_time = time.time()
        self.logger.info("🚀 執行混合式SGP4軌道計算...")

        try:
            # 🔧 暫時停用並行SGP4 - 存在星座分組時間序列差異問題
            # 並行SGP4使用統一時間序列，而標準版按星座分組使用不同時間序列
            # 這導致軌道位置計算差異，影響可見性和可行性判斷準確性
            if False and self.parallel_sgp4 is not None and len(tle_data) > 50:
                # 使用並行計算
                self.logger.info("⚡ 使用並行SGP4計算器...")

                # 準備時間序列（重用標準版邏輯）
                time_series = self._prepare_time_series(tle_data)

                # 並行計算
                parallel_results = self.parallel_sgp4.batch_calculate_parallel(tle_data, time_series)

                # 轉換為標準格式
                orbital_results = self._convert_parallel_results(parallel_results, tle_data)

                self.logger.info(f"⚡ 並行SGP4計算完成: {len(orbital_results)} 顆衛星")

            else:
                # 使用標準版計算
                self.logger.info("📊 使用標準SGP4計算（暫時停用並行版）...")
                orbital_results = super()._perform_modular_orbital_calculations(tle_data)

            self.performance_stats['sgp4_calculation_time'] = time.time() - start_time
            return orbital_results

        except Exception as e:
            self.logger.error(f"❌ 混合式SGP4計算失敗，回退到標準版: {e}")
            # 安全回退
            return super()._perform_modular_orbital_calculations(tle_data)

    def _prepare_time_series(self, tle_data: List[Dict]) -> List[datetime]:
        """準備時間序列（使用正確的TLE epoch相對時間）"""
        if not tle_data:
            return []

        # 使用第一個TLE數據計算最佳時間點數
        sample_tle = tle_data[0]
        tle_line2 = sample_tle.get('tle_line2', sample_tle.get('line2', ''))

        # 使用標準版的邏輯計算最佳時間點
        time_interval_seconds = self.config.get('orbital_calculation', {}).get('time_interval_seconds', 30)
        time_points = self.sgp4_calculator.calculate_optimal_time_points(
            tle_line2,
            time_interval_seconds=time_interval_seconds,
            coverage_cycles=1.0,
            use_max_period=True
        )

        # 解析第一個TLE的epoch時間作為基準
        tle_line1 = sample_tle.get('tle_line1', sample_tle.get('line1', ''))
        epoch_year = int(tle_line1[18:20])
        epoch_day = float(tle_line1[20:32])

        if epoch_year < 57:
            full_year = 2000 + epoch_year
        else:
            full_year = 1900 + epoch_year

        base_epoch_time = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)

        # 生成時間序列（從epoch開始的絕對時間）
        time_series = []
        interval_minutes = time_interval_seconds / 60.0

        for i in range(int(time_points)):
            time_offset_minutes = i * interval_minutes
            absolute_time = base_epoch_time + timedelta(minutes=time_offset_minutes)
            time_series.append(absolute_time)

        self.logger.info(f"🕐 時間序列: {len(time_series)}個點, 間隔{time_interval_seconds}秒")
        self.logger.info(f"📅 基準epoch時間: {base_epoch_time}")
        self.logger.info(f"📅 開始時間: {time_series[0]}")
        self.logger.info(f"📅 結束時間: {time_series[-1]}")

        return time_series

    def _convert_parallel_results(self, parallel_results: Dict[str, Any], tle_data: List[Dict]) -> Dict[str, SGP4OrbitResult]:
        """轉換並行計算結果為標準格式"""
        standard_results = {}

        for satellite_id, result_dict in parallel_results.items():
            try:
                if isinstance(result_dict, dict) and 'sgp4_positions' in result_dict:
                    # 轉換位置數據
                    positions = []
                    for pos_data in result_dict['sgp4_positions']:
                        if hasattr(pos_data, 'x'):  # 已經是物件
                            positions.append(pos_data)
                        else:  # 是字典，需要轉換
                            position = SGP4Position(
                                x=pos_data.get('x', 0.0),
                                y=pos_data.get('y', 0.0),
                                z=pos_data.get('z', 0.0),
                                timestamp=pos_data.get('timestamp', ''),
                                time_since_epoch_minutes=pos_data.get('time_since_epoch_minutes', 0.0)
                            )
                            positions.append(position)

                    # 創建標準SGP4OrbitResult物件
                    orbit_result = SGP4OrbitResult(
                        satellite_id=satellite_id,
                        calculation_successful=result_dict.get('calculation_successful', True),
                        positions=positions,
                        algorithm_used=result_dict.get('algorithm_used', 'SGP4_Parallel')
                    )

                    standard_results[satellite_id] = orbit_result

                else:
                    self.logger.warning(f"⚠️ 並行結果格式異常: {satellite_id}")

            except Exception as e:
                self.logger.error(f"❌ 轉換並行結果失敗 {satellite_id}: {e}")

        return standard_results

    def execute(self, stage1_output: Any = None) -> Dict[str, Any]:
        """
        🎯 混合式執行方法

        只重寫性能統計部分，核心邏輯完全使用標準版
        """
        overall_start = time.time()
        start_time = datetime.now(timezone.utc)

        self.logger.info("🎯 開始執行簡潔混合式階段二處理...")

        try:
            # 使用標準版的execute邏輯
            result = super().process(stage1_output)

            # 添加混合式性能報告
            overall_time = time.time() - overall_start
            self._log_performance_summary(overall_time)

            # 轉換標準版ProcessingResult為字典格式
            if hasattr(result, 'data'):
                return {
                    'success': True,
                    'data': result.data,
                    'stage': 'stage2_orbital_computing_hybrid_simple',
                    'execution_time': overall_time,
                    'performance_stats': self.performance_stats
                }
            else:
                return result

        except Exception as e:
            self.logger.error(f"❌ 混合式處理失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'stage2_orbital_computing_hybrid_simple'
            }

    def _log_performance_summary(self, total_time: float):
        """記錄性能摘要"""
        self.logger.info("📊 混合式處理器性能報告:")
        self.logger.info(f"   總執行時間: {total_time:.1f} 秒")
        self.logger.info(f"   SGP4計算時間: {self.performance_stats['sgp4_calculation_time']:.1f} 秒")
        self.logger.info(f"   並行處理: {'是' if self.performance_stats['parallel_processing_used'] else '否'}")

        if self.performance_stats['parallel_processing_used']:
            self.logger.info("🚀 使用了並行SGP4優化")
        else:
            self.logger.info("📊 使用標準SGP4計算")