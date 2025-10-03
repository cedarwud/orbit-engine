"""
🛰️ Stage 2: 軌道狀態傳播層處理器 - v3.0 重構版本

完全符合新架構的 Grade A 學術級實現：
✅ 使用 Stage 1 的 epoch_datetime，禁止 TLE 重新解析
✅ SGP4/SDP4 軌道傳播計算，輸出 TEME 座標
✅ 時間序列生成，支援可配置時間窗口
✅ 專業庫使用，禁止簡化算法
❌ 不做座標轉換 (留給 Stage 3)
❌ 不做可見性分析 (留給 Stage 4)
❌ 不做信號分析 (留給 Stage 5)

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/ACADEMIC_STANDARDS.md
- 階段二重點: 使用精確橢圓軌道方程、攝動計算符合JPL標準、無簡化二體問題
- 所有數值常量必須有 SOURCE 標記
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
import json
import os
import psutil
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

try:
    from shared.base_stage_processor import BaseStageProcessor
    from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus, create_processing_result
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shared.base_stage_processor import BaseStageProcessor
    from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus, create_processing_result

from .sgp4_calculator import SGP4Calculator, SGP4Position, SGP4OrbitResult
from .stage2_validator import Stage2Validator
from .stage2_result_manager import Stage2ResultManager
# 🆕 統一時間窗口管理器 (v3.1)
from .unified_time_window_manager import UnifiedTimeWindowManager

logger = logging.getLogger(__name__)

@dataclass
class TEMEPosition:
    """TEME 座標系統中的位置"""
    x: float  # km
    y: float  # km
    z: float  # km
    vx: float  # km/s
    vy: float  # km/s
    vz: float  # km/s
    timestamp: str  # ISO 8601 格式
    time_since_epoch_minutes: float

@dataclass
class OrbitalStateResult:
    """軌道狀態傳播結果"""
    satellite_id: str
    constellation: str
    teme_positions: List[TEMEPosition]
    epoch_datetime: str
    propagation_successful: bool
    algorithm_used: str = "SGP4"
    coordinate_system: str = "TEME"

class Stage2OrbitalPropagationProcessor(BaseStageProcessor):
    """
    Stage 2: 軌道狀態傳播層處理器 (v3.0 重構版本)

    v3.0 專職責任：
    1. 使用 Stage 1 的 epoch_datetime，零 TLE 重新解析
    2. SGP4/SDP4 軌道傳播計算
    3. 生成時間序列軌道狀態
    4. 輸出 TEME 座標系統數據

    ❌ 不再負責：座標轉換、可見性分析、信號分析
    ✅ 新架構：純軌道狀態傳播，為後續階段提供基礎數據
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化軌道狀態傳播處理器"""
        super().__init__(stage_name="orbital_computing", config=config or {})

        self.logger = logging.getLogger(f"{__name__}.Stage2OrbitalComputingProcessor")

        # 加載配置
        self._load_configuration()

        # 初始化 SGP4 計算器
        self.sgp4_calculator = SGP4Calculator()

        # 初始化驗證器和結果管理器
        self.validator = Stage2Validator()
        self.result_manager = Stage2ResultManager(logger_instance=self.logger)

        # 🆕 統一時間窗口管理器 (v3.1)
        self.time_window_manager = UnifiedTimeWindowManager(
            config=self.config,
            stage1_output_dir=self.config.get('stage1_output_dir', 'data/outputs/stage1')
        )

        # 🆕 載入參考時刻（如果是統一時間窗口模式）
        self.reference_time = self.time_window_manager.load_reference_time()

        # 🚀 動態 CPU 並行配置
        self.max_workers = self._get_optimal_workers()
        self.enable_parallel = self.max_workers > 1

        # 處理統計
        self.processing_stats = {
            'total_satellites_processed': 0,
            'successful_propagations': 0,
            'failed_propagations': 0,
            'total_teme_positions': 0,
            'processing_grade': 'A',
            'architecture_version': 'v3.0',
            'parallel_workers': self.max_workers
        }

        logger.info("✅ Stage 2 軌道狀態傳播處理器已初始化 - v3.0 架構")
        logger.info(f"🚀 並行處理配置: {self.max_workers} 個工作進程 ({'啟用' if self.enable_parallel else '禁用'})")

    def _load_configuration(self):
        """從配置文件加載參數"""
        try:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "../../../config/stage2_orbital_computing.yaml"
            )

            if os.path.exists(config_path):
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                self.config.update(file_config)

            # 時間序列配置 - 必須從配置文件讀取
            time_config = self.config.get('time_series')
            if not time_config:
                raise RuntimeError("配置文件缺少必要的 time_series 設定")

            self.time_interval_seconds = time_config.get('interval_seconds')
            if self.time_interval_seconds is None:
                raise RuntimeError("配置文件缺少 time_series.interval_seconds")

            # dynamic_calculation 必須為 True
            self.dynamic_calculation = time_config.get('dynamic_calculation')
            if self.dynamic_calculation is None:
                raise RuntimeError("配置文件缺少 time_series.dynamic_calculation")
            if not self.dynamic_calculation:
                raise RuntimeError("Stage 2 要求 dynamic_calculation=True (Grade A 標準)")

            self.min_positions = time_config.get('min_positions', 60)  # 合理的最小值
            self.coverage_cycles = time_config.get('coverage_cycles', 1.0)  # 合理的預設值

            # SGP4 配置
            sgp4_config = self.config.get('sgp4_propagation', {})
            self.coordinate_system = sgp4_config.get('output_coordinate_system', 'TEME')
            self.propagation_method = sgp4_config.get('method', 'SGP4')

            logger.info(f"✅ Stage 2 配置加載完成:")
            logger.info(f"   時間間隔: {self.time_interval_seconds}秒")
            logger.info(f"   動態計算: {self.dynamic_calculation} (Grade A 要求)")
            logger.info(f"   覆蓋週期: {self.coverage_cycles}x 軌道週期")
            logger.info(f"   最小點數: {self.min_positions}")
            logger.info(f"   座標系統: {self.coordinate_system}")

        except Exception as e:
            logger.error(f"❌ 配置文件加載失敗: {e}")
            raise RuntimeError(f"Stage 2 配置文件載入失敗，無法繼續: {e}")

    def _get_optimal_workers(self) -> int:
        """
        動態計算最優工作器數量 - 基於 CPU 狀態和配置

        優先級：配置文件 > 動態 CPU 檢測 > 保守預設值

        Returns:
            int: 最優工作器數量
        """
        try:
            # 1. 檢查配置文件設定（最高優先級）
            performance_config = self.config.get('performance', {})
            config_workers = performance_config.get('max_workers')

            if config_workers and config_workers > 0:
                logger.info(f"📋 使用配置文件設定: {config_workers} 個工作器")
                return config_workers

            # 2. 檢查是否強制單線程
            if performance_config.get('force_single_thread', False):
                logger.info("⚠️ 強制單線程模式")
                return 1

            # 3. 動態 CPU 狀態檢測
            total_cpus = mp.cpu_count()

            # 獲取當前 CPU 使用率（採樣 0.5 秒，減少等待時間）
            try:
                cpu_usage = psutil.cpu_percent(interval=0.5)
                available_cpu = 100 - cpu_usage

                # 動態策略配置（從配置文件讀取或使用預設值）
                strategy = performance_config.get('dynamic_worker_strategy', {})

                # ✅ 提高預設 CPU 使用率（更積極的並行策略）
                threshold_high = strategy.get('cpu_usage_threshold_high', 30)   # CPU < 30%: 使用 95% 核心
                threshold_medium = strategy.get('cpu_usage_threshold_medium', 50)  # CPU 30-50%: 使用 75% 核心
                # CPU > 50%: 使用 50% 核心

                if cpu_usage < threshold_high:
                    # CPU 空閒：使用 95% 核心（積極並行）
                    workers = max(1, int(total_cpus * 0.95))
                    logger.info(
                        f"💻 CPU 空閒（{cpu_usage:.1f}%）：使用 95% 核心 = {workers} 個工作器"
                    )
                elif cpu_usage < threshold_medium:
                    # CPU 中度使用：使用 75% 核心
                    workers = max(1, int(total_cpus * 0.75))
                    logger.info(
                        f"💻 CPU 中度使用（{cpu_usage:.1f}%）：使用 75% 核心 = {workers} 個工作器"
                    )
                else:
                    # CPU 繁忙：使用 50% 核心（保守策略）
                    workers = max(1, int(total_cpus * 0.5))
                    logger.info(
                        f"💻 CPU 繁忙（{cpu_usage:.1f}%）：使用 50% 核心 = {workers} 個工作器"
                    )

                logger.info(
                    f"📊 系統狀態: 總核心 {total_cpus}，CPU使用率 {cpu_usage:.1f}%，"
                    f"配置 {workers} 個並行工作器"
                )
                return workers

            except Exception as cpu_error:
                logger.warning(f"⚠️ CPU 狀態檢測失敗: {cpu_error}，使用預設配置")
                # 回退策略：總核心數 - 1（保留一個核心給系統）
                fallback_workers = max(1, total_cpus - 1)
                logger.info(f"📋 回退配置: {fallback_workers} 個工作器")
                return fallback_workers

        except Exception as e:
            logger.error(f"❌ 工作器配置失敗: {e}，使用單線程模式")
            return 1

    def process(self, input_data: Any) -> ProcessingResult:
        """
        主要處理方法 - 軌道狀態傳播

        Args:
            input_data: Stage 1 輸出的 ProcessingResult

        Returns:
            ProcessingResult: TEME 座標系統的軌道狀態數據
        """
        start_time = datetime.now(timezone.utc)
        logger.info("🚀 開始 Stage 2 軌道狀態傳播...")

        try:
            # 驗證輸入數據
            if not self._validate_stage1_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 1 輸出數據驗證失敗"
                )

            # 提取衛星數據
            satellites_data = self._extract_satellites_data(input_data)
            if not satellites_data:
                return create_processing_result(
                    status=ProcessingStatus.ERROR,
                    data={},
                    message="未找到有效的衛星數據"
                )

            logger.info(f"📊 輸入數據: {len(satellites_data)} 顆衛星")

            # 🆕 驗證參考時刻（如果是統一時間窗口模式）
            validation_result = self.time_window_manager.validate_reference_time(satellites_data)
            if not validation_result['valid']:
                logger.warning("⚠️ 參考時刻驗證未通過，但繼續執行（請檢查結果）")
                logger.warning(f"   符合率: {validation_result['compliance_rate']:.1f}%")
            else:
                logger.info(f"✅ 參考時刻驗證通過: {validation_result['compliance_rate']:.1f}% 衛星符合")

            # 🛰️ 核心步驟：軌道狀態傳播
            orbital_results = self._perform_orbital_propagation(satellites_data)

            if not orbital_results:
                return create_processing_result(
                    status=ProcessingStatus.ERROR,
                    data={},
                    message="軌道傳播失敗，無結果數據"
                )

            # 構建最終結果
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = self.result_manager.build_final_result(
                orbital_results=orbital_results,
                start_time=start_time,
                processing_time=processing_time,
                input_data=input_data,
                processing_stats=self.processing_stats,
                coordinate_system=self.coordinate_system,
                propagation_method=self.propagation_method,
                time_interval_seconds=self.time_interval_seconds,
                dynamic_calculation=self.dynamic_calculation,
                coverage_cycles=self.coverage_cycles
            )

            logger.info(
                f"✅ Stage 2 軌道狀態傳播完成："
                f"處理 {self.processing_stats['total_satellites_processed']} 顆衛星，"
                f"成功 {self.processing_stats['successful_propagations']} 顆，"
                f"生成 {self.processing_stats['total_teme_positions']} 個軌道狀態點"
            )

            # 🔬 執行5項專用驗證檢查
            validation_results = self.validator.run_validation_checks(result_data, satellites_data, orbital_results)
            result_data['validation'] = validation_results

            # 📋 保存驗證快照
            self.validator.save_validation_snapshot(
                result_data=result_data,
                processing_stats=self.processing_stats,
                coordinate_system=self.coordinate_system
            )

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功完成 {self.processing_stats['successful_propagations']} 顆衛星的軌道狀態傳播"
            )

        except Exception as e:
            logger.error(f"❌ Stage 2 軌道狀態傳播失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"軌道傳播錯誤: {str(e)}"
            )

    def _validate_stage1_output(self, input_data: Any) -> bool:
        """驗證 Stage 1 的輸出數據"""
        if not isinstance(input_data, dict):
            self.logger.error("輸入數據必須是字典格式")
            return False

        # 檢查是否有衛星數據
        if 'satellites' not in input_data and 'tle_data' not in input_data:
            self.logger.error("缺少衛星數據字段 (satellites 或 tle_data)")
            return False

        # 檢查 Stage 標識
        if 'stage' in input_data and input_data['stage'] != 'data_loading':
            self.logger.warning(f"Stage 字段值異常: {input_data['stage']}, 預期: data_loading")

        satellites_data = input_data.get('satellites', input_data.get('tle_data', []))
        if not satellites_data:
            self.logger.error("衛星數據為空")
            return False

        # 🚨 關鍵驗證：檢查是否有 epoch_datetime 字段
        sample_satellite = list(satellites_data.values())[0] if isinstance(satellites_data, dict) else satellites_data[0]
        if 'epoch_datetime' not in sample_satellite:
            self.logger.error("❌ 衛星數據缺少 epoch_datetime 字段，違反 v3.0 架構要求")
            return False

        total_count = len(satellites_data) if isinstance(satellites_data, (list, dict)) else 0
        self.logger.info(f"✅ Stage 1 輸出驗證通過，包含 {total_count} 顆衛星，具備 epoch_datetime 字段")
        return True

    def _extract_satellites_data(self, input_data: Dict[str, Any]) -> List[Dict]:
        """從 Stage 1 輸出中提取衛星數據"""
        try:
            satellites_data = input_data.get('satellites', input_data.get('tle_data', []))

            # 處理字典格式（Stage 1 新格式）
            if isinstance(satellites_data, dict):
                satellites_list = list(satellites_data.values())
            elif isinstance(satellites_data, list):
                satellites_list = satellites_data
            else:
                logger.error("衛星數據格式不支援")
                return []

            logger.info(f"📥 提取到 {len(satellites_list)} 顆衛星數據")

            # 檢查測試模式
            testing_config = self.config.get('performance', {}).get('testing_mode', {})
            if testing_config.get('enabled', False):
                return self._apply_sampling(satellites_list, testing_config)

            return satellites_list

        except Exception as e:
            logger.error(f"提取衛星數據失敗: {e}")
            return []

    def _apply_sampling(self, satellites_data: List[Dict], testing_config: Dict) -> List[Dict]:
        """應用取樣策略用於測試模式"""
        sample_size = testing_config.get('satellite_sample_size', 100)
        sample_method = testing_config.get('sample_method', 'first')

        logger.info(f"🧪 測試模式：取樣 {sample_size} 顆衛星 (方法: {sample_method})")

        if len(satellites_data) <= sample_size:
            return satellites_data

        if sample_method == 'first':
            sampled = satellites_data[:sample_size]
        elif sample_method == 'distributed':
            step = len(satellites_data) // sample_size
            sampled = [satellites_data[i * step] for i in range(sample_size)]
        else:
            # 預設使用 first
            sampled = satellites_data[:sample_size]

        logger.info(f"✅ 取樣完成: {len(sampled)} 顆衛星")
        return sampled

    def _perform_orbital_propagation(self, satellites_data: List[Dict]) -> Dict[str, OrbitalStateResult]:
        """
        執行軌道狀態傳播計算 - 自動選擇並行或串行模式

        Args:
            satellites_data: 衛星數據列表

        Returns:
            Dict[str, OrbitalStateResult]: 軌道傳播結果
        """
        logger.info("🛰️ 開始軌道狀態傳播計算...")
        self.processing_stats['total_satellites_processed'] = len(satellites_data)

        if self.enable_parallel:
            # 並行處理模式
            orbital_results = self._perform_parallel_propagation(satellites_data)
        else:
            # 單線程處理模式
            orbital_results = self._perform_sequential_propagation(satellites_data)

        # 計算統計
        success_rate = (self.processing_stats['successful_propagations'] /
                       max(1, self.processing_stats['total_satellites_processed'])) * 100

        logger.info(f"🛰️ 軌道傳播完成:")
        logger.info(f"   模式: {'並行處理' if self.enable_parallel else '單線程處理'}")
        logger.info(f"   成功: {self.processing_stats['successful_propagations']} 顆")
        logger.info(f"   失敗: {self.processing_stats['failed_propagations']} 顆")
        logger.info(f"   成功率: {success_rate:.1f}%")
        logger.info(f"   總軌道點: {self.processing_stats['total_teme_positions']} 個")

        return orbital_results

    def _perform_parallel_propagation(self, satellites_data: List[Dict]) -> Dict[str, OrbitalStateResult]:
        """
        並行軌道傳播處理

        Args:
            satellites_data: 衛星數據列表

        Returns:
            Dict[str, OrbitalStateResult]: 軌道傳播結果
        """
        logger.info(f"🚀 啟用並行處理：{self.max_workers} 個工作進程")

        orbital_results = {}
        start_time = datetime.now(timezone.utc)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有衛星計算任務
            future_to_sat = {
                executor.submit(self._process_single_satellite, sat_data): sat_data
                for sat_data in satellites_data
            }

            # 收集結果
            completed = 0
            for future in as_completed(future_to_sat):
                sat_data = future_to_sat[future]
                satellite_id = sat_data.get('satellite_id', sat_data.get('name', 'unknown'))

                try:
                    result = future.result()
                    if result:
                        orbital_results[result.satellite_id] = result
                        self.processing_stats['successful_propagations'] += 1
                        self.processing_stats['total_teme_positions'] += len(result.teme_positions)
                    else:
                        self.processing_stats['failed_propagations'] += 1

                    completed += 1
                    if completed % 500 == 0:  # 每 500 顆記錄進度
                        logger.info(f"📊 進度: {completed}/{len(satellites_data)} 顆衛星已處理")

                except Exception as e:
                    logger.error(f"❌ 衛星 {satellite_id} 並行處理失敗: {e}")
                    self.processing_stats['failed_propagations'] += 1

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        rate = len(satellites_data) / max(elapsed, 0.1)
        logger.info(f"⏱️ 並行處理完成: {elapsed:.1f}秒，處理速度 {rate:.1f} 顆/秒")

        return orbital_results

    def _perform_sequential_propagation(self, satellites_data: List[Dict]) -> Dict[str, OrbitalStateResult]:
        """
        單線程軌道傳播處理（原邏輯）

        Args:
            satellites_data: 衛星數據列表

        Returns:
            Dict[str, OrbitalStateResult]: 軌道傳播結果
        """
        logger.info("🔄 使用單線程處理模式")

        orbital_results = {}

        for satellite_data in satellites_data:
            try:
                result = self._process_single_satellite(satellite_data)
                if result:
                    orbital_results[result.satellite_id] = result
                    self.processing_stats['successful_propagations'] += 1
                    self.processing_stats['total_teme_positions'] += len(result.teme_positions)
                else:
                    self.processing_stats['failed_propagations'] += 1

            except Exception as e:
                satellite_id = satellite_data.get('satellite_id', satellite_data.get('name', 'unknown'))
                logger.error(f"❌ 衛星 {satellite_id} 處理失敗: {e}")
                self.processing_stats['failed_propagations'] += 1
                continue

        return orbital_results

    def _process_single_satellite(self, satellite_data: Dict) -> Optional[OrbitalStateResult]:
        """
        處理單顆衛星的軌道傳播（可被並行調用）

        Args:
            satellite_data: 單顆衛星數據

        Returns:
            Optional[OrbitalStateResult]: 軌道傳播結果，失敗返回 None
        """
        try:
            satellite_id = satellite_data.get('satellite_id', satellite_data.get('name', 'unknown'))

            # 🚨 關鍵：使用 Stage 1 的 epoch_datetime，禁止重新解析 TLE
            if 'epoch_datetime' not in satellite_data:
                logger.warning(f"衛星 {satellite_id} 缺少 epoch_datetime，跳過")
                return None

            # 生成時間序列 - 傳遞衛星數據進行動態計算
            time_series = self._generate_time_series(satellite_data['epoch_datetime'], satellite_data)

            # 批次計算軌道位置
            teme_positions = self._calculate_teme_positions(satellite_data, time_series)

            if not teme_positions:
                logger.warning(f"衛星 {satellite_id} 軌道傳播失敗")
                return None

            # 識別星座類型
            constellation = self._identify_constellation(satellite_data)

            orbital_result = OrbitalStateResult(
                satellite_id=satellite_id,
                constellation=constellation,
                teme_positions=teme_positions,
                epoch_datetime=satellite_data['epoch_datetime'],
                propagation_successful=True,
                algorithm_used=self.propagation_method,
                coordinate_system=self.coordinate_system
            )

            return orbital_result

        except Exception as e:
            satellite_id = satellite_data.get('satellite_id', satellite_data.get('name', 'unknown'))
            logger.error(f"衛星 {satellite_id} 單顆處理失敗: {e}")
            return None

    def _generate_time_series(self, epoch_datetime_str: str, satellite_data: Optional[Dict] = None) -> List[float]:
        """
        生成時間序列 (相對於 epoch 的分鐘數) - v3.1 支持統一時間窗口

        Args:
            epoch_datetime_str: 來自 Stage 1 的 epoch_datetime
            satellite_data: 衛星數據（用於識別星座和軌道週期）

        Returns:
            List[float]: 時間序列 (分鐘)
        """
        try:
            satellite_id = 'unknown'
            satellite_name = 'unknown'
            if satellite_data:
                satellite_id = satellite_data.get('satellite_id', satellite_data.get('name', 'unknown'))
                satellite_name = satellite_data.get('name', satellite_id)

            # 解析 epoch 時間
            epoch_time = datetime.fromisoformat(epoch_datetime_str.replace('Z', '+00:00'))

            # 🆕 使用統一時間窗口管理器生成時間序列
            time_series_datetimes = self.time_window_manager.generate_time_series(
                satellite_name=satellite_name,
                satellite_epoch=epoch_time
            )

            # 轉換為相對於 epoch 的分鐘數
            time_series = []
            for time_point in time_series_datetimes:
                # 移除時區資訊進行計算
                time_point_naive = time_point.replace(tzinfo=None) if time_point.tzinfo else time_point
                epoch_time_naive = epoch_time.replace(tzinfo=None) if epoch_time.tzinfo else epoch_time

                time_diff = (time_point_naive - epoch_time_naive).total_seconds() / 60.0
                time_series.append(time_diff)

            logger.debug(f"衛星 {satellite_id}: 生成 {len(time_series)} 個時間點 (模式: {self.time_window_manager.mode})")

            return time_series

        except Exception as e:
            logger.error(f"時間序列生成失敗: {e}")
            return []

    def _calculate_teme_positions(self, satellite_data: Dict, time_series: List[float]) -> List[TEMEPosition]:
        """計算 TEME 座標系統中的位置序列"""
        try:
            teme_positions = []
            epoch_datetime = satellite_data['epoch_datetime']
            epoch_time = datetime.fromisoformat(epoch_datetime.replace('Z', '+00:00'))

            for time_minutes in time_series:
                # 使用 SGP4Calculator 計算位置
                sgp4_position = self.sgp4_calculator.calculate_position(satellite_data, time_minutes)

                if sgp4_position:
                    # 計算該時間點的絕對時間
                    absolute_time = epoch_time + timedelta(minutes=time_minutes)

                    # ✅ 使用 SGP4Calculator 提供的位置和速度分量
                    teme_position = TEMEPosition(
                        x=sgp4_position.x,
                        y=sgp4_position.y,
                        z=sgp4_position.z,
                        vx=sgp4_position.vx,  # 使用計算的速度分量
                        vy=sgp4_position.vy,  # 使用計算的速度分量
                        vz=sgp4_position.vz,  # 使用計算的速度分量
                        timestamp=absolute_time.isoformat(),
                        time_since_epoch_minutes=time_minutes
                    )

                    teme_positions.append(teme_position)

            return teme_positions

        except Exception as e:
            logger.error(f"TEME 位置計算失敗: {e}")
            return []

    def _identify_constellation(self, satellite_data: Dict) -> str:
        """
        識別衛星星座類型 - Grade A 標準：僅基於數據字段，禁止硬編碼判斷

        學術原則：
        1. 優先使用明確的 constellation 字段
        2. 次要使用衛星名稱字符串匹配
        3. 禁止基於軌道參數的硬編碼範圍判斷
        4. 所有無法明確識別的歸類為 'other'
        """
        try:
            # 方法1: 檢查明確的 constellation 字段
            if 'constellation' in satellite_data and satellite_data['constellation']:
                constellation = satellite_data['constellation'].lower().strip()
                if constellation:
                    return constellation

            # 方法2: 從衛星名稱進行字符串匹配（非硬編碼判斷）
            name = satellite_data.get('name', satellite_data.get('satellite_id', '')).lower()

            # 基於名稱的字符串匹配（非參數硬編碼）
            if 'starlink' in name:
                return 'starlink'
            elif 'oneweb' in name:
                return 'oneweb'
            elif 'kuiper' in name:
                return 'kuiper'
            elif 'globalstar' in name:
                return 'globalstar'
            elif 'iridium' in name:
                return 'iridium'

            # 方法3: 檢查 TLE 中的衛星名稱字段（如果存在）
            if 'line0' in satellite_data:
                tle_name = satellite_data['line0'].lower()
                if 'starlink' in tle_name:
                    return 'starlink'
                elif 'oneweb' in tle_name:
                    return 'oneweb'

            # ✅ Grade A 合規：無法明確識別的歸類為 'other'，禁止基於硬編碼參數推測
            self.logger.debug(f"衛星 {satellite_data.get('name', 'unknown')} 無法明確識別星座，歸類為 'other'")
            return 'other'

        except Exception as e:
            logger.warning(f"星座識別失敗: {e}")
            return 'other'

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        errors = []
        warnings = []

        if self._validate_stage1_output(input_data):
            return {'valid': True, 'errors': errors, 'warnings': warnings}
        else:
            errors.append("Stage 1 輸出數據驗證失敗")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'satellites', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必要字段: {field}")

        if output_data.get('stage') != 'stage2_orbital_computing':
            errors.append("階段標識錯誤")

        # 檢查 v3.0 架構合規性
        metadata = output_data.get('metadata', {})
        if metadata.get('architecture_version') != 'v3.0':
            errors.append("架構版本不符合 v3.0 要求")

        if metadata.get('coordinate_system') != 'TEME':
            errors.append("座標系統必須為 TEME")

        if not metadata.get('tle_reparse_prohibited'):
            errors.append("必須禁止 TLE 重新解析")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage2_orbital_computing',
            'satellites_processed': self.processing_stats['total_satellites_processed'],
            'successful_propagations': self.processing_stats['successful_propagations'],
            'failed_propagations': self.processing_stats['failed_propagations'],
            'total_teme_positions': self.processing_stats['total_teme_positions'],
            'propagation_success_rate': (
                self.processing_stats['successful_propagations'] /
                max(1, self.processing_stats['total_satellites_processed'])
            ) * 100,
            'processing_grade': self.processing_stats['processing_grade'],
            'architecture_version': self.processing_stats['architecture_version']
        }

    def execute(self, input_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        執行階段處理 (兼容現有接口)

        Args:
            input_data: 輸入數據 (可選，自動載入 Stage 1 輸出)

        Returns:
            處理結果字典
        """
        try:
            self.logger.info("🚀 開始執行 Stage 2 軌道狀態傳播")

            # 如果沒有提供輸入數據，嘗試載入 Stage 1 輸出
            if input_data is None:
                input_data = self.result_manager.load_stage1_output()

            # 調用主要處理方法
            result = self.process(input_data)

            # 保存結果到文件
            if result.status == ProcessingStatus.SUCCESS:
                output_file = self.result_manager.save_results(result.data)
                self.logger.info(f"✅ Stage 2 結果已保存至: {output_file}")

                # 轉換為字典格式
                result_dict = result.data.copy()
                result_dict['output_file'] = output_file
                result_dict['success'] = True
                return result_dict
            else:
                return {
                    'success': False,
                    'stage': 'stage2_orbital_computing',
                    'satellites': {},
                    'error': result.metadata.get('message', 'Unknown error')
                }

        except Exception as e:
            self.logger.error(f"Stage 2 執行失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'stage2_orbital_computing'
            }


def create_stage2_processor(config: Optional[Dict[str, Any]] = None) -> Stage2OrbitalPropagationProcessor:
    """創建 Stage 2 軌道狀態傳播處理器"""
    return Stage2OrbitalPropagationProcessor(config)