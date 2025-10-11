"""
工具模組

整合來源：
- 各Stage中的通用工具函數
- 時間處理、數學計算、文件操作等

提供統一的工具函數接口
"""

from .time_utils import (
    TimeUtils,
    parse_tle_time,
    format_time_duration,
    create_prediction_timeline,
    get_current_utc,
    ensure_utc
)

from .math_utils import (
    MathUtils,
    Vector3D,
    distance_3d,
    deg2rad,
    rad2deg,
    safe_divide,
    normalize_angle_deg,
    normalize_angle_rad
)

from .file_utils import (
    FileUtils,
    read_json,
    write_json,
    ensure_dir,
    file_exists,
    get_file_size,
    create_timestamped_filename
)

from .ground_distance_calculator import (
    GroundDistanceCalculator,
    haversine_distance,
    vincenty_distance
)

from .coordinate_converter import (
    ecef_to_geodetic,
    geodetic_to_ecef,
    CoordinateConverter
)

__all__ = [
    # 時間工具
    'TimeUtils',
    'parse_tle_time',
    'format_time_duration',
    'create_prediction_timeline',
    'get_current_utc',
    'ensure_utc',

    # 數學工具
    'MathUtils',
    'Vector3D',
    'distance_3d',
    'deg2rad',
    'rad2deg',
    'safe_divide',
    'normalize_angle_deg',
    'normalize_angle_rad',

    # 文件工具
    'FileUtils',
    'read_json',
    'write_json',
    'ensure_dir',
    'file_exists',
    'get_file_size',
    'create_timestamped_filename',

    # 地面距离计算工具
    'GroundDistanceCalculator',
    'haversine_distance',
    'vincenty_distance',

    # 坐标转换工具
    'ecef_to_geodetic',
    'geodetic_to_ecef',
    'CoordinateConverter'
]