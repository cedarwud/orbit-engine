#!/usr/bin/env python3
"""
Resource Monitor - Stage 4 優化決策層
資源使用監控模組，用於追蹤記憶體、CPU和處理時間

功能特色：
- 記憶體使用監控
- CPU使用率追蹤
- 處理時間統計
- 資源警告和限制
- 性能基準驗證
"""

import os
import psutil
import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """資源使用快照"""
    timestamp: str
    memory_used_mb: float
    memory_percent: float
    cpu_percent: float
    process_id: int
    thread_count: int
    processing_stage: str


@dataclass
class PerformanceBenchmark:
    """性能基準"""
    max_memory_mb: float = 300.0
    max_cpu_percent: float = 80.0
    max_processing_time_seconds: float = 10.0
    warning_memory_mb: float = 250.0
    warning_cpu_percent: float = 70.0


class ResourceMonitor:
    """
    資源監控器

    提供實時資源使用監控，確保Stage 4處理器
    在性能基準內運行
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

        # 監控配置
        self.enable_monitoring = self.config.get('enable_monitoring', True)
        self.monitoring_interval = self.config.get('monitoring_interval_seconds', 0.1)
        self.enable_warnings = self.config.get('enable_warnings', True)

        # 性能基準
        benchmark_config = self.config.get('performance_benchmarks', {})
        self.benchmarks = PerformanceBenchmark(**benchmark_config)

        # 監控數據
        self.resource_snapshots: List[ResourceSnapshot] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # 當前進程信息
        self.process = psutil.Process()
        self.start_time = time.time()

        # 警告回調
        self.warning_callbacks: List[Callable[[str, ResourceSnapshot], None]] = []

        # 統計信息
        self.peak_memory_mb = 0.0
        self.peak_cpu_percent = 0.0
        self.total_warnings = 0

        self.logger.info("✅ 資源監控器初始化完成")

    def start_monitoring(self, stage_name: str = "optimization_processing"):
        """開始資源監控"""
        if not self.enable_monitoring:
            self.logger.debug("資源監控已禁用")
            return

        if self.monitoring_active:
            self.logger.warning("資源監控已在運行中")
            return

        self.monitoring_active = True
        self.current_stage = stage_name
        self.start_time = time.time()

        # 清除舊數據
        self.resource_snapshots.clear()
        self.peak_memory_mb = 0.0
        self.peak_cpu_percent = 0.0

        # 啟動監控線程
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="ResourceMonitor"
        )
        self.monitor_thread.start()

        self.logger.info(f"🔍 開始資源監控: {stage_name}")

    def stop_monitoring(self) -> Dict[str, Any]:
        """停止資源監控並返回統計"""
        if not self.monitoring_active:
            return {}

        self.monitoring_active = False

        # 等待監控線程結束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

        # 計算最終統計
        monitoring_duration = time.time() - self.start_time
        final_stats = self._calculate_final_statistics(monitoring_duration)

        self.logger.info(f"⏹️ 資源監控已停止，總時長: {monitoring_duration:.3f}s")
        return final_stats

    def _monitoring_loop(self):
        """監控循環"""
        try:
            while self.monitoring_active:
                # 收集資源快照
                snapshot = self._collect_resource_snapshot()
                self.resource_snapshots.append(snapshot)

                # 更新峰值
                self.peak_memory_mb = max(self.peak_memory_mb, snapshot.memory_used_mb)
                self.peak_cpu_percent = max(self.peak_cpu_percent, snapshot.cpu_percent)

                # 檢查警告條件
                if self.enable_warnings:
                    self._check_resource_warnings(snapshot)

                # 等待下次監控
                time.sleep(self.monitoring_interval)

        except Exception as e:
            self.logger.error(f"❌ 資源監控循環錯誤: {e}")

    def _collect_resource_snapshot(self) -> ResourceSnapshot:
        """收集資源使用快照"""
        try:
            # 獲取記憶體信息
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # 轉換為MB

            # 獲取系統記憶體百分比
            system_memory = psutil.virtual_memory()
            memory_percent = (memory_info.rss / system_memory.total) * 100

            # 獲取CPU使用率
            cpu_percent = self.process.cpu_percent()

            # 獲取線程數
            thread_count = self.process.num_threads()

            snapshot = ResourceSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                memory_used_mb=memory_mb,
                memory_percent=memory_percent,
                cpu_percent=cpu_percent,
                process_id=self.process.pid,
                thread_count=thread_count,
                processing_stage=getattr(self, 'current_stage', 'unknown')
            )

            return snapshot

        except Exception as e:
            self.logger.error(f"❌ 收集資源快照失敗: {e}")
            # 返回空快照
            return ResourceSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                memory_used_mb=0.0,
                memory_percent=0.0,
                cpu_percent=0.0,
                process_id=os.getpid(),
                thread_count=1,
                processing_stage="error"
            )

    def _check_resource_warnings(self, snapshot: ResourceSnapshot):
        """檢查資源使用警告"""
        warnings = []

        # 檢查記憶體警告
        if snapshot.memory_used_mb > self.benchmarks.warning_memory_mb:
            if snapshot.memory_used_mb > self.benchmarks.max_memory_mb:
                warnings.append(f"❌ 記憶體使用超限: {snapshot.memory_used_mb:.1f}MB > {self.benchmarks.max_memory_mb}MB")
            else:
                warnings.append(f"⚠️ 記憶體使用警告: {snapshot.memory_used_mb:.1f}MB > {self.benchmarks.warning_memory_mb}MB")

        # 檢查CPU警告
        if snapshot.cpu_percent > self.benchmarks.warning_cpu_percent:
            if snapshot.cpu_percent > self.benchmarks.max_cpu_percent:
                warnings.append(f"❌ CPU使用超限: {snapshot.cpu_percent:.1f}% > {self.benchmarks.max_cpu_percent}%")
            else:
                warnings.append(f"⚠️ CPU使用警告: {snapshot.cpu_percent:.1f}% > {self.benchmarks.warning_cpu_percent}%")

        # 處理警告
        for warning in warnings:
            self.total_warnings += 1
            self.logger.warning(warning)

            # 調用警告回調
            for callback in self.warning_callbacks:
                try:
                    callback(warning, snapshot)
                except Exception as e:
                    self.logger.error(f"❌ 警告回調執行失敗: {e}")

    def _calculate_final_statistics(self, monitoring_duration: float) -> Dict[str, Any]:
        """計算最終統計"""
        if not self.resource_snapshots:
            return {'status': 'no_data', 'duration': monitoring_duration}

        # 記憶體統計
        memory_values = [s.memory_used_mb for s in self.resource_snapshots]
        cpu_values = [s.cpu_percent for s in self.resource_snapshots if s.cpu_percent > 0]

        import statistics

        memory_stats = {
            'peak_mb': self.peak_memory_mb,
            'average_mb': statistics.mean(memory_values),
            'min_mb': min(memory_values),
            'std_dev_mb': statistics.stdev(memory_values) if len(memory_values) > 1 else 0.0
        }

        cpu_stats = {
            'peak_percent': self.peak_cpu_percent,
            'average_percent': statistics.mean(cpu_values) if cpu_values else 0.0,
            'min_percent': min(cpu_values) if cpu_values else 0.0,
            'std_dev_percent': statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0.0
        }

        # 性能基準檢查
        benchmark_compliance = {
            'memory_within_limit': self.peak_memory_mb <= self.benchmarks.max_memory_mb,
            'cpu_within_limit': self.peak_cpu_percent <= self.benchmarks.max_cpu_percent,
            'time_within_limit': monitoring_duration <= self.benchmarks.max_processing_time_seconds,
            'total_warnings': self.total_warnings,
            'overall_compliant': (
                self.peak_memory_mb <= self.benchmarks.max_memory_mb and
                self.peak_cpu_percent <= self.benchmarks.max_cpu_percent and
                monitoring_duration <= self.benchmarks.max_processing_time_seconds
            )
        }

        final_stats = {
            'monitoring_duration_seconds': monitoring_duration,
            'total_snapshots': len(self.resource_snapshots),
            'memory_statistics': memory_stats,
            'cpu_statistics': cpu_stats,
            'benchmark_compliance': benchmark_compliance,
            'performance_benchmarks': asdict(self.benchmarks),
            'monitoring_config': {
                'interval_seconds': self.monitoring_interval,
                'warnings_enabled': self.enable_warnings
            }
        }

        return final_stats

    def get_current_usage(self) -> Dict[str, Any]:
        """獲取當前資源使用情況"""
        if not self.resource_snapshots:
            return {'status': 'no_data'}

        latest = self.resource_snapshots[-1]
        current_time = time.time() - self.start_time

        return {
            'current_memory_mb': latest.memory_used_mb,
            'current_cpu_percent': latest.cpu_percent,
            'peak_memory_mb': self.peak_memory_mb,
            'peak_cpu_percent': self.peak_cpu_percent,
            'elapsed_time_seconds': current_time,
            'total_warnings': self.total_warnings,
            'monitoring_active': self.monitoring_active
        }

    def add_warning_callback(self, callback: Callable[[str, ResourceSnapshot], None]):
        """添加警告回調函數"""
        self.warning_callbacks.append(callback)

    def export_monitoring_data(self, export_path: str):
        """導出監控數據"""
        try:
            monitoring_data = {
                'export_metadata': {
                    'export_timestamp': datetime.now(timezone.utc).isoformat(),
                    'monitor_version': 'resource_monitor_v1.0',
                    'total_snapshots': len(self.resource_snapshots)
                },
                'performance_benchmarks': asdict(self.benchmarks),
                'final_statistics': self._calculate_final_statistics(time.time() - self.start_time),
                'resource_snapshots': [asdict(snapshot) for snapshot in self.resource_snapshots],
                'monitoring_summary': {
                    'peak_memory_mb': self.peak_memory_mb,
                    'peak_cpu_percent': self.peak_cpu_percent,
                    'total_warnings': self.total_warnings,
                    'monitoring_duration': time.time() - self.start_time
                }
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(monitoring_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"✅ 監控數據導出成功: {export_path}")

        except Exception as e:
            self.logger.error(f"❌ 監控數據導出失敗: {e}")
            raise

    def reset_monitoring_data(self):
        """重置監控數據"""
        self.resource_snapshots.clear()
        self.peak_memory_mb = 0.0
        self.peak_cpu_percent = 0.0
        self.total_warnings = 0
        self.logger.info("🧹 監控數據已重置")

    def is_within_benchmarks(self) -> bool:
        """檢查是否在性能基準內"""
        if not self.monitoring_active:
            return True

        return (
            self.peak_memory_mb <= self.benchmarks.max_memory_mb and
            self.peak_cpu_percent <= self.benchmarks.max_cpu_percent
        )

    def get_resource_efficiency_score(self) -> float:
        """計算資源效率分數 (0-1)"""
        if not self.resource_snapshots:
            return 0.0

        # 基於峰值使用率計算效率
        memory_efficiency = 1.0 - (self.peak_memory_mb / self.benchmarks.max_memory_mb)
        cpu_efficiency = 1.0 - (self.peak_cpu_percent / 100.0)

        # 警告懲罰
        warning_penalty = min(0.2, self.total_warnings * 0.05)

        efficiency_score = max(0.0, (memory_efficiency * 0.6 + cpu_efficiency * 0.4) - warning_penalty)
        return efficiency_score