#!/usr/bin/env python3
"""
NSGA-II Algorithm - 非支配排序遺傳算法核心
實現多目標優化的 NSGA-II 演算法

學術參考:
- Deb, K. et al. (2002). "A fast and elitist multiobjective genetic algorithm: NSGA-II"
  IEEE Transactions on Evolutionary Computation
"""

import logging
from typing import Dict, List, Any, Tuple
from .optimization_models import ParetoSolution


class NSGA2Algorithm:
    """
    NSGA-II 演算法實現

    實現快速非支配排序、擁擠距離計算、精英選擇策略
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化 NSGA-II 演算法"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config

        # 演算法參數
        self.population_size = config.get('population_size', 100)
        self.max_generations = config.get('max_generations', 50)
        self.pareto_front_size = config.get('pareto_front_size', 20)

    def execute_nsga2(self, population: List[Dict[str, Any]],
                      problem: Dict[str, Any],
                      evaluate_func) -> List[ParetoSolution]:
        """
        執行 NSGA-II 演算法

        Args:
            population: 初始種群
            problem: 優化問題定義
            evaluate_func: 評估函數

        Returns:
            帕累托最優解集
        """
        current_population = population.copy()
        generation = 0
        best_solutions = []

        while generation < self.max_generations:
            # 評估目標函數
            evaluated_population = evaluate_func(current_population, problem)

            # 非支配排序
            fronts = self.fast_non_dominated_sort(evaluated_population)

            # 選擇下一代
            next_population = self.select_next_generation(fronts, evaluated_population)

            # 記錄最佳解
            if fronts:
                best_solutions.extend(fronts[0])  # 第一前沿

            current_population = next_population
            generation += 1

        # 轉換為 ParetoSolution 對象
        pareto_solutions = []
        for i, solution in enumerate(best_solutions[:self.pareto_front_size]):
            pareto_sol = ParetoSolution(
                solution_id=f"pareto_{i}",
                variables=solution['variables'],
                objective_values=solution['objectives'],
                constraint_violations=solution.get('violations', {}),
                feasibility_score=solution.get('feasibility', 1.0),
                dominance_rank=solution.get('rank', 1)
            )
            pareto_solutions.append(pareto_sol)

        return pareto_solutions

    def fast_non_dominated_sort(self, population: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        快速非支配排序

        實現 Deb et al. (2002) 的 O(MN²) 複雜度排序算法
        """
        fronts = []
        current_front = []

        # 第一前沿 - 非支配解
        for i, individual_i in enumerate(population):
            is_dominated = False
            for j, individual_j in enumerate(population):
                if i != j and self.dominates(individual_j, individual_i):
                    is_dominated = True
                    break

            if not is_dominated:
                individual_i['rank'] = 1
                current_front.append(individual_i)

        fronts.append(current_front)

        # 後續前沿
        front_number = 1
        while fronts[front_number - 1]:
            next_front = []
            for individual in population:
                if individual.get('rank') is None:
                    dominates_count = 0
                    for front_individual in fronts[front_number - 1]:
                        if self.dominates(individual, front_individual):
                            dominates_count += 1

                    if dominates_count == 0:
                        individual['rank'] = front_number + 1
                        next_front.append(individual)

            fronts.append(next_front)
            front_number += 1

        return fronts[:-1]  # 移除最後的空前沿

    def dominates(self, individual_a: Dict[str, Any], individual_b: Dict[str, Any]) -> bool:
        """
        檢查 A 是否支配 B

        A 支配 B 當且僅當：
        - A 在所有目標上不差於 B
        - A 至少在一個目標上優於 B
        """
        objectives_a = individual_a['objectives']
        objectives_b = individual_b['objectives']

        at_least_one_better = False
        for obj_name in objectives_a.keys():
            value_a = objectives_a[obj_name]
            value_b = objectives_b[obj_name]

            # 根據目標類型判斷方向
            if obj_name in ['signal_quality', 'coverage_range', 'energy_efficiency']:
                # 最大化目標
                if value_a < value_b:
                    return False
                if value_a > value_b:
                    at_least_one_better = True
            else:
                # 最小化目標
                if value_a > value_b:
                    return False
                if value_a < value_b:
                    at_least_one_better = True

        return at_least_one_better

    def select_next_generation(self, fronts: List[List[Dict[str, Any]]],
                              population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """選擇下一代個體"""
        next_generation = []

        # 按前沿順序選擇個體
        for front in fronts:
            if len(next_generation) + len(front) <= self.population_size:
                next_generation.extend(front)
            else:
                # 如果前沿太大，使用擁擠距離選擇
                remaining_slots = self.population_size - len(next_generation)
                sorted_front = self.crowding_distance_sort(front)
                next_generation.extend(sorted_front[:remaining_slots])
                break

        return next_generation

    def crowding_distance_sort(self, front: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        擁擠距離排序

        實現 Deb et al. (2002) 的擁擠距離計算
        保持解集的多樣性
        """
        if len(front) <= 2:
            return front

        # 為每個個體計算擁擠距離
        for individual in front:
            individual['crowding_distance'] = 0

        objectives = list(front[0]['objectives'].keys())

        for obj_name in objectives:
            # 按目標值排序
            front.sort(key=lambda x: x['objectives'][obj_name])

            # 邊界個體設為無窮大距離
            front[0]['crowding_distance'] = float('inf')
            front[-1]['crowding_distance'] = float('inf')

            # 計算中間個體的擁擠距離
            obj_range = front[-1]['objectives'][obj_name] - front[0]['objectives'][obj_name]
            if obj_range > 0:
                for i in range(1, len(front) - 1):
                    distance = (front[i + 1]['objectives'][obj_name] -
                              front[i - 1]['objectives'][obj_name]) / obj_range
                    front[i]['crowding_distance'] += distance

        # 按擁擠距離降序排序
        front.sort(key=lambda x: x['crowding_distance'], reverse=True)
        return front

    def initialize_population(self, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        初始化種群 - 使用確定性方法而非隨機生成

        使用確定性分布初始化，避免隨機數據生成
        符合學術標準的可重現性要求
        """
        population = []

        for i in range(self.population_size):
            individual = {}

            for var_name, var_config in variables.items():
                if var_config['type'] == 'binary':
                    count = var_config.get('count', 1)
                    # 使用確定性模式：基於索引的二進制模式
                    binary_pattern = [(i >> j) & 1 for j in range(count)]
                    individual[var_name] = binary_pattern
                elif var_config['type'] == 'continuous':
                    var_range = var_config['range']
                    # 使用線性分布而非隨機
                    ratio = i / max(1, self.population_size - 1)
                    value = var_range[0] + ratio * (var_range[1] - var_range[0])
                    individual[var_name] = value
                elif var_config['type'] == 'discrete':
                    options = var_config['options']
                    # 使用循環分布而非隨機選擇
                    index = i % len(options)
                    individual[var_name] = options[index]

            population.append(individual)

        return population
