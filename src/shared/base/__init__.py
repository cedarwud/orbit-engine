"""
Base classes and interfaces for Orbit Engine processors

Core Components:
- BaseStageProcessor: Template for all stage processors
- BaseResultManager: Template for result management
- ProcessingResult, ProcessingStatus: Interface definitions

Author: Orbit Engine Refactoring Team
Date: 2025-10-15
Version: 2.1.0 (Phase 5 - Module Reorganization)
"""

from .base_processor import BaseStageProcessor
from .base_result_manager import BaseResultManager
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
    create_error_result,
)

__all__ = [
    # Base classes
    'BaseStageProcessor',
    'BaseResultManager',

    # Interfaces and enums
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

    # Helper functions
    'create_processing_result',
    'create_success_result',
    'create_error_result',
]
