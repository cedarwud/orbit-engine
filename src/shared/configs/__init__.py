"""
Configuration management for Orbit Engine stages

Core Components:
- BaseConfigManager: Template Method Pattern for unified configuration
  - YAML-based external configuration
  - Environment variable override (flat + nested keys)
  - Fail-Fast validation
  - Backward compatibility

Author: Orbit Engine Refactoring Team
Date: 2025-10-15
Version: 2.1.0 (Phase 5 - Module Reorganization)
"""

from .config_manager import BaseConfigManager

__all__ = ['BaseConfigManager']
