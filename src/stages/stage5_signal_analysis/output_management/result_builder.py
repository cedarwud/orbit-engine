#!/usr/bin/env python3
"""結果構建器 - Stage 5"""
from typing import Dict, Any
from datetime import datetime, timezone


class ResultBuilder:
    """Stage 5 結果構建器"""

    def __init__(self, validator, physics_consts):
        self.validator = validator
        self.physics_consts = physics_consts

    def build(self, analyzed_satellites: Dict, input_data: Dict,
              processing_stats: Dict, processing_time: float) -> Dict[str, Any]:
        """構建輸出結果"""

        # 計算統計
        from shared.constants.physics_constants import SignalConstants
        signal_consts = SignalConstants()

        all_rsrp = []
        all_sinr = []
        usable_satellites = 0
        total_time_points = 0  # ✅ 新增: 計算總時間點數

        for sat_data in analyzed_satellites.values():
            avg_rsrp = sat_data['summary']['average_rsrp_dbm']
            avg_sinr = sat_data['summary']['average_sinr_db']
            if avg_rsrp:
                all_rsrp.append(avg_rsrp)
                if avg_rsrp >= signal_consts.RSRP_FAIR:
                    usable_satellites += 1
            if avg_sinr:
                all_sinr.append(avg_sinr)
            # ✅ 累計時間點數
            total_time_points += sat_data['summary'].get('total_time_points', 0)

        avg_rsrp = sum(all_rsrp) / len(all_rsrp) if all_rsrp else None
        avg_sinr = sum(all_sinr) / len(all_sinr) if all_sinr else None

        # 構建metadata
        metadata = {
            'gpp_config': {
                'standard_version': 'TS_38.214_v18.5.1',
                'calculation_standard': '3GPP_TS_38.214'
            },
            'itur_config': {
                'recommendation': 'P.618-13',
                'atmospheric_model': 'complete'
            },
            'physical_constants': {
                'speed_of_light_ms': self.physics_consts.SPEED_OF_LIGHT,
                'boltzmann_constant': 1.380649e-23,  # CODATA 2018
                'standard_compliance': 'CODATA_2018'
            },
            'processing_duration_seconds': processing_time,
            'total_calculations': total_time_points * 3  # ✅ 新增: RSRP + RSRQ + SINR
        }

        # 驗證合規性
        gpp_compliant = self.validator.verify_3gpp_compliance(analyzed_satellites)
        itur_compliant = self.validator.verify_itur_compliance(metadata)
        academic_grade = 'Grade_A' if (gpp_compliant and itur_compliant) else 'Grade_B'

        metadata.update({
            'gpp_standard_compliance': gpp_compliant,
            'itur_standard_compliance': itur_compliant,
            'academic_standard': academic_grade,
            'time_series_processing': total_time_points > 0  # ✅ 新增: 基於實際處理數據
        })

        return {
            'stage': 5,
            'stage_name': 'signal_quality_analysis',
            'signal_analysis': analyzed_satellites,
            'connectable_satellites': input_data.get('connectable_satellites', {}),
            'analysis_summary': {
                'total_satellites_analyzed': len(analyzed_satellites),
                'usable_satellites': usable_satellites,
                'total_time_points_processed': total_time_points,  # ✅ 新增
                'signal_quality_distribution': {
                    'excellent': processing_stats['excellent_signals'],
                    'good': processing_stats['good_signals'],
                    'fair': processing_stats['fair_signals'],
                    'poor': processing_stats['poor_signals']
                },
                'average_rsrp_dbm': avg_rsrp,
                'average_sinr_db': avg_sinr
            },
            'metadata': metadata
        }
