#!/usr/bin/env python3
"""
Objective Evaluators - 目標函數評估器
評估多目標優化的各項目標函數值

根據 @docs/stages/stage4-optimization.md 設計
功能職責：
- 信號品質目標評估
- 覆蓋範圍目標評估
- 換手成本目標評估
- 能效目標評估
"""

import logging
from typing import Dict, List, Any
from .optimization_models import OptimizationObjective


class ObjectiveEvaluator:
    """
    目標函數評估器

    評估優化問題中的各項目標函數
    """

    def __init__(self):
        """初始化目標函數評估器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def evaluate_population(self, population: List[Dict[str, Any]],
                           problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        評估種群

        Args:
            population: 個體種群
            problem: 優化問題定義

        Returns:
            評估後的種群
        """
        evaluated = []

        for individual in population:
            # 計算目標函數值
            objectives = self.calculate_objective_values(individual, problem)

            evaluated_individual = {
                'variables': individual,
                'objectives': objectives,
                'violations': {},  # 將由約束求解器填充
                'feasibility': 1.0  # 將由約束求解器更新
            }
            evaluated.append(evaluated_individual)

        return evaluated

    def calculate_objective_values(self, individual: Dict[str, Any],
                                  problem: Dict[str, Any]) -> Dict[str, float]:
        """
        計算目標函數值

        Args:
            individual: 個體變量
            problem: 優化問題

        Returns:
            目標函數值字典
        """
        objectives = {}

        for obj_type, obj_func in problem['objectives'].items():
            if obj_type == OptimizationObjective.SIGNAL_QUALITY:
                value = self.evaluate_signal_quality(individual)
            elif obj_type == OptimizationObjective.COVERAGE_RANGE:
                value = self.evaluate_coverage(individual)
            elif obj_type == OptimizationObjective.HANDOVER_COST:
                value = self.evaluate_handover_cost(individual)
            elif obj_type == OptimizationObjective.ENERGY_EFFICIENCY:
                value = self.evaluate_energy_efficiency(individual)
            else:
                value = 0.0

            objectives[obj_type.value] = value

        return objectives

    def evaluate_signal_quality(self, individual: Dict[str, Any]) -> float:
        """
        評估信號品質目標

        基於選中衛星數和功率分配計算信號品質
        """
        satellites = individual.get('satellite_selection', [])
        power = individual.get('power_allocation', 0.5)

        selected_count = sum(satellites) if isinstance(satellites, list) else 1
        base_quality = -120 + (selected_count * 5) + (power * 20)

        return min(-60, max(-120, base_quality))

    def evaluate_coverage(self, individual: Dict[str, Any]) -> float:
        """
        評估覆蓋目標

        基於選中衛星數量計算覆蓋率
        """
        satellites = individual.get('satellite_selection', [])
        selected_count = sum(satellites) if isinstance(satellites, list) else 1

        # 基於選中衛星數量計算覆蓋率
        coverage_percentage = min(100, selected_count * 8)
        return coverage_percentage

    def evaluate_handover_cost(self, individual: Dict[str, Any]) -> float:
        """
        評估換手成本目標

        基於時機和頻率計算成本
        """
        timing = individual.get('handover_timing', 1800)
        frequency = individual.get('frequency_allocation', 2.4)

        # 基於時機和頻率計算成本
        timing_cost = abs(timing - 1800) / 1800 * 10  # 偏離最佳時機的成本
        frequency_cost = 2.0 if frequency == 28.0 else 1.0  # 高頻段成本更高

        return timing_cost + frequency_cost

    def evaluate_energy_efficiency(self, individual: Dict[str, Any]) -> float:
        """
        評估能效目標

        能效 = 覆蓋/功耗
        """
        power = individual.get('power_allocation', 0.5)
        satellites = individual.get('satellite_selection', [])
        selected_count = sum(satellites) if isinstance(satellites, list) else 1

        # 能效 = 覆蓋/功耗
        coverage = selected_count * 8
        power_consumption = power * selected_count
        efficiency = coverage / max(0.1, power_consumption) * 10

        return min(100, efficiency)
