"""
接口定義模組

提供統一的處理器接口規範
"""

from .processor_interface import (
    ProcessingStatus,
    ProcessingMetrics,
    ProcessingResult,
    BaseProcessor,
    StageProcessor,
    DataProcessor,
    AnalysisProcessor,
    PredictionProcessor,
    ValidationProcessor,
    MonitoringProcessor,
    create_processing_result,
    create_success_result,
    create_error_result
)

__all__ = [
    # 處理器接口
    'ProcessingStatus',
    'ProcessingMetrics',
    'ProcessingResult',
    'BaseProcessor',
    'StageProcessor',
    'DataProcessor',
    'AnalysisProcessor',
    'PredictionProcessor',
    'ValidationProcessor',
    'MonitoringProcessor',
    'create_processing_result',
    'create_success_result',
    'create_error_result',
]
