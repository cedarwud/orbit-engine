#!/usr/bin/env python3
"""
Stage 5 Grade A 學術合規性驗證器

實現零容忍的學術研究標準檢查，確保絕不使用：
- 硬編碼參數
- 預設/假數據
- 簡化算法
- Mock/模擬實現

符合 CLAUDE.md 中的 CRITICAL DEVELOPMENT PRINCIPLE 要求

作者：Claude Code
日期：2025-09-27
版本：v1.0
"""

import os
import json
import logging
import math
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GradeAComplianceValidator:
    """
    Grade A 學術合規性驗證器

    執行零容忍檢查，確保：
    1. 無硬編碼參數
    2. 無預設/假數據
    3. 無簡化算法
    4. 使用真實數據源
    5. 完整實現
    """

    def __init__(self):
        self.validation_results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'critical_violations': [],
            'warnings': [],
            'grade_assessment': 'unknown'
        }

        # 禁用的關鍵字和模式
        self.forbidden_patterns = {
            'hardcoded_coordinates': [
                r'24\.9426',  # NTPU latitude
                r'121\.3662',  # NTPU longitude
                r'observer_lat\s*=\s*[\d\.-]+',
                r'observer_lon\s*=\s*[\d\.-]+',
            ],
            'default_values': [
                r'\.get\(["\'][^"\']+["\']\s*,\s*-?[\d\.]+\)',  # .get('key', default_value)
                r'rsrp.*=.*-100\.0',  # Default RSRP
                r'snr.*=.*10\.0',     # Default SNR
                r'elevation.*>.*10\.0',  # Hardcoded elevation threshold
            ],
            'simplified_implementations': [
                r'簡化實現',
                r'simplified.*implementation',
                r'mock.*data',
                r'假設.*值',
                r'estimated.*value',
                r'假數據',
                r'預設值',
                r'return\s+0\.0.*#.*簡化',
            ],
            'linear_interpolation': [
                r'線性插值',
                r'linear.*interpolation',
                r'簡單.*插值',
            ],
            'fake_calculations': [
                r'compression_ratio\s*=\s*0\.7',  # Fake compression ratio
                r'return.*0\.0.*#.*假',
                r'假設.*比率',
            ]
        }

    def validate_stage5_compliance(self, stage5_path: str) -> Dict[str, Any]:
        """驗證 Stage 5 的 Grade A 合規性"""
        try:
            self.validation_results = {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'critical_violations': [],
                'warnings': [],
                'grade_assessment': 'unknown'
            }

            logger.info("🚨 開始 Stage 5 Grade A 合規性驗證")

            # 1. 檢查檔案結構
            self._check_file_structure(stage5_path)

            # 2. 檢查原始碼合規性
            self._check_source_code_compliance(stage5_path)

            # 3. 檢查配置檔案
            self._check_configuration_compliance(stage5_path)

            # 4. 檢查算法實現
            self._check_algorithm_implementations(stage5_path)

            # 5. 評估整體合規性
            self._assess_overall_compliance()

            logger.info(f"✅ Grade A 合規性驗證完成: {self.validation_results['grade_assessment']}")
            return self.validation_results

        except Exception as e:
            logger.error(f"❌ Grade A 合規性驗證失敗: {e}")
            self.validation_results['critical_violations'].append(f"驗證系統異常: {e}")
            self.validation_results['grade_assessment'] = 'FAILED'
            return self.validation_results

    def _check_file_structure(self, stage5_path: str) -> None:
        """檢查檔案結構合規性"""
        required_files = [
            'data_integration_processor.py',
            'timeseries_converter.py',
            'format_converter_hub.py',
            'layered_data_generator.py',
            'stage5_academic_standards_validator.py'
        ]

        for file_name in required_files:
            file_path = os.path.join(stage5_path, file_name)
            self.validation_results['total_checks'] += 1

            if os.path.exists(file_path):
                self.validation_results['passed_checks'] += 1
                logger.info(f"✅ 檔案存在: {file_name}")
            else:
                self.validation_results['failed_checks'] += 1
                self.validation_results['critical_violations'].append(f"缺少必需檔案: {file_name}")
                logger.error(f"❌ 缺少必需檔案: {file_name}")

    def _check_source_code_compliance(self, stage5_path: str) -> None:
        """檢查原始碼合規性"""
        python_files = []
        for root, dirs, files in os.walk(stage5_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                self._check_file_for_violations(file_path, content)

            except Exception as e:
                self.validation_results['warnings'].append(f"無法讀取檔案 {file_path}: {e}")

    def _check_file_for_violations(self, file_path: str, content: str) -> None:
        """檢查單個檔案的違規行為"""
        file_name = os.path.basename(file_path)

        for category, patterns in self.forbidden_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)

                self.validation_results['total_checks'] += 1

                if matches:
                    self.validation_results['failed_checks'] += 1
                    violation = f"{file_name}: 檢測到{category}違規 - {pattern} ({len(matches)}次)"
                    self.validation_results['critical_violations'].append(violation)
                    logger.error(f"❌ {violation}")
                else:
                    self.validation_results['passed_checks'] += 1

    def _check_configuration_compliance(self, stage5_path: str) -> None:
        """檢查配置檔案合規性"""
        # 檢查是否有適當的配置載入機制
        config_indicators = [
            'get_observer_coordinates_from_config',
            'get_elevation_threshold_from_config',
            'get_real_signal_parameters',
            'AcademicStandardsConfig'
        ]

        for root, dirs, files in os.walk(stage5_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for indicator in config_indicators:
                            self.validation_results['total_checks'] += 1

                            if indicator in content:
                                self.validation_results['passed_checks'] += 1
                                logger.info(f"✅ 發現配置機制: {indicator} in {os.path.basename(file_path)}")
                            else:
                                self.validation_results['warnings'].append(f"未在 {os.path.basename(file_path)} 中發現 {indicator}")

                    except Exception as e:
                        self.validation_results['warnings'].append(f"配置檢查異常 {file_path}: {e}")

    def _check_algorithm_implementations(self, stage5_path: str) -> None:
        """檢查算法實現品質"""
        algorithm_checks = [
            {
                'name': '三次樣條插值',
                'file': 'timeseries_converter.py',
                'indicators': ['cubic_spline', '_compute_cubic_spline_coefficients', 'Thomas']
            },
            {
                'name': '真實信號強度計算',
                'file': 'timeseries_converter.py',
                'indicators': ['FSPL', 'free_space_path_loss', 'physics_model']
            },
            {
                'name': '真實覆蓋範圍計算',
                'file': 'layered_data_generator.py',
                'indicators': ['horizon_distance', 'coverage_area', 'earth_radius']
            },
            {
                'name': '真實壓縮比計算',
                'file': 'format_converter_hub.py',
                'indicators': ['gzip.compress', '_calculate_real_compression_ratio']
            }
        ]

        for check in algorithm_checks:
            file_path = os.path.join(stage5_path, check['file'])

            if not os.path.exists(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                found_indicators = 0
                for indicator in check['indicators']:
                    if indicator in content:
                        found_indicators += 1

                self.validation_results['total_checks'] += 1

                if found_indicators >= len(check['indicators']) // 2:  # 至少一半的指標
                    self.validation_results['passed_checks'] += 1
                    logger.info(f"✅ {check['name']} 實現合規 ({found_indicators}/{len(check['indicators'])})")
                else:
                    self.validation_results['failed_checks'] += 1
                    self.validation_results['critical_violations'].append(
                        f"{check['name']} 實現不完整 ({found_indicators}/{len(check['indicators'])})"
                    )
                    logger.error(f"❌ {check['name']} 實現不完整")

            except Exception as e:
                self.validation_results['warnings'].append(f"算法檢查異常 {check['file']}: {e}")

    def _assess_overall_compliance(self) -> None:
        """評估整體合規性"""
        total_checks = self.validation_results['total_checks']
        passed_checks = self.validation_results['passed_checks']
        critical_violations = len(self.validation_results['critical_violations'])

        if total_checks == 0:
            compliance_rate = 0.0
        else:
            compliance_rate = passed_checks / total_checks

        # Grade A 要求
        if critical_violations == 0 and compliance_rate >= 0.95:
            grade = 'GRADE_A'
        elif critical_violations <= 2 and compliance_rate >= 0.85:
            grade = 'GRADE_B'
        elif critical_violations <= 5 and compliance_rate >= 0.70:
            grade = 'GRADE_C'
        else:
            grade = 'GRADE_F'

        self.validation_results['grade_assessment'] = grade
        self.validation_results['compliance_rate'] = compliance_rate

        logger.info(f"📊 合規性評估:")
        logger.info(f"   總檢查項目: {total_checks}")
        logger.info(f"   通過項目: {passed_checks}")
        logger.info(f"   失敗項目: {self.validation_results['failed_checks']}")
        logger.info(f"   嚴重違規: {critical_violations}")
        logger.info(f"   合規率: {compliance_rate:.2%}")
        logger.info(f"   最終等級: {grade}")

    def generate_compliance_report(self) -> str:
        """生成合規性報告"""
        report = f"""
# Stage 5 Grade A 學術合規性報告

## 總體評估
- **最終等級**: {self.validation_results['grade_assessment']}
- **合規率**: {self.validation_results.get('compliance_rate', 0.0):.2%}
- **總檢查項目**: {self.validation_results['total_checks']}
- **通過項目**: {self.validation_results['passed_checks']}
- **失敗項目**: {self.validation_results['failed_checks']}

## 嚴重違規 ({len(self.validation_results['critical_violations'])})
"""

        if self.validation_results['critical_violations']:
            for i, violation in enumerate(self.validation_results['critical_violations'], 1):
                report += f"{i}. {violation}\n"
        else:
            report += "🎉 無嚴重違規發現！\n"

        report += f"""
## 警告 ({len(self.validation_results['warnings'])})
"""

        if self.validation_results['warnings']:
            for i, warning in enumerate(self.validation_results['warnings'], 1):
                report += f"{i}. {warning}\n"
        else:
            report += "✅ 無警告項目\n"

        report += f"""
## Grade A 標準要求
- ✅ 使用真實數據源，絕不使用假數據
- ✅ 完整算法實現，絕不使用簡化
- ✅ 動態配置載入，絕不硬編碼
- ✅ 物理模型計算，絕不使用預設值
- ✅ 學術標準合規，零容忍違規

## 建議
{self._generate_recommendations()}

---
報告生成時間: {datetime.now(timezone.utc).isoformat()}
驗證器版本: v1.0
"""
        return report

    def _generate_recommendations(self) -> str:
        """生成改進建議"""
        if self.validation_results['grade_assessment'] == 'GRADE_A':
            return "🎉 恭喜！已達到 Grade A 學術研究標準。"

        recommendations = []

        if any('hardcoded' in v for v in self.validation_results['critical_violations']):
            recommendations.append("- 移除所有硬編碼參數，改用配置系統")

        if any('default' in v for v in self.validation_results['critical_violations']):
            recommendations.append("- 消除預設值使用，改用真實數據驗證")

        if any('simplified' in v for v in self.validation_results['critical_violations']):
            recommendations.append("- 完成所有簡化實現，使用完整算法")

        if any('linear' in v for v in self.validation_results['critical_violations']):
            recommendations.append("- 實現三次樣條插值替代線性插值")

        if not recommendations:
            recommendations.append("- 檢查所有模組的學術標準合規性")
            recommendations.append("- 確保所有計算使用真實物理模型")

        return "\n".join(recommendations)


def validate_stage5_grade_a_compliance(stage5_path: str = None) -> Dict[str, Any]:
    """
    驗證 Stage 5 的 Grade A 合規性

    Args:
        stage5_path: Stage 5 模組路徑

    Returns:
        合規性驗證結果
    """
    if stage5_path is None:
        stage5_path = "/home/sat/orbit-engine/src/stages/stage5_data_integration"

    validator = GradeAComplianceValidator()
    results = validator.validate_stage5_compliance(stage5_path)

    # 生成報告
    report = validator.generate_compliance_report()

    # 保存報告
    try:
        report_path = os.path.join(stage5_path, "grade_a_compliance_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 合規性報告已保存: {report_path}")
    except Exception as e:
        logger.warning(f"⚠️ 無法保存報告: {e}")

    return results


if __name__ == "__main__":
    # 執行驗證
    results = validate_stage5_grade_a_compliance()

    grade = results['grade_assessment']
    if grade == 'GRADE_A':
        print("🎉 Stage 5 已達到 Grade A 學術研究標準！")
        exit(0)
    else:
        print(f"❌ Stage 5 目前等級: {grade}")
        print(f"嚴重違規: {len(results['critical_violations'])}")
        exit(1)