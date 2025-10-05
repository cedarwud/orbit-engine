#!/usr/bin/env python3
"""
CPU 優化器 - Stage 5 並行處理模組

✅ Grade A+ 標準: 100% Fail-Fast
依據: docs/ACADEMIC_STANDARDS.md Line 265-274

動態計算最優工作器數量，基於：
- 環境變數配置（最高優先級）
- 配置文件設定
- 實時 CPU 使用率（psutil 可用時）
- 無配置時拋出異常（Fail-Fast）

Updated: 2025-10-04 - Fail-Fast 重構
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
    logger.warning("⚠️ psutil 不可用，將要求明確配置 max_workers")


class CPUOptimizer:
    """
    CPU 核心數量動態優化器

    ✅ Grade A+ 標準: Fail-Fast 工作器配置
    - psutil 可用時：動態調整（使用實時 CPU 狀態）
    - psutil 不可用時：要求配置中必須提供 max_workers
    - 禁止使用硬編碼預設值（75%、50% 等）

    優先級：
    1. 環境變數 ORBIT_ENGINE_MAX_WORKERS
    2. 配置文件 parallel_processing.max_workers
    3. 動態 CPU 檢測（psutil 可用時）
    4. 拋出異常（psutil 不可用且無配置時）
    """

    @staticmethod
    def get_optimal_workers(config: Dict[str, Any]) -> int:
        """
        動態計算最優工作器數量

        ✅ Grade A+ 標準: Fail-Fast 核心數配置
        - 環境變數優先
        - 配置文件次之
        - psutil 動態檢測（可用時）
        - 無配置時拋出異常

        Args:
            config: 配置字典

        Returns:
            int: 最優工作器數量

        Raises:
            ValueError: 配置不完整且 psutil 不可用
            TypeError: 配置類型錯誤
            RuntimeError: 未預期的錯誤
        """
        try:
            # ========================================================================
            # 第 1 層: 環境變數設定（最高優先級）
            # ========================================================================

            env_workers = os.environ.get('ORBIT_ENGINE_MAX_WORKERS')
            if env_workers and env_workers.isdigit():
                workers = int(env_workers)
                if workers > 0:
                    logger.info(f"📋 使用環境變數設定: {workers} 個工作器")
                    return workers

            # ========================================================================
            # 第 2 層: 配置文件設定
            # ========================================================================

            # 檢查配置文件中的 parallel_processing 配置
            if 'parallel_processing' in config:
                parallel_config = config['parallel_processing']

                # 如果 parallel_config 為 None（所有選項都被註釋），使用預設值
                if parallel_config is None:
                    parallel_config = {}

                if not isinstance(parallel_config, dict):
                    raise TypeError(
                        f"parallel_processing 配置類型錯誤: {type(parallel_config).__name__} (期望: dict)"
                    )

                # 檢查 max_workers
                if 'max_workers' in parallel_config:
                    config_workers = parallel_config['max_workers']

                    if not isinstance(config_workers, int):
                        raise TypeError(
                            f"max_workers 類型錯誤: {type(config_workers).__name__} (期望: int)"
                        )

                    if config_workers <= 0:
                        raise ValueError(
                            f"max_workers 值非法: {config_workers} (必須 > 0)"
                        )

                    logger.info(f"📋 使用配置文件設定: {config_workers} 個工作器")
                    return config_workers

            # ========================================================================
            # 第 3 層: 動態 CPU 狀態檢測（psutil 可用時）
            # ========================================================================

            if PSUTIL_AVAILABLE:
                total_cpus = mp.cpu_count()

                try:
                    # 獲取當前 CPU 使用率（採樣 0.5 秒）
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
                    # CPU 檢測失敗，如果沒有配置則拋出異常
                    raise ValueError(
                        f"CPU 狀態檢測失敗: {cpu_error}\n"
                        f"Grade A 標準禁止使用預設值回退\n"
                        f"請在配置中明確設定:\n"
                        f"  parallel_processing:\n"
                        f"    max_workers: <核心數>  # SOURCE: 系統配置，基於 CPU 核心數"
                    )

            # ========================================================================
            # 第 4 層: psutil 不可用且無配置 - 拋出異常
            # ========================================================================

            total_cpus = mp.cpu_count()
            raise ValueError(
                f"工作器數量配置缺失\n"
                f"Grade A 標準禁止使用預設值（75% 核心）\n"
                f"psutil 不可用，無法動態檢測 CPU 狀態\n"
                f"必須在配置中明確設定:\n"
                f"\n"
                f"方法 1 - 環境變數:\n"
                f"  export ORBIT_ENGINE_MAX_WORKERS=<數量>\n"
                f"\n"
                f"方法 2 - 配置文件:\n"
                f"  parallel_processing:\n"
                f"    max_workers: <數量>  # SOURCE: 系統配置，基於 CPU 核心數\n"
                f"\n"
                f"參考: 當前系統有 {total_cpus} 個 CPU 核心\n"
                f"建議: max_workers = {int(total_cpus * 0.75)} (75% 核心)"
            )

        except ValueError:
            # 數據驗證錯誤 - 直接拋出
            raise

        except TypeError:
            # 類型錯誤 - 直接拋出
            raise

        except Exception as e:
            # 未預期的錯誤 - 包裝後拋出
            raise RuntimeError(
                f"工作器數量計算失敗: {type(e).__name__}: {e}\n"
                f"請檢查配置或環境變數設定"
            ) from e
