"""
Shared modules for orbit-engine project

Core Components:
- base: Base classes and processor interfaces
- configs: Configuration management (BaseConfigManager)
- constants: Physical constants, academic standards, TLE constants
- coordinate_systems: Coordinate transformation engines
- utils: Time, math, and file utilities
- validation: Data validation and academic compliance

Import Examples:
    from shared.base import BaseStageProcessor, ProcessingResult
    from shared.configs import BaseConfigManager
    from shared.validation import ValidationEngine
    from shared.constants import PhysicsConstants
    from shared.coordinate_systems import SkyfieldCoordinateEngine
    from shared.utils import TimeUtils
"""

__version__ = "3.0.0"

__all__ = [
    'base',
    'configs',
    'constants',
    'coordinate_systems',
    'utils',
    'validation',
]
