"""
系統常數定義 - Orbit Engine 統一路徑配置

整合系統級配置常數，使用環境變數統一管理所有路徑
支援 orbit-engine 統一命名規範
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


def get_env(key: str, default: str) -> str:
    """獲取環境變數，提供默認值"""
    return os.environ.get(key, default)


@dataclass
class OrbitEngineSystemPaths:
    """Orbit Engine 統一系統路徑常數"""

    # 🚀 核心路徑配置 (基於環境變數)
    ORBIT_ENGINE_NAME: str = get_env('ORBIT_ENGINE_NAME', 'orbit-engine')
    PROJECT_ROOT_NAME: str = get_env('PROJECT_ROOT_NAME', 'orbit-engine-system')

    # 🐳 容器路徑配置
    CONTAINER_ROOT: str = get_env('CONTAINER_ROOT', '/orbit-engine')
    CONTAINER_DATA_ROOT: str = get_env('CONTAINER_DATA_ROOT', 'data')
    CONTAINER_SRC_ROOT: str = get_env('CONTAINER_SRC_ROOT', '/orbit-engine/src')
    CONTAINER_CONFIG_ROOT: str = get_env('CONTAINER_CONFIG_ROOT', '/orbit-engine/config')
    CONTAINER_SCRIPTS_ROOT: str = get_env('CONTAINER_SCRIPTS_ROOT', '/orbit-engine/scripts')
    CONTAINER_TESTS_ROOT: str = get_env('CONTAINER_TESTS_ROOT', '/orbit-engine/tests')

    # 📊 階段輸出路徑（容器內）
    CONTAINER_OUTPUTS_ROOT: str = get_env('CONTAINER_OUTPUTS_ROOT', 'data/outputs')
    CONTAINER_STAGE1_OUTPUT: str = get_env('CONTAINER_STAGE1_OUTPUT', 'data/outputs/stage1')
    CONTAINER_STAGE2_OUTPUT: str = get_env('CONTAINER_STAGE2_OUTPUT', 'data/outputs/stage2')
    CONTAINER_STAGE3_OUTPUT: str = get_env('CONTAINER_STAGE3_OUTPUT', 'data/outputs/stage3')
    CONTAINER_STAGE4_OUTPUT: str = get_env('CONTAINER_STAGE4_OUTPUT', 'data/outputs/stage4')
    CONTAINER_STAGE5_OUTPUT: str = get_env('CONTAINER_STAGE5_OUTPUT', 'data/outputs/stage5')
    CONTAINER_STAGE6_OUTPUT: str = get_env('CONTAINER_STAGE6_OUTPUT', 'data/outputs/stage6')

    # 🗂️ 其他數據路徑（容器內）
    CONTAINER_TLE_DATA: str = get_env('CONTAINER_TLE_DATA', 'data/tle_data')
    CONTAINER_VALIDATION_SNAPSHOTS: str = get_env('CONTAINER_VALIDATION_SNAPSHOTS', 'data/validation_snapshots')
    CONTAINER_LOGS: str = get_env('CONTAINER_LOGS', 'data/logs')

    # 📂 主機路徑配置
    HOST_ROOT: str = get_env('HOST_ROOT', './')
    HOST_DATA_ROOT: str = get_env('HOST_DATA_ROOT', './data')
    HOST_SRC_ROOT: str = get_env('HOST_SRC_ROOT', './src')
    HOST_CONFIG_ROOT: str = get_env('HOST_CONFIG_ROOT', './config')
    HOST_SCRIPTS_ROOT: str = get_env('HOST_SCRIPTS_ROOT', './scripts')
    HOST_TESTS_ROOT: str = get_env('HOST_TESTS_ROOT', './tests')

    # 📊 階段輸出路徑（主機）
    HOST_OUTPUTS_ROOT: str = get_env('HOST_OUTPUTS_ROOT', './data/outputs')
    HOST_STAGE1_OUTPUT: str = get_env('HOST_STAGE1_OUTPUT', './data/outputs/stage1')
    HOST_STAGE2_OUTPUT: str = get_env('HOST_STAGE2_OUTPUT', './data/outputs/stage2')
    HOST_STAGE3_OUTPUT: str = get_env('HOST_STAGE3_OUTPUT', './data/outputs/stage3')
    HOST_STAGE4_OUTPUT: str = get_env('HOST_STAGE4_OUTPUT', './data/outputs/stage4')
    HOST_STAGE5_OUTPUT: str = get_env('HOST_STAGE5_OUTPUT', './data/outputs/stage5')
    HOST_STAGE6_OUTPUT: str = get_env('HOST_STAGE6_OUTPUT', './data/outputs/stage6')

    # 🗂️ 其他數據路徑（主機）
    HOST_TLE_DATA: str = get_env('HOST_TLE_DATA', './data/tle_data')
    HOST_VALIDATION_SNAPSHOTS: str = get_env('HOST_VALIDATION_SNAPSHOTS', './data/validation_snapshots')
    HOST_LOGS: str = get_env('HOST_LOGS', './data/logs')

    @classmethod
    def detect_execution_environment(cls) -> str:
        """檢測當前執行環境（容器內 or 主機）"""
        if Path(cls.CONTAINER_ROOT).exists():
            return "container"
        else:
            return "host"

    @classmethod
    def get_current_paths(cls) -> Dict[str, str]:
        """
        根據執行環境獲取當前路徑

        支援雙模式架構（前端渲染 + RL 訓練）:
        - 環境變數 ORBIT_ENGINE_OUTPUT_DIR 設置時: 使用 RL 訓練輸出目錄
        - 未設置時: 使用原始前端渲染輸出目錄
        """
        import os
        env = cls.detect_execution_environment()

        # 檢查是否為 RL 訓練模式（環境變數優先）
        custom_output_dir = os.getenv('ORBIT_ENGINE_OUTPUT_DIR')

        if env == "container":
            base_paths = {
                "root": cls.CONTAINER_ROOT,
                "data_root": cls.CONTAINER_DATA_ROOT,
                "src_root": cls.CONTAINER_SRC_ROOT,
                "config_root": cls.CONTAINER_CONFIG_ROOT,
                "scripts_root": cls.CONTAINER_SCRIPTS_ROOT,
                "tests_root": cls.CONTAINER_TESTS_ROOT,
                "outputs_root": cls.CONTAINER_OUTPUTS_ROOT,
                "stage1_output": cls.CONTAINER_STAGE1_OUTPUT,
                "stage2_output": cls.CONTAINER_STAGE2_OUTPUT,
                "stage3_output": cls.CONTAINER_STAGE3_OUTPUT,
                "stage4_output": cls.CONTAINER_STAGE4_OUTPUT,
                "stage5_output": cls.CONTAINER_STAGE5_OUTPUT,
                "stage6_output": cls.CONTAINER_STAGE6_OUTPUT,
                "tle_data": cls.CONTAINER_TLE_DATA,
                "validation_snapshots": cls.CONTAINER_VALIDATION_SNAPSHOTS,
                "logs": cls.CONTAINER_LOGS,
                "environment": "container"
            }
        else:
            base_paths = {
                "root": cls.HOST_ROOT,
                "data_root": cls.HOST_DATA_ROOT,
                "src_root": cls.HOST_SRC_ROOT,
                "config_root": cls.HOST_CONFIG_ROOT,
                "scripts_root": cls.HOST_SCRIPTS_ROOT,
                "tests_root": cls.HOST_TESTS_ROOT,
                "outputs_root": cls.HOST_OUTPUTS_ROOT,
                "stage1_output": cls.HOST_STAGE1_OUTPUT,
                "stage2_output": cls.HOST_STAGE2_OUTPUT,
                "stage3_output": cls.HOST_STAGE3_OUTPUT,
                "stage4_output": cls.HOST_STAGE4_OUTPUT,
                "stage5_output": cls.HOST_STAGE5_OUTPUT,
                "stage6_output": cls.HOST_STAGE6_OUTPUT,
                "tle_data": cls.HOST_TLE_DATA,
                "validation_snapshots": cls.HOST_VALIDATION_SNAPSHOTS,
                "logs": cls.HOST_LOGS,
                "environment": "host"
            }

        # RL 訓練模式：覆蓋 stage 輸出路徑
        if custom_output_dir:
            for stage_num in range(1, 7):
                base_paths[f"stage{stage_num}_output"] = f"{custom_output_dir}/stage{stage_num}"

        return base_paths

    @classmethod
    def ensure_paths_exist(cls) -> Dict[str, bool]:
        """確保所有必要路徑存在"""
        paths_status = {}
        current_paths = cls.get_current_paths()

        # 排除環境標記和相對路徑標記
        excluded_keys = {"environment", "root"}

        for path_name, path_value in current_paths.items():
            if path_name in excluded_keys or path_value.startswith('./'):
                continue

            try:
                Path(path_value).mkdir(parents=True, exist_ok=True)
                paths_status[path_name] = True
            except Exception as e:
                paths_status[path_name] = False
                print(f"⚠️ 無法創建路徑 {path_name}: {path_value} - {e}")

        return paths_status


@dataclass
class ProcessingConstants:
    """處理參數常數"""

    # 時間相關
    DEFAULT_PREDICTION_HOURS: int = int(get_env('DEFAULT_PREDICTION_HOURS', '24'))
    DEFAULT_TIME_STEP_MINUTES: int = int(get_env('DEFAULT_TIME_STEP_MINUTES', '5'))
    MAX_PROCESSING_TIMEOUT_SECONDS: int = int(get_env('MAX_PROCESSING_TIMEOUT_SECONDS', '300'))

    # 數據量限制
    MAX_SATELLITES_PER_BATCH: int = int(get_env('MAX_SATELLITES_PER_BATCH', '10000'))
    MAX_TLE_RECORDS: int = int(get_env('MAX_TLE_RECORDS', '50000'))
    MAX_VISIBILITY_WINDOWS: int = int(get_env('MAX_VISIBILITY_WINDOWS', '1000'))

    # 性能參數
    PARALLEL_WORKERS: int = int(get_env('PARALLEL_WORKERS', '4'))
    CHUNK_SIZE: int = int(get_env('CHUNK_SIZE', '100'))
    MEMORY_LIMIT_MB: int = int(get_env('MEMORY_LIMIT_MB', '2048'))

    # 重試參數
    MAX_RETRIES: int = int(get_env('MAX_RETRIES', '3'))
    RETRY_DELAY_SECONDS: int = int(get_env('RETRY_DELAY_SECONDS', '1'))

    # 緩存參數
    CACHE_TTL_SECONDS: int = int(get_env('CACHE_TTL_SECONDS', '3600'))
    MAX_CACHE_SIZE: int = int(get_env('MAX_CACHE_SIZE', '1000'))


@dataclass
class ValidationConstants:
    """驗證相關常數"""

    # 數據驗證閾值
    MIN_VISIBLE_SATELLITES: int = int(get_env('MIN_VISIBLE_SATELLITES', '1'))
    MIN_COVERAGE_PERCENTAGE: float = float(get_env('MIN_COVERAGE_PERCENTAGE', '0.1'))
    MIN_SIGNAL_QUALITY_SCORE: float = float(get_env('MIN_SIGNAL_QUALITY_SCORE', '0.3'))

    # 精度容忍度
    POSITION_TOLERANCE_KM: float = float(get_env('POSITION_TOLERANCE_KM', '1.0'))
    ANGLE_TOLERANCE_DEG: float = float(get_env('ANGLE_TOLERANCE_DEG', '0.1'))
    TIME_TOLERANCE_SECONDS: float = float(get_env('TIME_TOLERANCE_SECONDS', '1.0'))

    # 檢查參數
    ENABLE_STRICT_VALIDATION: bool = get_env('ENABLE_STRICT_VALIDATION', 'true').lower() == 'true'
    ENABLE_ACADEMIC_COMPLIANCE: bool = get_env('ENABLE_ACADEMIC_COMPLIANCE', 'true').lower() == 'true'
    ENABLE_PHYSICS_VALIDATION: bool = get_env('ENABLE_PHYSICS_VALIDATION', 'true').lower() == 'true'


@dataclass
class ElevationStandards:
    """仰角標準常數 - 基於ITU-R和衛星切換文檔"""

    # 標準仰角門檻 (基於satellite_handover_standards.md)
    CRITICAL_ELEVATION_DEG: float = float(get_env('CRITICAL_ELEVATION_DEG', '5.0'))      # 臨界門檻
    STANDARD_ELEVATION_DEG: float = float(get_env('STANDARD_ELEVATION_DEG', '10.0'))     # 標準門檻
    PREFERRED_ELEVATION_DEG: float = float(get_env('PREFERRED_ELEVATION_DEG', '15.0'))   # 預備門檻

    # 距離限制 (基於LEO特性)
    MIN_DISTANCE_KM: float = float(get_env('MIN_DISTANCE_KM', '200.0'))
    MAX_DISTANCE_KM: float = float(get_env('MAX_DISTANCE_KM', '2000.0'))

    # 環境調整係數 (基於ITU-R P.618)
    URBAN_ADJUSTMENT_FACTOR: float = float(get_env('URBAN_ADJUSTMENT_FACTOR', '1.1'))
    MOUNTAIN_ADJUSTMENT_FACTOR: float = float(get_env('MOUNTAIN_ADJUSTMENT_FACTOR', '1.3'))
    RAIN_ADJUSTMENT_FACTOR: float = float(get_env('RAIN_ADJUSTMENT_FACTOR', '1.4'))
    CLEAR_SKY_FACTOR: float = float(get_env('CLEAR_SKY_FACTOR', '1.0'))

    # 星座特定門檻 (基於官方技術規格)
    STARLINK_MIN_ELEVATION: float = float(get_env('STARLINK_MIN_ELEVATION', '25.0'))
    ONEWEB_MIN_ELEVATION: float = float(get_env('ONEWEB_MIN_ELEVATION', '40.0'))
    GENERIC_LEO_MIN_ELEVATION: float = float(get_env('GENERIC_LEO_MIN_ELEVATION', '10.0'))


@dataclass
class LoggingConstants:
    """日誌相關常數"""

    DEFAULT_LOG_LEVEL: str = get_env('LOG_LEVEL', 'INFO')
    DEBUG_LOG_LEVEL: str = get_env('DEBUG_LOG_LEVEL', 'DEBUG')

    LOG_FORMAT: str = get_env('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    DEBUG_LOG_FORMAT: str = get_env('DEBUG_LOG_FORMAT',
                                   '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

    MAX_LOG_SIZE_MB: int = int(get_env('MAX_LOG_SIZE_MB', '10'))
    BACKUP_COUNT: int = int(get_env('BACKUP_COUNT', '5'))

    ENABLE_PERFORMANCE_LOGGING: bool = get_env('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true'
    PERFORMANCE_LOG_THRESHOLD_MS: float = float(get_env('PERFORMANCE_LOG_THRESHOLD_MS', '100.0'))


@dataclass
class NetworkConstants:
    """網路相關常數"""

    NETSTACK_BASE_URL: str = get_env('NETSTACK_BASE_URL', 'http://localhost:8080')
    SIMWORLD_BASE_URL: str = get_env('SIMWORLD_BASE_URL', 'http://localhost:8888')

    DEFAULT_TIMEOUT_SECONDS: int = int(get_env('DEFAULT_TIMEOUT_SECONDS', '30'))
    LONG_TIMEOUT_SECONDS: int = int(get_env('LONG_TIMEOUT_SECONDS', '120'))

    MAX_HTTP_RETRIES: int = int(get_env('MAX_HTTP_RETRIES', '3'))
    HTTP_RETRY_BACKOFF: float = float(get_env('HTTP_RETRY_BACKOFF', '1.0'))


class OrbitEngineConstantsManager:
    """Orbit Engine 系統常數管理器"""

    def __init__(self):
        self.paths = OrbitEngineSystemPaths()
        self.processing = ProcessingConstants()
        self.validation = ValidationConstants()
        self.elevation = ElevationStandards()
        self.logging = LoggingConstants()
        self.network = NetworkConstants()

    def get_system_paths(self) -> OrbitEngineSystemPaths:
        """獲取系統路徑常數"""
        return self.paths

    def get_processing_constants(self) -> ProcessingConstants:
        """獲取處理參數常數"""
        return self.processing

    def get_validation_constants(self) -> ValidationConstants:
        """獲取驗證相關常數"""
        return self.validation

    def get_elevation_standards(self) -> ElevationStandards:
        """獲取仰角標準常數"""
        return self.elevation

    def get_logging_constants(self) -> LoggingConstants:
        """獲取日誌相關常數"""
        return self.logging

    def get_network_constants(self) -> NetworkConstants:
        """獲取網路相關常數"""
        return self.network

    def initialize_system_environment(self) -> Dict[str, Any]:
        """初始化系統環境"""
        current_paths = self.paths.get_current_paths()
        result = {
            'execution_environment': current_paths['environment'],
            'paths_created': self.paths.ensure_paths_exist(),
            'current_paths': current_paths,
            'environment_ready': True,
            'errors': []
        }

        # 檢查關鍵路徑
        critical_paths = [
            current_paths['data_root'],
            current_paths['outputs_root']
        ]

        for path in critical_paths:
            if not path.startswith('./') and not Path(path).exists():
                result['errors'].append(f"關鍵路徑不存在: {path}")
                result['environment_ready'] = False

        return result

    def get_stage_output_path(self, stage_number: int) -> str:
        """獲取指定Stage的輸出路徑"""
        current_paths = self.paths.get_current_paths()
        stage_paths = {
            1: current_paths['stage1_output'],
            2: current_paths['stage2_output'],
            3: current_paths['stage3_output'],
            4: current_paths['stage4_output'],
            5: current_paths['stage5_output'],
            6: current_paths['stage6_output']
        }
        return stage_paths.get(stage_number, current_paths['outputs_root'])

    def export_constants(self) -> Dict[str, Any]:
        """導出所有系統常數"""
        current_paths = self.paths.get_current_paths()
        return {
            'execution_environment': current_paths['environment'],
            'system_paths': current_paths,
            'processing_constants': {
                'prediction_hours': self.processing.DEFAULT_PREDICTION_HOURS,
                'time_step_minutes': self.processing.DEFAULT_TIME_STEP_MINUTES,
                'max_processing_timeout': self.processing.MAX_PROCESSING_TIMEOUT_SECONDS,
                'max_satellites_per_batch': self.processing.MAX_SATELLITES_PER_BATCH,
                'parallel_workers': self.processing.PARALLEL_WORKERS,
                'chunk_size': self.processing.CHUNK_SIZE,
                'memory_limit_mb': self.processing.MEMORY_LIMIT_MB
            },
            'validation_constants': {
                'min_visible_satellites': self.validation.MIN_VISIBLE_SATELLITES,
                'min_coverage_percentage': self.validation.MIN_COVERAGE_PERCENTAGE,
                'min_signal_quality_score': self.validation.MIN_SIGNAL_QUALITY_SCORE,
                'position_tolerance_km': self.validation.POSITION_TOLERANCE_KM,
                'angle_tolerance_deg': self.validation.ANGLE_TOLERANCE_DEG,
                'enable_strict_validation': self.validation.ENABLE_STRICT_VALIDATION
            },
            'logging_constants': {
                'default_log_level': self.logging.DEFAULT_LOG_LEVEL,
                'log_format': self.logging.LOG_FORMAT,
                'max_log_size_mb': self.logging.MAX_LOG_SIZE_MB,
                'backup_count': self.logging.BACKUP_COUNT,
                'enable_performance_logging': self.logging.ENABLE_PERFORMANCE_LOGGING
            },
            'network_constants': {
                'netstack_base_url': self.network.NETSTACK_BASE_URL,
                'simworld_base_url': self.network.SIMWORLD_BASE_URL,
                'default_timeout': self.network.DEFAULT_TIMEOUT_SECONDS,
                'max_http_retries': self.network.MAX_HTTP_RETRIES
            }
        }


# 全局實例
_system_constants_instance = None


def get_system_constants() -> OrbitEngineConstantsManager:
    """獲取系統常數管理器實例 (單例模式)"""
    global _system_constants_instance
    if _system_constants_instance is None:
        _system_constants_instance = OrbitEngineConstantsManager()
    return _system_constants_instance


# 便捷訪問函數
def get_stage_output_path(stage_number: int) -> str:
    """便捷函數：獲取Stage輸出路徑"""
    return get_system_constants().get_stage_output_path(stage_number)


def get_current_paths() -> Dict[str, str]:
    """便捷函數：獲取當前環境路徑"""
    return get_system_constants().get_system_paths().get_current_paths()


def get_data_root() -> str:
    """便捷函數：獲取數據根目錄"""
    paths = get_current_paths()
    return paths['data_root']


def get_execution_environment() -> str:
    """便捷函數：獲取執行環境"""
    return get_system_constants().get_system_paths().detect_execution_environment()


def initialize_environment() -> Dict[str, Any]:
    """便捷函數：初始化系統環境"""
    return get_system_constants().initialize_system_environment()


# 快速訪問當前路徑（動態根據環境決定）
def get_current_data_root() -> str:
    return get_current_paths()['data_root']


def get_current_outputs_root() -> str:
    return get_current_paths()['outputs_root']


def get_current_config_root() -> str:
    return get_current_paths()['config_root']


# 向後兼容的常數（已廢棄，建議使用新的get_current_*函數）
# 這些會在運行時動態設置
_current_paths = get_current_paths()
DATA_ROOT = _current_paths['data_root']
OUTPUT_ROOT = _current_paths['outputs_root']