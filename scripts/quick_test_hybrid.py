#!/usr/bin/env python3
"""
🚀 快速測試混合式階段二處理器 - 小規模數據集

使用少量衛星進行快速功能驗證
"""

import os
import sys
import logging
import time
import json
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
from src.stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_data(satellite_count: int = 100) -> dict:
    """創建小規模測試數據"""

    # 載入真實數據
    stage1_file = project_root / "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"

    if not stage1_file.exists():
        logger.error("❌ 找不到Stage 1輸出文件")
        return None

    with open(stage1_file, 'r', encoding='utf-8') as f:
        full_data = json.load(f)

    # 取前N顆衛星作為測試數據
    satellites = full_data.get('satellites', [])[:satellite_count]

    test_data = {
        'stage': 'data_loading',
        'tle_data': satellites,
        'satellites': satellites,
        'metadata': {
            'test_mode': True,
            'original_count': len(full_data.get('satellites', [])),
            'test_count': len(satellites)
        }
    }

    logger.info(f"📊 創建測試數據: {len(satellites)} 顆衛星 (來自 {len(full_data.get('satellites', []))} 顆)")

    return test_data


def quick_test_processor(processor_class, processor_name: str, test_data: dict):
    """快速測試單個處理器"""
    logger.info(f"\n🧪 測試 {processor_name}...")

    try:
        # 創建處理器
        processor = processor_class()

        # 記錄時間
        start_time = time.time()

        # 執行處理
        result = processor.execute(test_data)

        # 記錄結束時間
        end_time = time.time()
        processing_time = end_time - start_time

        if result.get('success', False):
            metadata = result.get('metadata', {})
            satellites = result.get('satellites', {})

            logger.info(f"✅ {processor_name} 成功:")
            logger.info(f"   ⏱️ 時間: {processing_time:.2f}秒")
            logger.info(f"   📊 處理: {metadata.get('total_satellites_processed', 0)}顆")
            logger.info(f"   👁️ 可見: {metadata.get('visible_satellites_count', 0)}顆")
            logger.info(f"   🔗 可行: {metadata.get('feasible_satellites_count', 0)}顆")
            logger.info(f"   📁 輸出: {len(satellites)}顆")

            # 檢查混合版特定指標
            if 'hybrid_performance_metrics' in result:
                perf = result['hybrid_performance_metrics']
                logger.info(f"   🎮 GPU: {perf.get('gpu_acceleration_used', False)}")
                logger.info(f"   ⚡ 並行: {perf.get('parallel_processing_used', False)}")
                logger.info(f"   🧠 記憶體: {perf.get('memory_optimization_used', False)}")

            return {
                'success': True,
                'time': processing_time,
                'processed': metadata.get('total_satellites_processed', 0),
                'visible': metadata.get('visible_satellites_count', 0),
                'feasible': metadata.get('feasible_satellites_count', 0),
                'output_satellites': len(satellites),
                'result': result
            }
        else:
            logger.error(f"❌ {processor_name} 失敗: {result.get('error', 'Unknown')}")
            return {'success': False, 'error': result.get('error'), 'time': processing_time}

    except Exception as e:
        logger.error(f"❌ {processor_name} 異常: {e}")
        return {'success': False, 'error': str(e), 'time': 0}


def main():
    """主測試函數"""
    logger.info("🚀 快速測試混合式階段二處理器")

    # 創建小規模測試數據
    test_data = create_test_data(50)  # 只測試50顆衛星
    if not test_data:
        return

    # 測試標準版
    logger.info("\n" + "="*50)
    standard_result = quick_test_processor(
        Stage2OrbitalComputingProcessor,
        "標準版",
        test_data
    )

    # 測試混合版
    logger.info("\n" + "="*50)
    hybrid_result = quick_test_processor(
        HybridStage2Processor,
        "混合版",
        test_data
    )

    # 比較結果
    logger.info("\n" + "="*50)
    logger.info("📊 比較結果:")

    if standard_result.get('success') and hybrid_result.get('success'):
        std_time = standard_result['time']
        hyb_time = hybrid_result['time']

        if hyb_time > 0:
            speedup = std_time / hyb_time
            logger.info(f"⚡ 性能: 標準版 {std_time:.2f}s → 混合版 {hyb_time:.2f}s (加速 {speedup:.1f}x)")

        # 結果一致性
        std_feasible = standard_result['feasible']
        hyb_feasible = hybrid_result['feasible']
        std_output = standard_result['output_satellites']
        hyb_output = hybrid_result['output_satellites']

        logger.info(f"📊 可行衛星: 標準版 {std_feasible} → 混合版 {hyb_feasible} {'✅' if std_feasible == hyb_feasible else '❌'}")
        logger.info(f"📊 輸出衛星: 標準版 {std_output} → 混合版 {hyb_output} {'✅' if std_output == hyb_output else '❌'}")

        # 結論
        if std_feasible == hyb_feasible and std_output == hyb_output:
            logger.info("🎯 結果一致性: ✅ 通過")
        else:
            logger.info("🎯 結果一致性: ❌ 需要調查")

    else:
        logger.warning("⚠️ 無法比較結果 - 其中一個處理器失敗")

    # 最終摘要
    logger.info("\n🎯 測試摘要:")
    for name, result in [("標準版", standard_result), ("混合版", hybrid_result)]:
        if result.get('success'):
            logger.info(f"✅ {name}: {result['time']:.2f}s, 可行: {result['feasible']}, 輸出: {result['output_satellites']}")
        else:
            logger.info(f"❌ {name}: 失敗")


if __name__ == "__main__":
    main()