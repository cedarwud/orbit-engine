#!/usr/bin/env python3
"""
Multi-Objective Optimizer - Stage 6 優化決策層
多目標優化算法和約束求解模組（重構版）

根據 @docs/stages/stage4-optimization.md 設計
功能職責：
- 多目標優化算法協調
- 約束條件求解協調
- 權重平衡管理
- 帕累托最優解搜尋

架構設計：
- optimization_models.py: 資料模型層
- nsga2_algorithm.py: NSGA-II 演算法核心
- objective_evaluators.py: 目標函數評估器
- constraint_solver.py: 約束求解器
- pareto_analyzer.py: 帕累托分析器
- quality_cost_balancer.py: 品質成本平衡器
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# 導入重構後的模組
from .optimization_models import (
    OptimizationObjective,
    ObjectiveFunction,
    OptimizationConstraint,
    ParetoSolution
)
from .nsga2_algorithm import NSGA2Algorithm
from .objective_evaluators import ObjectiveEvaluator
from .constraint_solver import ConstraintSolver
from .pareto_analyzer import ParetoAnalyzer
from .quality_cost_balancer import QualityCostBalancer

class MultiObjectiveOptimizer:
    """
    多目標優化器

    實現多目標優化算法，處理信號品質、覆蓋範圍、
    切換成本等多個目標的平衡優化
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化多目標優化器（重構版）"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 預設目標權重 (從文檔配置)
        self.default_objectives = {
            OptimizationObjective.SIGNAL_QUALITY: ObjectiveFunction(
                objective_type=OptimizationObjective.SIGNAL_QUALITY,
                weight=0.4,
                target_value=-80.0,  # dBm
                min_acceptable=-100.0,
                max_penalty=50.0,
                optimization_direction="maximize"
            ),
            OptimizationObjective.COVERAGE_RANGE: ObjectiveFunction(
                objective_type=OptimizationObjective.COVERAGE_RANGE,
                weight=0.3,
                target_value=90.0,  # percentage
                min_acceptable=60.0,
                max_penalty=30.0,
                optimization_direction="maximize"
            ),
            OptimizationObjective.HANDOVER_COST: ObjectiveFunction(
                objective_type=OptimizationObjective.HANDOVER_COST,
                weight=0.2,
                target_value=5.0,  # normalized cost
                min_acceptable=0.0,
                max_penalty=20.0,
                optimization_direction="minimize"
            ),
            OptimizationObjective.ENERGY_EFFICIENCY: ObjectiveFunction(
                objective_type=OptimizationObjective.ENERGY_EFFICIENCY,
                weight=0.1,
                target_value=80.0,  # percentage
                min_acceptable=50.0,
                max_penalty=30.0,
                optimization_direction="maximize"
            )
        }

        # 更新配置權重
        if 'optimization_objectives' in self.config:
            self._update_objective_weights(self.config['optimization_objectives'])

        # 初始化子模組
        optimization_params = {
            'population_size': self.config.get('population_size', 100),
            'max_generations': self.config.get('max_generations', 50),
            'pareto_front_size': self.config.get('pareto_front_size', 20)
        }

        self.nsga2_algorithm = NSGA2Algorithm(optimization_params)
        self.objective_evaluator = ObjectiveEvaluator()
        self.constraint_solver = ConstraintSolver()
        self.pareto_analyzer = ParetoAnalyzer()
        self.quality_cost_balancer = QualityCostBalancer()

        # 預設約束條件
        self.default_constraints = self.constraint_solver.initialize_default_constraints()

        # 優化統計
        self.optimization_stats = {
            'optimizations_performed': 0,
            'pareto_solutions_found': 0,
            'average_convergence_time': 0.0,
            'constraint_violations_resolved': 0,
            'objective_improvements': {}
        }

        self.logger.info("✅ Multi-Objective Optimizer 初始化完成（重構版）")

    def optimize_multiple_objectives(self, objectives: Dict[str, float],
                                   constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        多目標優化求解（重構版 - 使用模組化架構）

        Args:
            objectives: 目標函數值
            constraints: 約束條件列表

        Returns:
            多目標優化結果
        """
        try:
            self.logger.info("🎯 開始多目標優化求解（重構版）")

            # 準備優化問題
            optimization_problem = self._prepare_optimization_problem(
                objectives, constraints
            )

            # 初始化種群（使用 NSGA2Algorithm）
            initial_population = self.nsga2_algorithm.initialize_population(
                optimization_problem['variables']
            )

            # 創建評估函數（組合目標評估器和約束求解器）
            def evaluate_func(pop, prob):
                # 評估目標函數
                evaluated = self.objective_evaluator.evaluate_population(pop, prob)
                # 更新約束違反和可行性
                evaluated = self.constraint_solver.update_population_with_constraints(evaluated, prob)
                return evaluated

            # 執行 NSGA-II 算法
            pareto_solutions = self.nsga2_algorithm.execute_nsga2(
                initial_population, optimization_problem, evaluate_func
            )

            # 分析帕累托前沿（使用 ParetoAnalyzer）
            pareto_analysis = self.pareto_analyzer.analyze_pareto_front(pareto_solutions)

            # 選擇推薦解（使用 ParetoAnalyzer）
            recommended_solution = self.pareto_analyzer.select_recommended_solution(
                pareto_solutions, optimization_problem
            )

            # 評估解的品質（使用 ParetoAnalyzer）
            solution_quality = self.pareto_analyzer.evaluate_solution_quality(
                recommended_solution, optimization_problem
            )

            # 更新統計
            self.optimization_stats['optimizations_performed'] += 1
            self.optimization_stats['pareto_solutions_found'] += len(pareto_solutions)

            result = {
                'optimization_problem': optimization_problem,
                'pareto_solutions': [sol.__dict__ for sol in pareto_solutions],
                'pareto_analysis': pareto_analysis,
                'recommended_solution': recommended_solution.__dict__ if recommended_solution else {},
                'solution_quality': solution_quality,
                'optimization_timestamp': datetime.now(timezone.utc).isoformat(),
                'statistics': self.optimization_stats.copy()
            }

            self.logger.info(f"✅ 多目標優化完成，找到 {len(pareto_solutions)} 個帕累托解")
            return result

        except Exception as e:
            self.logger.error(f"❌ 多目標優化失敗: {e}")
            return {'error': str(e), 'pareto_solutions': []}

    def balance_quality_cost(self, solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        平衡品質與成本（重構版 - 使用 QualityCostBalancer）

        Args:
            solutions: 候選解決方案

        Returns:
            平衡優化結果
        """
        try:
            self.logger.info("⚖️ 開始品質成本平衡分析（重構版）")

            # 分析解決方案的品質-成本權衡（使用 QualityCostBalancer）
            tradeoff_analysis = self.quality_cost_balancer.analyze_quality_cost_tradeoff(solutions)

            # 計算帕累托效率前沿（使用 QualityCostBalancer）
            efficient_frontier = self.quality_cost_balancer.compute_efficient_frontier(
                solutions, ['signal_quality', 'handover_cost']
            )

            # 找到最佳平衡點（使用 QualityCostBalancer）
            optimal_balance = self.quality_cost_balancer.find_optimal_balance_point(
                efficient_frontier, tradeoff_analysis
            )

            # 生成平衡建議（使用 QualityCostBalancer）
            balance_recommendations = self.quality_cost_balancer.generate_balance_recommendations(
                optimal_balance, tradeoff_analysis
            )

            result = {
                'tradeoff_analysis': tradeoff_analysis,
                'efficient_frontier': efficient_frontier,
                'optimal_balance': optimal_balance,
                'balance_recommendations': balance_recommendations,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'balance_score': self.quality_cost_balancer.calculate_balance_score(optimal_balance)
            }

            self.logger.info("⚖️ 品質成本平衡分析完成")
            return result

        except Exception as e:
            self.logger.error(f"❌ 品質成本平衡失敗: {e}")
            return {'error': str(e), 'optimal_balance': {}}

    def find_pareto_optimal(self, solution_set: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        尋找帕累托最優解（重構版 - 使用 ParetoAnalyzer）

        Args:
            solution_set: 解決方案集合

        Returns:
            帕累托最優解列表
        """
        try:
            self.logger.info(f"🔍 尋找帕累托最優解，候選解數量: {len(solution_set)}")

            if not solution_set:
                return []

            # 轉換為 ParetoSolution 對象（使用 ParetoAnalyzer）
            pareto_solutions = self.pareto_analyzer.convert_to_pareto_solutions(solution_set)

            # 執行支配性分析（使用 ParetoAnalyzer）
            dominated_solutions = self.pareto_analyzer.perform_dominance_analysis(pareto_solutions)

            # 提取非支配解（使用 ParetoAnalyzer）
            pareto_optimal = self.pareto_analyzer.extract_non_dominated_solutions(
                pareto_solutions, dominated_solutions
            )

            # 排序帕累托解（使用 ParetoAnalyzer）
            sorted_pareto = self.pareto_analyzer.sort_pareto_solutions(pareto_optimal)

            # 轉換回字典格式
            result_solutions = [sol.__dict__ for sol in sorted_pareto]

            self.logger.info(f"🔍 找到 {len(result_solutions)} 個帕累托最優解")
            return result_solutions

        except Exception as e:
            self.logger.error(f"❌ 帕累托最優解搜尋失敗: {e}")
            return []

    def _update_objective_weights(self, weight_config: Dict[str, float]):
        """更新目標權重"""
        weight_mapping = {
            'signal_quality_weight': OptimizationObjective.SIGNAL_QUALITY,
            'coverage_weight': OptimizationObjective.COVERAGE_RANGE,
            'handover_cost_weight': OptimizationObjective.HANDOVER_COST,
            'energy_efficiency_weight': OptimizationObjective.ENERGY_EFFICIENCY
        }

        for config_key, objective_type in weight_mapping.items():
            if config_key in weight_config:
                if objective_type in self.default_objectives:
                    self.default_objectives[objective_type].weight = weight_config[config_key]

    def _prepare_optimization_problem(self, objectives: Dict[str, float],
                                    constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """準備優化問題"""
        # 合併目標函數
        active_objectives = {}
        for obj_type, obj_func in self.default_objectives.items():
            if obj_type.value in objectives:
                obj_func.target_value = objectives[obj_type.value]
            active_objectives[obj_type] = obj_func

        # 處理約束條件
        active_constraints = self.default_constraints.copy()
        for constraint_data in constraints:
            constraint = OptimizationConstraint(
                constraint_name=constraint_data.get('name', 'custom'),
                constraint_type=constraint_data.get('type', 'inequality'),
                constraint_function=constraint_data.get('function', ''),
                violation_penalty=constraint_data.get('penalty', 50.0),
                is_hard_constraint=constraint_data.get('hard', False)
            )
            active_constraints.append(constraint)

        # 定義決策變量
        variables = {
            'satellite_selection': {'type': 'binary', 'count': 20},  # 衛星選擇
            'handover_timing': {'type': 'continuous', 'range': [0, 3600]},  # 換手時機
            'power_allocation': {'type': 'continuous', 'range': [0.1, 1.0]},  # 功率分配
            'frequency_allocation': {'type': 'discrete', 'options': [2.4, 5.0, 28.0]}  # 頻率分配
        }

        return {
            'objectives': active_objectives,
            'constraints': active_constraints,
            'variables': variables,
            'problem_size': sum(var.get('count', 1) for var in variables.values())
        }

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """獲取優化統計"""
        return self.optimization_stats.copy()

    def reset_statistics(self):
        """重置統計數據"""
        self.optimization_stats = {
            'optimizations_performed': 0,
            'pareto_solutions_found': 0,
            'average_convergence_time': 0.0,
            'constraint_violations_resolved': 0,
            'objective_improvements': {}
        }
        self.logger.info("📊 多目標優化統計已重置")
