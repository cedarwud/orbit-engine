#!/usr/bin/env python3
"""
Stage 6: 研究數據生成與優化層 - 六階段架構 v3.0

主要功能:
- 3GPP 事件檢測 (A4/A5/D2 換手事件)
- 動態衛星池優化
- ML 訓練數據生成
- 研究性能分析
- 多目標優化決策

符合 final.md 研究需求
"""

from .stage6_research_optimization_processor import (
    Stage6ResearchOptimizationProcessor,
    create_stage6_processor
)

__all__ = [
    'Stage6ResearchOptimizationProcessor',
    'create_stage6_processor'
]

__version__ = '3.0.0'
__stage__ = 6
__description__ = 'Research Data Generation and Optimization Layer'