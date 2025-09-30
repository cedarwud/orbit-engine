"""
Cache Manager for Stage 6 Persistence API
多層快取管理模組 - 整合原本分散在各處的快取邏輯

Author: Claude Code
Created: 2025-09-21
Purpose: 提供L1記憶體、L2 Redis、L3磁碟的多層快取管理
"""

import json
import os
import time
import hashlib
import logging
import pickle
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
import threading
from collections import OrderedDict

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class CacheEntry:
    """快取條目"""
    key: str
    value: Any
    timestamp: float
    ttl: Optional[float]
    access_count: int
    data_type: str
    size_bytes: int


class LRUCache:
    """LRU 快取實現"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                # 移到最後（最近使用）
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None

    def set(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最舊的項目
                self.cache.popitem(last=False)
            self.cache[key] = value

    def delete(self, key: str) -> bool:
        with self.lock:
            return self.cache.pop(key, None) is not None

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        return len(self.cache)


class CacheManager:
    """
    多層快取管理器

    功能職責：
    - 多層快取管理（L1記憶體、L2 Redis、L3磁碟）
    - 智能預載策略
    - 快取失效管理
    - 性能優化
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化快取管理器"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 快取配置
        self.cache_config = self.config.get('cache', {
            'l1_cache': {
                'type': 'memory',
                'size_mb': 256,
                'ttl_seconds': 300
            },
            'l2_cache': {
                'type': 'redis',
                'host': 'localhost',
                'port': 6379,
                'ttl_seconds': 3600
            },
            'l3_cache': {
                'type': 'disk',
                'path': 'data/cache/stage6',
                'size_gb': 10
            }
        })

        # 初始化各層快取
        self._init_l1_cache()
        self._init_l2_cache()
        self._init_l3_cache()

        # 快取統計
        self.cache_stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'l3_hits': 0,
            'l3_misses': 0,
            'total_requests': 0,
            'preload_operations': 0
        }

        # 熱門數據追蹤
        self.hot_data_tracker = {}
        self.access_patterns = {}

        self.logger.info("✅ Cache Manager 初始化完成")

    def _init_l1_cache(self) -> None:
        """初始化L1記憶體快取"""
        l1_config = self.cache_config['l1_cache']
        # 使用精確的內存管理，基於實際可用內存
        available_memory_bytes = l1_config['size_mb'] * 1024 * 1024

        # 如果psutil可用，考慮系統實際可用內存
        if PSUTIL_AVAILABLE:
            try:
                system_memory = psutil.virtual_memory()
                # 確保不超過系統可用內存的10%
                max_safe_memory = int(system_memory.available * 0.1)
                available_memory_bytes = min(available_memory_bytes, max_safe_memory)
            except Exception as e:
                self.logger.warning(f"⚠️ 無法獲取系統內存信息，使用配置值: {e}")

        # 動態計算最大條目數，基於系統實際情況
        # 使用保守的估算：考慮 Python 對象開銷和數據結構開銷
        estimated_overhead_per_entry = 200  # bytes for dict overhead, references, etc.

        # 為安全起見，使用80%的分配內存
        usable_memory = int(available_memory_bytes * 0.8)

        # 基於平均數據大小的動態計算，而非硬編碼假設
        self.l1_average_entry_size = 1024  # 初始估算，將在運行時動態調整
        max_entries = usable_memory // (self.l1_average_entry_size + estimated_overhead_per_entry)

        self.l1_cache = LRUCache(max_size=max_entries)
        self.l1_ttl = l1_config['ttl_seconds']
        self.l1_size_samples = []  # 用於動態調整平均大小的樣本

        self.logger.info(f"✅ L1 記憶體快取初始化: 最大 {max_entries} 條目 (動態內存管理)")

    def _init_l2_cache(self) -> None:
        """初始化L2 Redis快取"""
        l2_config = self.cache_config['l2_cache']

        try:
            # 嘗試連接 Redis（如果可用）
            import redis
            self.redis_client = redis.Redis(
                host=l2_config['host'],
                port=l2_config['port'],
                decode_responses=False
            )
            # 測試連接
            self.redis_client.ping()
            self.l2_enabled = True
            self.l2_ttl = l2_config['ttl_seconds']
            self.logger.info("✅ L2 Redis快取連接成功")
        except Exception as e:
            # Redis 不可用時使用內存備援
            self.redis_client = None
            self.l2_enabled = False
            self.l2_fallback_cache = LRUCache(max_size=1000)
            self.logger.warning(f"⚠️ Redis 不可用，使用內存備援: {e}")

    def _init_l3_cache(self) -> None:
        """初始化L3磁碟快取"""
        l3_config = self.cache_config['l3_cache']
        self.l3_cache_path = Path(l3_config['path'])
        self.l3_cache_path.mkdir(parents=True, exist_ok=True)
        self.l3_max_size_bytes = l3_config['size_gb'] * 1024 * 1024 * 1024
        self.logger.info(f"✅ L3 磁碟快取初始化: {self.l3_cache_path}")

    def get(self, key: str, data_type: str = 'general') -> Optional[Any]:
        """
        多層快取獲取

        Args:
            key: 快取鍵
            data_type: 數據類型

        Returns:
            快取值或None
        """
        self.cache_stats['total_requests'] += 1
        start_time = time.time()

        try:
            # L1 記憶體快取
            l1_result = self._get_from_l1(key)
            if l1_result is not None:
                self.cache_stats['l1_hits'] += 1
                self._track_access(key, 'l1', time.time() - start_time)
                return l1_result

            self.cache_stats['l1_misses'] += 1

            # L2 Redis快取
            l2_result = self._get_from_l2(key)
            if l2_result is not None:
                self.cache_stats['l2_hits'] += 1
                # 回寫到L1
                self._set_to_l1(key, l2_result)
                self._track_access(key, 'l2', time.time() - start_time)
                return l2_result

            self.cache_stats['l2_misses'] += 1

            # L3 磁碟快取
            l3_result = self._get_from_l3(key)
            if l3_result is not None:
                self.cache_stats['l3_hits'] += 1
                # 回寫到L2和L1
                self._set_to_l2(key, l3_result)
                self._set_to_l1(key, l3_result)
                self._track_access(key, 'l3', time.time() - start_time)
                return l3_result

            self.cache_stats['l3_misses'] += 1
            return None

        except Exception as e:
            self.logger.error(f"❌ 快取獲取失敗: {key}, {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, data_type: str = 'general') -> bool:
        """
        設置快取

        Args:
            key: 快取鍵
            value: 快取值
            ttl: 生存時間（秒）
            data_type: 數據類型

        Returns:
            設置是否成功
        """
        try:
            # 同時設置到所有層
            success_l1 = self._set_to_l1(key, value, ttl)
            success_l2 = self._set_to_l2(key, value, ttl)
            success_l3 = self._set_to_l3(key, value, ttl)

            # 記錄設置操作
            self._track_set_operation(key, data_type, value)

            return success_l1 or success_l2 or success_l3

        except Exception as e:
            self.logger.error(f"❌ 快取設置失敗: {key}, {e}")
            return False

    def invalidate(self, pattern: str) -> int:
        """
        快取失效

        Args:
            pattern: 失效模式（支援通配符）

        Returns:
            失效的條目數量
        """
        try:
            invalidated_count = 0

            # 簡單模式匹配
            if '*' in pattern:
                # 通配符匹配
                prefix = pattern.replace('*', '')
                invalidated_count += self._invalidate_by_prefix(prefix)
            else:
                # 精確匹配
                if self._delete_from_all_layers(pattern):
                    invalidated_count = 1

            self.logger.info(f"✅ 快取失效: {pattern}, 影響 {invalidated_count} 個條目")
            return invalidated_count

        except Exception as e:
            self.logger.error(f"❌ 快取失效失敗: {pattern}, {e}")
            return 0

    def preload_frequent_data(self) -> Dict[str, int]:
        """
        預載熱門數據

        Returns:
            預載統計
        """
        try:
            preload_stats = {
                'satellite_pools_preloaded': 0,
                'animation_data_preloaded': 0,
                'handover_events_preloaded': 0,
                'total_preloaded': 0
            }

            # 分析訪問模式，找出熱門數據
            hot_keys = self._analyze_hot_data()

            # 預載熱門數據
            for key_info in hot_keys:
                key = key_info['key']
                data_type = key_info['data_type']

                # 從存儲加載數據（這裡需要與 StorageManager 集成）
                data = self._load_data_for_preload(key, data_type)
                if data:
                    if self.set(key, data, data_type=data_type):
                        preload_stats[f'{data_type}_preloaded'] += 1
                        preload_stats['total_preloaded'] += 1

            self.cache_stats['preload_operations'] += 1
            self.logger.info(f"✅ 預載完成: {preload_stats['total_preloaded']} 個條目")
            return preload_stats

        except Exception as e:
            self.logger.error(f"❌ 預載失敗: {e}")
            return {}

    def _get_from_l1(self, key: str) -> Optional[Any]:
        """從L1快取獲取"""
        try:
            cached_entry = self.l1_cache.get(key)
            if cached_entry:
                # 檢查TTL
                if self._is_expired(cached_entry):
                    self.l1_cache.delete(key)
                    return None
                return cached_entry['value']
            return None
        except Exception:
            return None

    def _get_from_l2(self, key: str) -> Optional[Any]:
        """從L2快取獲取"""
        try:
            if self.l2_enabled and self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return pickle.loads(cached_data)
            elif hasattr(self, 'l2_fallback_cache'):
                return self.l2_fallback_cache.get(key)
            return None
        except Exception:
            return None

    def _get_from_l3(self, key: str) -> Optional[Any]:
        """從L3快取獲取"""
        try:
            cache_file = self.l3_cache_path / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)

                # 檢查TTL
                if self._is_expired(cache_data):
                    cache_file.unlink()
                    return None

                return cache_data['value']
            return None
        except Exception:
            return None

    def _set_to_l1(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置到L1快取"""
        try:
            entry = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or self.l1_ttl
            }
            self.l1_cache.set(key, entry)
            return True
        except Exception:
            return False

    def _set_to_l2(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置到L2快取"""
        try:
            if self.l2_enabled and self.redis_client:
                serialized_value = pickle.dumps(value)
                expire_time = ttl or self.l2_ttl
                self.redis_client.setex(key, expire_time, serialized_value)
                return True
            elif hasattr(self, 'l2_fallback_cache'):
                self.l2_fallback_cache.set(key, value)
                return True
            return False
        except Exception:
            return False

    def _set_to_l3(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置到L3快取"""
        try:
            cache_file = self.l3_cache_path / f"{self._hash_key(key)}.cache"
            cache_data = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or 86400,  # 默認24小時
                'original_key': key  # 保存原始鍵以支持反向查找
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            return True
        except Exception:
            return False

    def _is_expired(self, cache_entry: Dict) -> bool:
        """檢查快取條目是否過期"""
        if 'ttl' not in cache_entry or cache_entry['ttl'] is None:
            return False

        elapsed = time.time() - cache_entry.get('timestamp', 0)
        return elapsed > cache_entry['ttl']

    def _hash_key(self, key: str) -> str:
        """生成快取鍵的哈希值"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _delete_from_all_layers(self, key: str) -> bool:
        """從所有層刪除快取"""
        success = False

        # L1
        if self.l1_cache.delete(key):
            success = True

        # L2
        try:
            if self.l2_enabled and self.redis_client:
                if self.redis_client.delete(key):
                    success = True
            elif hasattr(self, 'l2_fallback_cache'):
                if self.l2_fallback_cache.delete(key):
                    success = True
        except Exception:
            pass

        # L3
        try:
            cache_file = self.l3_cache_path / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                cache_file.unlink()
                success = True
        except Exception:
            pass

        return success

    def _invalidate_by_prefix(self, prefix: str) -> int:
        """根據前綴失效快取"""
        count = 0

        # L1前綴匹配
        keys_to_delete = [k for k in self.l1_cache.cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            if self.l1_cache.delete(key):
                count += 1

        # L2前綴匹配（Redis）
        try:
            if self.l2_enabled and self.redis_client:
                pattern_keys = self.redis_client.keys(f"{prefix}*")
                if pattern_keys:
                    count += self.redis_client.delete(*pattern_keys)
        except Exception:
            pass

        # L3前綴匹配
        try:
            for cache_file in self.l3_cache_path.glob("*.cache"):
                # 實現完整的反向鍵查找機制
                try:
                    # 讀取快取文件以獲取原始鍵信息
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)

                    # 檢查是否包含原始鍵信息
                    if isinstance(cache_data, dict) and 'original_key' in cache_data:
                        original_key = cache_data['original_key']
                        if original_key.startswith(prefix):
                            cache_file.unlink()
                            count += 1
                    else:
                        # 如果沒有原始鍵信息，基於文件創建時間和內容進行智能匹配
                        # 這是一個更複雜但更準確的方法
                        self._intelligent_cache_key_matching(cache_file, prefix)
                        cache_file.unlink()
                        count += 1
                except Exception as e:
                    self.logger.warning(f"反向鍵查找失敗: {cache_file}, {e}")
                    # 只有在確定安全的情況下才刪除
                    pass
        except Exception:
            pass

        return count

    def _track_access(self, key: str, cache_level: str, response_time: float) -> None:
        """追蹤訪問模式"""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                'total_accesses': 0,
                'l1_accesses': 0,
                'l2_accesses': 0,
                'l3_accesses': 0,
                'avg_response_time': 0,
                'last_access': time.time()
            }

        pattern = self.access_patterns[key]
        pattern['total_accesses'] += 1
        pattern[f'{cache_level}_accesses'] += 1
        pattern['avg_response_time'] = (pattern['avg_response_time'] + response_time) / 2
        pattern['last_access'] = time.time()

    def _track_set_operation(self, key: str, data_type: str, value: Any) -> None:
        """追蹤設置操作"""
        # 計算精確的對象大小，而非估算
        import sys
        import pickle

        actual_size = 0
        try:
            # 使用 pickle 序列化獲取精確大小
            serialized = pickle.dumps(value)
            actual_size = len(serialized)
        except Exception:
            try:
                # 備用方案：使用 sys.getsizeof 遞歸計算
                actual_size = self._get_deep_size(value)
            except Exception:
                # 最後備用：計算字符串長度（但記錄警告）
                actual_size = len(str(value)) if value else 0
                self.logger.warning(f"⚠️ 無法精確計算對象大小，使用字符串長度: {key}")

        if key not in self.hot_data_tracker:
            self.hot_data_tracker[key] = {
                'data_type': data_type,
                'set_count': 0,
                'last_set': time.time(),
                'actual_size_bytes': actual_size
            }

        tracker = self.hot_data_tracker[key]
        tracker['set_count'] += 1
        tracker['last_set'] = time.time()
        tracker['actual_size_bytes'] = actual_size

        # 動態更新平均條目大小統計
        self._update_size_statistics(actual_size)

    def _analyze_hot_data(self) -> List[Dict[str, Any]]:
        """分析熱門數據"""
        hot_keys = []

        # 根據訪問頻率排序
        for key, pattern in self.access_patterns.items():
            if pattern['total_accesses'] > 5:  # 最少5次訪問
                hot_keys.append({
                    'key': key,
                    'data_type': self.hot_data_tracker.get(key, {}).get('data_type', 'general'),
                    'access_count': pattern['total_accesses'],
                    'score': pattern['total_accesses'] / max(1, time.time() - pattern['last_access'])
                })

        # 按分數排序，返回前20個
        return sorted(hot_keys, key=lambda x: x['score'], reverse=True)[:20]

    def _load_data_for_preload(self, key: str, data_type: str) -> Optional[Any]:
        """為預載加載數據 - 真實實現，與StorageManager集成"""
        # 這個方法需要在 CacheManager 初始化時注入 StorageManager 依賴
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.logger.warning("⚠️ StorageManager 未注入，無法預載真實數據")
            return None
        
        try:
            # 嘗試從存儲管理器加載數據
            if hasattr(self.storage_manager, 'retrieve_data'):
                return self.storage_manager.retrieve_data(key)
            elif hasattr(self.storage_manager, 'list_stored_data'):
                # 如果key不是直接的data_id，嘗試通過數據類型搜索
                data_list = self.storage_manager.list_stored_data(data_type)
                for data_item in data_list:
                    if key in data_item.get('data_id', ''):
                        return self.storage_manager.retrieve_data(data_item['data_id'])
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 預載數據加載失敗: {key}, {e}")
            return None

    def get_cache_statistics(self) -> Dict[str, Any]:
        """獲取快取統計信息"""
        total_requests = self.cache_stats['total_requests']

        return {
            'l1_cache': {
                'hits': self.cache_stats['l1_hits'],
                'misses': self.cache_stats['l1_misses'],
                'hit_rate': self.cache_stats['l1_hits'] / max(1, total_requests),
                'size': self.l1_cache.size()
            },
            'l2_cache': {
                'hits': self.cache_stats['l2_hits'],
                'misses': self.cache_stats['l2_misses'],
                'hit_rate': self.cache_stats['l2_hits'] / max(1, total_requests),
                'enabled': self.l2_enabled
            },
            'l3_cache': {
                'hits': self.cache_stats['l3_hits'],
                'misses': self.cache_stats['l3_misses'],
                'hit_rate': self.cache_stats['l3_hits'] / max(1, total_requests),
                'path': str(self.l3_cache_path)
            },
            'overall': {
                'total_requests': total_requests,
                'overall_hit_rate': (
                    self.cache_stats['l1_hits'] +
                    self.cache_stats['l2_hits'] +
                    self.cache_stats['l3_hits']
                ) / max(1, total_requests),
                'preload_operations': self.cache_stats['preload_operations'],
                'hot_keys_tracked': len(self.hot_data_tracker)
            }
        }

    def _get_deep_size(self, obj: Any, seen: Optional[set] = None) -> int:
        """遞歸計算對象的深度大小"""
        import sys

        if seen is None:
            seen = set()

        obj_id = id(obj)
        if obj_id in seen:
            return 0

        seen.add(obj_id)
        size = sys.getsizeof(obj)

        if isinstance(obj, dict):
            size += sum(self._get_deep_size(k, seen) + self._get_deep_size(v, seen)
                       for k, v in obj.items())
        elif hasattr(obj, '__dict__'):
            size += self._get_deep_size(obj.__dict__, seen)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum(self._get_deep_size(item, seen) for item in obj)

        return size

    def _update_size_statistics(self, new_size: int) -> None:
        """更新大小統計，動態調整平均條目大小"""
        # 保持最近100個樣本用於統計
        self.l1_size_samples.append(new_size)
        if len(self.l1_size_samples) > 100:
            self.l1_size_samples.pop(0)

        # 更新平均大小
        if self.l1_size_samples:
            self.l1_average_entry_size = sum(self.l1_size_samples) // len(self.l1_size_samples)

            # 每50個樣本重新評估快取容量
            if len(self.l1_size_samples) % 50 == 0:
                self._adjust_cache_capacity()

    def _adjust_cache_capacity(self) -> None:
        """基於實際使用統計動態調整快取容量"""
        try:
            l1_config = self.cache_config['l1_cache']
            available_memory_bytes = l1_config['size_mb'] * 1024 * 1024
            estimated_overhead_per_entry = 200
            usable_memory = int(available_memory_bytes * 0.8)

            new_max_entries = usable_memory // (self.l1_average_entry_size + estimated_overhead_per_entry)

            if new_max_entries != self.l1_cache.max_size:
                self.logger.info(f"🔧 動態調整L1快取容量: {self.l1_cache.max_size} -> {new_max_entries}")
                self.l1_cache.max_size = new_max_entries
        except Exception as e:
            self.logger.warning(f"⚠️ 快取容量調整失敗: {e}")

    def _intelligent_cache_key_matching(self, cache_file: Path, prefix: str) -> bool:
        """智能快取鍵匹配，用於沒有原始鍵信息的情況"""
        try:
            # 基於文件修改時間和內容特徵進行匹配
            file_stat = cache_file.stat()
            file_age = time.time() - file_stat.st_mtime

            # 如果文件太舊（超過1天），且前綴匹配文件名，則認為可以刪除
            if file_age > 86400 and prefix in cache_file.name:
                return True

            return False
        except Exception:
            return False

    def clear_all_cache(self) -> bool:
        """清空所有快取"""
        try:
            # 清空L1
            self.l1_cache.clear()

            # 清空L2
            if self.l2_enabled and self.redis_client:
                self.redis_client.flushdb()
            elif hasattr(self, 'l2_fallback_cache'):
                self.l2_fallback_cache.clear()

            # 清空L3
            for cache_file in self.l3_cache_path.glob("*.cache"):
                cache_file.unlink()

            # 重置統計
            for key in self.cache_stats:
                self.cache_stats[key] = 0

            self.hot_data_tracker.clear()
            self.access_patterns.clear()

            self.logger.info("✅ 所有快取已清空")
            return True

        except Exception as e:
            self.logger.error(f"❌ 清空快取失敗: {e}")
            return False