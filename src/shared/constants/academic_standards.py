"""
學術研究標準定義

基於天體力學、軌道動力學和衛星工程的科學原理
參考文獻:
- Vallado, D. A. "Fundamentals of Astrodynamics and Applications" 4th Edition
- Hoots, F. R. & Roehrich, R. L. "Models for Propagation of NORAD Element Sets"
- Kelso, T. S. "Validation of SGP4 and IS-GPS-200D Against GPS Precision Ephemerides"
"""

from typing import Dict, Any
import math


class AcademicValidationStandards:
    """學術級驗證標準"""

    # === TLE數據品質標準 ===
    # 基於軌道預測精度研究 (Kelso et al., 2006)

    # TLE數據新鮮度標準 (基於軌道預測誤差增長率)
    # 研究顯示：TLE預測誤差隨時間呈指數增長
    TLE_QUALITY_THRESHOLDS = {
        'excellent': {
            'max_age_days': 3,
            'expected_position_error_km': 0.5,  # 500m
            'confidence_level': 0.95
        },
        'very_good': {
            'max_age_days': 7,
            'expected_position_error_km': 1.0,  # 1km
            'confidence_level': 0.90
        },
        'good': {
            'max_age_days': 14,
            'expected_position_error_km': 2.0,  # 2km
            'confidence_level': 0.85
        },
        'acceptable': {
            'max_age_days': 30,
            'expected_position_error_km': 5.0,  # 5km
            'confidence_level': 0.75
        },
        'poor': {
            'max_age_days': 60,
            'expected_position_error_km': 10.0,  # 10km
            'confidence_level': 0.60
        }
    }

    # === 軌道參數物理約束 ===
    # 基於天體力學基本原理

    ORBITAL_CONSTRAINTS = {
        # 傾角約束 (基於幾何限制)
        'inclination_deg': {
            'min': 0.0,      # 赤道軌道
            'max': 180.0     # 極地逆行軌道
        },

        # 偏心率約束 (基於軌道類型)
        'eccentricity': {
            'min': 0.0,      # 圓軌道
            'max': 0.95      # 高橢圓軌道上限 (避免大氣層碰撞)
        },

        # 平均運動約束 (基於地球重力場和軌道高度)
        # 從開普勒第三定律推導: n = sqrt(μ/a³)
        'mean_motion_rev_per_day': {
            'min': 0.5,      # 極高軌道 (~126,000 km)
            'max': 17.0      # 低地軌道下限 (~160 km)
        },

        # 軌道週期約束 (基於物理可達範圍)
        'orbital_period_minutes': {
            'min': 85,       # 理論最低軌道週期
            'max': 2880      # 2天週期 (合理上限)
        }
    }

    # === 學術評分標準 ===
    # 基於國際學術評分慣例 (A+, A, A-, B+, B, B-, C+, C, C-, F)

    ACADEMIC_GRADE_THRESHOLDS = {
        'A+': {'min_score': 97.0, 'description': '優秀 (Excellent)'},
        'A':  {'min_score': 93.0, 'description': '極佳 (Very Good)'},
        'A-': {'min_score': 90.0, 'description': '良好+ (Good Plus)'},
        'B+': {'min_score': 87.0, 'description': '良好 (Good)'},
        'B':  {'min_score': 83.0, 'description': '中上 (Above Average)'},
        'B-': {'min_score': 80.0, 'description': '中等+ (Average Plus)'},
        'C+': {'min_score': 77.0, 'description': '中等 (Average)'},
        'C':  {'min_score': 73.0, 'description': '及格+ (Passing Plus)'},
        'C-': {'min_score': 70.0, 'description': '及格 (Passing)'},
        'F':  {'min_score': 0.0,  'description': '不及格 (Failing)'}
    }

    # === 時間精度標準 ===
    # 基於TLE數據特性和軌道預測限制

    TIME_PRECISION_STANDARDS = {
        # TLE時間精度等級 (基於實際觀測和預測能力)
        'ultra_high': {
            'precision_seconds': 1.0,    # 1秒 (理論最佳)
            'applicability': 'recent_observations',
            'confidence': 0.60
        },
        'high': {
            'precision_seconds': 60.0,   # 1分鐘 (實際可達)
            'applicability': 'standard_tle',
            'confidence': 0.85
        },
        'medium': {
            'precision_seconds': 600.0,  # 10分鐘 (典型精度)
            'applicability': 'routine_operations',
            'confidence': 0.90
        },
        'low': {
            'precision_seconds': 3600.0, # 1小時 (粗略估計)
            'applicability': 'long_term_prediction',
            'confidence': 0.70
        }
    }

    # === 統計顯著性標準 ===
    # 基於統計學和品質保證原理

    STATISTICAL_THRESHOLDS = {
        # 資料完整性要求
        'data_completeness_excellent': 0.98,  # 98% 完整性
        'data_completeness_good': 0.95,       # 95% 完整性
        'data_completeness_acceptable': 0.90,  # 90% 完整性

        # 一致性檢查通過率
        'consistency_check_excellent': 0.95,  # 95% 通過率
        'consistency_check_good': 0.90,       # 90% 通過率
        'consistency_check_acceptable': 0.85,  # 85% 通過率

        # 驗證信心水準
        'confidence_level_high': 0.95,        # 95% 信心水準
        'confidence_level_standard': 0.90,    # 90% 信心水準
        'confidence_level_basic': 0.85        # 85% 信心水準
    }


def calculate_grade_from_score(score: float) -> str:
    """
    根據學術標準將數值分數轉換為等級

    基於國際學術評分慣例

    Args:
        score: 數值分數 (0-100)

    Returns:
        學術等級 (A+, A, A-, B+, B, B-, C+, C, C-, F)
    """
    thresholds = AcademicValidationStandards.ACADEMIC_GRADE_THRESHOLDS

    for grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-']:
        if score >= thresholds[grade]['min_score']:
            return grade

    return 'F'


def validate_orbital_parameters(inclination: float, eccentricity: float,
                              mean_motion: float) -> Dict[str, Any]:
    """
    驗證軌道參數的物理合理性

    基於天體力學基本原理

    Args:
        inclination: 軌道傾角 (度)
        eccentricity: 軌道偏心率
        mean_motion: 平均運動 (轉/天)

    Returns:
        驗證結果字典
    """
    constraints = AcademicValidationStandards.ORBITAL_CONSTRAINTS
    results = {
        'valid': True,
        'violations': [],
        'warnings': []
    }

    # 檢查傾角
    if not (constraints['inclination_deg']['min'] <= inclination <= constraints['inclination_deg']['max']):
        results['valid'] = False
        results['violations'].append(f"軌道傾角超出物理範圍: {inclination}° (有效範圍: 0-180°)")

    # 檢查偏心率
    if not (constraints['eccentricity']['min'] <= eccentricity <= constraints['eccentricity']['max']):
        results['valid'] = False
        results['violations'].append(f"軌道偏心率超出合理範圍: {eccentricity} (有效範圍: 0-0.95)")

    # 檢查平均運動
    if not (constraints['mean_motion_rev_per_day']['min'] <= mean_motion <= constraints['mean_motion_rev_per_day']['max']):
        results['valid'] = False
        results['violations'].append(f"平均運動超出物理範圍: {mean_motion} 轉/天 (有效範圍: 0.5-17.0)")

    # 計算軌道週期並檢查一致性
    if mean_motion > 0:
        orbital_period_minutes = 1440.0 / mean_motion  # 分鐘
        period_constraints = constraints['orbital_period_minutes']

        if not (period_constraints['min'] <= orbital_period_minutes <= period_constraints['max']):
            results['valid'] = False
            results['violations'].append(
                f"軌道週期超出合理範圍: {orbital_period_minutes:.1f} 分鐘 "
                f"(有效範圍: {period_constraints['min']}-{period_constraints['max']} 分鐘)"
            )

    return results


def assess_tle_data_quality(age_days: float) -> Dict[str, Any]:
    """
    基於科學研究評估TLE數據品質

    基於軌道預測誤差增長率研究

    Args:
        age_days: TLE數據年齡 (天)

    Returns:
        品質評估結果
    """
    thresholds = AcademicValidationStandards.TLE_QUALITY_THRESHOLDS

    for quality_level, criteria in thresholds.items():
        if age_days <= criteria['max_age_days']:
            return {
                'quality_level': quality_level,
                'expected_error_km': criteria['expected_position_error_km'],
                'confidence_level': criteria['confidence_level'],
                'age_days': age_days,
                'grade': calculate_quality_grade(quality_level)
            }

    # 超出所有門檻
    return {
        'quality_level': 'outdated',
        'expected_error_km': 20.0,  # 估計誤差 > 20km
        'confidence_level': 0.30,
        'age_days': age_days,
        'grade': 'F'
    }


def calculate_quality_grade(quality_level: str) -> str:
    """將品質等級轉換為學術等級"""
    quality_to_grade = {
        'excellent': 'A+',
        'very_good': 'A',
        'good': 'B+',
        'acceptable': 'B-',
        'poor': 'C',
        'outdated': 'F'
    }
    return quality_to_grade.get(quality_level, 'F')