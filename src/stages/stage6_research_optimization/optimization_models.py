#!/usr/bin/env python3
"""
Optimization Models - 優化資料模型層
定義多目標優化的資料結構和類型

根據 @docs/stages/stage4-optimization.md 設計
功能職責：
- 優化目標類型定義
- 目標函數結構
- 約束條件模型
- 帕累托解表示
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class OptimizationObjective(Enum):
    """優化目標類型"""
    SIGNAL_QUALITY = "signal_quality"
    COVERAGE_RANGE = "coverage_range"
    HANDOVER_COST = "handover_cost"
    ENERGY_EFFICIENCY = "energy_efficiency"
    NETWORK_LOAD = "network_load"
    USER_EXPERIENCE = "user_experience"


@dataclass
class ObjectiveFunction:
    """目標函數定義"""
    objective_type: OptimizationObjective
    weight: float
    target_value: float
    min_acceptable: float
    max_penalty: float
    optimization_direction: str  # "maximize" or "minimize"


@dataclass
class OptimizationConstraint:
    """優化約束條件"""
    constraint_name: str
    constraint_type: str  # "equality", "inequality", "bound"
    constraint_function: str  # 約束表達式
    violation_penalty: float
    is_hard_constraint: bool


@dataclass
class ParetoSolution:
    """帕累托解"""
    solution_id: str
    variables: Dict[str, float]
    objective_values: Dict[str, float]
    constraint_violations: Dict[str, float]
    feasibility_score: float
    dominance_rank: int
