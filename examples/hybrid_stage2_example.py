#!/usr/bin/env python3
"""
🎯 混合式階段二處理器使用範例

展示如何使用新的HybridStage2Processor來獲得最佳性能和正確性
"""

import os
import sys
import logging
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.stages.stage2_orbital_computing.hybrid_stage2_processor import create_hybrid_stage2_processor

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """混合式處理器使用範例"""
    logger.info("🎯 混合式階段二處理器使用範例")

    try:
        # 1. 創建混合式處理器 (使用預設配置)
        logger.info("🔧 創建混合式處理器...")
        processor = create_hybrid_stage2_processor()

        # 2. 可選：使用自定義配置
        custom_config = {
            'performance': {
                'testing_mode': {
                    'enabled': True,
                    'satellite_sample_size': 1000,  # 測試用較小樣本
                    'sample_method': 'distributed'
                }
            },
            'visibility_filter': {
                'min_elevation_deg': 10.0,
                'max_distance_km': 2000.0,
                'constellation_elevation_thresholds': {
                    'starlink': 5.0,
                    'oneweb': 10.0,
                    'other': 15.0
                }
            },
            'link_feasibility_filter': {
                'min_service_window_minutes': 2.0,
                'min_feasibility_score': 0.6
            }
        }

        # 創建配置版本
        # processor = create_hybrid_stage2_processor(custom_config)

        # 3. 執行處理 (自動載入Stage 1輸出)
        logger.info("🚀 開始處理...")
        result = processor.execute()

        # 4. 檢查結果
        if result.get('success', False):
            logger.info("✅ 處理成功！")

            # 基本統計
            metadata = result.get('metadata', {})
            logger.info(f"📊 處理統計:")
            logger.info(f"   總衛星數: {metadata.get('total_satellites_processed', 0)}")
            logger.info(f"   可見衛星: {metadata.get('visible_satellites_count', 0)}")
            logger.info(f"   可行衛星: {metadata.get('feasible_satellites_count', 0)}")
            logger.info(f"   處理時間: {metadata.get('processing_duration_seconds', 0):.2f}秒")

            # 性能指標
            if 'hybrid_performance_metrics' in result:
                perf = result['hybrid_performance_metrics']
                logger.info(f"\n🚀 性能指標:")
                logger.info(f"   總執行時間: {perf.get('total_processing_time', 0):.2f}秒")
                logger.info(f"   SGP4計算時間: {perf.get('sgp4_calculation_time', 0):.2f}秒")
                logger.info(f"   座標轉換時間: {perf.get('coordinate_conversion_time', 0):.2f}秒")
                logger.info(f"   可見性分析時間: {perf.get('visibility_analysis_time', 0):.2f}秒")

                logger.info(f"\n🔧 優化狀態:")
                logger.info(f"   GPU加速: {perf.get('gpu_acceleration_used', False)}")
                logger.info(f"   並行處理: {perf.get('parallel_processing_used', False)}")
                logger.info(f"   記憶體優化: {perf.get('memory_optimization_used', False)}")

            # 輸出文件
            output_file = result.get('output_file')
            if output_file:
                logger.info(f"\n📁 結果已保存至: {output_file}")

            # 5. 可選：分析特定衛星的結果
            satellites = result.get('satellites', {})
            if satellites:
                # 找出品質最高的衛星
                best_satellite = None
                best_score = -1

                for sat_id, sat_data in satellites.items():
                    feasibility_score = sat_data.get('feasibility_score', 0)
                    if feasibility_score > best_score:
                        best_score = feasibility_score
                        best_satellite = (sat_id, sat_data)

                if best_satellite:
                    sat_id, sat_data = best_satellite
                    logger.info(f"\n🏆 品質最佳衛星: {sat_id}")
                    logger.info(f"   可行性評分: {sat_data.get('feasibility_score', 0):.3f}")
                    logger.info(f"   品質等級: {sat_data.get('quality_grade', 'N/A')}")
                    logger.info(f"   可見性狀態: {sat_data.get('visibility_status', 'N/A')}")

        else:
            logger.error(f"❌ 處理失敗: {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"❌ 範例執行失敗: {e}")
        import traceback
        logger.error(f"錯誤詳情: {traceback.format_exc()}")


def advanced_usage_example():
    """進階使用範例：自定義配置和錯誤處理"""
    logger.info("\n🔬 進階使用範例...")

    # 高性能配置
    high_performance_config = {
        'orbital_calculation': {
            'time_points': 288,  # 增加時間點提高精度
            'time_interval_seconds': 30,  # 更密集的時間間隔
            'algorithm': 'SGP4_Parallel'
        },
        'visibility_filter': {
            'constellation_elevation_thresholds': {
                'starlink': 3.0,  # 更低的門檻以獲得更多結果
                'oneweb': 8.0,
                'other': 12.0
            }
        },
        'performance': {
            'gpu_optimization': True,
            'parallel_processing': True,
            'memory_optimization': True,
            'batch_size': 1000
        }
    }

    try:
        # 創建高性能配置的處理器
        processor = create_hybrid_stage2_processor(high_performance_config)

        # 載入特定的Stage 1數據
        stage1_data = processor._load_stage1_output()

        # 可選：修改數據進行測試
        if 'tle_data' in stage1_data:
            original_count = len(stage1_data['tle_data'])
            # 限制為前1000顆衛星進行快速測試
            stage1_data['tle_data'] = stage1_data['tle_data'][:1000]
            logger.info(f"📊 測試模式: {original_count} → {len(stage1_data['tle_data'])} 顆衛星")

        # 執行處理
        result = processor.execute(stage1_data)

        if result.get('success'):
            logger.info("✅ 進階處理成功")

            # 詳細性能分析
            if 'hybrid_performance_metrics' in result:
                perf = result['hybrid_performance_metrics']
                total_time = perf.get('total_processing_time', 0)

                # 計算各階段時間佔比
                sgp4_ratio = (perf.get('sgp4_calculation_time', 0) / total_time) * 100 if total_time > 0 else 0
                coord_ratio = (perf.get('coordinate_conversion_time', 0) / total_time) * 100 if total_time > 0 else 0
                vis_ratio = (perf.get('visibility_analysis_time', 0) / total_time) * 100 if total_time > 0 else 0

                logger.info(f"\n📊 時間分佈:")
                logger.info(f"   SGP4計算: {sgp4_ratio:.1f}%")
                logger.info(f"   座標轉換: {coord_ratio:.1f}%")
                logger.info(f"   可見性分析: {vis_ratio:.1f}%")

        else:
            logger.error(f"❌ 進階處理失敗: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 進階範例失敗: {e}")


if __name__ == "__main__":
    # 基本使用範例
    main()

    # 進階使用範例
    advanced_usage_example()