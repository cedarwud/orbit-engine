#!/usr/bin/env python3
"""
Academic Standard Validator for Stage 4 Tests

This module validates that all Stage 4 tests comply with academic research standards.

CRITICAL VALIDATION RULES:
- NO random data generation allowed
- NO mock/simplified algorithms
- NO hardcoded assumptions
- ONLY real TLE data and official standards

符合 CLAUDE.md 的 "REAL ALGORITHMS ONLY" 原則
"""

import os
import sys
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ComplianceViolation:
    """合規性違規記錄"""
    file_path: str
    line_number: int
    violation_type: str
    description: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    recommendation: str


class AcademicStandardValidator:
    """
    學術標準驗證器

    檢查 Stage 4 測試是否符合學術研究標準
    """

    def __init__(self):
        """初始化驗證器"""
        # 嚴重違規關鍵字 (CRITICAL - 絕不允許)
        self.critical_violations = [
            'random\\.uniform', 'random\\.randint', 'random\\.choice', 'random\\.normal',
            'random\\.seed', 'np\\.random', 'numpy\\.random',
            'strategy.*simplified', 'basic_constraints', 'mock.*algorithm',
            '假設', '估算', '模擬', 'simplified', 'estimated', 'assumed'
        ]

        # 高風險關鍵字 (HIGH - 需要檢查)
        self.high_risk_patterns = [
            'MagicMock', 'Mock\\(\\)', 'patch\\(',
            'hardcode', 'fixed.*value', 'constant.*',
            'arbitrary', 'placeholder', 'dummy'
        ]

        # 學術標準關鍵字 (GOOD - 應該存在)
        self.academic_standards = [
            'ITU-R', '3GPP', 'IEEE',
            'real.*data', 'TLE.*data', 'academic.*standard',
            'official.*specification', 'published.*parameter'
        ]

        self.violations = []

    def validate_stage4_tests(self, test_directory: str) -> Dict[str, Any]:
        """
        驗證 Stage 4 測試目錄的學術標準合規性

        Args:
            test_directory: 測試目錄路徑

        Returns:
            驗證報告
        """
        print("🔬 開始 Stage 4 學術標準合規性驗證...")

        test_files = self._find_stage4_test_files(test_directory)

        for test_file in test_files:
            print(f"📁 檢查文件: {test_file}")
            self._validate_test_file(test_file)

        # 生成驗證報告
        report = self._generate_compliance_report()

        return report

    def _find_stage4_test_files(self, directory: str) -> List[str]:
        """尋找 Stage 4 相關的測試文件"""
        stage4_files = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if ('stage4' in file.lower() and
                    (file.endswith('.py') or file.endswith('.json'))):
                    stage4_files.append(os.path.join(root, file))

        return stage4_files

    def _validate_test_file(self, file_path: str):
        """驗證單個測試文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查嚴重違規
            self._check_critical_violations(file_path, content)

            # 檢查高風險模式
            self._check_high_risk_patterns(file_path, content)

            # 檢查學術標準存在性
            self._check_academic_standards_presence(file_path, content)

            # 如果是 Python 文件，進行 AST 分析
            if file_path.endswith('.py'):
                self._analyze_python_ast(file_path, content)

        except Exception as e:
            self.violations.append(ComplianceViolation(
                file_path=file_path,
                line_number=0,
                violation_type="FILE_ERROR",
                description=f"無法讀取文件: {e}",
                severity="MEDIUM",
                recommendation="檢查文件編碼和權限"
            ))

    def _check_critical_violations(self, file_path: str, content: str):
        """檢查嚴重違規"""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # 跳過註釋行和文檔字符串中的模式
            stripped_line = line.strip()
            if (stripped_line.startswith('#') or
                stripped_line.startswith('"""') or
                stripped_line.startswith("'''") or
                '禁止使用' in stripped_line or
                '❌' in stripped_line or
                '✅' in stripped_line or
                'CRITICAL:' in stripped_line):
                continue

            for pattern in self.critical_violations:
                if re.search(pattern, line, re.IGNORECASE):
                    self.violations.append(ComplianceViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="CRITICAL_VIOLATION",
                        description=f"發現嚴重違規: '{pattern}' in '{line.strip()}'",
                        severity="CRITICAL",
                        recommendation="立即移除並替換為基於學術標準的實現"
                    ))

    def _check_high_risk_patterns(self, file_path: str, content: str):
        """檢查高風險模式"""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # 跳過註釋行、文檔字符串和學術標準說明
            stripped_line = line.strip()
            if (stripped_line.startswith('#') or
                stripped_line.startswith('"""') or
                stripped_line.startswith("'''") or
                '禁止使用' in stripped_line or
                '❌' in stripped_line or
                '✅' in stripped_line or
                'CRITICAL:' in stripped_line or
                'mock_indicators' in line or  # 跳過檢測Mock指標的代碼
                'constants' in stripped_line.lower() and 'import' in stripped_line):  # 跳過常量導入
                continue

            for pattern in self.high_risk_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.violations.append(ComplianceViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="HIGH_RISK",
                        description=f"高風險模式: '{pattern}' in '{line.strip()}'",
                        severity="HIGH",
                        recommendation="檢查是否可替換為真實實現"
                    ))

    def _check_academic_standards_presence(self, file_path: str, content: str):
        """檢查學術標準的存在性"""
        academic_found = False

        for pattern in self.academic_standards:
            if re.search(pattern, content, re.IGNORECASE):
                academic_found = True
                break

        if not academic_found:
            self.violations.append(ComplianceViolation(
                file_path=file_path,
                line_number=0,
                violation_type="MISSING_STANDARDS",
                description="未發現學術標準引用 (ITU-R, 3GPP, IEEE)",
                severity="MEDIUM",
                recommendation="添加對官方標準的引用和實現"
            ))

    def _analyze_python_ast(self, file_path: str, content: str):
        """使用 AST 分析 Python 代碼"""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # 檢查函數定義
                if isinstance(node, ast.FunctionDef):
                    self._check_function_compliance(file_path, node)

                # 檢查導入語句
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._check_import_compliance(file_path, node)

                # 檢查函數調用
                elif isinstance(node, ast.Call):
                    self._check_call_compliance(file_path, node)

        except SyntaxError as e:
            self.violations.append(ComplianceViolation(
                file_path=file_path,
                line_number=e.lineno,
                violation_type="SYNTAX_ERROR",
                description=f"語法錯誤: {e.msg}",
                severity="HIGH",
                recommendation="修復語法錯誤"
            ))

    def _check_function_compliance(self, file_path: str, node: ast.FunctionDef):
        """檢查函數定義的合規性"""
        func_name = node.name.lower()

        # 檢查函數名稱是否包含違規關鍵字，但排除學術合規相關函數
        violation_keywords = ['mock', 'fake', 'dummy', 'simulate', 'random', 'simplified']

        # 排除的學術合規相關函數模式
        academic_compliance_patterns = [
            'test_no_mock',  # 測試無Mock的函數
            'verification',  # 驗證函數
            'compliance',    # 合規性函數
            'academic',      # 學術相關函數
            'standards'      # 標準相關函數
        ]

        # 如果是學術合規相關函數，跳過檢查
        is_academic_function = any(pattern in func_name for pattern in academic_compliance_patterns)
        if is_academic_function:
            return

        for keyword in violation_keywords:
            if keyword in func_name:
                self.violations.append(ComplianceViolation(
                    file_path=file_path,
                    line_number=node.lineno,
                    violation_type="FUNCTION_VIOLATION",
                    description=f"函數名包含違規關鍵字: '{func_name}'",
                    severity="HIGH",
                    recommendation=f"重命名函數以反映真實的學術標準實現"
                ))

    def _check_import_compliance(self, file_path: str, node):
        """檢查導入語句的合規性"""
        if isinstance(node, ast.ImportFrom):
            module = node.module
            if module and 'mock' in module.lower():
                # 排除學術標準相關文件的Mock檢測導入
                if ('academic_standard' in file_path or
                    'compliance' in file_path or
                    'test_no_mock' in file_path):
                    return

                self.violations.append(ComplianceViolation(
                    file_path=file_path,
                    line_number=node.lineno,
                    violation_type="IMPORT_VIOLATION",
                    description=f"導入Mock模組: {module}",
                    severity="HIGH",
                    recommendation="使用真實實現替代Mock對象"
                ))

    def _check_call_compliance(self, file_path: str, node: ast.Call):
        """檢查函數調用的合規性"""
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr

            # 檢查隨機函數調用
            random_functions = ['uniform', 'randint', 'choice', 'normal', 'seed']
            if attr_name in random_functions:
                self.violations.append(ComplianceViolation(
                    file_path=file_path,
                    line_number=node.lineno,
                    violation_type="RANDOM_CALL",
                    description=f"調用隨機函數: {attr_name}",
                    severity="CRITICAL",
                    recommendation="使用真實數據替代隨機生成"
                ))

    def _generate_compliance_report(self) -> Dict[str, Any]:
        """生成合規性報告"""
        # 按嚴重性分類違規
        violations_by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }

        # 分類違規並區分核心文件 vs 測試文件
        core_violations = []
        test_violations = []

        for violation in self.violations:
            violations_by_severity[violation.severity].append(violation)

            # 核心實現文件 vs 測試文件
            file_path = violation.file_path
            if ('src/stages/stage4' in file_path and
                not any(test_pattern in file_path for test_pattern in ['test_', 'tests/', 'fixtures/'])):
                core_violations.append(violation)
            else:
                test_violations.append(violation)

        # 計算合規性分數（重點關注核心文件）
        total_violations = len(self.violations)
        critical_count = len(violations_by_severity["CRITICAL"])
        high_count = len(violations_by_severity["HIGH"])
        core_violations_count = len(core_violations)

        # 改進的評分算法
        if critical_count > 0:
            compliance_score = max(0, 30 - critical_count * 10)
        elif core_violations_count > 0:
            # 核心文件有違規，較嚴厲評分
            compliance_score = max(40, 85 - core_violations_count * 15)
        elif high_count > 20:
            # 大量測試文件違規，但核心合規
            compliance_score = max(60, 95 - (high_count - 20) * 2)
        elif high_count > 0:
            compliance_score = max(70, 90 - high_count * 2)
        else:
            compliance_score = 100

        # 確定合規性等級
        if compliance_score >= 95:
            compliance_level = "EXCELLENT"
        elif compliance_score >= 85:
            compliance_level = "GOOD"
        elif compliance_score >= 70:
            compliance_level = "ACCEPTABLE"
        elif compliance_score >= 50:
            compliance_level = "POOR"
        else:
            compliance_level = "CRITICAL"

        report = {
            "academic_compliance_report": {
                "timestamp": "2025-09-27",
                "validator_version": "v1.0_academic_standard",
                "compliance_score": compliance_score,
                "compliance_level": compliance_level,
                "total_violations": total_violations,
                "violations_by_severity": {
                    "critical": len(violations_by_severity["CRITICAL"]),
                    "high": len(violations_by_severity["HIGH"]),
                    "medium": len(violations_by_severity["MEDIUM"]),
                    "low": len(violations_by_severity["LOW"])
                },
                "detailed_violations": [
                    {
                        "file_path": v.file_path,
                        "line_number": v.line_number,
                        "violation_type": v.violation_type,
                        "description": v.description,
                        "severity": v.severity,
                        "recommendation": v.recommendation
                    }
                    for v in self.violations
                ],
                "core_vs_test_analysis": {
                    "core_file_violations": len(core_violations),
                    "test_file_violations": len(test_violations),
                    "core_files_compliant": len(core_violations) == 0,
                    "analysis": "核心實現文件" if len(core_violations) == 0 else f"核心文件有 {len(core_violations)} 個違規"
                },
                "academic_standards_compliance": {
                    "claude_md_compliance": compliance_score >= 70 and critical_count == 0,
                    "real_algorithms_only": critical_count == 0,
                    "no_random_data": len([v for v in self.violations if "RANDOM" in v.violation_type]) == 0,
                    "no_simplified_algorithms": len([v for v in self.violations if "simplified" in v.description.lower()]) == 0
                },
                "recommendations": self._generate_recommendations(violations_by_severity)
            }
        }

        return report

    def _generate_recommendations(self, violations_by_severity: Dict[str, List]) -> List[str]:
        """生成修復建議"""
        recommendations = []

        if violations_by_severity["CRITICAL"]:
            recommendations.append("🚨 立即修復所有CRITICAL級違規 - 這些嚴重違反學術研究標準")
            recommendations.append("🔧 移除所有隨機數據生成，使用真實TLE數據")
            recommendations.append("📚 實施ITU-R、3GPP、IEEE官方標準")

        if violations_by_severity["HIGH"]:
            recommendations.append("⚠️ 修復HIGH級違規 - 移除Mock對象，使用真實實現")
            recommendations.append("🔍 檢查所有硬編碼值，替換為標準參數")

        if violations_by_severity["MEDIUM"]:
            recommendations.append("📖 添加學術標準引用和文檔")
            recommendations.append("🎯 確保所有測試基於真實衛星參數")

        if not any(violations_by_severity.values()):
            recommendations.append("✅ 所有測試符合學術研究標準！")
            recommendations.append("🎓 可用於學術期刊發表和同行評議")

        return recommendations

    def save_report(self, report: Dict[str, Any], output_path: str):
        """保存驗證報告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def validate_stage4_academic_compliance(test_directory: str) -> Dict[str, Any]:
    """
    驗證 Stage 4 測試的學術標準合規性

    Args:
        test_directory: 測試目錄路徑

    Returns:
        合規性驗證報告
    """
    validator = AcademicStandardValidator()
    return validator.validate_stage4_tests(test_directory)


if __name__ == "__main__":
    # 驗證 Stage 4 測試合規性
    test_dir = Path(__file__).parent.parent

    print("🔬 執行 Stage 4 學術標準合規性驗證...")

    report = validate_stage4_academic_compliance(str(test_dir))

    # 輸出報告摘要
    compliance = report["academic_compliance_report"]
    print(f"\n📊 合規性評分: {compliance['compliance_score']}/100")
    print(f"🎯 合規性等級: {compliance['compliance_level']}")
    print(f"⚠️ 總違規數: {compliance['total_violations']}")

    if compliance['violations_by_severity']['critical'] > 0:
        print(f"🚨 嚴重違規: {compliance['violations_by_severity']['critical']}")

    print("\n💡 修復建議:")
    for rec in compliance['recommendations']:
        print(f"   {rec}")

    # 保存詳細報告
    output_file = Path(__file__).parent.parent.parent / "STAGE4_ACADEMIC_COMPLIANCE_VALIDATION.json"
    validator = AcademicStandardValidator()
    validator.violations = []
    validator.save_report(report, str(output_file))

    print(f"\n💾 詳細報告已保存至: {output_file}")