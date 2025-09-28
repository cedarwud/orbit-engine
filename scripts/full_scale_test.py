#!/usr/bin/env python3
"""
🚀 全量衛星測試 - 測試混合式處理器在真實規模下的性能

測試8995顆衛星的處理性能，展示並行處理和GPU加速的真實效果
"""

import os
import sys
import logging
import time
import json
import threading
import psutil
import yaml
from pathlib import Path
from datetime import datetime

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


class PerformanceMonitor:
    """性能監控器"""

    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.gpu_usage = []
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """開始監控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("📊 性能監控已啟動")

    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("📊 性能監控已停止")

    def _monitor_loop(self):
        """監控循環"""
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.append(cpu_percent)

                # 記憶體使用
                memory = psutil.virtual_memory()
                self.memory_usage.append(memory.percent)

                # 嘗試獲取GPU使用率 (如果有的話)
                try:
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        self.gpu_usage.append(gpus[0].load * 100)
                except ImportError:
                    pass

            except Exception as e:
                logger.warning(f"監控異常: {e}")

    def get_stats(self):
        """獲取統計信息"""
        stats = {
            'cpu_avg': sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
            'cpu_max': max(self.cpu_usage) if self.cpu_usage else 0,
            'memory_avg': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
            'memory_max': max(self.memory_usage) if self.memory_usage else 0,
            'sample_count': len(self.cpu_usage)
        }

        if self.gpu_usage:
            stats['gpu_avg'] = sum(self.gpu_usage) / len(self.gpu_usage)
            stats['gpu_max'] = max(self.gpu_usage)

        return stats


def load_config_file(config_path: Path) -> dict:
    """載入配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"❌ 無法載入配置文件 {config_path}: {e}")
        return {}


def load_full_dataset():
    """載入完整數據集"""
    logger.info("📥 載入全量衛星數據...")

    stage1_file = project_root / "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"

    if not stage1_file.exists():
        logger.error("❌ 找不到Stage 1輸出文件")
        return None

    with open(stage1_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 確保數據格式兼容性
    if 'satellites' in data and 'tle_data' not in data:
        data['tle_data'] = data['satellites']

    satellite_count = len(data.get('tle_data', []))
    logger.info(f"📊 載入完成: {satellite_count} 顆衛星")

    return data


def test_processor_with_monitoring(processor_factory, processor_name: str, test_data: dict, timeout_minutes: int = 15):
    """測試處理器並監控性能"""
    logger.info(f"\n🧪 測試 {processor_name} (全量: {len(test_data.get('tle_data', []))} 顆衛星)")

    # 初始化性能監控
    monitor = PerformanceMonitor()

    try:
        # 創建處理器 (支持類或 lambda 函數)
        if callable(processor_factory) and not hasattr(processor_factory, '__name__'):
            # Lambda 函數
            processor = processor_factory()
        else:
            # 類
            processor = processor_factory()

        # 開始監控
        monitor.start_monitoring()

        # 記錄開始時間
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / (1024**3)  # GB

        logger.info(f"⏰ 開始時間: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"💾 初始記憶體: {start_memory:.2f} GB")

        # 執行處理
        result = processor.execute(test_data)

        # 記錄結束時間
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / (1024**3)  # GB
        processing_time = end_time - start_time

        # 停止監控
        monitor.stop_monitoring()

        # 獲取性能統計
        perf_stats = monitor.get_stats()

        logger.info(f"⏰ 結束時間: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"⏱️ 總耗時: {processing_time:.2f}秒 ({processing_time/60:.1f}分鐘)")
        logger.info(f"💾 記憶體變化: {start_memory:.2f} → {end_memory:.2f} GB (Δ{end_memory-start_memory:+.2f} GB)")

        # 性能監控結果
        logger.info(f"📊 性能監控 ({perf_stats['sample_count']} 個樣本):")
        logger.info(f"   CPU使用率: 平均 {perf_stats['cpu_avg']:.1f}%, 峰值 {perf_stats['cpu_max']:.1f}%")
        logger.info(f"   記憶體使用率: 平均 {perf_stats['memory_avg']:.1f}%, 峰值 {perf_stats['memory_max']:.1f}%")

        if 'gpu_avg' in perf_stats:
            logger.info(f"   GPU使用率: 平均 {perf_stats['gpu_avg']:.1f}%, 峰值 {perf_stats['gpu_max']:.1f}%")

        if result.get('success', False):
            metadata = result.get('metadata', {})
            satellites = result.get('satellites', {})

            logger.info(f"✅ {processor_name} 處理成功:")
            logger.info(f"   📊 處理衛星: {metadata.get('total_satellites_processed', 0)}")
            logger.info(f"   👁️ 可見衛星: {metadata.get('visible_satellites_count', 0)}")
            logger.info(f"   🔗 可行衛星: {metadata.get('feasible_satellites_count', 0)}")
            logger.info(f"   📁 輸出衛星: {len(satellites)}")
            logger.info(f"   📈 處理速度: {metadata.get('total_satellites_processed', 0)/processing_time:.1f} 衛星/秒")

            # 混合版本特定指標
            if 'hybrid_performance_metrics' in result:
                perf = result['hybrid_performance_metrics']
                logger.info(f"   🚀 SGP4計算: {perf.get('sgp4_calculation_time', 0):.2f}秒")
                logger.info(f"   🌐 座標轉換: {perf.get('coordinate_conversion_time', 0):.2f}秒")
                logger.info(f"   👁️ 可見性分析: {perf.get('visibility_analysis_time', 0):.2f}秒")
                logger.info(f"   🔗 鏈路可行性: {perf.get('link_feasibility_time', 0):.2f}秒")

                # 計算各階段佔比
                total_time = perf.get('total_processing_time', processing_time)
                if total_time > 0:
                    sgp4_ratio = (perf.get('sgp4_calculation_time', 0) / total_time) * 100
                    coord_ratio = (perf.get('coordinate_conversion_time', 0) / total_time) * 100
                    vis_ratio = (perf.get('visibility_analysis_time', 0) / total_time) * 100

                    logger.info(f"   📊 時間分佈: SGP4({sgp4_ratio:.1f}%) + 座標({coord_ratio:.1f}%) + 可見性({vis_ratio:.1f}%)")

                logger.info(f"   🎮 GPU加速: {perf.get('gpu_acceleration_used', False)}")
                logger.info(f"   ⚡ 並行處理: {perf.get('parallel_processing_used', False)}")
                logger.info(f"   🧠 記憶體優化: {perf.get('memory_optimization_used', False)}")

            return {
                'success': True,
                'processing_time': processing_time,
                'processed': metadata.get('total_satellites_processed', 0),
                'visible': metadata.get('visible_satellites_count', 0),
                'feasible': metadata.get('feasible_satellites_count', 0),
                'output_satellites': len(satellites),
                'processing_speed': metadata.get('total_satellites_processed', 0)/processing_time,
                'memory_delta': end_memory - start_memory,
                'performance_stats': perf_stats,
                'result': result
            }
        else:
            logger.error(f"❌ {processor_name} 處理失敗: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'processing_time': processing_time,
                'memory_delta': end_memory - start_memory,
                'performance_stats': perf_stats
            }

    except Exception as e:
        monitor.stop_monitoring()
        logger.error(f"❌ {processor_name} 測試異常: {e}")
        import traceback
        logger.error(f"錯誤詳情: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e),
            'processing_time': 0,
            'memory_delta': 0,
            'performance_stats': monitor.get_stats()
        }


def compare_full_scale_results(standard_result: dict, hybrid_result: dict):
    """比較全量測試結果"""
    logger.info("\n" + "="*80)
    logger.info("📊 全量測試結果比較")
    logger.info("="*80)

    if not (standard_result.get('success') and hybrid_result.get('success')):
        logger.warning("⚠️ 無法比較結果：其中一個處理器失敗")
        return

    # 性能比較
    std_time = standard_result['processing_time']
    hyb_time = hybrid_result['processing_time']

    speedup = std_time / hyb_time if hyb_time > 0 else 0
    time_saved = std_time - hyb_time
    improvement = (time_saved / std_time) * 100 if std_time > 0 else 0

    logger.info(f"⚡ 性能比較:")
    logger.info(f"   標準版時間: {std_time:.1f}秒 ({std_time/60:.1f}分鐘)")
    logger.info(f"   混合版時間: {hyb_time:.1f}秒 ({hyb_time/60:.1f}分鐘)")
    logger.info(f"   時間節省: {time_saved:.1f}秒 ({time_saved/60:.1f}分鐘)")
    logger.info(f"   加速比: {speedup:.1f}x")
    logger.info(f"   性能改善: {improvement:.1f}%")

    # 處理速度比較
    std_speed = standard_result['processing_speed']
    hyb_speed = hybrid_result['processing_speed']

    logger.info(f"📈 處理速度:")
    logger.info(f"   標準版: {std_speed:.1f} 衛星/秒")
    logger.info(f"   混合版: {hyb_speed:.1f} 衛星/秒")
    logger.info(f"   速度提升: {hyb_speed/std_speed:.1f}x" if std_speed > 0 else "   速度提升: N/A")

    # 記憶體使用比較
    std_memory = standard_result['memory_delta']
    hyb_memory = hybrid_result['memory_delta']

    logger.info(f"💾 記憶體使用:")
    logger.info(f"   標準版: {std_memory:+.2f} GB")
    logger.info(f"   混合版: {hyb_memory:+.2f} GB")

    # 資源使用比較
    std_perf = standard_result['performance_stats']
    hyb_perf = hybrid_result['performance_stats']

    logger.info(f"🔧 資源使用:")
    logger.info(f"   CPU使用率: 標準版 {std_perf['cpu_avg']:.1f}% vs 混合版 {hyb_perf['cpu_avg']:.1f}%")
    logger.info(f"   記憶體使用率: 標準版 {std_perf['memory_avg']:.1f}% vs 混合版 {hyb_perf['memory_avg']:.1f}%")

    if 'gpu_avg' in hyb_perf:
        logger.info(f"   GPU使用率: 混合版 {hyb_perf['gpu_avg']:.1f}% (標準版無GPU)")

    # 結果一致性檢查
    std_feasible = standard_result['feasible']
    hyb_feasible = hybrid_result['feasible']
    std_output = standard_result['output_satellites']
    hyb_output = hybrid_result['output_satellites']

    tolerance = 0.05  # 5%容錯
    feasible_ok = abs(std_feasible - hyb_feasible) / max(std_feasible, 1) <= tolerance
    output_ok = abs(std_output - hyb_output) / max(std_output, 1) <= tolerance

    logger.info(f"🎯 結果一致性:")
    logger.info(f"   可行衛星: 標準版 {std_feasible} vs 混合版 {hyb_feasible} {'✅' if feasible_ok else '❌'}")
    logger.info(f"   輸出衛星: 標準版 {std_output} vs 混合版 {hyb_output} {'✅' if output_ok else '❌'}")

    if feasible_ok and output_ok:
        logger.info("✅ 結果一致性檢查通過")
    else:
        logger.warning("⚠️ 結果一致性檢查需要進一步調查")

    # 總體評估
    logger.info(f"\n🏆 總體評估:")
    if speedup >= 2.0:
        logger.info(f"🚀 優秀: {speedup:.1f}x加速，顯著性能提升")
    elif speedup >= 1.5:
        logger.info(f"✅ 良好: {speedup:.1f}x加速，明顯性能改善")
    elif speedup >= 1.2:
        logger.info(f"📈 有效: {speedup:.1f}x加速，中等性能提升")
    else:
        logger.info(f"📊 有限: {speedup:.1f}x加速，性能提升有限")


def main():
    """主測試函數"""
    logger.info("🚀 開始全量衛星混合式處理器測試")
    logger.info(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 系統信息
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)

    logger.info(f"💻 系統信息:")
    logger.info(f"   CPU核心: {cpu_count}")
    logger.info(f"   總記憶體: {memory_gb:.1f} GB")

    # 載入全量數據
    test_data = load_full_dataset()
    if not test_data:
        logger.error("❌ 無法載入測試數據，測試終止")
        return

    satellite_count = len(test_data.get('tle_data', []))
    logger.info(f"📊 準備測試 {satellite_count} 顆衛星")

    # 載入正確的配置文件
    config_path = project_root / "config/stage2_orbital_computing.yaml"
    config_dict = load_config_file(config_path)

    logger.info(f"📄 載入配置文件: {config_path}")
    logger.info(f"   Starlink 仰角: {config_dict.get('visibility_filter', {}).get('constellation_elevation_thresholds', {}).get('starlink', 'N/A')}°")
    logger.info(f"   OneWeb 仰角: {config_dict.get('visibility_filter', {}).get('constellation_elevation_thresholds', {}).get('oneweb', 'N/A')}°")

    # 測試標準版處理器（使用正確配置）
    logger.info("\n" + "="*60)
    logger.info("測試標準版處理器（正確配置）")
    logger.info("="*60)
    standard_result = test_processor_with_monitoring(
        lambda: Stage2OrbitalComputingProcessor(config=config_dict),
        "標準版（正確配置）",
        test_data,
        timeout_minutes=20
    )

    # 測試混合版處理器（使用正確配置）
    logger.info("\n" + "="*60)
    logger.info("測試混合版處理器（正確配置）")
    logger.info("="*60)

    hybrid_result = test_processor_with_monitoring(
        lambda: HybridStage2Processor(config=config_dict),
        "混合版（正確配置）",
        test_data,
        timeout_minutes=20
    )

    # 比較結果
    compare_full_scale_results(standard_result, hybrid_result)

    # 保存詳細結果
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'satellite_count': satellite_count,
        'system_info': {
            'cpu_count': cpu_count,
            'memory_gb': memory_gb
        },
        'standard_result': standard_result,
        'hybrid_result': hybrid_result
    }

    # 保存測試結果
    results_file = project_root / f"data/outputs/full_scale_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"\n📁 詳細測試結果已保存: {results_file}")
    logger.info("🎯 全量測試完成")


if __name__ == "__main__":
    main()