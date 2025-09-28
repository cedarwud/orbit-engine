#!/usr/bin/env python3
"""
🎯 修復版混合處理器 - 正確的架構設計

設計原則：
✅ 完全繼承標準版的業務邏輯和數據流程
✅ 只在底層計算組件中使用GPU優化
✅ 不重寫任何業務邏輯方法
✅ 保持與標準版完全一致的結果

架構：
- SGP4計算: 使用並行GPU計算器 (僅計算優化)
- 座標轉換: 使用標準版業務邏輯 (保持正確性)
- 可見性分析: 使用標準版業務邏輯 (保持正確性)
- 鏈路可行性: 使用標準版業務邏輯 (保持正確性)
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 導入標準處理器作為基礎 (確保業務邏輯正確)
from .stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

# 導入優化組件 (僅用於計算性能優化)
from .parallel_sgp4_calculator import ParallelSGP4Calculator, ParallelConfig
from .sgp4_calculator import SGP4OrbitResult, SGP4Position
from .gpu_coordinate_converter import check_gpu_availability

# 導入處理結果和狀態類型
try:
    from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus, create_processing_result
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus, create_processing_result

logger = logging.getLogger(__name__)


class HybridStage2ProcessorFixed(Stage2OrbitalComputingProcessor):
    """
    🎯 修復版混合處理器 - 正確的架構

    設計理念：
    - 100% 繼承標準版的業務邏輯
    - 只在計算層面使用GPU優化
    - 不改變任何數據流程和篩選邏輯
    - 確保結果與標準版完全一致
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化修復版混合處理器"""
        # 🔧 完全繼承標準版的初始化
        super().__init__(config)

        self.logger = logging.getLogger(f"{__name__}.HybridStage2ProcessorFixed")

        # 🎯 性能優化標記
        self.enable_gpu_optimization = True
        self.enable_parallel_processing = True

        # 性能統計
        self.performance_stats = {
            'sgp4_calculation_time': 0.0,
            'total_processing_time': 0.0,
            'gpu_acceleration_used': False,
            'parallel_processing_used': False
        }

        # 檢查硬體可用性
        self.gpu_info = check_gpu_availability()
        self.logger.info(f"🔧 GPU狀態: {self.gpu_info}")

        # 初始化性能優化組件
        self._initialize_performance_components()

        self.logger.info("🎯 修復版混合處理器初始化完成")
        self.logger.info("📋 架構: 標準業務邏輯 + 僅計算優化")

    def _initialize_performance_components(self):
        """初始化性能優化組件"""
        try:
            # 🚀 並行SGP4計算器 (僅優化計算)
            if self.enable_parallel_processing:
                parallel_config = ParallelConfig(
                    enable_gpu=self.gpu_info.get('cupy_available', False),
                    enable_multiprocessing=True,
                    gpu_batch_size=5000,
                    cpu_workers=min(16, max(8, os.cpu_count())),
                    memory_limit_gb=8.0
                )

                self.parallel_sgp4_calculator = ParallelSGP4Calculator(parallel_config)
                self.logger.info("✅ 並行SGP4計算器已初始化")
                self.performance_stats['gpu_acceleration_used'] = True
                self.performance_stats['parallel_processing_used'] = True
            else:
                self.parallel_sgp4_calculator = None

        except Exception as e:
            self.logger.warning(f"⚠️ 性能優化組件初始化失敗: {e}")
            self.parallel_sgp4_calculator = None
            self.enable_gpu_optimization = False
            self.enable_parallel_processing = False

    def _perform_modular_orbital_calculations(self, tle_data: List[Dict]) -> Dict[str, SGP4OrbitResult]:
        """
        🚀 重寫SGP4計算 - 使用並行GPU優化

        這是唯一允許重寫的方法，因為它純粹是計算優化，不涉及業務邏輯
        """
        self.logger.info("🚀 執行混合式SGP4軌道計算...")
        start_time = time.time()

        try:
            if (self.enable_parallel_processing and
                self.parallel_sgp4_calculator is not None and
                len(tle_data) > 100):  # 大數據集才使用GPU

                self.logger.info("⚡ 使用並行SGP4計算器...")

                # 🎯 獲取時間序列 (使用標準版邏輯確保正確性)
                if tle_data:
                    sample_satellite = tle_data[0]
                    constellation = self._determine_satellite_constellation(
                        sample_satellite.get('satellite_id', ''),
                        sample_satellite
                    )

                    # 使用標準版的時間序列獲取方法
                    time_minutes_series = self._get_constellation_time_series(constellation, sample_satellite)

                    # 轉換為datetime對象列表
                    base_time_str = self._get_calculation_base_time([sample_satellite])
                    base_time = datetime.fromisoformat(base_time_str.replace('Z', '+00:00'))
                    datetime_series = [
                        base_time + timedelta(minutes=float(minutes))
                        for minutes in time_minutes_series
                    ]

                    self.logger.info(f"📊 時間序列準備完成: {len(datetime_series)} 個時間點")

                    # 🚀 使用並行計算器進行GPU優化計算
                    orbital_results = self.parallel_sgp4_calculator.calculate_batch(
                        tle_data, datetime_series
                    )

                    self.performance_stats['sgp4_calculation_time'] = time.time() - start_time
                    self.logger.info(f"✅ 混合式SGP4計算完成: {len(orbital_results)} 顆衛星")
                    return orbital_results

            # 回退到標準版計算
            self.logger.info("📊 回退到標準SGP4計算...")
            return super()._perform_modular_orbital_calculations(tle_data)

        except Exception as e:
            self.logger.error(f"❌ 混合式SGP4計算失敗: {e}")
            # 安全回退到標準版
            return super()._perform_modular_orbital_calculations(tle_data)

    # 🔧 完全移除所有其他重寫方法
    # 讓混合處理器100%使用標準版的業務邏輯：
    # - _perform_coordinate_conversions (使用標準版)
    # - _perform_modular_visibility_analysis (使用標準版)
    # - _perform_link_feasibility_filtering (使用標準版)
    # - _perform_trajectory_prediction (使用標準版)

    def save_results(self, results):
        """保存結果 - 使用壓縮優化"""
        try:
            # 使用gzip壓縮保存 (僅系統效率優化)
            import gzip
            import json
            from pathlib import Path

            # 確保輸出目錄存在
            output_dir = Path("data/outputs/stage2")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hybrid_stage2_output_{timestamp}.json.gz"
            filepath = output_dir / filename

            # 壓縮保存
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ 結果已壓縮保存: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.warning(f"⚠️ 壓縮保存失敗，使用標準保存: {e}")
            # 回退到標準保存方法
            return super().save_results(results)

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        return {
            **self.performance_stats,
            'processor_type': 'hybrid_fixed',
            'gpu_available': self.gpu_info.get('cupy_available', False),
            'parallel_enabled': self.enable_parallel_processing
        }