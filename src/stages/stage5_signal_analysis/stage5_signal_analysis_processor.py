#!/usr/bin/env python3
"""
Stage 5: 信號品質分析層處理器

核心職責：3GPP NTN 標準信號品質計算與物理層分析
學術合規：Grade A 標準，使用 ITU-R 和 3GPP 官方規範
接口標準：100% BaseStageProcessor 合規

按照 docs/stages/stage5-signal-analysis.md 文檔要求實現：
- 僅對可連線衛星進行精確信號分析
- 基於 Stage 4 篩選結果
- 使用 3GPP TS 38.214 標準實現
- 使用 ITU-R P.618 物理模型

🎓 學術合規性檢查提醒:
- 修改此文件前，請先閱讀: docs/ACADEMIC_STANDARDS.md
- 階段五重點: 訊號模型符合3GPP TS 38.214、大氣衰減使用ITU-R P.676完整模型(44+35條譜線)
- 都卜勒計算必須使用 Stage 2 實際速度數據 (velocity_km_per_s)
- 所有數值常量必須有 SOURCE 標記
- 禁用詞: 假設、估計、簡化、模擬
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import math
import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

# 🚨 Grade A要求：使用學術級物理常數 (優先 Astropy CODATA 2018/2022)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# psutil 用於動態 CPU 檢測（可選依賴）
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("⚠️ psutil 不可用，將使用保守的 CPU 核心配置")

# Fail-Fast: Astropy 是必需依賴，不可用時立即報錯
try:
    from src.shared.constants.astropy_physics_constants import get_astropy_constants
except ModuleNotFoundError:
    from shared.constants.astropy_physics_constants import get_astropy_constants

physics_consts = get_astropy_constants()
logger.info("✅ 使用 Astropy 官方物理常數 (CODATA 2022)")


# 共享模組導入
try:
    from src.shared.base import BaseStageProcessor
    from src.shared.base import ProcessingStatus, ProcessingResult, create_processing_result
    from src.shared.validation import ValidationEngine
except ModuleNotFoundError:
    from shared.base import BaseStageProcessor
    from shared.base import ProcessingStatus, ProcessingResult, create_processing_result
    from shared.validation import ValidationEngine
# Stage 5核心模組 (重構後專注信號品質分析)
from .itur_physics_calculator import create_itur_physics_calculator
from .stage5_compliance_validator import create_stage5_validator
from .time_series_analyzer import create_time_series_analyzer

# ✅ 重構後的模組化組件
from .parallel_processing import CPUOptimizer, SignalAnalysisWorkerManager
from .data_processing import ConfigManager, InputExtractor
from .output_management import ResultBuilder, SnapshotManager

# NEW: 動態傳播條件模擬 (Proposal 002)
from .propagation_simulator import PropagationConditionSimulator

logger = logging.getLogger(__name__)


class Stage5SignalAnalysisProcessor(BaseStageProcessor):
    """
    Stage 5: 信號品質分析層處理器

    專職責任：
    1. 3GPP 標準信號計算 (RSRP/RSRQ/SINR)
    2. ITU-R 物理傳播模型
    3. 智能信號品質評估
    4. 學術級精度保證
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(stage_number=5, stage_name="signal_quality_analysis", config=config or {})

        # ✅ 使用模組化配置管理器
        self.config_manager = ConfigManager(self.config)
        self.signal_thresholds = self.config_manager.get_thresholds()

        # NEW: 動態傳播條件模擬器 (Proposal 002)
        # SOURCE: Proposal 002 - Training Data Diversity Enhancement
        # ⚠️ 必須在初始化 time_series_analyzer 之前初始化
        self.enable_propagation_sim = self.config.get('enable_propagation_simulation', False)
        self.propagation_simulator = None

        if self.enable_propagation_sim:
            # 初始化傳播模擬器
            prop_sim_config = self.config.get('propagation_simulation', {})
            try:
                self.propagation_simulator = PropagationConditionSimulator(
                    prop_sim_config,
                    self.logger
                )
                self.logger.info("✅ 動態傳播條件模擬器已啟用")
                self.logger.info(
                    f"   環境: {self.propagation_simulator.loo_model.config.environment.value}"
                )
            except Exception as e:
                self.logger.error(f"❌ 傳播模擬器初始化失敗: {e}")
                self.propagation_simulator = None
                self.enable_propagation_sim = False
        else:
            self.logger.info("ℹ️  動態傳播條件模擬：停用 (向後兼容模式)")

        # 初始化核心組件（傳入 propagation_simulator）
        self.physics_calculator = create_itur_physics_calculator(self.config)
        self.validator = create_stage5_validator()
        self.time_series_analyzer = create_time_series_analyzer(
            self.config,
            self.signal_thresholds,
            self.propagation_simulator  # 🆕 傳遞 propagation_simulator
        )

        # 處理統計
        self.processing_stats = {
            'total_satellites_analyzed': 0,
            'excellent_signals': 0,
            'good_signals': 0,
            'fair_signals': 0,
            'poor_signals': 0
        }

        # ✅ 使用模組化並行處理（也需要傳入 propagation_simulator）
        self.max_workers = CPUOptimizer.get_optimal_workers(self.config)
        self.enable_parallel = self.max_workers > 1
        self.worker_manager = SignalAnalysisWorkerManager(
            self.max_workers, self.config, self.signal_thresholds,
            self.propagation_simulator  # 🆕 傳遞給 worker_manager
        )

        # ✅ 使用模組化輸出管理
        self.result_builder = ResultBuilder(self.validator, physics_consts)
        self.snapshot_manager = SnapshotManager(self.validator)

        self.logger.info("Stage 5 信號品質分析處理器已初始化 - 3GPP/ITU-R 標準模式 (模組化)")
        self.logger.info(f"🚀 並行處理: {self.max_workers} 工作器 ({'啟用' if self.enable_parallel else '禁用'})")

    def process(self, input_data: Any) -> ProcessingResult:
        """主要處理方法 - 按照文檔格式輸出，無任何硬編碼值 - ✅ 已移除 execute() 覆蓋"""
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 5信號品質分析處理...")

        try:
            # 驗證輸入數據
            if not self._validate_stage4_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 4輸出數據驗證失敗"
                )

            # 提取可見衛星數據
            satellites_data = self._extract_satellite_data(input_data)
            if not satellites_data:
                return create_processing_result(
                    status=ProcessingStatus.ERROR,
                    data={},
                    message="未找到有效的衛星數據"
                )

            # 執行信號分析
            analyzed_satellites = self._perform_signal_analysis(satellites_data)

            # ✅ 使用 ResultBuilder 構建輸出（替代150行手動構建代碼）
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            self.logger.info("🔍 執行學術合規性驗證並構建結果...")
            result_data = self.result_builder.build(
                analyzed_satellites=analyzed_satellites,
                input_data=input_data,
                processing_stats=self.processing_stats,
                processing_time=processing_time
            )

            # 💾 保存結果到文件 (移自 execute() 覆蓋)
            try:
                output_file = self.save_results(result_data)
                self.logger.info(f"Stage 5結果已保存: {output_file}")
            except Exception as e:
                self.logger.warning(f"保存Stage 5結果失敗: {e}")
                output_file = None

            # 💾 保存驗證快照 (移自 execute() 覆蓋)
            try:
                snapshot_success = self.save_validation_snapshot(result_data)
                if snapshot_success:
                    self.logger.info("✅ Stage 5驗證快照保存成功")
            except Exception as e:
                self.logger.warning(f"⚠️ Stage 5驗證快照保存失敗: {e}")

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功分析{len(analyzed_satellites)}顆衛星的信號品質",
                metadata={'output_file': output_file} if output_file else {}
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 5信號品質分析失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"信號品質分析錯誤: {str(e)}"
            )

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據 - 委託給 validator"""
        return self.validator.validate_input(input_data)

    def _validate_stage4_output(self, input_data: Any) -> bool:
        """驗證Stage 4的輸出數據"""
        if not isinstance(input_data, dict):
            return False

        # 🔧 修復: 檢查新的 connectable_satellites 字段（Stage 4 重構後的輸出格式）
        # Stage 4 輸出包含: connectable_satellites, metadata, stage
        required_fields = ['stage', 'connectable_satellites']
        for field in required_fields:
            if field not in input_data:
                # 向後兼容: 如果沒有 connectable_satellites，檢查舊的 satellites 字段
                if field == 'connectable_satellites' and 'satellites' in input_data:
                    continue
                return False

        # ✅ Fail-Fast: 明確檢查 stage 字段
        if 'stage' not in input_data:
            return False

        # Stage 5 應該接收 Stage 4 的可連線衛星輸出
        return input_data['stage'] in ['stage4_link_feasibility', 'stage4_optimization']

    def _extract_satellite_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取衛星數據 - 使用 InputExtractor 模組

        支援 RL 訓練模式：
        - 如果環境變數 ORBIT_ENGINE_STAGE5_USE_CANDIDATE_POOL=true
        - 則使用候選池 (connectable_satellites_candidate) 而非優化池
        """
        import os

        # 檢查是否使用候選池（RL 訓練模式）
        use_candidate_pool = os.getenv('ORBIT_ENGINE_STAGE5_USE_CANDIDATE_POOL', 'false').lower() == 'true'

        if use_candidate_pool and 'connectable_satellites_candidate' in input_data:
            self.logger.info("🎯 RL 訓練模式：使用候選池 (connectable_satellites_candidate)")
            # 創建修改後的 input_data，將候選池替換為主池
            input_data_modified = input_data.copy()
            input_data_modified['connectable_satellites'] = input_data['connectable_satellites_candidate']
            result = InputExtractor.extract(input_data_modified)
        else:
            # 正常模式：使用優化池
            if use_candidate_pool:
                self.logger.warning("⚠️ 環境變數要求使用候選池，但 input_data 中不存在 connectable_satellites_candidate")
            result = InputExtractor.extract(input_data)

        # 詳細統計日誌 (每個星座的時間序列資訊)
        connectable_satellites = result['connectable_satellites']
        for constellation, sats in connectable_satellites.items():
            if sats:
                # ✅ Fail-Fast: 明確檢查 time_series 字段
                total_time_points = 0
                for sat in sats:
                    if 'time_series' not in sat:
                        self.logger.debug(f"衛星缺少 time_series 字段，跳過統計")
                        continue
                    total_time_points += len(sat['time_series'])

                avg_points = total_time_points / len(sats) if len(sats) > 0 else 0
                self.logger.info(f"   {constellation}: {len(sats)} 顆衛星, 平均 {avg_points:.0f} 個時間點")

        return result

    def _perform_signal_analysis(self, satellites_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行信號分析 - 重構版本

        符合文檔要求:
        1. 遍歷可連線衛星池 (按星座)
        2. 對每顆衛星的時間序列逐點計算信號品質
        3. 使用星座特定配置 (constellation_configs)
        4. 輸出 time_series 格式數據
        5. 移除 3GPP 事件檢測 (移至 Stage 6)
        """
        analyzed_satellites = {}

        # ✅ 重構後不需要在此初始化 calculator，已由 time_series_analyzer 內部處理

        # ✅ Fail-Fast: 提取可連線衛星池和星座配置（InputExtractor 已驗證）
        # 這些字段由 InputExtractor.extract() 保證存在
        if 'connectable_satellites' not in satellites_data:
            raise ValueError(
                "內部錯誤：satellites_data 缺少 connectable_satellites 字段\n"
                "這表示 InputExtractor.extract() 返回格式異常"
            )
        connectable_satellites = satellites_data['connectable_satellites']

        if 'metadata' not in satellites_data:
            raise ValueError(
                "內部錯誤：satellites_data 缺少 metadata 字段\n"
                "這表示 InputExtractor.extract() 返回格式異常"
            )
        metadata = satellites_data['metadata']

        if 'constellation_configs' not in metadata:
            raise ValueError(
                "內部錯誤：metadata 缺少 constellation_configs 字段\n"
                "這表示 InputExtractor.extract() 返回格式異常"
            )
        constellation_configs = metadata['constellation_configs']

        # ✅ Grade A 要求: constellation_configs 必須存在，禁止回退到硬編碼預設值
        if not constellation_configs:
            error_msg = (
                "❌ Grade A 學術標準違規: constellation_configs 缺失。\n"
                "   依據: docs/stages/stage5-signal-analysis.md Line 221-235\n"
                "   原因: Stage 5 必須使用 Stage 1 傳遞的星座特定配置 (tx_power, frequency, gain)\n"
                "   修復: 確保 Stage 1 正確生成 constellation_configs 並透過 metadata 向下傳遞"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("🔬 開始信號品質分析 (時間序列遍歷模式)...")
        self.logger.info(f"   ✅ constellation_configs 已載入: {list(constellation_configs.keys())}")

        # 遍歷每個星座
        for constellation, satellites in connectable_satellites.items():
            if not satellites:
                continue

            # ✅ Fail-Fast: 獲取星座特定配置（明確檢查）
            if constellation in constellation_configs:
                constellation_config = constellation_configs[constellation]
                self.logger.debug(f"使用 {constellation} 特定配置")
            elif 'default' in constellation_configs:
                constellation_config = constellation_configs['default']
                self.logger.warning(
                    f"⚠️ 星座 {constellation} 配置缺失，使用 'default' 配置\n"
                    f"   建議在 Stage 1 配置中為 {constellation} 明確定義配置"
                )
            else:
                error_msg = (
                    f"❌ Grade A 學術標準違規: 星座 {constellation} 配置缺失且無 'default' 配置\n"
                    f"   可用配置: {list(constellation_configs.keys())}\n"
                    f"   依據: docs/stages/stage5-signal-analysis.md Line 261-267\n"
                    f"   修復: 在 Stage 1 配置中添加 constellation_configs.{constellation} 或 constellation_configs.default"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # ⚠️ 嚴格驗證: 星座配置不能為空字典
            if not constellation_config:
                error_msg = (
                    f"❌ Grade A 學術標準違規: 星座 {constellation} 配置為空字典\n"
                    f"   配置內容: {constellation_config}\n"
                    f"   依據: docs/stages/stage5-signal-analysis.md Line 226-234"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # 星座特定參數 (從 Stage 1 傳遞) - 嚴格模式，禁止回退
            required_params = ['tx_power_dbw', 'tx_antenna_gain_db', 'frequency_ghz']
            missing_params = [p for p in required_params if p not in constellation_config]

            if missing_params:
                error_msg = (
                    f"❌ Grade A 學術標準違規: 星座 {constellation} 配置缺少必要參數: {missing_params}\n"
                    f"   依據: docs/stages/stage5-signal-analysis.md Line 226-234\n"
                    f"   當前配置: {constellation_config}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            tx_power_dbw = constellation_config['tx_power_dbw']
            tx_gain_db = constellation_config['tx_antenna_gain_db']
            frequency_ghz = constellation_config['frequency_ghz']

            self.logger.info(f"📡 處理 {constellation} 星座:")
            self.logger.info(f"   配置: Tx={tx_power_dbw}dBW, Freq={frequency_ghz}GHz, Gain={tx_gain_db}dB")
            self.logger.info(f"   衛星數: {len(satellites)}")

            # ✅ Fail-Fast: 從 constellation_config 提取接收器參數（明確檢查）
            # Grade A 要求: 依據 docs/stages/stage5-signal-analysis.md Line 221-235
            if 'rx_antenna_diameter_m' not in constellation_config:
                error_msg = (
                    f"❌ Grade A 學術標準違規: 星座 {constellation} 配置缺少 rx_antenna_diameter_m\n"
                    f"   當前配置: {constellation_config}\n"
                    f"   依據: docs/stages/stage5-signal-analysis.md Line 221-235\n"
                    f"   修復: 在 Stage 1 配置的 constellation_configs.{constellation} 中添加 rx_antenna_diameter_m"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            if 'rx_antenna_efficiency' not in constellation_config:
                error_msg = (
                    f"❌ Grade A 學術標準違規: 星座 {constellation} 配置缺少 rx_antenna_efficiency\n"
                    f"   當前配置: {constellation_config}\n"
                    f"   依據: docs/stages/stage5-signal-analysis.md Line 221-235\n"
                    f"   修復: 在 Stage 1 配置的 constellation_configs.{constellation} 中添加 rx_antenna_efficiency"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            rx_antenna_diameter_m = constellation_config['rx_antenna_diameter_m']
            rx_antenna_efficiency = constellation_config['rx_antenna_efficiency']

            # 驗證參數有效性
            if not isinstance(rx_antenna_diameter_m, (int, float)) or rx_antenna_diameter_m <= 0:
                error_msg = (
                    f"❌ Grade A 學術標準違規: rx_antenna_diameter_m 必須是正數\n"
                    f"   當前值: {rx_antenna_diameter_m}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            if not isinstance(rx_antenna_efficiency, (int, float)) or not (0 < rx_antenna_efficiency <= 1):
                error_msg = (
                    f"❌ Grade A 學術標準違規: rx_antenna_efficiency 必須在 (0, 1] 範圍內\n"
                    f"   當前值: {rx_antenna_efficiency}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # 計算接收器增益 (基於星座特定參數) - 使用重構後的 physics_calculator
            rx_gain_db = self.physics_calculator.calculate_receiver_gain_from_config(
                frequency_ghz=frequency_ghz,
                antenna_diameter_m=rx_antenna_diameter_m,
                antenna_efficiency=rx_antenna_efficiency
            )

            self.logger.debug(
                f"   接收器增益: {rx_gain_db:.2f}dB "
                f"(天線直徑={rx_antenna_diameter_m}m, 效率={rx_antenna_efficiency:.1%})"
            )

            # System configuration for this constellation
            system_config = {
                'frequency_ghz': frequency_ghz,
                'tx_power_dbm': tx_power_dbw + 30,  # dBW to dBm
                'tx_gain_db': tx_gain_db,
                'rx_gain_db': rx_gain_db,
                'rx_antenna_diameter_m': rx_antenna_diameter_m,
                'rx_antenna_efficiency': rx_antenna_efficiency
            }

            # ✅ 使用 WorkerManager 處理衛星 (自動選擇並行/順序模式)
            constellation_results = self.worker_manager.process_satellites(
                satellites=satellites,
                constellation=constellation,
                system_config=system_config,
                time_series_analyzer=self.time_series_analyzer
            )

            # 合併結果
            analyzed_satellites.update(constellation_results['satellites'])

            # 更新統計
            for quality_level, count in constellation_results['stats'].items():
                if quality_level in self.processing_stats:
                    self.processing_stats[quality_level] += count

        self.logger.info(f"✅ 信號分析完成: {len(analyzed_satellites)} 顆衛星")
        return analyzed_satellites

    def _initialize_shared_services(self):
        """初始化共享服務 - 精簡為純粹信號分析"""
        # 移除預測和監控功能，專注純粹信號分析
        self.logger.info("共享服務初始化完成 - 純粹信號分析模式")

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據 - 委託給 validator"""
        return self.validator.validate_output(output_data)

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage5_signal_analysis',
            'satellites_analyzed': self.processing_stats['total_satellites_analyzed'],
            'excellent_signals': self.processing_stats['excellent_signals'],
            'good_signals': self.processing_stats['good_signals'],
            'fair_signals': self.processing_stats['fair_signals'],
            'poor_signals': self.processing_stats['poor_signals']
            # ✅ 已移除 gpp_events_detected - 已移至 Stage 6
        }

    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """執行驗證檢查 - 委託給 validator"""
        return self.validator.run_validation_checks(results)

    def save_results(self, results: Dict[str, Any]) -> str:
        """保存處理結果到文件"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"stage5_signal_analysis_{timestamp}.json"
            
            # 確保輸出目錄存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存結果
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Stage 5結果已保存: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"保存結果失敗: {e}")
            raise IOError(f"無法保存Stage 5結果: {str(e)}")

    def save_validation_snapshot(self, processing_results: Dict[str, Any]) -> bool:
        """保存Stage 5驗證快照 - 使用 SnapshotManager 模組"""
        return self.snapshot_manager.save(processing_results)

    # ✅ 以下方法已移至模組:
    # - _process_satellites_serial() → worker_manager.py
    # - _process_satellites_parallel() → worker_manager.py
    # - _get_optimal_workers() → cpu_optimizer.py
    # - _process_single_satellite_worker() → worker_manager.py


def create_stage5_processor(config: Optional[Dict[str, Any]] = None) -> Stage5SignalAnalysisProcessor:
    """創建Stage 5處理器實例"""
    return Stage5SignalAnalysisProcessor(config)