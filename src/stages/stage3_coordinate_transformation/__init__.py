"""
Stage 3: 座標系統轉換層 - v3.1 模組化架構

專業級 TEME→ITRF→WGS84 座標轉換
使用 Skyfield 專業庫，確保 IAU 標準合規

🏗️ v3.1 模組化架構：
- Stage3CoordinateTransformProcessor: 主協調器
- Stage3DataValidator: 輸入/輸出驗證
- Stage3DataExtractor: TEME 數據提取
- Stage3TransformationEngine: 核心座標轉換
- Stage3ComplianceValidator: 學術合規檢查
- Stage3ResultsManager: 結果管理
- GeometricPrefilter: 幾何預篩選（優化）
"""

# 主處理器
from .stage3_coordinate_transform_processor import (
    Stage3CoordinateTransformProcessor,
    create_stage3_processor
)

# v3.1 專業模組
from .stage3_data_validator import Stage3DataValidator, create_data_validator
from .stage3_data_extractor import Stage3DataExtractor, create_data_extractor
from .stage3_transformation_engine import Stage3TransformationEngine, create_transformation_engine
from .stage3_compliance_validator import Stage3ComplianceValidator, create_compliance_validator
from .stage3_results_manager import Stage3ResultsManager, create_results_manager
from .geometric_prefilter import GeometricPrefilter, create_geometric_prefilter

__all__ = [
    # 主處理器
    'Stage3CoordinateTransformProcessor',
    'create_stage3_processor',

    # v3.1 專業模組
    'Stage3DataValidator',
    'create_data_validator',
    'Stage3DataExtractor',
    'create_data_extractor',
    'Stage3TransformationEngine',
    'create_transformation_engine',
    'Stage3ComplianceValidator',
    'create_compliance_validator',
    'Stage3ResultsManager',
    'create_results_manager',
    'GeometricPrefilter',
    'create_geometric_prefilter',
]