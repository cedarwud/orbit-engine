#!/usr/bin/env python3
"""
Stage 2 回退機制檢查工具 - Fail-Fast 原則驗證
檢查是否有不當的回退機制掩蓋問題
"""
import re
import os

print("=" * 80)
print("Stage 2 回退機制深度檢查 - Fail-Fast 原則驗證")
print("=" * 80)
print()

# Stage 2 相關文件列表
stage2_files = [
    'src/stages/stage2_orbital_computing/sgp4_calculator.py',
    'src/stages/stage2_orbital_computing/stage2_orbital_computing_processor.py',
    'src/stages/stage2_orbital_computing/unified_time_window_manager.py',
    'src/stages/stage2_orbital_computing/stage2_validator.py',
    'src/stages/stage2_orbital_computing/stage2_result_manager.py',
]

# 回退機制模式
fallback_patterns = [
    # Pattern 1: .get() with default value
    (r'\.get\([\'"]([^\'\"]+)[\'\"],\s*([^)]+)\)', 'get() 帶預設值'),
    
    # Pattern 2: or operator for fallback
    (r'(\w+)\s*=\s*([^=\s]+)\s+or\s+([^\n;]+)', 'or 運算符回退'),
    
    # Pattern 3: if not x: x = default
    (r'if\s+not\s+(\w+):\s*\n\s*\1\s*=\s*([^\n]+)', 'if not 條件設定預設值'),
    
    # Pattern 4: try-except with return/continue
    (r'except[^:]*:\s*\n(?:\s*#[^\n]*\n)*\s*(return|continue)\s', 'try-except 後繼續執行'),
]

all_issues = []
all_compliant = []

def check_file(filepath):
    """檢查單個文件的回退機制"""
    print(f"\n【檢查文件】{filepath}")
    print("-" * 80)
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在")
        return [], []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    file_issues = []
    file_compliant = []
    
    # 檢查 Pattern 1: .get() 帶預設值
    get_pattern = r'\.get\([\'"]([^\'\"]+)[\'\"],\s*([^)]+)\)'
    for match in re.finditer(get_pattern, content):
        field_name = match.group(1)
        default_value = match.group(2)
        line_num = content[:match.start()].count('\n') + 1
        
        # 跳過註釋行
        line_content = lines[line_num - 1].strip()
        if line_content.startswith('#'):
            continue
        
        # 檢查是否有 Fail-Fast 註釋說明
        context_start = max(0, line_num - 5)
        context = '\n'.join(lines[context_start:line_num + 2])
        
        # 檢查上下文是否有合理性說明
        has_justification = any([
            'optional' in context.lower(),
            '可選' in context,
            '非必要' in context,
            'default' in context.lower(),
            '預設' in context,
            'backward' in context.lower(),
            '向後兼容' in context,
            '容錯' in context,
        ])
        
        if not has_justification and default_value not in ['None', '{}', '[]', "''", '""', '0', 'False']:
            file_issues.append({
                'type': 'get_with_default',
                'line': line_num,
                'field': field_name,
                'default': default_value,
                'severity': 'high',
                'message': f"Line {line_num}: .get('{field_name}', {default_value}) - 可能掩蓋必要數據缺失"
            })
        else:
            file_compliant.append({
                'line': line_num,
                'reason': '合理預設值或有說明'
            })
    
    # 檢查 Pattern 2: or 運算符回退
    or_pattern = r'(\w+)\s*=\s*([^=\s]+)\s+or\s+([^\n;]+)'
    for match in re.finditer(or_pattern, content):
        var_name = match.group(1)
        source = match.group(2)
        fallback = match.group(3).strip()
        line_num = content[:match.start()].count('\n') + 1
        
        # 跳過註釋行
        line_content = lines[line_num - 1].strip()
        if line_content.startswith('#'):
            continue
        
        # 檢查是否是合理的多來源回退（例: line1 or tle_line1）
        if 'tle' in source.lower() and 'tle' in fallback.lower():
            file_compliant.append({
                'line': line_num,
                'reason': '多來源欄位名稱回退（合理）'
            })
            continue
        
        # 其他 or 回退需要檢查
        file_issues.append({
            'type': 'or_fallback',
            'line': line_num,
            'var': var_name,
            'source': source,
            'fallback': fallback,
            'severity': 'medium',
            'message': f"Line {line_num}: {var_name} = {source} or {fallback} - 可能掩蓋問題"
        })
    
    # 檢查 Pattern 3: try-except 後 return None 或 continue
    try_except_pattern = r'except[^:]*:\s*\n((?:\s*#[^\n]*\n|\s*self\.logger[^\n]*\n)*)\s*(return\s+None|continue)'
    for match in re.finditer(try_except_pattern, content, re.MULTILINE):
        line_num = content[:match.start()].count('\n') + 1
        action = match.group(2).strip()
        comments = match.group(1).strip()
        
        # 檢查是否有批次處理容錯說明
        context_start = max(0, line_num - 10)
        context = '\n'.join(lines[context_start:line_num + 5])
        
        is_batch_tolerance = any([
            '批次處理' in context,
            '批次容錯' in context,
            'batch' in context.lower(),
            '單顆衛星失敗' in context,
            'single satellite' in context.lower(),
        ])
        
        if is_batch_tolerance:
            file_compliant.append({
                'line': line_num,
                'reason': f'批次處理容錯（{action}）- 合理'
            })
        else:
            file_issues.append({
                'type': 'try_except_continue',
                'line': line_num,
                'action': action,
                'severity': 'high',
                'message': f"Line {line_num}: except → {action} - 可能掩蓋系統性錯誤"
            })
    
    return file_issues, file_compliant

# 執行檢查
all_issues = []
all_compliant = []

for filepath in stage2_files:
    file_issues, file_compliant = check_file(filepath)
    all_issues.extend(file_issues)
    all_compliant.extend(file_compliant)

# 輸出結果
print("\n" + "=" * 80)
print("檢查結果摘要")
print("=" * 80)
print()

if all_issues:
    print("【發現的潛在問題】")
    print("-" * 80)
    
    # 按嚴重性分組
    high_severity = [i for i in all_issues if i['severity'] == 'high']
    medium_severity = [i for i in all_issues if i['severity'] == 'medium']
    
    if high_severity:
        print("\n🚨 高嚴重性（違反 Fail-Fast 原則）:")
        for issue in high_severity:
            print(f"   ❌ {issue['message']}")
    
    if medium_severity:
        print("\n⚠️  中等嚴重性（需要審查）:")
        for issue in medium_severity:
            print(f"   ⚠️  {issue['message']}")
    print()
else:
    print("✅ 未發現違反 Fail-Fast 原則的回退機制")
    print()

print("【合規項目】")
print("-" * 80)
for item in all_compliant[:15]:
    print(f"   ✅ Line {item['line']}: {item['reason']}")
if len(all_compliant) > 15:
    print(f"   ... 還有 {len(all_compliant) - 15} 項合規")
print()

# 總結
print("=" * 80)
print("總結")
print("=" * 80)
print(f"檢查文件數: {len(stage2_files)}")
print(f"發現潛在問題: {len(all_issues)}")
print(f"  - 高嚴重性: {len([i for i in all_issues if i['severity'] == 'high'])}")
print(f"  - 中等嚴重性: {len([i for i in all_issues if i['severity'] == 'medium'])}")
print(f"合規項目: {len(all_compliant)}")
print()

if all_issues:
    high_count = len([i for i in all_issues if i['severity'] == 'high'])
    if high_count > 0:
        print(f"⚠️  發現 {high_count} 個高嚴重性問題，需要修復")
    else:
        print("⚠️  發現中等嚴重性問題，建議審查")
else:
    print("✅ Stage 2 完全符合 Fail-Fast 原則")
