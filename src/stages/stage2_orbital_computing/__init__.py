"""
🛰️ Stage 2: 軌道狀態傳播層 - v3.0 重構版本

符合新架構的 Grade A 學術級實現：
✅ 使用 Stage 1 的 epoch_datetime，禁止 TLE 重新解析
✅ SGP4/SDP4 軌道傳播計算，輸出 TEME 座標
✅ 時間序列生成，支援可配置時間窗口
❌ 不做座標轉換 (留給 Stage 3)
❌ 不做可見性分析 (留給 Stage 4)

v3.0 架構變更：
- 移除座標轉換功能 → Stage 3
- 移除可見性分析功能 → Stage 4
- 移除GPU計算功能 → 不需要
- 專注於軌道狀態傳播

核心組件：
- SGP4Calculator: 標準軌道傳播計算
- Stage2OrbitalPropagationProcessor: 軌道狀態傳播流程
- TEMEPosition: TEME 座標系統數據結構
- OrbitalStateResult: 軌道狀態結果
"""

from .sgp4_calculator import SGP4Calculator, SGP4Position, SGP4OrbitResult
from .stage2_orbital_computing_processor import (
    Stage2OrbitalPropagationProcessor,
    create_stage2_processor,
    TEMEPosition,
    OrbitalStateResult
)

# 公開API
__all__ = [
    # 核心組件
    'SGP4Calculator',
    'Stage2OrbitalPropagationProcessor',
    'create_stage2_processor',

    # 數據結構
    'SGP4Position',
    'SGP4OrbitResult',
    'TEMEPosition',
    'OrbitalStateResult'
]

# 版本信息
__version__ = "3.0.0"
__author__ = "Orbit Engine System"
__description__ = "Grade A Academic Orbital State Propagation Layer (v3.0)"

# v3.0 學術標準聲明
ACADEMIC_STANDARDS = {
    "grade": "A",
    "algorithm_compliance": "SGP4/SDP4_standard",
    "coordinate_system": "TEME",
    "architecture_version": "3.0",
    "stage_concept": "orbital_state_propagation",
    "tle_reparse_prohibited": True,
    "epoch_datetime_source": "stage1_provided",
    "data_source": "real_tle_only",
    "simulation_allowed": False,
    "simplification_allowed": False
}

def get_academic_standards():
    """獲取 v3.0 學術級標準聲明"""
    return ACADEMIC_STANDARDS.copy()

def validate_v3_compliance(processor_instance):
    """驗證處理器是否符合 v3.0 架構標準"""
    validation_result = {
        "compliant": True,
        "version": "3.0",
        "grade": "A",
        "issues": []
    }

    # 檢查核心組件
    if not hasattr(processor_instance, 'sgp4_calculator'):
        validation_result["compliant"] = False
        validation_result["issues"].append("缺少 SGP4Calculator 組件")

    # 檢查架構版本
    if hasattr(processor_instance, 'processing_stats'):
        if processor_instance.processing_stats.get('architecture_version') != 'v3.0':
            validation_result["compliant"] = False
            validation_result["issues"].append("架構版本不符合 v3.0 要求")

    # 檢查座標系統
    if hasattr(processor_instance, 'coordinate_system'):
        if processor_instance.coordinate_system != 'TEME':
            validation_result["compliant"] = False
            validation_result["issues"].append("座標系統必須為 TEME")

    # 確認移除了不當功能
    removed_components = ['coordinate_converter', 'visibility_filter', 'gpu_coordinate_converter']
    for component in removed_components:
        if hasattr(processor_instance, component):
            validation_result["compliant"] = False
            validation_result["issues"].append(f"v3.0 架構不應包含 {component} 組件")

    return validation_result