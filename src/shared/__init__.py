"""
Shared modules for orbit-engine project

⚠️ MIGRATION NOTICE (Phase 5 Complete - v2.1.0):
Module structure has been reorganized for better clarity:

OLD STRUCTURE → NEW STRUCTURE
├── base_processor.py           → base/base_processor.py
├── base_result_manager.py      → base/base_result_manager.py
├── config_manager.py            → configs/config_manager.py
├── interfaces/                  → base/ (merged)
└── validation_framework/        → validation/

RECOMMENDED IMPORTS (New Structure):
    from shared.base import BaseStageProcessor, ProcessingResult
    from shared.configs import BaseConfigManager
    from shared.validation import ValidationEngine
    from shared.constants import PhysicsConstants
    from shared.coordinate_systems import SkyfieldCoordinateEngine
    from shared.utils import TimeUtils

OLD IMPORT PATHS (deprecated, backward compatibility maintained):
    from shared.base_processor import BaseStageProcessor         # ⚠️ Deprecated
    from shared.config_manager import BaseConfigManager          # ⚠️ Deprecated
    from shared.interfaces import ProcessingResult               # ⚠️ Deprecated
    from shared.validation_framework import ValidationEngine     # ⚠️ Deprecated

Backward compatibility will be removed in v3.0.0 (2025-12-31)

Core Components:
- base: Base classes and processor interfaces
- configs: Configuration management (BaseConfigManager)
- constants: Physical constants, academic standards, TLE constants
- coordinate_systems: Coordinate transformation engines
- utils: Time, math, and file utilities
- validation: Data validation and academic compliance

Author: Orbit Engine Refactoring Team
Date: 2025-10-15
Version: 2.1.0 (Phase 5 - Module Reorganization Complete)
"""

import warnings

# Version after Phase 5 complete
__version__ = "2.1.0"

# Public API (new structure)
__all__ = [
    'base',
    'configs',
    'constants',
    'coordinate_systems',
    'utils',
    'validation',
]


# Backward compatibility layer with deprecation warnings
def __getattr__(name):
    """
    Provide backward compatibility for old import paths with deprecation warnings.

    This allows old code to continue working while encouraging migration to new paths.
    Will be removed in v3.0.0 (2025-12-31).
    """

    # Map old imports to new locations
    compatibility_map = {
        # Base classes
        'BaseStageProcessor': ('shared.base', 'base_processor', 'BaseStageProcessor'),
        'BaseResultManager': ('shared.base', 'base_result_manager', 'BaseResultManager'),

        # Config manager
        'BaseConfigManager': ('shared.configs', 'config_manager', 'BaseConfigManager'),

        # Processor interfaces
        'ProcessingStatus': ('shared.base', 'processor_interface', 'ProcessingStatus'),
        'ProcessingResult': ('shared.base', 'processor_interface', 'ProcessingResult'),
        'ProcessingMetrics': ('shared.base', 'processor_interface', 'ProcessingMetrics'),
        'BaseProcessor': ('shared.base', 'processor_interface', 'BaseProcessor'),
        'StageProcessor': ('shared.base', 'processor_interface', 'StageProcessor'),
        'create_processing_result': ('shared.base', 'processor_interface', 'create_processing_result'),
        'create_success_result': ('shared.base', 'processor_interface', 'create_success_result'),
        'create_error_result': ('shared.base', 'processor_interface', 'create_error_result'),

        # Validation framework
        'ValidationEngine': ('shared.validation', 'validation_engine', 'ValidationEngine'),
        'AcademicValidationFramework': ('shared.validation', 'academic_validation_framework', 'AcademicValidationFramework'),
    }

    if name in compatibility_map:
        new_module, submodule, attr_name = compatibility_map[name]

        # Issue deprecation warning
        warnings.warn(
            f"Importing '{name}' directly from 'shared' is deprecated. "
            f"Use 'from {new_module} import {attr_name}' instead. "
            f"This compatibility shim will be removed in v3.0.0 (2025-12-31).",
            DeprecationWarning,
            stacklevel=2
        )

        # Dynamically import and return the attribute
        import importlib
        module = importlib.import_module(f'{new_module}.{submodule}')
        return getattr(module, attr_name)

    raise AttributeError(f"module 'shared' has no attribute '{name}'")
