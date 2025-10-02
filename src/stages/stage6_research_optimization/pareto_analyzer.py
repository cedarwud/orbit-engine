#!/usr/bin/env python3
"""
Pareto Analyzer - 帕累托分析器
分析和選擇帕累托最優解

根據 @docs/stages/stage4-optimization.md 設計
功能職責：
- 帕累托前沿分析
- 解的品質評估
- 推薦解選擇
- 多樣性計算
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from .optimization_models import ParetoSolution, OptimizationObjective


class ParetoAnalyzer:
    """
    帕累托分析器

    分析帕累托解集，選擇推薦解，評估解的品質
    """

    def __init__(self):
        """初始化帕累托分析器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def analyze_pareto_front(self, solutions: List[ParetoSolution]) -> Dict[str, Any]:
        """
        分析帕累托前沿

        Args:
            solutions: 帕累托解集

        Returns:
            前沿分析結果
        """
        if not solutions:
            return {'status': 'no_solutions'}

        # 提取目標值
        objective_names = list(solutions[0].objective_values.keys())
        objective_ranges = {}

        for obj_name in objective_names:
            values = [sol.objective_values[obj_name] for sol in solutions]
            objective_ranges[obj_name] = {
                'min': min(values),
                'max': max(values),
                'mean': np.mean(values),
                'std': np.std(values)
            }

        # 計算前沿指標
        front_metrics = {
            'solution_count': len(solutions),
            'objective_ranges': objective_ranges,
            'average_feasibility': np.mean([sol.feasibility_score for sol in solutions]),
            'diversity_score': self.calculate_diversity_score(solutions),
            'convergence_quality': self.assess_convergence_quality(solutions)
        }

        return front_metrics

    def select_recommended_solution(self, solutions: List[ParetoSolution],
                                   problem: Dict[str, Any]) -> Optional[ParetoSolution]:
        """
        選擇推薦解

        基於權重計算加權評分，選擇最佳平衡解

        Args:
            solutions: 帕累托解集
            problem: 優化問題

        Returns:
            推薦的帕累托解
        """
        if not solutions:
            return None

        # 基於權重計算加權評分
        best_solution = None
        best_score = -float('inf')

        for solution in solutions:
            score = 0
            for obj_type, obj_func in problem['objectives'].items():
                obj_value = solution.objective_values.get(obj_type.value, 0)
                normalized_value = self.normalize_objective_value(obj_value, obj_type)

                if obj_func.optimization_direction == "maximize":
                    score += obj_func.weight * normalized_value
                else:
                    score += obj_func.weight * (1 - normalized_value)

            # 懲罰約束違反
            penalty = sum(solution.constraint_violations.values()) * 0.1
            score -= penalty

            if score > best_score:
                best_score = score
                best_solution = solution

        return best_solution

    def evaluate_solution_quality(self, solution: Optional[ParetoSolution],
                                 problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估解的品質

        Args:
            solution: 帕累托解
            problem: 優化問題

        Returns:
            品質評估結果
        """
        if not solution:
            return {'quality_score': 0.0, 'status': 'no_solution'}

        # 目標達成度
        objective_achievement = {}
        for obj_type, obj_func in problem['objectives'].items():
            obj_value = solution.objective_values.get(obj_type.value, 0)
            target = obj_func.target_value

            if obj_func.optimization_direction == "maximize":
                achievement = min(1.0, obj_value / target) if target > 0 else 0.5
            else:
                achievement = min(1.0, target / obj_value) if obj_value > 0 else 0.5

            objective_achievement[obj_type.value] = achievement

        # 約束滿足度
        constraint_satisfaction = 1.0 - min(1.0, sum(solution.constraint_violations.values()) / 10)

        # 整體品質分數
        avg_achievement = np.mean(list(objective_achievement.values()))
        quality_score = (avg_achievement * 0.7 + constraint_satisfaction * 0.3)

        return {
            'quality_score': quality_score,
            'objective_achievement': objective_achievement,
            'constraint_satisfaction': constraint_satisfaction,
            'feasibility_score': solution.feasibility_score,
            'status': 'evaluated'
        }

    def normalize_objective_value(self, value: float, obj_type: OptimizationObjective) -> float:
        """
        正規化目標值

        Args:
            value: 目標值
            obj_type: 目標類型

        Returns:
            正規化後的值 (0-1)
        """
        if obj_type == OptimizationObjective.SIGNAL_QUALITY:
            return max(0, min(1, (value + 120) / 60))  # -120 to -60 dBm
        elif obj_type == OptimizationObjective.COVERAGE_RANGE:
            return max(0, min(1, value / 100))  # 0 to 100%
        elif obj_type == OptimizationObjective.HANDOVER_COST:
            return max(0, min(1, 1 - value / 20))  # 0 to 20 cost units
        elif obj_type == OptimizationObjective.ENERGY_EFFICIENCY:
            return max(0, min(1, value / 100))  # 0 to 100%
        else:
            return 0.5

    def calculate_diversity_score(self, solutions: List[ParetoSolution]) -> float:
        """
        計算多樣性分數

        Args:
            solutions: 帕累托解集

        Returns:
            多樣性分數
        """
        if len(solutions) < 2:
            return 0.0

        # 計算解之間的平均距離
        total_distance = 0
        count = 0

        for i in range(len(solutions)):
            for j in range(i + 1, len(solutions)):
                distance = self.calculate_solution_distance(solutions[i], solutions[j])
                total_distance += distance
                count += 1

        return total_distance / count if count > 0 else 0.0

    def calculate_solution_distance(self, sol1: ParetoSolution, sol2: ParetoSolution) -> float:
        """
        計算兩個解之間的歐氏距離

        Args:
            sol1: 第一個解
            sol2: 第二個解

        Returns:
            歐氏距離
        """
        distance = 0
        for obj_name in sol1.objective_values.keys():
            diff = sol1.objective_values[obj_name] - sol2.objective_values[obj_name]
            distance += diff ** 2
        return np.sqrt(distance)

    def assess_convergence_quality(self, solutions: List[ParetoSolution]) -> float:
        """
        評估收斂品質

        Args:
            solutions: 帕累托解集

        Returns:
            收斂品質分數
        """
        # 簡化的收斂品質評估
        feasible_solutions = [sol for sol in solutions if sol.feasibility_score > 0.9]
        return len(feasible_solutions) / len(solutions) if solutions else 0.0

    def convert_to_pareto_solutions(self, solution_set: List[Dict[str, Any]]) -> List[ParetoSolution]:
        """
        轉換為帕累托解對象

        Args:
            solution_set: 字典格式的解集

        Returns:
            ParetoSolution 對象列表
        """
        pareto_solutions = []
        for i, sol in enumerate(solution_set):
            pareto_sol = ParetoSolution(
                solution_id=f"solution_{i}",
                variables=sol.get('variables', {}),
                objective_values=sol.get('objectives', {}),
                constraint_violations=sol.get('violations', {}),
                feasibility_score=sol.get('feasibility', 1.0),
                dominance_rank=1
            )
            pareto_solutions.append(pareto_sol)
        return pareto_solutions

    def perform_dominance_analysis(self, solutions: List[ParetoSolution]) -> List[bool]:
        """
        執行支配性分析

        Args:
            solutions: 帕累托解集

        Returns:
            支配標記列表
        """
        # 簡化的支配性分析
        return [False] * len(solutions)  # 假設沒有被支配的解

    def extract_non_dominated_solutions(self, solutions: List[ParetoSolution],
                                       dominated: List[bool]) -> List[ParetoSolution]:
        """
        提取非支配解

        Args:
            solutions: 解集
            dominated: 支配標記

        Returns:
            非支配解列表
        """
        return [sol for i, sol in enumerate(solutions) if not dominated[i]]

    def sort_pareto_solutions(self, solutions: List[ParetoSolution]) -> List[ParetoSolution]:
        """
        排序帕累托解

        Args:
            solutions: 解集

        Returns:
            排序後的解集
        """
        return sorted(solutions, key=lambda x: x.feasibility_score, reverse=True)
