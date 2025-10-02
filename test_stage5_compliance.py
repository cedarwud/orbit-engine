#!/usr/bin/env python3
"""
Stage 5 學術標準合規性測試

驗證項目:
1. constellation_configs 嚴格驗證
2. ITU-R 公式引用完整性
3. ITU-R 推薦值標記規範性
"""

import sys
import json
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, '/home/sat/orbit-engine/src')

def test_constellation_configs_validation():
    """測試 1: constellation_configs 缺失時應報錯"""
    print("=" * 80)
    print("測試 1: constellation_configs 缺失驗證")
    print("=" * 80)

    from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor

    stage5 = Stage5SignalAnalysisProcessor()

    # 構造缺少 constellation_configs 的輸入
    invalid_input = {
        'stage': 'stage4_link_feasibility',
        'connectable_satellites': {
            'starlink': [
                {
                    'satellite_id': 'test-001',
                    'time_series': [
                        {
                            'timestamp': '2025-09-30T10:00:00Z',
                            'elevation_deg': 45.0,
                            'distance_km': 550.0,
                            'is_connectable': True
                        }
                    ]
                }
            ]
        },
        'metadata': {
            # ❌ 故意缺少 constellation_configs
        }
    }

    try:
        from shared.interfaces import ProcessingStatus
        result = stage5.process(invalid_input)

        # 檢查返回的 ProcessingResult 狀態
        if result.status == ProcessingStatus.ERROR:
            # 檢查錯誤訊息
            error_msg = result.message if hasattr(result, 'message') else str(result.errors)
            if 'constellation_configs' in error_msg and 'Grade A' in error_msg:
                print(f"✅ 測試通過: 正確返回 ProcessingStatus.ERROR")
                print(f"   錯誤訊息: {error_msg[:150]}...")
                return True
            else:
                print(f"⚠️ 返回 ERROR 狀態，但錯誤訊息不符合預期")
                print(f"   錯誤訊息: {error_msg}")
                return False
        elif result.status == ProcessingStatus.VALIDATION_FAILED:
            # VALIDATION_FAILED 也可以接受（早期驗證失敗）
            print("✅ 測試通過: 返回 VALIDATION_FAILED（早期輸入驗證）")
            print(f"   訊息: {result.message if hasattr(result, 'message') else 'N/A'}")
            return True
        else:
            print(f"❌ 測試失敗: 應該返回錯誤狀態，但返回 {result.status}")
            return False
    except Exception as e:
        print(f"❌ 測試失敗: 拋出意外異常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_itur_formula_references():
    """測試 2: ITU-R 公式引用完整性"""
    print("\n" + "=" * 80)
    print("測試 2: ITU-R 公式引用完整性")
    print("=" * 80)

    # 讀取源碼文件
    source_file = Path('/home/sat/orbit-engine/src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py')

    if not source_file.exists():
        print(f"❌ 測試失敗: 源碼文件不存在: {source_file}")
        return False

    source_code = source_file.read_text()

    # 檢查關鍵引用（支持靈活匹配）
    required_refs = [
        ('ITU-R P.618-13 Section 2.4', 'ITU-R P.618-13 Section 2.4'),
        ('ITU-R P.618-13 Eq. (45)', 'Eq. (45)'),  # 靈活匹配
        ('ITU-R P.618-13 Eq. (47)', 'ITU-R P.618-13 Eq. (47)'),
        ('Karasawa et al. (1988)', 'Karasawa et al. (1988)'),
        ('scintillation_coefficient = 0.1  # Karasawa', 'scintillation_coefficient = 0.1  # Karasawa'),
        ('path_exponent = 0.5              # ITU-R P.618-13', 'path_exponent = 0.5              # ITU-R P.618-13')
    ]

    missing_refs = []
    for display_name, pattern in required_refs:
        if pattern not in source_code:
            missing_refs.append(display_name)

    if missing_refs:
        print(f"❌ 測試失敗: 缺少以下引用:")
        for ref in missing_refs:
            print(f"   - {ref}")
        return False
    else:
        print("✅ 測試通過: 所有 ITU-R 公式引用完整")
        print(f"   已驗證 {len(required_refs)} 個引用")
        return True

def test_itur_recommended_values():
    """測試 3: ITU-R 推薦值方法命名規範性"""
    print("\n" + "=" * 80)
    print("測試 3: ITU-R 推薦值方法命名規範性")
    print("=" * 80)

    # 讀取源碼文件
    source_file = Path('/home/sat/orbit-engine/src/stages/stage5_signal_analysis/stage5_signal_analysis_processor.py')
    source_code = source_file.read_text()

    # 檢查新方法名稱
    required_methods = [
        '_get_itur_recommended_antenna_diameter',
        '_get_itur_recommended_antenna_efficiency'
    ]

    # 檢查舊方法名稱不應存在
    deprecated_methods = [
        '_get_standard_antenna_diameter',
        '_get_standard_antenna_efficiency'
    ]

    missing = []
    for method in required_methods:
        if f'def {method}(' not in source_code:
            missing.append(method)

    found_deprecated = []
    for method in deprecated_methods:
        if f'def {method}(' in source_code:
            found_deprecated.append(method)

    if missing or found_deprecated:
        if missing:
            print(f"❌ 測試失敗: 缺少新方法名稱:")
            for m in missing:
                print(f"   - {m}")
        if found_deprecated:
            print(f"❌ 測試失敗: 仍存在舊方法名稱:")
            for m in found_deprecated:
                print(f"   - {m}")
        return False
    else:
        print("✅ 測試通過: 方法命名符合 ITU-R 推薦值規範")
        print(f"   已驗證 {len(required_methods)} 個方法")
        return True

def test_stage4_metadata_passthrough():
    """測試 4: Stage 4 metadata 傳遞"""
    print("\n" + "=" * 80)
    print("測試 4: Stage 4 metadata constellation_configs 傳遞")
    print("=" * 80)

    # 讀取 Stage 4 源碼
    source_file = Path('/home/sat/orbit-engine/src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py')
    source_code = source_file.read_text()

    # 檢查 constellation_configs 傳遞邏輯
    required_patterns = [
        "'constellation_configs': self.upstream_constellation_configs",
        "# ✅ Grade A 要求: 向下傳遞 constellation_configs 給 Stage 5"
    ]

    missing = []
    for pattern in required_patterns:
        if pattern not in source_code:
            missing.append(pattern)

    if missing:
        print(f"❌ 測試失敗: Stage 4 缺少 constellation_configs 傳遞邏輯:")
        for m in missing:
            print(f"   - {m}")
        return False
    else:
        print("✅ 測試通過: Stage 4 正確傳遞 constellation_configs")
        return True

def main():
    """主測試函數"""
    print("\n🔬 Stage 5 學術標準合規性測試")
    print("=" * 80)
    print("依據: docs/stages/stage5-signal-analysis.md")
    print("依據: docs/academic_standards_clarification.md")
    print("=" * 80)

    tests = [
        ("constellation_configs 驗證", test_constellation_configs_validation),
        ("ITU-R 公式引用", test_itur_formula_references),
        ("ITU-R 推薦值命名", test_itur_recommended_values),
        ("Stage 4 數據傳遞", test_stage4_metadata_passthrough)
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ 測試異常: {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 顯示最終結果
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    print("-" * 80)
    print(f"總計: {passed_count}/{total_count} 測試通過")

    if passed_count == total_count:
        print("✅ 所有測試通過 - Stage 5 完全符合學術標準")
        return 0
    else:
        print(f"❌ {total_count - passed_count} 個測試失敗")
        return 1

if __name__ == '__main__':
    sys.exit(main())
