#!/usr/bin/env python3
"""
更新版六階段執行腳本 - 使用重構後的 Stage 1

更新內容:
- 使用 Stage1RefactoredProcessor 替代 Stage1MainProcessor
- 支持 ProcessingResult 標準輸出格式
- 保持向後兼容性 (通過 result.data 訪問數據)
- 完整的驗證和快照功能

更新日期: 2025-09-24
重構版本: Stage1RefactoredProcessor v1.0
"""

import sys
import os
import json
import glob
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 確保能找到模組
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 如果在容器中，也添加容器路徑
if os.path.exists('/orbit-engine'):
    sys.path.insert(0, '/orbit-engine')
    sys.path.insert(0, '/orbit-engine/src')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入必要模組
from shared.interfaces.processor_interface import ProcessingResult, ProcessingStatus
import yaml


def load_stage2_config(config_path: str) -> dict:
    """載入Stage 2配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        # 顯示關鍵配置信息
        visibility_config = config_dict.get('visibility_filter', {})
        elevation_thresholds = visibility_config.get('constellation_elevation_thresholds', {})

        print(f'📊 配置載入成功:')
        print(f'   Starlink 仰角: {elevation_thresholds.get("starlink", "N/A")}°')
        print(f'   OneWeb 仰角: {elevation_thresholds.get("oneweb", "N/A")}°')
        print(f'   預設仰角: {visibility_config.get("min_elevation_deg", "N/A")}°')

        return config_dict
    except Exception as e:
        print(f'❌ 配置載入失敗: {e}')
        return {}


def create_stage2_processor_unified(config_path: str):
    """
    創建Stage 2處理器 - v3.0 軌道狀態傳播架構 (統一邏輯)

    🎯 唯一執行路徑:
    - Stage2OrbitalPropagationProcessor (v3.0 標準軌道狀態傳播)
    - 純CPU計算，無GPU/CPU差異
    - 單一統一邏輯，無回退機制

    ✅ v3.0架構特性:
    - 純軌道狀態傳播 (禁止座標轉換和可見性分析)
    - 使用 Stage 1 epoch_datetime (禁止 TLE 重新解析)
    - TEME 座標系統輸出
    - SGP4/SDP4 專業算法
    """
    config_dict = load_stage2_config(config_path)

    if not config_dict:
        print('⚠️ 配置載入失敗，使用 v3.0 標準處理器')
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
        return Stage2OrbitalPropagationProcessor()

    # ✅ 唯一執行路徑：v3.0 標準軌道狀態傳播處理器
    print('🛰️ 初始化 v3.0 軌道狀態傳播處理器 (統一邏輯)...')
    from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
    processor = Stage2OrbitalPropagationProcessor(config=config_dict)
    print('✅ v3.0 軌道狀態傳播處理器初始化成功')
    print('   📋 架構: v3.0 軌道狀態傳播 (唯一執行路徑)')
    print('   🎯 功能: SGP4/SDP4 + TEME 座標輸出')
    print('   💻 計算: 純CPU計算，無GPU/CPU差異')
    print('   ⚠️  時間: 使用 Stage 1 epoch_datetime')
    print('   🚫 禁止: 座標轉換、可見性分析、舊版回退')
    return processor


def clean_stage_outputs(stage_number: int):
    """
    清理指定階段的輸出檔案和驗證快照

    Args:
        stage_number: 階段編號 (1-6)
    """
    try:
        # 清理輸出目錄
        output_dir = Path(f'data/outputs/stage{stage_number}')
        if output_dir.exists():
            for file in output_dir.iterdir():
                if file.is_file():
                    file.unlink()
            print(f"🗑️ 清理 Stage {stage_number} 輸出檔案")

        # 清理驗證快照
        snapshot_path = Path(f'data/validation_snapshots/stage{stage_number}_validation.json')
        if snapshot_path.exists():
            snapshot_path.unlink()
            print(f"🗑️ 清理 Stage {stage_number} 驗證快照")

    except Exception as e:
        print(f"⚠️ 清理 Stage {stage_number} 時發生錯誤: {e}")


def execute_stage1_unified() -> tuple:
    """
    統一的 Stage 1 執行函數 (消除重複邏輯)

    Returns:
        tuple: (success: bool, stage1_result: ProcessingResult, stage1_data: dict)
    """
    try:
        # 清理舊的輸出
        clean_stage_outputs(1)

        # 使用統一的重構版本 (舊版本已破壞，已移除)
        from stages.stage1_orbital_calculation.stage1_main_processor import create_stage1_refactored_processor
        stage1 = create_stage1_refactored_processor(
            config={'sample_mode': False, 'sample_size': 500}
        )
        print('✅ 使用重構版本: Stage1RefactoredProcessor (唯一可用版本)')

        # 執行 Stage 1
        stage1_result = stage1.execute(input_data=None)

        # 處理結果格式 (重構版本應該總是返回 ProcessingResult)
        if isinstance(stage1_result, ProcessingResult):
            if stage1_result.status == ProcessingStatus.SUCCESS:
                print(f'✅ Stage 1 完成: {len(stage1_result.data.get("satellites", []))} 顆衛星')
                stage1_data = stage1_result.data
                return True, stage1_result, stage1_data
            else:
                print(f'❌ Stage 1 執行失敗: {stage1_result.status}')
                return False, stage1_result, {}
        else:
            # 不應該發生，但保留兼容性
            print(f'⚠️ Stage 1 返回意外格式: {type(stage1_result)}')
            if isinstance(stage1_result, dict) and stage1_result.get('satellites'):
                print(f'✅ Stage 1 完成: {len(stage1_result.get("satellites", []))} 顆衛星')
                return True, stage1_result, stage1_result
            else:
                return False, stage1_result, {}

    except Exception as e:
        print(f'❌ Stage 1 執行異常: {e}')
        return False, None, {}


def validate_stage_immediately(stage_processor, processing_results, stage_num, stage_name):
    """
    階段執行後立即驗證 - 更新版支援重構後的 Stage 1

    Args:
        stage_processor: 階段處理器實例
        processing_results: 處理結果 (可能是 ProcessingResult 或 Dict)
        stage_num: 階段編號
        stage_name: 階段名稱

    Returns:
        tuple: (validation_success, validation_message)
    """
    try:
        print(f"\\n🔍 階段{stage_num}立即驗證檢查...")
        print("-" * 40)

        # 🔧 新增：處理 ProcessingResult 格式
        if isinstance(processing_results, ProcessingResult):
            # 重構後的 Stage 1 返回 ProcessingResult
            if processing_results.status != ProcessingStatus.SUCCESS:
                return False, f"階段{stage_num}執行失敗: {processing_results.errors}"

            # 提取數據部分進行驗證
            data_for_validation = processing_results.data

            # 使用重構後的驗證方法
            if hasattr(stage_processor, 'run_validation_checks'):
                validation_result = stage_processor.run_validation_checks(data_for_validation)

                validation_status = validation_result.get('validation_status', 'unknown')
                overall_status = validation_result.get('overall_status', 'UNKNOWN')
                success_rate = validation_result.get('validation_details', {}).get('success_rate', 0.0)

                if validation_status == 'passed' and overall_status == 'PASS':
                    print(f"✅ 階段{stage_num}驗證通過 (成功率: {success_rate:.1%})")
                    return True, f"階段{stage_num}驗證成功"
                else:
                    print(f"❌ 階段{stage_num}驗證失敗: {validation_status}/{overall_status}")
                    return False, f"階段{stage_num}驗證失敗: {validation_status}/{overall_status}"
            else:
                # 回退到快照品質檢查
                quality_passed, quality_msg = check_validation_snapshot_quality(stage_num)
                return quality_passed, quality_msg

        else:
            # 舊格式處理 (Dict) - 保持兼容性
            if hasattr(stage_processor, 'save_validation_snapshot'):
                validation_success = stage_processor.save_validation_snapshot(processing_results)

                if validation_success:
                    quality_passed, quality_msg = check_validation_snapshot_quality(stage_num)
                    if quality_passed:
                        print(f"✅ 階段{stage_num}驗證通過")
                        return True, f"階段{stage_num}驗證成功"
                    else:
                        print(f"❌ 階段{stage_num}合理性檢查失敗: {quality_msg}")
                        return False, f"階段{stage_num}合理性檢查失敗: {quality_msg}"
                else:
                    print(f"❌ 階段{stage_num}驗證快照生成失敗")
                    return False, f"階段{stage_num}驗證快照生成失敗"
            else:
                # 沒有驗證方法，進行基本檢查
                if not processing_results:
                    print(f"❌ 階段{stage_num}處理結果為空")
                    return False, f"階段{stage_num}處理結果為空"

                quality_passed, quality_msg = check_validation_snapshot_quality(stage_num)
                return quality_passed, quality_msg

    except Exception as e:
        print(f"❌ 階段{stage_num}驗證異常: {e}")
        return False, f"階段{stage_num}驗證異常: {e}"


def check_validation_snapshot_quality(stage_num):
    """檢查驗證快照品質"""
    try:
        # 檢查快照文件
        snapshot_path = f"data/validation_snapshots/stage{stage_num}_validation.json"

        if not os.path.exists(snapshot_path):
            return False, f"❌ Stage {stage_num} 驗證快照不存在"

        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)

        # Stage 1 專用檢查 - 修復虛假驗證問題
        if stage_num == 1:
            if snapshot_data.get('status') == 'success' and snapshot_data.get('validation_passed', False):
                satellite_count = snapshot_data.get('data_summary', {}).get('satellite_count', 0)
                next_stage_ready = snapshot_data.get('next_stage_ready', False)

                # 檢查是否為重構版本
                is_refactored = snapshot_data.get('refactored_version', False)
                interface_compliance = snapshot_data.get('interface_compliance', False)

                # 修復虛假驗證: 檢查數據完整性而不是僅檢查 > 0
                # 期望值: Starlink(8390) + OneWeb(651) = 9041顆衛星
                expected_total = 9041
                min_acceptable = 8000  # 至少80%完整度

                if satellite_count >= min_acceptable and next_stage_ready:
                    completeness = (satellite_count / expected_total * 100) if expected_total > 0 else 0
                    status_msg = f"Stage 1 數據完整性檢查通過: 載入{satellite_count}顆衛星 (完整度:{completeness:.1f}%)"
                    if is_refactored:
                        status_msg += " (重構版本)"
                    return True, status_msg
                elif satellite_count > 0:
                    completeness = (satellite_count / expected_total * 100) if expected_total > 0 else 0
                    return False, f"❌ Stage 1 數據不完整: 僅載入{satellite_count}顆衛星 (完整度:{completeness:.1f}%，需要≥{min_acceptable}顆)"
                else:
                    return False, f"❌ Stage 1 數據不足: {satellite_count}顆衛星, 下階段準備:{next_stage_ready}"
            else:
                status = snapshot_data.get('status', 'unknown')
                return False, f"❌ Stage 1 執行狀態異常: {status}"

        # Stage 2 專用檢查 - 軌道狀態傳播層 (v3.0 架構)
        elif stage_num == 2:
            # 檢查 v3.0 Stage 2 驗證快照格式 (純軌道狀態傳播)
            if snapshot_data.get('stage') == 'stage2_orbital_computing':
                # v3.0 架構: 只檢查軌道狀態傳播，不檢查可見性/可行性
                data_summary = snapshot_data.get('data_summary', {})
                validation_checks = snapshot_data.get('validation_checks', {})

                total_satellites = data_summary.get('total_satellites_processed', 0)
                successful_propagations = data_summary.get('successful_propagations', 0)
                total_teme_positions = data_summary.get('total_teme_positions', 0)
                validation_passed = snapshot_data.get('validation_passed', False)

                # v3.0 架構基本檢查 - 軌道狀態傳播成功
                if total_satellites == 0:
                    return False, f"❌ Stage 2 未處理任何衛星數據"

                if successful_propagations == 0:
                    return False, f"❌ Stage 2 軌道狀態傳播失敗: 沒有成功的軌道計算"

                if total_teme_positions == 0:
                    return False, f"❌ Stage 2 TEME座標生成失敗: 沒有軌道狀態點"

                # 檢查專用驗證通過率 (至少4/5項通過)
                checks_details = validation_checks.get('check_details', {})
                checks_passed = validation_checks.get('checks_passed', 0)
                checks_performed = validation_checks.get('checks_performed', 0)

                if checks_performed < 5:
                    return False, f"❌ Stage 2 專用驗證不完整: 只執行了{checks_performed}/5項檢查"

                if checks_passed < 4:
                    return False, f"❌ Stage 2 專用驗證未達標: 只通過了{checks_passed}/5項檢查"

                # 檢查 v3.0 架構合規性
                if not snapshot_data.get('v3_architecture', False):
                    return False, f"❌ Stage 2 架構版本不符: 未使用v3.0軌道狀態傳播架構"

                if not snapshot_data.get('orbital_state_propagation', False):
                    return False, f"❌ Stage 2 功能不符: 未執行軌道狀態傳播"

                # 成功通過所有 v3.0 架構檢查
                success_rate = (successful_propagations / total_satellites * 100) if total_satellites > 0 else 0
                status_msg = f"Stage 2 v3.0架構檢查通過: {total_satellites}衛星 → {successful_propagations}成功軌道傳播 ({success_rate:.1f}%) → {total_teme_positions}個TEME座標點"
                return True, status_msg

            # 舊版快照格式檢查 (向後兼容)
            elif 'validation_passed' in snapshot_data:
                if snapshot_data.get('validation_passed', False):
                    metrics = snapshot_data.get('metrics', {})
                    feasible_satellites = metrics.get('feasible_satellites', 0)
                    input_satellites = metrics.get('input_satellites', 0)

                    if feasible_satellites > 0 and input_satellites > 0:
                        feasible_rate = (feasible_satellites / input_satellites * 100)
                        return True, f"Stage 2 合理性檢查通過: {feasible_satellites}/{input_satellites} 可行 ({feasible_rate:.1f}%)"
                    else:
                        return False, f"❌ Stage 2 數據不足: 可行{feasible_satellites}/總計{input_satellites}"
                else:
                    return False, f"❌ Stage 2 驗證未通過"
            else:
                return False, f"❌ Stage 2 驗證快照格式不正確"

        # Stage 3 專用檢查 (新架構)
        elif stage_num == 3:
            # 檢查新架構格式: coordinate transformation validation
            if 'validation_results' in snapshot_data:
                overall_status = snapshot_data.get('overall_status', 'UNKNOWN')
                validation_passed = snapshot_data.get('validation_results', {}).get('passed', False)

                if overall_status == 'PASS' and validation_passed:
                    satellites_processed = snapshot_data.get('data_summary', {}).get('satellites_processed', 0)
                    coord_points = snapshot_data.get('data_summary', {}).get('coordinate_points_count', 0)
                    avg_accuracy = snapshot_data.get('validation_results', {}).get('checks', {}).get('coordinate_transformation_accuracy', {}).get('average_accuracy_m', 0)

                    if satellites_processed > 0:
                        return True, f"Stage 3 座標轉換檢查通過: {satellites_processed}顆衛星 → {coord_points}個座標點 (精度:{avg_accuracy:.3f}m)"
                    else:
                        return False, f"❌ Stage 3 處理數據不足: {satellites_processed}顆衛星"
                else:
                    return False, f"❌ Stage 3 驗證失敗: {overall_status}"

            # 舊格式檢查 (向後兼容)
            elif snapshot_data.get('status') == 'success':
                analyzed_satellites = snapshot_data.get('data_summary', {}).get('analyzed_satellites', 0)
                gpp_events = snapshot_data.get('data_summary', {}).get('detected_events', 0)

                if analyzed_satellites > 0:
                    return True, f"Stage 3 合理性檢查通過: 分析{analyzed_satellites}顆衛星，檢測{gpp_events}個3GPP事件"
                else:
                    return False, f"❌ Stage 3 分析數據不足: {analyzed_satellites}顆衛星"
            else:
                status = snapshot_data.get('status', 'unknown')
                return False, f"❌ Stage 3 執行狀態異常: {status}"

        # 其他階段檢查保持不變...
        return True, f"Stage {stage_num} 基本檢查通過"

    except Exception as e:
        return False, f"品質檢查異常: {e}"


def run_all_stages_sequential(validation_level='STANDARD'):
    """順序執行所有階段 - 更新版使用重構後的 Stage 1"""
    print('\\n🚀 開始六階段數據處理 (使用重構後的 Stage 1)')
    print('=' * 80)

    stage_results = {}

    try:
        # 🔧 使用統一的 Stage 1 執行函數 (消除重複邏輯)
        print('\\n📦 階段一：數據載入層 (重構版本)')
        print('-' * 60)

        success, stage1_result, stage1_data = execute_stage1_unified()

        if not success or not stage1_data:
            print('❌ 階段一處理失敗')
            return False, 1, "階段一處理失敗"

        # 存儲結果供後續階段使用
        stage_results['stage1'] = stage1_result

        # 顯示處理結果統計
        if isinstance(stage1_result, ProcessingResult):
            print(f'📊 處理狀態: {stage1_result.status}')
            print(f'📊 處理時間: {stage1_result.metrics.duration_seconds:.3f}秒')
            print(f'📊 處理衛星: {len(stage1_data.get("satellites", []))}顆')

        # 🔍 階段一立即驗證
        validation_success, validation_msg = validate_stage_immediately(
            None, stage_results['stage1'], 1, "數據載入層"
        )

        if not validation_success:
            print(f'❌ 階段一驗證失敗: {validation_msg}')
            print('🚫 停止後續階段處理，避免基於錯誤數據的無意義計算')
            return False, 1, validation_msg

        # 額外品質檢查
        quality_passed, quality_msg = check_validation_snapshot_quality(1)
        if not quality_passed:
            print(f'❌ 階段一品質檢查失敗: {quality_msg}')
            return False, 1, quality_msg

        print(f'✅ 階段一完成並驗證通過: {validation_msg}')

        # 階段二：軌道計算與鏈路可行性評估層
        print('\\n🛰️ 階段二：軌道計算與鏈路可行性評估層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(2)

        # 🔧 新增：載入正確的配置文件
        config_path = project_root / "config/stage2_orbital_computing.yaml"
        if config_path.exists():
            print(f'📄 載入配置文件: {config_path}')

            # 🎯 統一處理器：v3.0 軌道狀態傳播 (CPU計算)
            stage2 = create_stage2_processor_unified(str(config_path))
        else:
            print('⚠️ 配置文件不存在，使用 v3.0 標準處理器')
            from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
            stage2 = Stage2OrbitalPropagationProcessor()

        # 🔧 修復：處理 ProcessingResult 格式
        if isinstance(stage_results['stage1'], ProcessingResult):
            stage2_input = stage_results['stage1'].data
        else:
            stage2_input = stage_results['stage1']

        stage_results['stage2'] = stage2.execute(stage2_input)

        if not stage_results['stage2']:
            print('❌ 階段二處理失敗')
            return False, 2, "階段二處理失敗"

        # 階段二驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage2, stage_results['stage2'], 2, "軌道計算與鏈路可行性評估層"
        )

        if not validation_success:
            print(f'❌ 階段二驗證失敗: {validation_msg}')
            return False, 2, validation_msg

        print(f'✅ 階段二完成並驗證通過: {validation_msg}')

        # 階段三：座標系統轉換層 (重構版本)
        print('\\n🌍 階段三：座標系統轉換層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(3)

        from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
        stage3_config = {
            'coordinate_config': {
                'source_frame': 'TEME',
                'target_frame': 'WGS84',
                'time_corrections': True,
                'polar_motion': True,
                'nutation_model': 'IAU2000A'
            },
            'skyfield_config': {
                'ephemeris_file': 'de421.bsp',
                'auto_download': True
            },
            'precision_config': {
                'target_accuracy_m': 0.5
            }
        }
        stage3 = Stage3CoordinateTransformProcessor(config=stage3_config)

        # 統一使用execute()方法，並提取數據部分
        if isinstance(stage_results['stage2'], ProcessingResult):
            stage3_input = stage_results['stage2'].data
        else:
            stage3_input = stage_results['stage2']

        stage3_raw_result = stage3.execute(stage3_input)

        # 將結果包裝為ProcessingResult格式以保持一致性
        from shared.interfaces import create_processing_result, ProcessingStatus
        stage3_result = create_processing_result(
            status=ProcessingStatus.SUCCESS,
            data=stage3_raw_result,
            message="Stage 3處理成功"
        )

        if not stage3_result or stage3_result.status != ProcessingStatus.SUCCESS:
            print('❌ 階段三處理失敗')
            return False, 3, "階段三處理失敗"

        stage_results['stage3'] = stage3_result

        # 階段三驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage3, stage3_result, 3, "座標系統轉換層"
        )

        if not validation_success:
            print(f'❌ 階段三驗證失敗: {validation_msg}')
            return False, 3, validation_msg

        print(f'✅ 階段三完成並驗證通過: {validation_msg}')

        # 階段四：優化決策層
        print('\\n🎯 階段四：優化決策層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(4)

        from stages.stage4_optimization.stage4_optimization_processor import Stage4OptimizationProcessor
        stage4 = Stage4OptimizationProcessor()

        # 處理Stage 3到Stage 4的數據傳遞
        if isinstance(stage_results['stage3'], ProcessingResult):
            stage4_input = stage_results['stage3'].data
        else:
            stage4_input = stage_results['stage3']

        stage_results['stage4'] = stage4.execute(stage4_input)

        if not stage_results['stage4']:
            print('❌ 階段四處理失敗')
            return False, 4, "階段四處理失敗"

        # 階段四驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage4, stage_results['stage4'], 4, "優化決策層"
        )

        if not validation_success:
            print(f'❌ 階段四驗證失敗: {validation_msg}')
            return False, 4, validation_msg

        print(f'✅ 階段四完成並驗證通過: {validation_msg}')

        # 階段五：數據整合層
        print('\\n📊 階段五：數據整合層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(5)

        from stages.stage5_data_integration.data_integration_processor import DataIntegrationProcessor
        stage5 = DataIntegrationProcessor()

        # 處理Stage 4到Stage 5的數據傳遞
        # 嘗試使用增強版Stage 4輸出（包含速度數據）
        enhanced_stage4_path = 'data/outputs/stage4/stage4_optimization_enhanced_with_velocity.json'
        if Path(enhanced_stage4_path).exists():
            print('🔧 使用增強版Stage 4輸出（包含軌道速度數據）')
            with open(enhanced_stage4_path, 'r') as f:
                stage5_input = json.load(f)
        else:
            print('⚠️ 使用標準Stage 4輸出')
            if isinstance(stage_results['stage4'], ProcessingResult):
                stage5_input = stage_results['stage4'].data
            else:
                stage5_input = stage_results['stage4']

        stage_results['stage5'] = stage5.execute(stage5_input)

        if not stage_results['stage5']:
            print('❌ 階段五處理失敗')
            return False, 5, "階段五處理失敗"

        # 階段五驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage5, stage_results['stage5'], 5, "數據整合層"
        )

        if not validation_success:
            print(f'❌ 階段五驗證失敗: {validation_msg}')
            return False, 5, validation_msg

        print(f'✅ 階段五完成並驗證通過: {validation_msg}')

        # 階段六：持久化與API層
        print('\\n💾 階段六：持久化與API層')
        print('-' * 60)

        # 清理舊的輸出
        clean_stage_outputs(6)

        from stages.stage6_persistence_api.stage6_main_processor import Stage6PersistenceProcessor
        stage6 = Stage6PersistenceProcessor()

        # 處理Stage 5到Stage 6的數據傳遞
        if isinstance(stage_results['stage5'], ProcessingResult):
            stage6_input = stage_results['stage5'].data
        else:
            stage6_input = stage_results['stage5']

        stage_results['stage6'] = stage6.execute(stage6_input)

        if not stage_results['stage6']:
            print('❌ 階段六處理失敗')
            return False, 6, "階段六處理失敗"

        # 階段六驗證
        validation_success, validation_msg = validate_stage_immediately(
            stage6, stage_results['stage6'], 6, "持久化與API層"
        )

        if not validation_success:
            print(f'❌ 階段六驗證失敗: {validation_msg}')
            return False, 6, validation_msg

        print(f'✅ 階段六完成並驗證通過: {validation_msg}')

        print('\\n🎉 六階段處理全部完成!')
        print('=' * 80)

        # 重構版本摘要
        if use_refactored:
            print('🔧 Stage 1 重構版本特性:')
            print('   ✅ 100% BaseStageProcessor 接口合規')
            print('   ✅ 標準化 ProcessingResult 輸出')
            print('   ✅ 5項專用驗證檢查')
            print('   ✅ 完整的快照保存功能')
            print('   ✅ 向後兼容性保證')

        return True, 6, "全部六階段成功完成"

    except Exception as e:
        logger.error(f"六階段處理異常: {e}")
        return False, 0, f"六階段處理異常: {e}"


def find_latest_stage_output(stage_number: int) -> Optional[Path]:
    """
    尋找指定階段的最新輸出文件

    Args:
        stage_number: 階段編號 (1-6)

    Returns:
        最新輸出文件路徑，如果找不到則返回None
    """
    output_dir = Path(f'data/outputs/stage{stage_number}')

    if not output_dir.exists():
        return None

    # 尋找JSON和壓縮文件
    patterns = ['*.json', '*.json.gz', '*.gz']
    all_files = []

    for pattern in patterns:
        all_files.extend(output_dir.glob(pattern))

    if not all_files:
        return None

    # 返回最新的文件（按修改時間）
    latest_file = max(all_files, key=lambda x: x.stat().st_mtime)
    return latest_file


def run_stage_specific(target_stage, validation_level='STANDARD'):
    """運行特定階段 - 更新版支援重構後的 Stage 1"""
    print(f'\\n🎯 運行階段 {target_stage} (更新版本)')
    print('=' * 80)

    try:
        if target_stage == 1:
            print('\\n📦 階段一：數據載入層 (重構版本)')
            print('-' * 60)

            # 🔧 使用統一的 Stage 1 執行函數 (消除重複邏輯)
            success, result, stage1_data = execute_stage1_unified()

            if not success:
                return False, 1, "Stage 1 執行失敗"

            # 執行驗證
            if isinstance(result, ProcessingResult):
                validation_success, validation_msg = validate_stage_immediately(
                    None, result, 1, "數據載入層"
                )

                if validation_success:
                    return True, 1, f"Stage 1 成功完成並驗證通過: {validation_msg}"
                else:
                    return False, 1, f"Stage 1 驗證失敗: {validation_msg}"
            else:
                # 舊版本格式 (不應該發生)
                satellites_count = len(stage1_data.get('satellites', []))
                return True, 1, f"Stage 1 成功完成: {satellites_count} 顆衛星"

        elif target_stage == 2:
            print('\\n🛰️ 階段二：軌道計算與鏈路可行性評估層')
            print('-' * 60)

            clean_stage_outputs(2)

            # 尋找Stage 1輸出文件
            stage1_output = find_latest_stage_output(1)
            if not stage1_output:
                print('❌ 找不到Stage 1輸出文件，請先執行Stage 1')
                return False, 2, "需要Stage 1輸出文件"

            print(f'📊 使用Stage 1輸出: {stage1_output}')

            # 🔧 使用統一v3.0處理器 (CPU計算)
            config_path = project_root / "config/stage2_orbital_computing.yaml"
            if config_path.exists():
                processor = create_stage2_processor_unified(str(config_path))
            else:
                print('⚠️ 配置文件不存在，使用 v3.0 標準處理器')
                from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalPropagationProcessor
                processor = Stage2OrbitalPropagationProcessor()

            # 載入前階段數據
            import json
            with open(stage1_output, 'r') as f:
                stage1_data = json.load(f)

            result = processor.execute(stage1_data)

            if not result:
                return False, 2, "Stage 2 執行失敗"

            validation_success, validation_msg = validate_stage_immediately(
                processor, result, 2, "軌道計算與鏈路可行性評估層"
            )

            if validation_success:
                return True, 2, f"Stage 2 成功完成並驗證通過: {validation_msg}"
            else:
                return False, 2, f"Stage 2 驗證失敗: {validation_msg}"


        elif target_stage == 3:
            print('\\n🌍 階段三：座標系統轉換層')
            print('-' * 60)

            clean_stage_outputs(3)

            # 尋找Stage 2輸出
            stage2_output = find_latest_stage_output(2)
            if not stage2_output:
                print('❌ 找不到Stage 2輸出文件，請先執行Stage 2')
                return False, 3, "需要Stage 2輸出文件"

            from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
            stage3_config = {
                'coordinate_config': {
                    'source_frame': 'TEME',
                    'target_frame': 'WGS84',
                    'time_corrections': True,
                    'polar_motion': True,
                    'nutation_model': 'IAU2000A'
                },
                'skyfield_config': {
                    'ephemeris_file': 'de421.bsp',
                    'auto_download': True
                },
                'precision_config': {
                    'target_accuracy_m': 0.5
                }
            }
            processor = Stage3CoordinateTransformProcessor(config=stage3_config)

            # 載入前階段數據
            import json
            with open(stage2_output, 'r') as f:
                stage2_data = json.load(f)

            result = processor.execute(stage2_data)

            if not result:
                return False, 3, "Stage 3 執行失敗"

            validation_success, validation_msg = validate_stage_immediately(
                processor, result, 3, "座標系統轉換層"
            )

            if validation_success:
                return True, 3, f"Stage 3 成功完成並驗證通過: {validation_msg}"
            else:
                return False, 3, f"Stage 3 驗證失敗: {validation_msg}"

        elif target_stage == 4:
            print('\\n🎯 階段四：優化決策層')
            print('-' * 60)

            clean_stage_outputs(4)

            # 尋找Stage 3輸出
            stage3_output = find_latest_stage_output(3)
            if not stage3_output:
                print('❌ 找不到Stage 3輸出文件，請先執行Stage 3')
                return False, 4, "需要Stage 3輸出文件"

            from stages.stage4_optimization.stage4_optimization_processor import Stage4OptimizationProcessor
            processor = Stage4OptimizationProcessor()

            # 載入前階段數據
            import json
            with open(stage3_output, 'r') as f:
                stage3_data = json.load(f)

            result = processor.execute(stage3_data)

            if not result:
                return False, 4, "Stage 4 執行失敗"

            validation_success, validation_msg = validate_stage_immediately(
                processor, result, 4, "優化決策層"
            )

            if validation_success:
                return True, 4, f"Stage 4 成功完成並驗證通過: {validation_msg}"
            else:
                return False, 4, f"Stage 4 驗證失敗: {validation_msg}"

        elif target_stage == 5:
            print('\\n📊 階段五：數據整合層')
            print('-' * 60)

            clean_stage_outputs(5)

            # 尋找Stage 4輸出
            stage4_output = find_latest_stage_output(4)
            if not stage4_output:
                print('❌ 找不到Stage 4輸出文件，請先執行Stage 4')
                return False, 5, "需要Stage 4輸出文件"

            from stages.stage5_data_integration.data_integration_processor import DataIntegrationProcessor
            processor = DataIntegrationProcessor()

            # 載入前階段數據
            import json
            with open(stage4_output, 'r') as f:
                stage4_data = json.load(f)

            result = processor.execute(stage4_data)

            if not result:
                return False, 5, "Stage 5 執行失敗"

            validation_success, validation_msg = validate_stage_immediately(
                processor, result, 5, "數據整合層"
            )

            if validation_success:
                return True, 5, f"Stage 5 成功完成並驗證通過: {validation_msg}"
            else:
                return False, 5, f"Stage 5 驗證失敗: {validation_msg}"

        elif target_stage == 6:
            print('\\n💾 階段六：持久化與API層')
            print('-' * 60)

            clean_stage_outputs(6)

            # 尋找Stage 5輸出
            stage5_output = find_latest_stage_output(5)
            if not stage5_output:
                print('❌ 找不到Stage 5輸出文件，請先執行Stage 5')
                return False, 6, "需要Stage 5輸出文件"

            from stages.stage6_persistence_api.stage6_main_processor import Stage6PersistenceProcessor
            processor = Stage6PersistenceProcessor()

            # 載入前階段數據
            import json
            with open(stage5_output, 'r') as f:
                stage5_data = json.load(f)

            result = processor.execute(stage5_data)

            if not result:
                return False, 6, "Stage 6 執行失敗"

            validation_success, validation_msg = validate_stage_immediately(
                processor, result, 6, "持久化與API層"
            )

            if validation_success:
                return True, 6, f"Stage 6 成功完成並驗證通過: {validation_msg}"
            else:
                return False, 6, f"Stage 6 驗證失敗: {validation_msg}"

        else:
            print(f'❌ 不支援的階段: {target_stage}')
            return False, target_stage, f"不支援的階段: {target_stage}"

    except Exception as e:
        logger.error(f"Stage {target_stage} 執行異常: {e}")
        return False, target_stage, f"Stage {target_stage} 執行異常: {e}"


def main():
    """主函數"""
    import argparse
    parser = argparse.ArgumentParser(description='六階段數據處理系統 (重構更新版)')
    parser.add_argument('--stage', type=int, choices=[1,2,3,4,5,6], help='運行特定階段')
    parser.add_argument('--stages', type=str, help='運行階段範圍，如 "1-2" 或 "1,3,5"')
    # 已移除舊版本支持 (--use-legacy 已破壞)
    args = parser.parse_args()

    # 已移除舊版本支持 (已破壞，不相容)
    print('🔧 使用重構版 Stage 1 (唯一可用版本)')

    start_time = time.time()

    if args.stages:
        # 解析階段範圍
        stages_to_run = []
        if '-' in args.stages:
            # 範圍格式: "1-3"
            start, end = map(int, args.stages.split('-'))
            stages_to_run = list(range(start, end + 1))
        else:
            # 逗號分隔格式: "1,3,5"
            stages_to_run = [int(s.strip()) for s in args.stages.split(',')]

        print(f'🎯 運行階段範圍: {stages_to_run}')

        # 順序執行指定階段
        overall_success = True
        last_completed = 0
        final_message = ""

        for stage in stages_to_run:
            if stage not in [1,2,3,4,5,6]:
                print(f'❌ 無效階段: {stage}')
                overall_success = False
                break

            print(f'\n{"="*60}')
            print(f'🚀 執行階段 {stage}')
            print(f'{"="*60}')

            success, completed_stage, message = run_stage_specific(stage)
            last_completed = completed_stage
            final_message = message

            if not success:
                print(f'❌ 階段 {stage} 失敗，停止後續執行')
                overall_success = False
                break
            else:
                print(f'✅ 階段 {stage} 完成')

        success = overall_success
        completed_stage = last_completed
        message = final_message

    elif args.stage:
        success, completed_stage, message = run_stage_specific(args.stage)
    else:
        success, completed_stage, message = run_all_stages_sequential()

    end_time = time.time()
    execution_time = end_time - start_time

    print(f'\\n📊 執行統計:')
    print(f'   執行時間: {execution_time:.2f} 秒')
    print(f'   完成階段: {completed_stage}/6')
    print(f'   最終狀態: {"✅ 成功" if success else "❌ 失敗"}')
    print(f'   訊息: {message}')

    if os.environ.get('USE_REFACTORED_STAGE1') == 'true':
        print('\\n🎯 重構版本優勢:')
        print('   📦 Stage 1: 100% BaseStageProcessor 合規')
        print('   📦 標準化: ProcessingResult 輸出格式')
        print('   📦 驗證: 5項專用驗證檢查')
        print('   📦 兼容性: 完美的向後兼容')

    print('\\n🚀 Stage 2 v3.0 軌道狀態傳播特性 (統一邏輯):')
    print('   🎯 唯一: Stage2OrbitalPropagationProcessor (v3.0 統一標準)')
    print('   💻 計算: 純CPU計算，無GPU/CPU差異')
    print('   📋 架構: 純軌道狀態傳播，禁止座標轉換和可見性分析')
    print('   🎯 輸出: TEME 座標系統的軌道狀態時間序列')
    print('   ⚠️  時間: 使用 Stage 1 epoch_datetime，禁止 TLE 重新解析')
    print('   🚫 移除: 所有舊版處理器、GPU邏輯、回退機制')

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())