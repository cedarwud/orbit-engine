"""
Stage 5 並行處理模組

提供並行處理能力，包括：
- CPU 優化器：動態計算最優工作器數量
- 工作器管理器：管理並行/順序處理
"""

from .cpu_optimizer import CPUOptimizer
from .worker_manager import SignalAnalysisWorkerManager

__all__ = [
    'CPUOptimizer',
    'SignalAnalysisWorkerManager'
]
