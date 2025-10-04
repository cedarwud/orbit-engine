#!/usr/bin/env python3
"""
CPU 優化器 - Stage 5 並行處理模組

動態計算最優工作器數量，基於：
- 環境變數配置
- 配置文件設定
- 實時 CPU 使用率
"""

import logging
import os
import multiprocessing as mp
from typing import Dict, Any

logger = logging.getLogger(__name__)

# psutil 用於動態 CPU 檢測（可選依賴）
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("⚠️ psutil 不可用，將使用保守的 CPU 核心配置")


class CPUOptimizer:
    """
    CPU 核心數量動態優化器

    優先級：
    1. 環境變數 ORBIT_ENGINE_MAX_WORKERS
    2. 配置文件 performance.max_workers
    3. 動態 CPU 檢測（使用 psutil）
    4. 保守預設值（75% 核心）
    """

    @staticmethod
    def get_optimal_workers(config: Dict[str, Any]) -> int:
        """
        動態計算最優工作器數量

        Args:
            config: 配置字典

        Returns:
            int: 最優工作器數量
        """
        try:
            # 1. 檢查環境變數設定（最高優先級）
            env_workers = os.environ.get('ORBIT_ENGINE_MAX_WORKERS')
            if env_workers and env_workers.isdigit():
                workers = int(env_workers)
                if workers > 0:
                    logger.info(f"📋 使用環境變數設定: {workers} 個工作器")
                    return workers

            # 2. 檢查配置文件設定
            performance_config = config.get('performance', {})
            config_workers = performance_config.get('max_workers')

            if config_workers and config_workers > 0:
                logger.info(f"📋 使用配置文件設定: {config_workers} 個工作器")
                return config_workers

            # 3. 檢查是否強制單線程
            if performance_config.get('force_single_thread', False):
                logger.info("⚠️ 強制單線程模式")
                return 1

            # 4. 動態 CPU 狀態檢測
            total_cpus = mp.cpu_count()

            if not PSUTIL_AVAILABLE:
                # 沒有 psutil，使用 75% 核心作為預設
                workers = max(1, int(total_cpus * 0.75))
                logger.info(f"💻 未安裝 psutil，使用預設 75% 核心 = {workers} 個工作器")
                return workers

            # 獲取當前 CPU 使用率（採樣 0.5 秒）
            try:
                cpu_usage = psutil.cpu_percent(interval=0.5)

                # 動態策略：根據 CPU 使用率調整
                if cpu_usage < 30:
                    # CPU 空閒：使用 95% 核心（積極並行）
                    workers = max(1, int(total_cpus * 0.95))
                    logger.info(
                        f"💻 CPU 空閒（{cpu_usage:.1f}%）：使用 95% 核心 = {workers} 個工作器"
                    )
                elif cpu_usage < 50:
                    # CPU 中度使用：使用 75% 核心
                    workers = max(1, int(total_cpus * 0.75))
                    logger.info(
                        f"💻 CPU 中度使用（{cpu_usage:.1f}%）：使用 75% 核心 = {workers} 個工作器"
                    )
                else:
                    # CPU 繁忙：使用 50% 核心
                    workers = max(1, int(total_cpus * 0.5))
                    logger.info(
                        f"💻 CPU 繁忙（{cpu_usage:.1f}%）：使用 50% 核心 = {workers} 個工作器"
                    )

                return workers

            except Exception as cpu_error:
                logger.warning(f"⚠️ CPU 狀態檢測失敗: {cpu_error}，使用預設配置")
                # 回退策略：75% 核心
                fallback_workers = max(1, int(total_cpus * 0.75))
                logger.info(f"📋 回退配置: {fallback_workers} 個工作器")
                return fallback_workers

        except Exception as e:
            logger.error(f"❌ 工作器數量計算失敗: {e}，使用單核心")
            return 1
