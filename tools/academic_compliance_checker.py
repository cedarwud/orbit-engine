#!/usr/bin/env python3
"""
學術合規性自動檢查器

用途: 自動掃描代碼，檢查是否違反 CRITICAL DEVELOPMENT PRINCIPLE
執行: python tools/academic_compliance_checker.py src/

檢查項目:
1. 硬編碼數值是否有來源標記
2. 算法是否有學術引用
3. 是否使用禁止的關鍵字（估計、假設等）
4. 門檻值是否有依據說明
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# 禁止的關鍵字（違反 NO ESTIMATED/ASSUMED VALUES）
FORBIDDEN_KEYWORDS = [
    # 中文
    '估計', '假設', '約', '大約', '模擬', '簡化',
    # 英文
    'estimated', 'assumed', 'roughly', 'approximately',
    'simplified', 'mock', 'fake', 'simulated'
]

# 必須有來源標記的數值模式
# 匹配: variable = 數字 但沒有 SOURCE 標記
HARDCODED_NUMBER_PATTERN = re.compile(
    r'^\s*[\w_]+\s*[=:]\s*[\d.]+\s*(?:#(?!.*(?:SOURCE|來源|依據|實測|Official|Standard)).*)?$',
    re.MULTILINE
)

# 來源標記模式（合規）
SOURCE_TAG_PATTERN = re.compile(
    r'#.*(?:SOURCE|來源|依據|實測|Official|Standard|Measured)',
    re.IGNORECASE
)

# 算法關鍵字（需要學術引用）
ALGORITHM_KEYWORDS = [
    'algorithm', 'weight', 'threshold', 'contribution',
    '算法', '權重', '門檻', '貢獻度'
]

# 學術引用模式
CITATION_PATTERN = re.compile(
    r'(?:Vallado|Kelso|Chvátal|Johnson|ITU-R|3GPP|IEEE|NORAD|NASA)',
    re.IGNORECASE
)


class ComplianceViolation:
    """合規性違規記錄"""

    def __init__(self, file_path: str, line_num: int, line_content: str,
                 violation_type: str, severity: str, message: str):
        self.file_path = file_path
        self.line_num = line_num
        self.line_content = line_content
        self.violation_type = violation_type
        self.severity = severity
        self.message = message

    def __str__(self):
        severity_icon = '🔴' if self.severity == 'CRITICAL' else '⚠️'
        return (
            f"{severity_icon} {self.file_path}:{self.line_num}\n"
            f"   類型: {self.violation_type}\n"
            f"   內容: {self.line_content.strip()}\n"
            f"   問題: {self.message}\n"
        )


class AcademicComplianceChecker:
    """學術合規性檢查器"""

    def __init__(self):
        self.violations: List[ComplianceViolation] = []

    def check_file(self, file_path: Path) -> List[ComplianceViolation]:
        """檢查單個文件"""
        violations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️ 無法讀取文件 {file_path}: {e}")
            return violations

        # 檢查 1: 禁止關鍵字
        violations.extend(self._check_forbidden_keywords(file_path, lines))

        # 檢查 2: 硬編碼數值
        violations.extend(self._check_hardcoded_numbers(file_path, lines))

        # 檢查 3: 算法引用
        violations.extend(self._check_algorithm_citations(file_path, lines))

        return violations

    def _check_forbidden_keywords(self, file_path: Path, lines: List[str]) -> List[ComplianceViolation]:
        """檢查禁止關鍵字"""
        violations = []

        for line_num, line in enumerate(lines, 1):
            # 跳過純註釋行和文檔字符串
            if line.strip().startswith('#') or line.strip().startswith('"""'):
                continue

            for keyword in FORBIDDEN_KEYWORDS:
                if keyword in line:
                    violations.append(ComplianceViolation(
                        file_path=str(file_path),
                        line_num=line_num,
                        line_content=line,
                        violation_type='FORBIDDEN_KEYWORD',
                        severity='CRITICAL',
                        message=f"使用禁止的關鍵字 '{keyword}' (違反 NO ESTIMATED/ASSUMED VALUES)"
                    ))

        return violations

    def _check_hardcoded_numbers(self, file_path: Path, lines: List[str]) -> List[ComplianceViolation]:
        """檢查硬編碼數值是否有來源標記"""
        violations = []

        for line_num, line in enumerate(lines, 1):
            # 跳過空行和純註釋
            if not line.strip() or line.strip().startswith('#'):
                continue

            # 檢查是否有硬編碼數字
            if re.search(r'=\s*[\d.]+', line):
                # 檢查是否有來源標記
                if not SOURCE_TAG_PATTERN.search(line):
                    # 排除一些常見的合規情況
                    if any(skip in line for skip in ['range(', 'len(', 'enumerate(', 'return']):
                        continue

                    violations.append(ComplianceViolation(
                        file_path=str(file_path),
                        line_num=line_num,
                        line_content=line,
                        violation_type='MISSING_SOURCE',
                        severity='CRITICAL',
                        message="硬編碼數值缺少來源標記 (需要 # SOURCE: 或 # 來源: 標記)"
                    ))

        return violations

    def _check_algorithm_citations(self, file_path: Path, lines: List[str]) -> List[ComplianceViolation]:
        """檢查算法是否有學術引用"""
        violations = []

        # 尋找算法相關的函數/類
        in_algorithm_block = False
        block_start_line = 0
        block_lines = []

        for line_num, line in enumerate(lines, 1):
            # 檢測算法塊開始
            if any(keyword in line.lower() for keyword in ALGORITHM_KEYWORDS):
                in_algorithm_block = True
                block_start_line = line_num
                block_lines = [line]
                continue

            if in_algorithm_block:
                block_lines.append(line)

                # 檢測塊結束（空行或下一個函數）
                if line.strip() == '' or line.strip().startswith('def '):
                    # 檢查整個塊是否有學術引用
                    block_text = ''.join(block_lines)
                    if not CITATION_PATTERN.search(block_text):
                        violations.append(ComplianceViolation(
                            file_path=str(file_path),
                            line_num=block_start_line,
                            line_content=block_lines[0],
                            violation_type='MISSING_CITATION',
                            severity='WARNING',
                            message="算法實現缺少學術文獻引用 (建議引用相關論文)"
                        ))

                    in_algorithm_block = False
                    block_lines = []

        return violations

    def check_directory(self, directory: Path) -> Dict[str, List[ComplianceViolation]]:
        """檢查整個目錄"""
        results = {}

        for py_file in directory.rglob('*.py'):
            # 跳過測試文件和 __pycache__
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue

            violations = self.check_file(py_file)
            if violations:
                results[str(py_file)] = violations

        return results

    def generate_report(self, results: Dict[str, List[ComplianceViolation]]) -> str:
        """生成檢查報告"""
        report = []
        report.append("╔═══════════════════════════════════════════════════════════════╗")
        report.append("║          學術合規性自動檢查報告                                ║")
        report.append("╚═══════════════════════════════════════════════════════════════╝")
        report.append("")

        if not results:
            report.append("✅ 未發現合規性違規")
            return '\n'.join(report)

        # 統計
        total_files = len(results)
        total_violations = sum(len(v) for v in results.values())
        critical_count = sum(
            1 for violations in results.values()
            for v in violations if v.severity == 'CRITICAL'
        )

        report.append(f"📊 檢查統計:")
        report.append(f"   文件數: {total_files}")
        report.append(f"   違規總數: {total_violations}")
        report.append(f"   CRITICAL: {critical_count}")
        report.append("")
        report.append("─" * 70)
        report.append("")

        # 詳細違規
        for file_path, violations in results.items():
            report.append(f"📄 {file_path}")
            report.append(f"   違規數: {len(violations)}")
            report.append("")

            for v in violations:
                report.append(str(v))

        report.append("─" * 70)
        report.append("")
        report.append("🔧 修正建議:")
        report.append("   1. FORBIDDEN_KEYWORD: 移除估計/假設關鍵字，使用實測值")
        report.append("   2. MISSING_SOURCE: 添加 # SOURCE: 或 # 來源: 標記")
        report.append("   3. MISSING_CITATION: 添加學術文獻引用")

        return '\n'.join(report)


def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("用法: python academic_compliance_checker.py <目錄路徑>")
        print("範例: python tools/academic_compliance_checker.py src/stages/stage4_link_feasibility/")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"❌ 目錄不存在: {directory}")
        sys.exit(1)

    print("🔍 開始學術合規性檢查...")
    print(f"📂 目標目錄: {directory}")
    print("")

    checker = AcademicComplianceChecker()
    results = checker.check_directory(directory)

    report = checker.generate_report(results)
    print(report)

    # 如果有 CRITICAL 違規，返回非零退出碼
    critical_count = sum(
        1 for violations in results.values()
        for v in violations if v.severity == 'CRITICAL'
    )

    if critical_count > 0:
        print("")
        print(f"❌ 發現 {critical_count} 個 CRITICAL 違規，請修正後再提交")
        sys.exit(1)
    else:
        print("")
        print("✅ 學術合規性檢查通過")
        sys.exit(0)


if __name__ == '__main__':
    main()
