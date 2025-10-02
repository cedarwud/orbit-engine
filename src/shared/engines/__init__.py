"""
共享引擎模組
包含各階段共用的核心引擎組件

注意：SGP4OrbitalEngine 已棄用，請使用 stages.stage2_orbital_computing.sgp4_calculator.SGP4Calculator
"""

from .skyfield_orbital_engine import SkyfieldOrbitalEngine

__all__ = ['SkyfieldOrbitalEngine']