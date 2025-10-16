#!/usr/bin/env python3
"""
系統性檢查 Stage 3 代碼中的所有回退機制

檢查項目:
1. 異常處理後返回默認值
2. 異常處理後回退到簡化算法
3. 硬編碼回退值
4. 靜默失敗（僅記錄日誌但繼續）
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple

def find_fallback_patterns(file_path: Path) -> List[Dict]:
    """查找可疑的回退模式"""
    violations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 查找 try-except 塊
    in_except = False
    except_start = 0
    indent_level = 0

    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()

        # 檢測 except 塊開始
        if re.match(r'except\s+.*:', stripped):
            in_except = True
            except_start = i
            indent_level = len(line) - len(stripped)
            continue

        if in_except:
            # 檢測 except 塊結束（縮進回退）
            current_indent = len(line) - len(line.lstrip())
            if stripped and current_indent <= indent_level:
                in_except = False
                continue

            # 檢查可疑模式
            # 模式 1: return 默認值
            if re.search(r'return\s+', stripped):
                # 排除 raise 語句
                if not re.search(r'raise\s+', stripped):
                    violations.append({
                        'file': str(file_path),
                        'line': i,
                        'type': 'RETURN_IN_EXCEPT',
                        'code': line.rstrip(),
                        'severity': 'HIGH' if any(keyword in stripped.lower() for keyword in
                                                   ['none', '0', '[]', '{}', 'false', 'true', '-90', 'eye(3)']) else 'MEDIUM'
                    })

            # 模式 2: 回退註釋
            if re.search(r'回退|fallback|降級|degrade|簡化|simplified|預設|default', stripped, re.IGNORECASE):
                violations.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'FALLBACK_COMMENT',
                    'code': line.rstrip(),
                    'severity': 'HIGH'
                })

            # 模式 3: 僅 log.warning/error 但不 raise
            if re.search(r'(log\w*\.(warning|error)|logger\.(warning|error))', stripped):
                # 檢查後續是否有 raise
                has_raise = False
                for j in range(i, min(i+5, len(lines))):
                    if 'raise' in lines[j]:
                        has_raise = True
                        break
                if not has_raise:
                    violations.append({
                        'file': str(file_path),
                        'line': i,
                        'type': 'LOG_WITHOUT_RAISE',
                        'code': line.rstrip(),
                        'severity': 'MEDIUM'
                    })

    return violations


def check_hardcoded_fallbacks(file_path: Path) -> List[Dict]:
    """檢查硬編碼的回退值"""
    violations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 可疑的硬編碼模式
    suspicious_patterns = [
        (r'=\s*8\s*$', '硬編碼回退值: 8'),
        (r'=\s*0\.0\s*$', '硬編碼回退值: 0.0'),
        (r'=\s*-90\.0', '假數據: -90.0 度'),
        (r'np\.eye\(3\)', '單位矩陣回退'),
        (r'=\s*\[\]\s*$', '空列表回退'),
        (r'=\s*\{\}\s*$', '空字典回退'),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, desc in suspicious_patterns:
            if re.search(pattern, line):
                # 排除註釋行
                if not line.lstrip().startswith('#'):
                    violations.append({
                        'file': str(file_path),
                        'line': i,
                        'type': 'HARDCODED_FALLBACK',
                        'code': line.rstrip(),
                        'description': desc,
                        'severity': 'HIGH'
                    })

    return violations


def main():
    """主函數"""
    print("=" * 80)
    print("Stage 3 Fail-Fast 合規性檢查")
    print("=" * 80)

    # Stage 3 相關文件
    stage3_files = [
        'src/shared/coordinate_systems/skyfield_coordinate_engine.py',
        'src/shared/coordinate_systems/iers_data_manager.py',
        'src/shared/coordinate_systems/wgs84_manager.py',
        'src/stages/stage3_coordinate_transformation/stage3_coordinate_transform_processor.py',
        'src/stages/stage3_coordinate_transformation/stage3_transformation_engine.py',
        'src/stages/stage3_coordinate_transformation/stage3_results_manager.py',
    ]

    all_violations = []

    for file_path_str in stage3_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue

        print(f"\n檢查: {file_path}")
        print("-" * 80)

        # 查找回退模式
        fallback_violations = find_fallback_patterns(file_path)
        hardcoded_violations = check_hardcoded_fallbacks(file_path)

        file_violations = fallback_violations + hardcoded_violations

        if file_violations:
            print(f"⚠️  發現 {len(file_violations)} 個可疑模式")
            all_violations.extend(file_violations)
        else:
            print("✅ 未發現可疑模式")

    # 彙總報告
    print("\n" + "=" * 80)
    print("檢查結果彙總")
    print("=" * 80)

    if not all_violations:
        print("✅ 未發現 Fail-Fast 違規")
        return 0

    # 按嚴重程度分組
    high_severity = [v for v in all_violations if v['severity'] == 'HIGH']
    medium_severity = [v for v in all_violations if v['severity'] == 'MEDIUM']

    print(f"\n高嚴重度問題: {len(high_severity)} 個")
    print(f"中等嚴重度問題: {len(medium_severity)} 個")
    print(f"總計: {len(all_violations)} 個")

    # 顯示高嚴重度問題
    if high_severity:
        print("\n" + "=" * 80)
        print("🚨 高嚴重度問題 (必須修復)")
        print("=" * 80)

        for i, v in enumerate(high_severity, 1):
            print(f"\n#{i} {v['type']}")
            print(f"文件: {v['file']}:{v['line']}")
            print(f"代碼: {v['code']}")
            if 'description' in v:
                print(f"說明: {v['description']}")

    # 顯示中等嚴重度問題（僅前10個）
    if medium_severity:
        print("\n" + "=" * 80)
        print("⚠️  中等嚴重度問題 (需要審查)")
        print("=" * 80)

        for i, v in enumerate(medium_severity[:10], 1):
            print(f"\n#{i} {v['type']}")
            print(f"文件: {v['file']}:{v['line']}")
            print(f"代碼: {v['code']}")

        if len(medium_severity) > 10:
            print(f"\n... 還有 {len(medium_severity) - 10} 個中等嚴重度問題")

    return 1


if __name__ == "__main__":
    exit(main())
