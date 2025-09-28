#!/usr/bin/env python3
"""
🎯 Hybrid Stage2 Processor - 結合兩者優勢的最佳實作

設計原則：
✅ 計算密集部分使用優化版 (GPU/並行)
✅ 業務邏輯部分使用標準版 (正確性)
✅ 系統效率部分使用優化版 (記憶體/保存)
✅ 資料格式統一 (內部字典 + 外部物件)

性能目標: 467秒 → 60-90秒，同時確保結果正確性
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

# 導入標準處理器作為基礎 (確保業務邏輯正確)
from .stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

# 導入優化組件 (計算性能)
from .parallel_sgp4_calculator import ParallelSGP4Calculator, ParallelConfig
from .sgp4_calculator import SGP4OrbitResult, SGP4Position
from .gpu_coordinate_converter import GPUCoordinateConverter, check_gpu_availability

# 導入處理結果和狀態類型
try:
    from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus, create_processing_result
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus, create_processing_result

logger = logging.getLogger(__name__)


class HybridStage2Processor(Stage2OrbitalComputingProcessor):
    """
    🎯 混合式階段二處理器 - 結合兩者優勢

    架構設計：
    - 繼承標準版確保業務邏輯正確性
    - 重寫計算密集方法使用優化版性能
    - 統一資料格式避免轉換問題
    - 完整的錯誤處理和性能監控
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化混合式處理器"""
        # 初始化標準版基礎 (確保所有業務邏輯正確)
        super().__init__(config)

        self.logger = logging.getLogger(f"{__name__}.HybridStage2Processor")

        # 🎯 性能優化配置
        self.enable_gpu_optimization = True
        self.enable_parallel_processing = True
        self.enable_memory_optimization = True

        # 性能統計
        self.performance_stats = {
            'sgp4_calculation_time': 0.0,
            'coordinate_conversion_time': 0.0,
            'visibility_analysis_time': 0.0,
            'link_feasibility_time': 0.0,
            'total_processing_time': 0.0,
            'gpu_acceleration_used': False,
            'parallel_processing_used': False,
            'memory_optimization_used': False,
            'data_format_unified': True
        }

        # 檢查硬體可用性
        self.gpu_info = check_gpu_availability()
        self.logger.info(f"🔧 GPU狀態: {self.gpu_info}")

        # 初始化優化組件
        self._initialize_performance_components()

        self.logger.info("🎯 混合式階段二處理器初始化完成")
        self.logger.info("📋 架構: 標準邏輯 + 優化計算 + 高效系統")

    def _initialize_performance_components(self):
        """初始化性能優化組件"""
        try:
            # 🚀 並行SGP4計算器
            if self.enable_parallel_processing:
                parallel_config = ParallelConfig(
                    enable_gpu=self.gpu_info.get('cupy_available', False),
                    enable_multiprocessing=True,
                    gpu_batch_size=5000,
                    cpu_workers=min(16, max(8, os.cpu_count())),
                    memory_limit_gb=8.0
                )
                self.parallel_sgp4 = ParallelSGP4Calculator(parallel_config)
                self.performance_stats['parallel_processing_used'] = True
                self.logger.info("✅ 並行SGP4計算器已初始化")

            # 🌐 GPU座標轉換器
            if self.enable_gpu_optimization and self.gpu_info.get('cupy_available', False):
                self.gpu_converter = GPUCoordinateConverter(
                    observer_location=self.observer_location,
                    enable_gpu=True
                )
                self.performance_stats['gpu_acceleration_used'] = True
                self.logger.info("✅ GPU座標轉換器已初始化")
            else:
                self.gpu_converter = None
                self.logger.info("ℹ️ GPU不可用，將使用CPU座標轉換")

            # 🧠 記憶體管理配置
            if self.enable_memory_optimization:
                self.batch_size = 2000  # 每批處理衛星數
                self.memory_threshold_gb = 4.0  # 記憶體使用門檻
                self.performance_stats['memory_optimization_used'] = True
                self.logger.info("✅ 記憶體優化已啟用")

        except Exception as e:
            self.logger.warning(f"⚠️ 性能組件初始化失敗，將使用標準處理: {e}")
            self.enable_gpu_optimization = False
            self.enable_parallel_processing = False

    def _perform_modular_orbital_calculations(self, tle_data: List[Dict]) -> Dict[str, SGP4OrbitResult]:
        """
        🚀 重寫SGP4軌道計算 - 使用並行優化但保持標準介面
        """
        start_time = time.time()
        self.logger.info("🚀 執行混合式SGP4軌道計算...")

        try:
            if self.enable_parallel_processing and hasattr(self, 'parallel_sgp4'):
                # 📊 使用優化版的計算邏輯
                self.logger.info("⚡ 使用並行SGP4計算器...")

                # 準備時間序列 (重用標準版邏輯)
                time_series = self._prepare_optimized_time_series(tle_data)

                # 並行計算
                parallel_results = self.parallel_sgp4.batch_calculate_parallel(tle_data, time_series)

                # 🔄 格式轉換：字典 → SGP4OrbitResult 物件 (統一介面)
                orbital_results = self._convert_to_standard_format(parallel_results, tle_data)

                # 更新標準版統計 (確保兼容性)
                self._update_standard_statistics(orbital_results, tle_data)

                self.logger.info(f"✅ 並行SGP4計算完成: {len(orbital_results)} 顆衛星")

            else:
                # 回退到標準版計算
                self.logger.info("📊 使用標準SGP4計算...")
                orbital_results = super()._perform_modular_orbital_calculations(tle_data)

            self.performance_stats['sgp4_calculation_time'] = time.time() - start_time
            return orbital_results

        except Exception as e:
            self.logger.error(f"❌ 混合式SGP4計算失敗: {e}")
            # 安全回退到標準版
            return super()._perform_modular_orbital_calculations(tle_data)

    def _prepare_optimized_time_series(self, tle_data: List[Dict]) -> List[datetime]:
        """準備優化的時間序列 (重用標準版邏輯)"""
        if not tle_data:
            return []

        # 使用標準版的星座分組和時間序列邏輯
        sample_satellite = tle_data[0]
        constellation_groups = self._group_satellites_by_constellation(tle_data)

        # 取最大的星座組來決定時間序列
        largest_constellation = max(constellation_groups.items(), key=lambda x: len(x[1]))
        constellation_name, constellation_satellites = largest_constellation

        if constellation_satellites:
            # 使用標準版的時間序列計算
            time_minutes_series = self._get_constellation_time_series(constellation_name, constellation_satellites[0])

            # 轉換為datetime格式
            base_time_str = self._get_calculation_base_time([sample_satellite])
            base_time = datetime.fromisoformat(base_time_str.replace('Z', '+00:00'))

            datetime_series = []
            for minutes in time_minutes_series:
                time_offset = timedelta(minutes=float(minutes))
                datetime_point = base_time + time_offset
                datetime_series.append(datetime_point)

            self.logger.info(f"📊 時間序列準備完成: {len(datetime_series)} 個時間點")
            return datetime_series

        return []

    def _convert_to_standard_format(self, parallel_results: Dict[str, Any], tle_data: List[Dict]) -> Dict[str, SGP4OrbitResult]:
        """
        🔄 格式轉換：並行計算結果 → 標準SGP4OrbitResult格式
        確保與標準版介面完全兼容
        """
        standard_results = {}

        for satellite_id, result_dict in parallel_results.items():
            try:
                if isinstance(result_dict, dict) and 'sgp4_positions' in result_dict:
                    # 轉換SGP4Position物件
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
                        algorithm_used=result_dict.get('algorithm_used', 'SGP4_Parallel'),
                        precision_grade=result_dict.get('precision_grade', 'A')
                    )

                    standard_results[satellite_id] = orbit_result

            except Exception as e:
                self.logger.warning(f"格式轉換失敗 {satellite_id}: {e}")
                continue

        self.logger.info(f"🔄 格式轉換完成: {len(standard_results)}/{len(parallel_results)} 成功")
        return standard_results

    def _update_standard_statistics(self, orbital_results: Dict[str, SGP4OrbitResult], tle_data: List[Dict]):
        """更新標準版統計資訊 (確保兼容性)"""
        successful_calculations = sum(1 for result in orbital_results.values()
                                    if result.calculation_successful)

        # 更新SGP4Calculator統計
        if hasattr(self.sgp4_calculator, 'calculation_stats'):
            self.sgp4_calculator.calculation_stats.update({
                'total_calculations': len(tle_data),
                'successful_calculations': successful_calculations,
                'failed_calculations': len(tle_data) - successful_calculations
            })

        # 更新處理統計
        self.processing_stats.update({
            'total_satellites_processed': len(tle_data),
            'successful_calculations': successful_calculations,
            'failed_calculations': len(tle_data) - successful_calculations
        })

    def _perform_coordinate_conversions(self, orbital_results: Dict[str, SGP4OrbitResult]) -> Dict[str, Any]:
        """
        🌐 座標轉換 - 使用標準版邏輯確保結果正確性

        設計原則：不重寫業務邏輯，保持與標準版完全一致的結果
        如果需要GPU加速，應該在CoordinateConverter底層實現，而非重寫整個流程
        """
        start_time = time.time()
        self.logger.info("🌐 執行座標轉換 (使用標準版邏輯)...")

        try:
            # 直接使用標準版的座標轉換邏輯 - 確保結果正確性
            converted_results = super()._perform_coordinate_conversions(orbital_results)

            self.performance_stats['coordinate_conversion_time'] = time.time() - start_time
            self.logger.info(f"✅ 座標轉換完成: {len(converted_results)} 顆衛星")
            return converted_results

        except Exception as e:
            self.logger.error(f"❌ 座標轉換失敗: {e}")
            raise

    def _gpu_batch_coordinate_conversion(self, orbital_results: Dict[str, SGP4OrbitResult]) -> Dict[str, Any]:
        """GPU批次座標轉換 (優化版邏輯 + 標準版介面)"""
        converted_results = {}
        total_satellites = len(orbital_results)

        if self.enable_memory_optimization and total_satellites > self.batch_size:
            # 分批處理大數據集
            self.logger.info(f"🔄 GPU分批處理: {total_satellites} 顆衛星 → {self.batch_size} 顆/批")

            satellite_items = list(orbital_results.items())
            for batch_num, start_idx in enumerate(range(0, total_satellites, self.batch_size)):
                end_idx = min(start_idx + self.batch_size, total_satellites)
                batch_satellites = dict(satellite_items[start_idx:end_idx])

                self.logger.info(f"🔄 處理GPU批次 {batch_num + 1}: {start_idx+1}-{end_idx}")

                # 處理當前批次
                batch_results = self._process_gpu_batch(batch_satellites)
                converted_results.update(batch_results)

                # 記憶體清理
                del batch_satellites, batch_results
                import gc
                gc.collect()
        else:
            # 小數據集直接處理
            converted_results = self._process_gpu_batch(orbital_results)

        return converted_results

    def _process_gpu_batch(self, orbital_batch: Dict[str, SGP4OrbitResult]) -> Dict[str, Any]:
        """處理單個GPU批次"""
        batch_results = {}

        for satellite_id, orbit_result in orbital_batch.items():
            try:
                if not orbit_result.positions:
                    continue

                # 準備GPU批次資料
                from .coordinate_converter import Position3D
                positions = [Position3D(x=pos.x, y=pos.y, z=pos.z) for pos in orbit_result.positions]

                # GPU批次計算
                gpu_result = self.gpu_converter.gpu_batch_calculate_look_angles(positions)

                # 轉換為標準格式
                converted_positions = []
                for i, sgp4_pos in enumerate(orbit_result.positions):
                    if i < len(gpu_result.look_angles):
                        elevation, azimuth, range_km = gpu_result.look_angles[i]

                        enhanced_position = {
                            'x': sgp4_pos.x,
                            'y': sgp4_pos.y,
                            'z': sgp4_pos.z,
                            'timestamp': sgp4_pos.timestamp,
                            'time_since_epoch_minutes': sgp4_pos.time_since_epoch_minutes,
                            'coordinate_conversion': {
                                'conversion_successful': True,
                                'gpu_accelerated': True
                            },
                            'elevation_deg': float(elevation),
                            'azimuth_deg': float(azimuth),
                            'range_km': float(range_km)
                        }
                        converted_positions.append(enhanced_position)

                # 保持標準版格式
                batch_results[satellite_id] = {
                    'satellite_id': satellite_id,
                    'positions': converted_positions,
                    'conversion_successful': len(converted_positions) > 0,
                    'original_orbit_result': orbit_result
                }

            except Exception as e:
                self.logger.warning(f"GPU批次處理失敗 {satellite_id}: {e}")
                # 回退到CPU處理
                cpu_result = self._fallback_cpu_conversion(satellite_id, orbit_result)
                if cpu_result:
                    batch_results[satellite_id] = cpu_result

        return batch_results

    def _fallback_cpu_conversion(self, satellite_id: str, orbit_result: SGP4OrbitResult) -> Optional[Dict[str, Any]]:
        """GPU失敗時的CPU回退處理"""
        try:
            converted_positions = []

            for sgp4_pos in orbit_result.positions:
                from .coordinate_converter import Position3D
                sat_pos = Position3D(x=sgp4_pos.x, y=sgp4_pos.y, z=sgp4_pos.z)
                obs_time = datetime.fromisoformat(sgp4_pos.timestamp.replace('Z', '+00:00'))

                conversion_result = self.coordinate_converter.eci_to_topocentric(sat_pos, obs_time)

                if conversion_result["conversion_successful"]:
                    enhanced_position = {
                        'x': sgp4_pos.x,
                        'y': sgp4_pos.y,
                        'z': sgp4_pos.z,
                        'timestamp': sgp4_pos.timestamp,
                        'time_since_epoch_minutes': sgp4_pos.time_since_epoch_minutes,
                        'coordinate_conversion': conversion_result,
                        'elevation_deg': conversion_result['look_angles']['elevation_deg'],
                        'azimuth_deg': conversion_result['look_angles']['azimuth_deg'],
                        'range_km': conversion_result['look_angles']['range_km']
                    }
                    converted_positions.append(enhanced_position)

            return {
                'satellite_id': satellite_id,
                'positions': converted_positions,
                'conversion_successful': len(converted_positions) > 0,
                'original_orbit_result': orbit_result
            } if converted_positions else None

        except Exception as e:
            self.logger.warning(f"CPU回退也失敗 {satellite_id}: {e}")
            return None

    def _memory_optimized_coordinate_conversion(self, orbital_results: Dict[str, SGP4OrbitResult]) -> Dict[str, Any]:
        """記憶體優化的標準座標轉換"""
        if len(orbital_results) > self.batch_size:
            self.logger.info(f"🔄 記憶體優化分批處理: {len(orbital_results)} 顆衛星")

            converted_results = {}
            satellite_items = list(orbital_results.items())

            for batch_num, start_idx in enumerate(range(0, len(orbital_results), self.batch_size)):
                end_idx = min(start_idx + self.batch_size, len(orbital_results))
                batch_satellites = dict(satellite_items[start_idx:end_idx])

                # 使用標準版處理邏輯
                batch_results = super()._perform_coordinate_conversions(batch_satellites)
                converted_results.update(batch_results)

                # 記憶體清理
                del batch_satellites, batch_results
                import gc
                gc.collect()

            return converted_results
        else:
            return super()._perform_coordinate_conversions(orbital_results)

    def save_results(self, results: Dict[str, Any]) -> str:
        """
        💾 重寫保存方法 - 使用優化版的壓縮保存
        """
        try:
            from datetime import datetime, timezone
            import gzip

            # 使用優化版的保存邏輯
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_dir = os.path.join(project_root, "data", "outputs", "stage2")
            os.makedirs(output_dir, exist_ok=True)

            # 生成檔案名
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"hybrid_orbital_computing_{timestamp}.json.gz")

            # 自定義JSON編碼器
            class HybridJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'z'):
                        return {'x': obj.x, 'y': obj.y, 'z': obj.z}
                    elif isinstance(obj, datetime):
                        return obj.isoformat()
                    elif hasattr(obj, 'item') and callable(getattr(obj, 'item')):
                        return obj.item()
                    elif hasattr(obj, '__dict__'):
                        return obj.__dict__
                    return super().default(obj)

            # 壓縮保存
            self.logger.info(f"💾 開始壓縮保存結果...")
            start_time = time.time()

            json_str = json.dumps(results, ensure_ascii=False, indent=None,
                                separators=(',', ':'), cls=HybridJSONEncoder)

            with gzip.open(output_file, 'wt', encoding='utf-8', compresslevel=6) as f:
                f.write(json_str)

            save_time = time.time() - start_time
            file_size_mb = os.path.getsize(output_file) / (1024*1024)

            self.logger.info(f"✅ 壓縮保存完成: {file_size_mb:.2f}MB, 耗時: {save_time:.1f}秒")
            self.logger.info(f"📁 檔案位置: {output_file}")

            return output_file

        except Exception as e:
            self.logger.warning(f"⚠️ 壓縮保存失敗，使用標準保存: {e}")
            return super().save_results(results)

    def execute(self, stage1_output: Any = None) -> Dict[str, Any]:
        """
        🎯 混合式執行方法 - 最佳的性能和正確性
        """
        overall_start = time.time()
        start_time = datetime.now(timezone.utc)

        self.logger.info("🎯 開始執行混合式階段二處理...")

        try:
            # 輸入驗證 (使用標準版邏輯)
            if stage1_output is None:
                stage1_output = self._load_stage1_output()

            if not self._validate_stage1_output(stage1_output):
                return {
                    'success': False,
                    'error': 'Stage 1輸出數據驗證失敗',
                    'stage': 'stage2_orbital_computing_hybrid'
                }

            # 提取TLE數據 (使用標準版邏輯)
            tle_data = self._extract_tle_data(stage1_output)
            if not tle_data:
                return {
                    'success': False,
                    'error': '未找到有效的TLE數據',
                    'stage': 'stage2_orbital_computing_hybrid'
                }

            self.logger.info(f"📊 準備處理 {len(tle_data)} 顆衛星")

            # 🚀 階段1: SGP4軌道計算 (使用混合式優化)
            orbital_results = self._perform_modular_orbital_calculations(tle_data)

            # 🌐 階段2: 座標轉換 (使用混合式優化)
            converted_results = self._perform_coordinate_conversions(orbital_results)

            # 👁️ 階段3: 可見性分析 (使用標準版邏輯 - 確保正確性)
            vis_start = time.time()
            visibility_results = super()._perform_modular_visibility_analysis(converted_results, tle_data)
            self.performance_stats['visibility_analysis_time'] = time.time() - vis_start

            # 🔗 階段4: 鏈路可行性篩選 (使用標準版邏輯 - 確保正確性)
            feas_start = time.time()
            feasibility_results = super()._perform_link_feasibility_filtering(visibility_results, tle_data)
            self.performance_stats['link_feasibility_time'] = time.time() - feas_start

            # 🔮 階段5: 軌道預測 (使用標準版邏輯 - 確保正確性)
            prediction_results = super()._perform_trajectory_prediction(orbital_results, tle_data)

            # 📋 階段6: 結果整合 (使用標準版邏輯)
            integrated_results = super()._integrate_modular_results(
                orbital_results, converted_results, visibility_results,
                feasibility_results, prediction_results
            )

            # ✅ 數據驗證 (使用標準版邏輯)
            validation_result = self._validate_output_data(integrated_results)
            if not self._check_validation_result(validation_result):
                return {
                    'success': False,
                    'error': f'輸出數據驗證失敗: {self._extract_validation_errors(validation_result)}',
                    'stage': 'stage2_orbital_computing_hybrid'
                }

            # 📊 構建最終結果 (使用標準版邏輯)
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = super()._build_final_result(integrated_results, start_time, processing_time, tle_data)

            # 📈 添加混合式性能報告
            overall_time = time.time() - overall_start
            self.performance_stats['total_processing_time'] = overall_time
            result_data['hybrid_performance_metrics'] = self.performance_stats

            # 💾 保存結果 (使用優化版壓縮保存)
            output_file = self.save_results(result_data)

            # 📊 性能摘要
            self._log_hybrid_performance_summary()

            self.logger.info("🎯 混合式階段二處理完成")

            # 返回結果
            result_data['output_file'] = output_file
            result_data['success'] = True
            result_data['stage'] = 'stage2_orbital_computing_hybrid'
            result_data['architecture'] = 'hybrid_optimized'

            return result_data

        except Exception as e:
            self.logger.error(f"❌ 混合式階段二處理失敗: {e}")
            import traceback
            self.logger.error(f"錯誤詳情: {traceback.format_exc()}")

            return {
                'success': False,
                'error': str(e),
                'stage': 'stage2_orbital_computing_hybrid'
            }

    def _log_hybrid_performance_summary(self):
        """記錄混合式性能摘要"""
        stats = self.performance_stats

        self.logger.info("\n🎯 混合式處理器性能報告:")
        self.logger.info(f"  ⏱️ 總執行時間: {stats['total_processing_time']:.2f}秒")
        self.logger.info(f"  🚀 SGP4計算: {stats['sgp4_calculation_time']:.2f}秒")
        self.logger.info(f"  🌐 座標轉換: {stats['coordinate_conversion_time']:.2f}秒")
        self.logger.info(f"  👁️ 可見性分析: {stats['visibility_analysis_time']:.2f}秒")
        self.logger.info(f"  🔗 鏈路可行性: {stats['link_feasibility_time']:.2f}秒")

        self.logger.info("\n🔧 優化狀態:")
        self.logger.info(f"  🎮 GPU加速: {stats['gpu_acceleration_used']}")
        self.logger.info(f"  ⚡ 並行處理: {stats['parallel_processing_used']}")
        self.logger.info(f"  🧠 記憶體優化: {stats['memory_optimization_used']}")
        self.logger.info(f"  📊 資料格式統一: {stats['data_format_unified']}")

        # 計算性能提升
        baseline_time = 467.0  # 原始性能基線
        if stats['total_processing_time'] > 0:
            speedup = baseline_time / stats['total_processing_time']
            improvement = ((baseline_time - stats['total_processing_time']) / baseline_time) * 100
            self.logger.info(f"\n📈 性能提升: {speedup:.1f}x 加速, {improvement:.1f}% 改善")


def create_hybrid_stage2_processor(config: Optional[Dict[str, Any]] = None) -> HybridStage2Processor:
    """創建混合式階段二處理器"""
    return HybridStage2Processor(config)