#!/usr/bin/env python3
"""
Stage 2 驗證快照回退機制檢查工具 - Fail-Fast 原則驗證
專門檢查驗證快照生成和驗證邏輯中的回退機制
"""
import re
import os

print("=" * 80)
print("Stage 2 驗證快照回退機制檢查 - Fail-Fast 原則驗證")
print("=" * 80)
print()

# Stage 2 驗證快照相關文件
validation_files = [
    'src/stages/stage2_orbital_computing/stage2_validator.py',
    'scripts/stage_validators/stage2_validator.py',
]

all_issues = []

def check_file(filepath):
    """檢查單個文件的回退機制"""
    print(f"\n【檢查文件】{filepath}")
    print("-" * 80)
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    file_issues = []
    
    # 1. 檢查 metadata = result_data.get('metadata', {})
    pattern = r'metadata\s*=\s*\w+\.get\(["\']metadata["\']\s*,\s*\{\}\)'
    for match in re.finditer(pattern, content):
        line_num = content[:match.start()].count('\n') + 1
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 5)
        context_lines = lines[context_start:context_end]
        
        # 檢查後續是否有 Fail-Fast 檢查
        has_failfast_check = False
        for ctx_line in context_lines:
            if 'raise' in ctx_line and 'metadata' in ctx_line:
                has_failfast_check = True
                break
            if 'not in metadata' in ctx_line or 'metadata缺少' in ctx_line:
                has_failfast_check = True
                break
        
        if not has_failfast_check:
            file_issues.append({
                'type': 'metadata_empty_dict_fallback',
                'line': line_num,
                'severity': 'high',
                'code': lines[line_num - 1].strip(),
                'message': f"Line {line_num}: metadata 使用空字典預設值，且後續未見 Fail-Fast 檢查"
            })
    
    # 2. 檢查驗證快照保存方法中的 .get() 回退
    # 找到 save_validation_snapshot 方法
    save_method_pattern = r'def save_validation_snapshot.*?(?=\n    def |\n\nclass |\Z)'
    save_method_match = re.search(save_method_pattern, content, re.DOTALL)
    
    if save_method_match:
        save_method_content = save_method_match.group()
        save_method_start = content[:save_method_match.start()].count('\n') + 1
        
        # 檢查 save_validation_snapshot 中的 .get() 預設值
        get_pattern = r'\.get\(["\']([^"\']+)["\']\s*,\s*([^)]+)\)'
        for match in re.finditer(get_pattern, save_method_content):
            field_name = match.group(1)
            default_value = match.group(2).strip()
            line_num_in_method = save_method_content[:match.start()].count('\n')
            actual_line = save_method_start + line_num_in_method
            
            # 排除合理的預設值
            reasonable_defaults = ['{}', '[]', '0', 'False', 'True', "''", '""']
            if default_value in reasonable_defaults:
                continue
            
            # 關鍵欄位不應有預設值
            critical_fields = [
                'processing_duration_seconds',
                'total_satellites_processed',
                'total_teme_positions',
                'checks_performed',
                'checks_passed',
                'overall_status'
            ]
            
            if field_name in critical_fields:
                file_issues.append({
                    'type': 'critical_field_with_default',
                    'line': actual_line,
                    'severity': 'high',
                    'field': field_name,
                    'default': default_value,
                    'message': f"Line {actual_line}: 關鍵欄位 '{field_name}' 使用預設值 {default_value}"
                })
    
    # 3. 檢查驗證方法中的 .get() 預設值
    # 找到 perform_stage_specific_validation 或類似方法
    validation_method_pattern = r'def (perform_stage_specific_validation|_validate_legacy_format|_check_\w+).*?(?=\n    def |\n\nclass |\Z)'
    for match in re.finditer(validation_method_pattern, content, re.DOTALL):
        method_content = match.group()
        method_start = content[:match.start()].count('\n') + 1
        method_name = match.group(1)
        
        # 檢查方法中的 .get() 預設值
        get_pattern = r'\.get\(["\']([^"\']+)["\']\s*,\s*([^)]+)\)'
        for get_match in re.finditer(get_pattern, method_content):
            field_name = get_match.group(1)
            default_value = get_match.group(2).strip()
            line_num_in_method = method_content[:get_match.start()].count('\n')
            actual_line = method_start + line_num_in_method
            
            # 關鍵驗證欄位不應有預設值
            critical_validation_fields = [
                'total_satellites_processed',
                'successful_propagations',
                'total_teme_positions',
                'validation_passed',
                'overall_status'
            ]
            
            if field_name in critical_validation_fields and default_value not in ['None', '{}', '[]']:
                file_issues.append({
                    'type': 'validation_field_with_default',
                    'line': actual_line,
                    'severity': 'medium',
                    'field': field_name,
                    'default': default_value,
                    'method': method_name,
                    'message': f"Line {actual_line}: 驗證方法 {method_name} 中，欄位 '{field_name}' 使用預設值 {default_value}"
                })
    
    return file_issues

# 執行檢查
for filepath in validation_files:
    file_issues = check_file(filepath)
    all_issues.extend(file_issues)

# 輸出結果
print("\n" + "=" * 80)
print("檢查結果摘要")
print("=" * 80)
print()

if all_issues:
    print("【發現的問題】")
    print("-" * 80)
    
    # 按嚴重性分組
    high_severity = [i for i in all_issues if i['severity'] == 'high']
    medium_severity = [i for i in all_issues if i['severity'] == 'medium']
    
    if high_severity:
        print("\n🚨 高嚴重性（違反 Fail-Fast 原則）:")
        for issue in high_severity:
            print(f"   ❌ {issue['message']}")
            if 'code' in issue:
                print(f"      代碼: {issue['code']}")
    
    if medium_severity:
        print("\n⚠️  中等嚴重性（需要審查）:")
        for issue in medium_severity:
            print(f"   ⚠️  {issue['message']}")
    print()
else:
    print("✅ 未發現違反 Fail-Fast 原則的回退機制")
    print()

# 總結
print("=" * 80)
print("總結")
print("=" * 80)
print(f"檢查文件數: {len(validation_files)}")
print(f"發現問題: {len(all_issues)}")
if all_issues:
    print(f"  - 高嚴重性: {len([i for i in all_issues if i['severity'] == 'high'])}")
    print(f"  - 中等嚴重性: {len([i for i in all_issues if i['severity'] == 'medium'])}")
print()

if all_issues:
    high_count = len([i for i in all_issues if i['severity'] == 'high'])
    if high_count > 0:
        print(f"⚠️  發現 {high_count} 個高嚴重性問題，需要修復")
    else:
        print("⚠️  發現中等嚴重性問題，建議審查")
else:
    print("✅ Stage 2 驗證快照完全符合 Fail-Fast 原則")
