#!/usr/bin/env python3
"""
Stage 4: 鏈路可行性評估層 - 六階段架構 v3.0

主要功能:
- 星座感知篩選 (Starlink 5° vs OneWeb 10°)
- NTPU 地面站可見性分析 (24°56'39"N, 121°22'17"E)
- 軌道週期感知處理
- 服務窗口計算
- 為後續階段提供可連線衛星池

符合 final.md 研究需求
"""

from .stage4_link_feasibility_processor import (
    Stage4LinkFeasibilityProcessor,
    create_stage4_processor
)

from .constellation_filter import (
    ConstellationFilter,
    create_constellation_filter
)

__all__ = [
    'Stage4LinkFeasibilityProcessor',
    'create_stage4_processor',
    'ConstellationFilter',
    'create_constellation_filter'
]

__version__ = '3.0.0'
__stage__ = 4
__description__ = 'Link Feasibility Assessment Layer'