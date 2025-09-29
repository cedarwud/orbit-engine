"""
真實座標系統模組

包含：
- IERS 數據管理器
- WGS84 參數管理器
- Skyfield 座標轉換引擎

嚴格遵循 CRITICAL DEVELOPMENT PRINCIPLE
"""

from .iers_data_manager import get_iers_manager, IERSDataManager, EOPData
from .wgs84_manager import get_wgs84_manager, WGS84Manager, WGS84Parameters
from .skyfield_coordinate_engine import get_coordinate_engine, SkyfieldCoordinateEngine, CoordinateTransformResult

__all__ = [
    'get_iers_manager', 'IERSDataManager', 'EOPData',
    'get_wgs84_manager', 'WGS84Manager', 'WGS84Parameters',
    'get_coordinate_engine', 'SkyfieldCoordinateEngine', 'CoordinateTransformResult'
]