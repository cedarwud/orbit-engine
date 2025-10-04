#!/usr/bin/env python3
"""結果構建器 - Stage 4"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ResultBuilder:
    """Stage 4 結果構建器"""

    def __init__(self, constellation_filter, link_budget_analyzer):
        """
        初始化結果構建器

        Args:
            constellation_filter: 星座過濾器實例
            link_budget_analyzer: 鏈路預算分析器實例
        """
        self.constellation_filter = constellation_filter
        self.link_budget_analyzer = link_budget_analyzer
        self.logger = logging.getLogger(__name__)

    def build(self,
              original_data: Dict[str, Any],
              time_series_metrics: Dict[str, Dict[str, Any]],
              connectable_satellites: Dict[str, List[Dict[str, Any]]],
              optimized_pools: Dict[str, List[Dict[str, Any]]],
              optimization_results: Optional[Dict[str, Any]],
              ntpu_coverage: Dict[str, Any],
              upstream_constellation_configs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        構建 Stage 4 標準化輸出

        符合 stage4-link-feasibility.md 規範的完整時間序列輸出
        包含階段 4.1 (候選池) 和階段 4.2 (優化池) 數據
        """

        stage4_output = {
            'stage': 'stage4_link_feasibility',

            # 階段 4.1: 候選衛星池 (完整候選)
            'connectable_satellites_candidate': connectable_satellites,

            # 階段 4.2: 優化衛星池 (最優子集) - 用於後續階段
            'connectable_satellites': optimized_pools,

            'feasibility_summary': {
                # 階段 4.1 統計
                'candidate_pool': {
                    'total_connectable': sum(len(sats) for sats in connectable_satellites.values()),
                    'by_constellation': {
                        constellation: len(sats)
                        for constellation, sats in connectable_satellites.items()
                        if len(sats) > 0
                    }
                },
                # 階段 4.2 統計
                'optimized_pool': {
                    'total_optimized': sum(len(sats) for sats in optimized_pools.values()),
                    'by_constellation': {
                        constellation: len(sats)
                        for constellation, sats in optimized_pools.items()
                        if len(sats) > 0
                    }
                },
                'total_connectable_satellites': sum(len(sats) for sats in optimized_pools.values()),
                'ntpu_coverage': ntpu_coverage  # 基於優化池的覆蓋分析
            },

            'metadata': {
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_input_satellites': len(original_data),
                'total_processed_satellites': len(time_series_metrics),
                'link_budget_constraints': self.link_budget_analyzer.get_constraint_info(),
                'constellation_thresholds': {
                    'starlink': self.constellation_filter.CONSTELLATION_THRESHOLDS['starlink'],
                    'oneweb': self.constellation_filter.CONSTELLATION_THRESHOLDS['oneweb']
                },
                # ✅ Grade A 要求: 向下傳遞 constellation_configs 給 Stage 5
                'constellation_configs': upstream_constellation_configs or {},
                'processing_stage': 4,
                'stage_4_1_completed': True,
                'stage_4_2_completed': optimization_results is not None
            }
        }

        # 添加池優化結果
        if optimization_results:
            stage4_output['pool_optimization'] = optimization_results

        return stage4_output
