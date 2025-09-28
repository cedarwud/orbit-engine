#!/usr/bin/env python3
"""
🧪 混合式階段二處理器測試腳本

測試目標：
✅ 驗證混合式處理器功能正確性
✅ 確認性能提升
✅ 驗證結果與標準版一致性
✅ 測試記憶體和GPU優化
"""

import os
import sys
import logging
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.stages.stage2_orbital_computing.hybrid_stage2_processor import HybridStage2Processor
from src.stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
from src.stages.stage2_orbital_computing.optimized_stage2_processor import OptimizedStage2Processor

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data():
    """載入測試數據"""
    logger.info("📥 載入測試數據...")

    # 查找最新的Stage 1輸出
    stage1_output_dir = project_root / "data" / "outputs" / "stage1"

    if not stage1_output_dir.exists():
        logger.error("❌ Stage 1輸出目錄不存在")
        return None

    import glob
    # 查找多種可能的Stage 1輸出文件格式
    patterns = [
        str(stage1_output_dir / "data_loading_output_*.json"),
        str(stage1_output_dir / "tle_data_loading_output_*.json")
    ]

    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    if not files:
        logger.error("❌ 未找到Stage 1輸出文件")
        return None

    # 選擇最新文件
    latest_file = max(files, key=os.path.getmtime)
    logger.info(f"📂 使用Stage 1輸出: {latest_file}")

    import json
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_processor_performance(processor_class, processor_name: str, test_data: dict):
    """測試單個處理器的性能"""
    logger.info(f"\n🧪 測試 {processor_name} 處理器...")

    try:
        # 創建處理器實例
        processor = processor_class()

        # 記錄開始時間
        start_time = time.time()

        # 執行處理
        result = processor.execute(test_data)

        # 記錄結束時間
        end_time = time.time()
        processing_time = end_time - start_time

        # 檢查結果
        if result.get('success', False):
            satellites_data = result.get('satellites', {})
            metadata = result.get('metadata', {})

            logger.info(f"✅ {processor_name} 處理成功:")
            logger.info(f"   ⏱️ 處理時間: {processing_time:.2f}秒")
            logger.info(f"   📊 處理衛星: {metadata.get('total_satellites_processed', 0)}顆")
            logger.info(f"   👁️ 可見衛星: {metadata.get('visible_satellites_count', 0)}顆")
            logger.info(f"   🔗 可行衛星: {metadata.get('feasible_satellites_count', 0)}顆")
            logger.info(f"   📁 輸出文件: {result.get('output_file', 'N/A')}")

            # 混合版本額外資訊
            if 'hybrid_performance_metrics' in result:
                perf = result['hybrid_performance_metrics']
                logger.info(f"   🎮 GPU加速: {perf.get('gpu_acceleration_used', False)}")
                logger.info(f"   ⚡ 並行處理: {perf.get('parallel_processing_used', False)}")
                logger.info(f"   🧠 記憶體優化: {perf.get('memory_optimization_used', False)}")

            return {
                'success': True,
                'processing_time': processing_time,
                'satellites_processed': metadata.get('total_satellites_processed', 0),
                'visible_satellites': metadata.get('visible_satellites_count', 0),
                'feasible_satellites': metadata.get('feasible_satellites_count', 0),
                'result': result
            }
        else:
            logger.error(f"❌ {processor_name} 處理失敗: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'processing_time': processing_time
            }

    except Exception as e:
        logger.error(f"❌ {processor_name} 測試異常: {e}")
        import traceback
        logger.error(f"錯誤詳情: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e),
            'processing_time': 0
        }


def compare_results(standard_result: dict, hybrid_result: dict):
    """比較標準版和混合版的結果"""
    logger.info("\n📊 結果比較分析...")

    if not (standard_result.get('success') and hybrid_result.get('success')):
        logger.warning("⚠️ 無法比較結果：其中一個處理器失敗")
        return

    # 性能比較
    std_time = standard_result['processing_time']
    hyb_time = hybrid_result['processing_time']

    if hyb_time > 0:
        speedup = std_time / hyb_time
        improvement = ((std_time - hyb_time) / std_time) * 100

        logger.info(f"⚡ 性能提升:")
        logger.info(f"   標準版時間: {std_time:.2f}秒")
        logger.info(f"   混合版時間: {hyb_time:.2f}秒")
        logger.info(f"   加速比: {speedup:.1f}x")
        logger.info(f"   改善率: {improvement:.1f}%")

    # 結果一致性比較
    std_satellites = standard_result['satellites_processed']
    hyb_satellites = hybrid_result['satellites_processed']

    std_visible = standard_result['visible_satellites']
    hyb_visible = hybrid_result['visible_satellites']

    std_feasible = standard_result['feasible_satellites']
    hyb_feasible = hybrid_result['feasible_satellites']

    logger.info(f"📊 結果一致性:")
    logger.info(f"   處理衛星: 標準版 {std_satellites} vs 混合版 {hyb_satellites} {'✅' if std_satellites == hyb_satellites else '❌'}")
    logger.info(f"   可見衛星: 標準版 {std_visible} vs 混合版 {hyb_visible} {'✅' if std_visible == hyb_visible else '❌'}")
    logger.info(f"   可行衛星: 標準版 {std_feasible} vs 混合版 {hyb_feasible} {'✅' if std_feasible == hyb_feasible else '❌'}")

    # 容錯範圍檢查 (允許小幅差異)
    tolerance = 0.02  # 2%容錯

    def within_tolerance(val1, val2, total):
        if total == 0:
            return val1 == val2
        return abs(val1 - val2) / total <= tolerance

    visible_ok = within_tolerance(std_visible, hyb_visible, std_satellites)
    feasible_ok = within_tolerance(std_feasible, hyb_feasible, std_satellites)

    if visible_ok and feasible_ok:
        logger.info("✅ 結果一致性檢查通過 (在容錯範圍內)")
    else:
        logger.warning("⚠️ 結果一致性檢查失敗，需要進一步調查")


def test_memory_usage():
    """測試記憶體使用情況"""
    logger.info("\n🧠 記憶體使用測試...")

    try:
        import psutil
        process = psutil.Process()

        # 獲取初始記憶體
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        logger.info(f"   初始記憶體: {initial_memory:.1f} MB")

        return initial_memory
    except ImportError:
        logger.warning("⚠️ psutil未安裝，無法監控記憶體使用")
        return None


def main():
    """主測試函數"""
    logger.info("🧪 開始混合式階段二處理器測試")

    # 記憶體監控
    initial_memory = test_memory_usage()

    # 載入測試數據
    test_data = load_test_data()
    if not test_data:
        logger.error("❌ 無法載入測試數據，測試終止")
        return

    satellite_count = len(test_data.get('tle_data', test_data.get('satellites', [])))
    logger.info(f"📊 測試數據: {satellite_count} 顆衛星")

    # 確保數據格式兼容性
    if 'satellites' in test_data and 'tle_data' not in test_data:
        test_data['tle_data'] = test_data['satellites']
        logger.info("🔄 數據格式轉換: satellites → tle_data")

    # 測試標準版處理器
    logger.info("\n" + "="*60)
    standard_result = test_processor_performance(
        Stage2OrbitalComputingProcessor,
        "標準版",
        test_data
    )

    # 測試混合版處理器
    logger.info("\n" + "="*60)
    hybrid_result = test_processor_performance(
        HybridStage2Processor,
        "混合版",
        test_data
    )

    # 可選：測試優化版處理器 (比較用)
    logger.info("\n" + "="*60)
    optimized_result = test_processor_performance(
        OptimizedStage2Processor,
        "優化版",
        test_data
    )

    # 結果比較
    logger.info("\n" + "="*60)
    if standard_result.get('success') and hybrid_result.get('success'):
        compare_results(standard_result, hybrid_result)

    # 最終摘要
    logger.info("\n" + "="*60)
    logger.info("🎯 測試摘要:")

    processors = [
        ("標準版", standard_result),
        ("混合版", hybrid_result),
        ("優化版", optimized_result)
    ]

    for name, result in processors:
        if result.get('success'):
            logger.info(f"✅ {name}: {result['processing_time']:.2f}秒, "
                       f"可行衛星: {result['feasible_satellites']}顆")
        else:
            logger.info(f"❌ {name}: 失敗 - {result.get('error', 'Unknown error')}")

    # 推薦結論
    if (standard_result.get('success') and hybrid_result.get('success') and
        hybrid_result['processing_time'] < standard_result['processing_time']):

        speedup = standard_result['processing_time'] / hybrid_result['processing_time']
        logger.info(f"\n🏆 推薦使用混合版處理器 (加速 {speedup:.1f}x)")
    else:
        logger.info(f"\n📋 建議進一步優化混合版處理器")


if __name__ == "__main__":
    main()