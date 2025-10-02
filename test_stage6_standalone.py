#!/usr/bin/env python3
"""
Stage 6 獨立測試腳本

測試 Stage 6 的所有核心組件和驗證框架
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone

# 設置測試模式
os.environ['ORBIT_ENGINE_TEST_MODE'] = '1'

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

from src.stages.stage6_research_optimization.stage6_research_optimization_processor import create_stage6_processor


def create_mock_stage5_output():
    """創建模擬的 Stage 5 輸出數據"""
    return {
        'stage': 'stage5_signal_analysis',
        'satellites': [
            {
                'satellite_id': 'STARLINK-1234',
                'constellation': 'starlink',
                'time_series': [
                    {
                        'timestamp': '2025-09-30T00:00:00.000000+00:00',
                        'current_position': {
                            'latitude_deg': 25.0337,
                            'longitude_deg': 121.5645,
                            'altitude_km': 550.0
                        },
                        'signal_quality': {
                            'rsrp_dbm': -85.2,
                            'rs_sinr_db': 12.8,
                            'rsrq_db': -10.5
                        },
                        'visibility_metrics': {
                            'elevation_deg': 45.0,
                            'is_visible': True
                        },
                        'physical_parameters': {
                            'distance_km': 750.5,
                            'range_rate_km_s': -0.5
                        },
                        'quality_assessment': {
                            'is_usable': True,
                            'quality_score': 0.85,
                            'quality_level': 'excellent',
                            'link_margin_db': 15.0
                        }
                    },
                    {
                        'timestamp': '2025-09-30T00:00:30.000000+00:00',
                        'current_position': {
                            'latitude_deg': 25.0338,
                            'longitude_deg': 121.5646,
                            'altitude_km': 550.1
                        },
                        'signal_quality': {
                            'rsrp_dbm': -84.8,
                            'rs_sinr_db': 13.1,
                            'rsrq_db': -10.2
                        },
                        'visibility_metrics': {
                            'elevation_deg': 46.0,
                            'is_visible': True
                        },
                        'physical_parameters': {
                            'distance_km': 748.2,
                            'range_rate_km_s': -0.6
                        },
                        'quality_assessment': {
                            'is_usable': True,
                            'quality_score': 0.87,
                            'quality_level': 'excellent',
                            'link_margin_db': 16.0
                        }
                    }
                ]
            },
            {
                'satellite_id': 'STARLINK-5678',
                'constellation': 'starlink',
                'time_series': [
                    {
                        'timestamp': '2025-09-30T00:00:00.000000+00:00',
                        'current_position': {
                            'latitude_deg': 25.0340,
                            'longitude_deg': 121.5650,
                            'altitude_km': 551.0
                        },
                        'signal_quality': {
                            'rsrp_dbm': -88.5,
                            'rs_sinr_db': 10.2,
                            'rsrq_db': -12.1
                        },
                        'visibility_metrics': {
                            'elevation_deg': 35.0,
                            'is_visible': True
                        },
                        'physical_parameters': {
                            'distance_km': 820.3,
                            'range_rate_km_s': -0.3
                        },
                        'quality_assessment': {
                            'is_usable': True,
                            'quality_score': 0.72,
                            'quality_level': 'good',
                            'link_margin_db': 10.0
                        }
                    }
                ]
            },
            {
                'satellite_id': 'ONEWEB-101',
                'constellation': 'oneweb',
                'time_series': [
                    {
                        'timestamp': '2025-09-30T00:00:00.000000+00:00',
                        'current_position': {
                            'latitude_deg': 25.0335,
                            'longitude_deg': 121.5640,
                            'altitude_km': 1200.0
                        },
                        'signal_quality': {
                            'rsrp_dbm': -90.2,
                            'rs_sinr_db': 8.5,
                            'rsrq_db': -14.0
                        },
                        'visibility_metrics': {
                            'elevation_deg': 25.0,
                            'is_visible': True
                        },
                        'physical_parameters': {
                            'distance_km': 1500.0,
                            'range_rate_km_s': 0.2
                        },
                        'quality_assessment': {
                            'is_usable': True,
                            'quality_score': 0.65,
                            'quality_level': 'fair',
                            'link_margin_db': 8.0
                        }
                    }
                ]
            }
        ],
        'connectable_satellites': {
            'starlink': [
                {
                    'satellite_id': 'STARLINK-1234',
                    'time_series': [
                        {
                            'timestamp': '2025-09-30T00:00:00.000000+00:00',
                            'visibility_metrics': {'is_connectable': True}
                        },
                        {
                            'timestamp': '2025-09-30T00:00:30.000000+00:00',
                            'visibility_metrics': {'is_connectable': True}
                        }
                    ]
                },
                {
                    'satellite_id': 'STARLINK-5678',
                    'time_series': [
                        {
                            'timestamp': '2025-09-30T00:00:00.000000+00:00',
                            'visibility_metrics': {'is_connectable': True}
                        }
                    ]
                }
            ],
            'oneweb': [
                {
                    'satellite_id': 'ONEWEB-101',
                    'time_series': [
                        {
                            'timestamp': '2025-09-30T00:00:00.000000+00:00',
                            'visibility_metrics': {'is_connectable': True}
                        }
                    ]
                }
            ]
        },
        'metadata': {
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_satellites': 3,
            'processing_stage': 5
        }
    }


def test_stage6_processor():
    """測試 Stage 6 處理器"""
    print("\n" + "="*80)
    print("🧪 Stage 6 獨立測試")
    print("="*80)

    # 1. 創建處理器
    print("\n1️⃣ 初始化 Stage 6 處理器...")
    processor = create_stage6_processor()
    print(f"✅ 處理器初始化成功: {processor.stage_name}")
    print(f"   - GPP Detector: {'✅' if processor.gpp_detector else '❌'}")
    print(f"   - Pool Verifier: {'✅' if processor.pool_verifier else '❌'}")
    print(f"   - ML Generator: {'✅' if processor.ml_generator else '❌'}")
    print(f"   - Decision Support: {'✅' if processor.decision_support else '❌'}")

    # 2. 創建模擬輸入數據
    print("\n2️⃣ 創建模擬 Stage 5 輸出數據...")
    input_data = create_mock_stage5_output()
    print(f"✅ 模擬數據創建完成")
    print(f"   - 衛星數量: {len(input_data['satellites'])}")
    print(f"   - Starlink 候選池: {len(input_data['connectable_satellites']['starlink'])}")
    print(f"   - OneWeb 候選池: {len(input_data['connectable_satellites']['oneweb'])}")

    # 3. 執行處理
    print("\n3️⃣ 執行 Stage 6 處理流程...")
    try:
        result = processor.execute(input_data)
        print("✅ Stage 6 處理完成")

        # 4. 顯示結果統計
        print("\n4️⃣ 處理結果統計:")
        metadata = result.get('metadata', {})
        print(f"   - 3GPP 事件檢測: {metadata.get('total_events_detected', 0)} 個")
        print(f"   - ML 訓練樣本: {metadata.get('ml_training_samples', 0)} 個")
        print(f"   - 池驗證狀態: {'✅ 通過' if metadata.get('pool_verification_passed') else '❌ 失敗'}")
        print(f"   - 決策支援調用: {metadata.get('decision_support_calls', 0)} 次")
        print(f"   - 換手決策: {metadata.get('handover_decisions', 0)} 次")

        # 5. 驗證框架結果
        print("\n5️⃣ 驗證框架結果:")
        validation = result.get('validation_results', {})
        print(f"   - 驗證狀態: {validation.get('overall_status', 'UNKNOWN')}")
        print(f"   - 通過率: {validation.get('validation_details', {}).get('success_rate', 0):.1%}")
        print(f"   - 通過檢查: {validation.get('checks_passed', 0)}/{validation.get('checks_performed', 0)}")

        # 6. 詳細驗證結果
        print("\n6️⃣ 詳細驗證檢查:")
        check_details = validation.get('check_details', {})
        for check_name, check_result in check_details.items():
            status = "✅ 通過" if check_result.get('passed') else "❌ 失敗"
            score = check_result.get('score', 0)
            print(f"   - {check_name}: {status} (分數: {score:.2f})")

        # 7. 保存測試結果
        print("\n7️⃣ 保存測試結果...")
        output_file = f"data/outputs/stage6/stage6_test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('data/outputs/stage6', exist_ok=True)

        # 轉換 numpy 類型為 Python 原生類型
        def convert_numpy_types(obj):
            """遞歸轉換 numpy 類型為 Python 原生類型"""
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj

        result_converted = convert_numpy_types(result)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_converted, f, indent=2, ensure_ascii=False)
        print(f"✅ 測試結果已保存: {output_file}")

        # 8. 測試總結
        print("\n" + "="*80)
        print("📊 測試總結")
        print("="*80)

        all_passed = validation.get('overall_status') == 'PASS'
        if all_passed:
            print("✅ Stage 6 端到端測試 - 通過")
            print("   所有核心組件運行正常")
            print("   驗證框架檢查通過")
            return 0
        else:
            print("⚠️  Stage 6 端到端測試 - 部分失敗")
            print("   某些驗證檢查未通過")
            print("   建議檢查詳細日誌")
            return 1

    except Exception as e:
        print(f"❌ Stage 6 處理失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = test_stage6_processor()
    sys.exit(exit_code)