# P2: HDF5 儲存策略統一

**優先級**: 🟠 P2 - 中等優先級（應該執行）
**預估時間**: 0.5天
**依賴**: Phase 3 完成（BaseResultManager 已建立）
**影響範圍**: Stage 2（雙格式輸出）, Stage 3（緩存策略）

---

## 📊 問題分析

### 當前狀態

**HDF5 使用現況**:

| Stage | HDF5用途 | 實作方式 | 數據規模 | 問題 |
|-------|---------|---------|---------|------|
| **Stage 2** | 雙格式輸出（JSON + HDF5） | `save_results(output_format='both')` | ~1.7M 坐標點 | 實作與其他階段不一致 |
| **Stage 3** | 坐標緩存（加速重算） | `Stage3HDF5Cache` 類別 | 154MB 緩存檔 | 緩存邏輯散落在多處 |
| **Stage 1,4,5,6** | 不使用 HDF5 | 僅 JSON 輸出 | - | - |

---

### Stage 2: 雙格式輸出模式

**檔案位置**: `src/stages/stage2_orbital_computing/stage2_result_manager.py`

**實作方式**:

```python
def save_results(self, results, output_format='json', custom_filename=None):
    """
    覆寫基類 save_results() 支援 HDF5 輸出

    Args:
        output_format: 'json' | 'hdf5' | 'both'
    """
    # Step 1: 先呼叫基類保存 JSON
    json_path = super().save_results(results, 'json', custom_filename)

    # Step 2: 如果需要 HDF5，額外保存
    if output_format in ['hdf5', 'both']:
        hdf5_path = self._save_hdf5(results, custom_filename)

        if output_format == 'hdf5':
            return hdf5_path
        else:  # 'both'
            return json_path, hdf5_path

    return json_path
```

**設計考量**:
- ✅ **優點**: 完全向後相容（預設仍是 JSON）
- ✅ **優點**: HDF5 作為可選輸出格式
- ⚠️ **問題**: 實作邏輯與 BaseResultManager 設計模式不一致（覆寫 template method）

---

### Stage 3: HDF5 緩存模式

**檔案位置**: `src/stages/stage3_coordinate_transformation/stage3_hdf5_cache.py`

**實作方式**:

```python
class Stage3HDF5Cache:
    """
    Stage 3 坐標轉換 HDF5 緩存管理器

    功能:
    1. 檢查緩存是否存在且有效（基於 Stage 2 輸出時間戳）
    2. 從 HDF5 緩存讀取坐標數據
    3. 將新計算的坐標數據寫入 HDF5 緩存
    """

    def __init__(self, cache_dir='data/cache/stage3'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_cache_valid(self, stage2_timestamp):
        """
        檢查緩存是否有效

        邏輯: HDF5 檔案修改時間 > Stage 2 輸出檔案修改時間
        """
        cache_file = self.cache_dir / 'coordinate_cache.h5'
        if not cache_file.exists():
            return False

        cache_mtime = cache_file.stat().st_mtime
        return cache_mtime > stage2_timestamp

    def load_from_cache(self, satellite_id):
        """從 HDF5 緩存讀取單個衛星的坐標數據"""
        with h5py.File(self.cache_dir / 'coordinate_cache.h5', 'r') as f:
            if satellite_id in f:
                return f[satellite_id][:]
            return None

    def save_to_cache(self, satellite_data_dict):
        """將所有衛星坐標數據寫入 HDF5 緩存"""
        with h5py.File(self.cache_dir / 'coordinate_cache.h5', 'w') as f:
            for sat_id, coord_array in satellite_data_dict.items():
                f.create_dataset(sat_id, data=coord_array, compression='gzip')
```

**使用場景**:

```python
# Stage 3 Processor 中的使用

cache = Stage3HDF5Cache()

# 檢查緩存
if cache.is_cache_valid(stage2_output_timestamp):
    logger.info("✅ 使用 HDF5 緩存（跳過坐標轉換計算）")
    for sat_id in satellite_ids:
        coordinates = cache.load_from_cache(sat_id)
        results[sat_id] = coordinates
else:
    logger.info("🔄 執行完整坐標轉換（無有效緩存）")
    for sat_id in satellite_ids:
        coordinates = transform_coordinates(sat_id)
        results[sat_id] = coordinates

    # 計算完成後保存緩存
    cache.save_to_cache(results)
```

**設計考量**:
- ✅ **優點**: 顯著加速 Stage 3 重算（25min → 2min）
- ✅ **優點**: 基於時間戳的智能緩存失效檢測
- ⚠️ **問題**: 緩存邏輯與 ResultManager 解耦（獨立類別）
- ⚠️ **問題**: 緩存有效性檢查散落在 Processor 中

---

### 核心問題

**1. 實作模式不統一**:
- Stage 2: HDF5 邏輯嵌入 ResultManager
- Stage 3: HDF5 邏輯獨立為 Cache 類別
- 兩種模式缺少統一抽象

**2. 代碼重複**:
```python
# Stage 2 和 Stage 3 都有類似的 HDF5 寫入邏輯
with h5py.File(output_path, 'w') as f:
    for sat_id, data in satellite_data.items():
        f.create_dataset(sat_id, data=data, compression='gzip')
```

**3. 緩存策略不明確**:
- 何時應該使用 HDF5？（數據規模 > 1GB？）
- 何時應該啟用緩存？（計算時間 > 10min？）
- 缺少統一的決策指引

**4. 測試覆蓋不足**:
- Stage 2 HDF5 輸出：有基本測試
- Stage 3 HDF5 緩存：缺少單元測試（僅集成測試）

---

## 🎯 設計目標

### 主要目標

1. **抽取共同模式** - 建立 `BaseHDF5Handler` 統一 HDF5 操作
2. **策略模式分離** - HDF5 輸出 vs 緩存使用不同策略
3. **保持現有優勢** - Stage 2 雙格式輸出、Stage 3 快速緩存不受影響
4. **向後相容** - 所有現有接口保持不變
5. **測試覆蓋** - 補充 HDF5 相關單元測試

### 成功指標

- ✅ HDF5 操作代碼減少 ~50行（抽取共同邏輯）
- ✅ Stage 2/3 使用統一 HDF5 handler
- ✅ HDF5 相關單元測試覆蓋率 ≥ 80%
- ✅ 性能無退化（Stage 3 緩存加速 ≥ 90%）
- ✅ 向後相容性 100%

---

## 🏗️ 設計方案

### Strategy Pattern 應用

**核心設計**: 使用 Strategy Pattern 分離「HDF5 輸出」和「HDF5 緩存」兩種場景

```
BaseHDF5Handler (抽象基類)
├── HDF5OutputStrategy (Stage 2: 雙格式輸出)
└── HDF5CacheStrategy (Stage 3: 緩存加速)
```

---

## 💻 實作細節

### 1. BaseHDF5Handler 基類

**檔案位置**: `src/shared/hdf5_handler.py` (新建)

```python
"""
💾 HDF5 Handler - Strategy Pattern for HDF5 Operations

Unified HDF5 handling for output and caching strategies.
Eliminates code duplication between Stage 2 (output) and Stage 3 (cache).

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)

Design Philosophy:
-----------------
1. **Strategy Pattern**: Separate output vs cache strategies
2. **Template Method**: Common HDF5 operations in base class
3. **Fail-Fast**: Validate HDF5 data integrity
4. **Performance**: gzip compression for large datasets

Usage Example:
--------------
# Stage 2: Output strategy
handler = HDF5OutputStrategy(output_dir='data/outputs/stage2')
handler.save(satellite_data, filename='stage2_orbital_propagation.h5')

# Stage 3: Cache strategy
cache = HDF5CacheStrategy(cache_dir='data/cache/stage3')
if cache.is_valid(upstream_timestamp):
    data = cache.load(satellite_id)
else:
    data = compute_coordinates()
    cache.save({satellite_id: data})
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Union
import h5py
import numpy as np


class BaseHDF5Handler(ABC):
    """
    Base class for HDF5 operations

    Provides common HDF5 read/write operations with compression and validation.
    Subclasses implement specific strategies (output vs cache).

    Template Methods (implemented here):
    ------------------------------------
    - save(): Save data to HDF5 file
    - load(): Load data from HDF5 file
    - _write_hdf5_dataset(): Write single dataset with compression
    - _read_hdf5_dataset(): Read single dataset

    Abstract Methods (subclass must implement):
    -------------------------------------------
    - get_hdf5_path(): Return HDF5 file path for given context
    - is_valid(): Check if HDF5 data is valid (for cache strategy)
    """

    def __init__(
        self,
        base_dir: Union[str, Path],
        compression: str = 'gzip',
        compression_opts: int = 4,
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Initialize HDF5 handler

        Args:
            base_dir: Base directory for HDF5 files
            compression: Compression algorithm ('gzip', 'lzf', or None)
            compression_opts: Compression level (1-9 for gzip)
            logger_instance: Optional logger instance
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.compression = compression
        self.compression_opts = compression_opts

        self.logger = logger_instance or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    # ==================== Abstract Methods ====================

    @abstractmethod
    def get_hdf5_path(self, identifier: str) -> Path:
        """
        Get HDF5 file path for given identifier

        Args:
            identifier: Context-specific identifier (filename or cache key)

        Returns:
            HDF5 file path

        Example (Output Strategy):
            identifier='stage2_output_20251015_120000'
            returns: Path('data/outputs/stage2/stage2_output_20251015_120000.h5')

        Example (Cache Strategy):
            identifier='coordinate_cache'
            returns: Path('data/cache/stage3/coordinate_cache.h5')
        """
        pass

    # ==================== Template Methods ====================

    def save(
        self,
        data: Dict[str, Union[np.ndarray, Dict[str, Any]]],
        identifier: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Template method: Save data to HDF5 file

        Standard workflow:
        1. Get HDF5 file path from subclass
        2. Write all datasets with compression
        3. Optionally write metadata as attributes
        4. Validate written data
        5. Log success

        Args:
            data: Dictionary mapping dataset names to numpy arrays
            identifier: Context-specific identifier for file path
            metadata: Optional metadata to store as HDF5 attributes

        Returns:
            Path to saved HDF5 file

        Example:
            handler.save(
                data={'SAT-12345': coordinates_array},
                identifier='stage2_output_20251015_120000',
                metadata={'stage': 2, 'timestamp': '...'}
            )
        """
        hdf5_path = self.get_hdf5_path(identifier)

        try:
            with h5py.File(hdf5_path, 'w') as f:
                # Write datasets
                for dataset_name, dataset_data in data.items():
                    self._write_hdf5_dataset(f, dataset_name, dataset_data)

                # Write metadata as root attributes
                if metadata:
                    for key, value in metadata.items():
                        f.attrs[key] = str(value)  # Convert to string for safety

            # Validate written data
            if not self._validate_hdf5_file(hdf5_path, list(data.keys())):
                raise IOError(f"HDF5 validation failed: {hdf5_path}")

            file_size_mb = hdf5_path.stat().st_size / (1024 * 1024)
            self.logger.info(
                f"💾 HDF5 文件已保存: {hdf5_path} ({file_size_mb:.1f} MB)"
            )

            return hdf5_path

        except Exception as e:
            self.logger.error(f"❌ HDF5 保存失敗: {hdf5_path} - {e}")
            raise IOError(f"無法保存 HDF5 文件: {e}")

    def load(
        self,
        identifier: str,
        dataset_name: Optional[str] = None
    ) -> Union[Dict[str, np.ndarray], np.ndarray]:
        """
        Template method: Load data from HDF5 file

        Args:
            identifier: Context-specific identifier for file path
            dataset_name: Optional specific dataset name to load
                         If None, loads all datasets

        Returns:
            - If dataset_name provided: numpy array
            - If dataset_name is None: dict mapping names to arrays

        Example:
            # Load all datasets
            all_data = handler.load('stage2_output_20251015_120000')

            # Load specific satellite
            sat_data = handler.load('coordinate_cache', 'SAT-12345')
        """
        hdf5_path = self.get_hdf5_path(identifier)

        if not hdf5_path.exists():
            raise FileNotFoundError(f"HDF5 文件不存在: {hdf5_path}")

        try:
            with h5py.File(hdf5_path, 'r') as f:
                if dataset_name:
                    # Load specific dataset
                    if dataset_name not in f:
                        raise KeyError(f"Dataset '{dataset_name}' not found in {hdf5_path}")
                    return self._read_hdf5_dataset(f, dataset_name)
                else:
                    # Load all datasets
                    data = {}
                    for name in f.keys():
                        data[name] = self._read_hdf5_dataset(f, name)
                    return data

        except Exception as e:
            self.logger.error(f"❌ HDF5 讀取失敗: {hdf5_path} - {e}")
            raise IOError(f"無法讀取 HDF5 文件: {e}")

    def exists(self, identifier: str) -> bool:
        """
        Check if HDF5 file exists

        Args:
            identifier: Context-specific identifier

        Returns:
            True if file exists
        """
        return self.get_hdf5_path(identifier).exists()

    def get_metadata(self, identifier: str) -> Dict[str, Any]:
        """
        Load metadata from HDF5 file attributes

        Args:
            identifier: Context-specific identifier

        Returns:
            Metadata dictionary
        """
        hdf5_path = self.get_hdf5_path(identifier)

        if not hdf5_path.exists():
            return {}

        try:
            with h5py.File(hdf5_path, 'r') as f:
                return dict(f.attrs)
        except Exception as e:
            self.logger.warning(f"⚠️ 無法讀取 HDF5 metadata: {e}")
            return {}

    # ==================== Helper Methods ====================

    def _write_hdf5_dataset(
        self,
        hdf5_file: h5py.File,
        dataset_name: str,
        data: np.ndarray
    ) -> None:
        """
        Write single dataset with compression

        Args:
            hdf5_file: Opened HDF5 file handle
            dataset_name: Dataset name
            data: Numpy array data
        """
        if not isinstance(data, np.ndarray):
            data = np.array(data)

        hdf5_file.create_dataset(
            dataset_name,
            data=data,
            compression=self.compression,
            compression_opts=self.compression_opts
        )

    def _read_hdf5_dataset(
        self,
        hdf5_file: h5py.File,
        dataset_name: str
    ) -> np.ndarray:
        """
        Read single dataset

        Args:
            hdf5_file: Opened HDF5 file handle
            dataset_name: Dataset name

        Returns:
            Numpy array data
        """
        return hdf5_file[dataset_name][:]

    def _validate_hdf5_file(
        self,
        hdf5_path: Path,
        expected_datasets: list
    ) -> bool:
        """
        Validate HDF5 file integrity

        Args:
            hdf5_path: HDF5 file path
            expected_datasets: List of expected dataset names

        Returns:
            True if valid
        """
        try:
            with h5py.File(hdf5_path, 'r') as f:
                for dataset_name in expected_datasets:
                    if dataset_name not in f:
                        self.logger.error(f"❌ Dataset '{dataset_name}' 缺失")
                        return False
            return True
        except Exception as e:
            self.logger.error(f"❌ HDF5 驗證失敗: {e}")
            return False


# ==================== Strategy 1: Output Strategy ====================

class HDF5OutputStrategy(BaseHDF5Handler):
    """
    HDF5 Output Strategy - For dual-format output (JSON + HDF5)

    Used by Stage 2 to save orbital propagation results in both formats.

    Usage Example:
        handler = HDF5OutputStrategy(output_dir='data/outputs/stage2')

        # Save orbital propagation results
        hdf5_path = handler.save(
            data={'SAT-12345': teme_coordinates_array},
            identifier='stage2_orbital_propagation_20251015_120000',
            metadata={'stage': 2, 'satellite_count': 9015}
        )
    """

    def get_hdf5_path(self, identifier: str) -> Path:
        """
        Get HDF5 output file path

        Args:
            identifier: Filename without extension

        Returns:
            Full HDF5 file path

        Example:
            identifier='stage2_output_20251015_120000'
            returns: Path('data/outputs/stage2/stage2_output_20251015_120000.h5')
        """
        if not identifier.endswith('.h5'):
            identifier = f"{identifier}.h5"

        return self.base_dir / identifier


# ==================== Strategy 2: Cache Strategy ====================

class HDF5CacheStrategy(BaseHDF5Handler):
    """
    HDF5 Cache Strategy - For computation result caching

    Used by Stage 3 to cache coordinate transformation results.
    Provides cache validation based on upstream timestamp.

    Usage Example:
        cache = HDF5CacheStrategy(cache_dir='data/cache/stage3')

        # Check cache validity
        if cache.is_valid('coordinate_cache', upstream_timestamp):
            coordinates = cache.load('coordinate_cache', 'SAT-12345')
        else:
            coordinates = transform_coordinates()
            cache.save(
                data={'SAT-12345': coordinates},
                identifier='coordinate_cache',
                metadata={'upstream_timestamp': upstream_timestamp}
            )
    """

    def get_hdf5_path(self, identifier: str) -> Path:
        """
        Get HDF5 cache file path

        Args:
            identifier: Cache identifier (typically 'coordinate_cache')

        Returns:
            Full HDF5 cache file path

        Example:
            identifier='coordinate_cache'
            returns: Path('data/cache/stage3/coordinate_cache.h5')
        """
        if not identifier.endswith('.h5'):
            identifier = f"{identifier}.h5"

        return self.base_dir / identifier

    def is_valid(self, identifier: str, upstream_timestamp: float) -> bool:
        """
        Check if cache is valid based on upstream timestamp

        Cache is valid if:
        1. Cache file exists
        2. Cache file modification time > upstream timestamp

        Args:
            identifier: Cache identifier
            upstream_timestamp: Upstream file timestamp (Unix epoch)

        Returns:
            True if cache is valid and can be used

        Example:
            stage2_timestamp = Path('data/outputs/stage2/output.json').stat().st_mtime
            if cache.is_valid('coordinate_cache', stage2_timestamp):
                # Use cache
            else:
                # Recompute
        """
        cache_path = self.get_hdf5_path(identifier)

        if not cache_path.exists():
            self.logger.info(f"🔄 HDF5 緩存不存在: {cache_path}")
            return False

        cache_mtime = cache_path.stat().st_mtime

        if cache_mtime > upstream_timestamp:
            self.logger.info(f"✅ HDF5 緩存有效: {cache_path}")
            return True
        else:
            self.logger.info(
                f"🔄 HDF5 緩存過期: cache_mtime={cache_mtime}, "
                f"upstream_timestamp={upstream_timestamp}"
            )
            return False

    def invalidate(self, identifier: str) -> bool:
        """
        Invalidate (delete) cache file

        Args:
            identifier: Cache identifier

        Returns:
            True if cache was deleted
        """
        cache_path = self.get_hdf5_path(identifier)

        if cache_path.exists():
            cache_path.unlink()
            self.logger.info(f"🗑️ HDF5 緩存已清除: {cache_path}")
            return True

        return False
```

---

### 2. Stage 2 遷移

**檔案**: `src/stages/stage2_orbital_computing/stage2_result_manager.py`

**修改前**:
```python
def _save_hdf5(self, results, custom_filename=None):
    """自定義 HDF5 保存邏輯"""
    # 約 40 行 HDF5 操作代碼...
    with h5py.File(hdf5_path, 'w') as f:
        for sat_id, coords in satellite_coords.items():
            f.create_dataset(sat_id, data=coords, compression='gzip')
    # ...
```

**修改後**:
```python
from shared.hdf5_handler import HDF5OutputStrategy

class Stage2ResultManager(BaseResultManager):
    def __init__(self, logger_instance=None):
        super().__init__(logger_instance)
        # 初始化 HDF5 handler
        self.hdf5_handler = HDF5OutputStrategy(
            output_dir='data/outputs/stage2',
            compression='gzip',
            compression_opts=4,
            logger_instance=self.logger
        )

    def save_results(self, results, output_format='json', custom_filename=None):
        """覆寫基類支援雙格式輸出"""
        # Step 1: 保存 JSON（呼叫基類）
        json_path = super().save_results(results, 'json', custom_filename)

        # Step 2: 如果需要 HDF5，使用 handler 保存
        if output_format in ['hdf5', 'both']:
            # 提取衛星坐標數據
            satellite_coords = self._extract_coordinate_arrays(results)

            # 使用 HDF5 handler 保存
            hdf5_identifier = custom_filename or Path(json_path).stem
            hdf5_path = self.hdf5_handler.save(
                data=satellite_coords,
                identifier=hdf5_identifier,
                metadata={
                    'stage': 2,
                    'timestamp': results['metadata']['processing_start_time'],
                    'satellite_count': len(satellite_coords)
                }
            )

            if output_format == 'hdf5':
                return str(hdf5_path)
            else:  # 'both'
                return json_path, str(hdf5_path)

        return json_path
```

**代碼減少**: ~30行（HDF5 操作邏輯移至 handler）

---

### 3. Stage 3 遷移

**檔案**: `src/stages/stage3_coordinate_transformation/stage3_hdf5_cache.py`

**修改前**:
```python
class Stage3HDF5Cache:
    """約 80 行自定義 HDF5 緩存邏輯"""

    def is_cache_valid(self, stage2_timestamp):
        # 自定義檢查邏輯...
        pass

    def load_from_cache(self, satellite_id):
        # 自定義讀取邏輯...
        with h5py.File(...) as f:
            return f[satellite_id][:]

    def save_to_cache(self, satellite_data_dict):
        # 自定義寫入邏輯...
        with h5py.File(...) as f:
            for sat_id, data in satellite_data_dict.items():
                f.create_dataset(sat_id, data=data, compression='gzip')
```

**修改後**:
```python
from shared.hdf5_handler import HDF5CacheStrategy

class Stage3HDF5Cache:
    """簡化為 HDF5CacheStrategy 的薄包裝"""

    def __init__(self, cache_dir='data/cache/stage3', logger_instance=None):
        self.cache_strategy = HDF5CacheStrategy(
            base_dir=cache_dir,
            compression='gzip',
            compression_opts=4,
            logger_instance=logger_instance
        )
        self.cache_identifier = 'coordinate_cache'

    def is_cache_valid(self, stage2_timestamp: float) -> bool:
        """檢查緩存是否有效（委託給 strategy）"""
        return self.cache_strategy.is_valid(
            self.cache_identifier,
            stage2_timestamp
        )

    def load_from_cache(self, satellite_id: str) -> np.ndarray:
        """從緩存讀取單個衛星數據"""
        return self.cache_strategy.load(
            self.cache_identifier,
            dataset_name=satellite_id
        )

    def save_to_cache(self, satellite_data_dict: Dict[str, np.ndarray]) -> Path:
        """保存所有衛星數據到緩存"""
        return self.cache_strategy.save(
            data=satellite_data_dict,
            identifier=self.cache_identifier,
            metadata={'cache_version': '1.0'}
        )

    def invalidate_cache(self) -> bool:
        """清除緩存"""
        return self.cache_strategy.invalidate(self.cache_identifier)
```

**代碼減少**: ~50行（HDF5 操作邏輯移至 strategy）

---

## 📋 實施計劃

### 階段劃分

| 階段 | 任務 | 預估時間 | 依賴 |
|-----|------|---------|------|
| **Step 1** | 創建 `src/shared/hdf5_handler.py` | 1.5小時 | 無 |
| **Step 2** | 編寫 HDF5 handler 單元測試 | 1小時 | Step 1 |
| **Step 3** | 遷移 Stage 2 使用 HDF5OutputStrategy | 0.5小時 | Step 1 |
| **Step 4** | 遷移 Stage 3 使用 HDF5CacheStrategy | 0.5小時 | Step 1 |
| **Step 5** | 執行全量測試驗證性能和相容性 | 0.5小時 | Step 3-4 |

**總計**: 4小時（約 0.5天）

---

### 測試策略

**單元測試**: `tests/unit/shared/test_hdf5_handler.py`

```python
import pytest
import numpy as np
from pathlib import Path
from src.shared.hdf5_handler import (
    HDF5OutputStrategy,
    HDF5CacheStrategy
)


def test_output_strategy_save_load(tmp_path):
    """測試 HDF5OutputStrategy 保存和讀取"""
    handler = HDF5OutputStrategy(base_dir=tmp_path)

    # 準備測試數據
    test_data = {
        'SAT-12345': np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
        'SAT-67890': np.array([[7.0, 8.0, 9.0]])
    }

    # 保存
    hdf5_path = handler.save(
        data=test_data,
        identifier='test_output',
        metadata={'stage': 2, 'count': 2}
    )

    assert hdf5_path.exists()

    # 讀取所有數據
    loaded_data = handler.load('test_output')
    assert 'SAT-12345' in loaded_data
    np.testing.assert_array_equal(loaded_data['SAT-12345'], test_data['SAT-12345'])

    # 讀取單個數據集
    sat_data = handler.load('test_output', 'SAT-12345')
    np.testing.assert_array_equal(sat_data, test_data['SAT-12345'])


def test_cache_strategy_validation(tmp_path):
    """測試 HDF5CacheStrategy 緩存驗證"""
    cache = HDF5CacheStrategy(base_dir=tmp_path)

    import time
    current_time = time.time()

    # 緩存不存在，應該無效
    assert not cache.is_valid('test_cache', current_time)

    # 保存緩存
    test_data = {'SAT-123': np.array([1, 2, 3])}
    cache.save(test_data, 'test_cache', metadata={'timestamp': current_time})

    # 緩存應該有效（緩存時間 > upstream時間）
    assert cache.is_valid('test_cache', current_time - 10)

    # 如果 upstream 更新，緩存應該無效
    future_time = time.time() + 100
    assert not cache.is_valid('test_cache', future_time)


def test_cache_invalidation(tmp_path):
    """測試緩存清除"""
    cache = HDF5CacheStrategy(base_dir=tmp_path)

    # 保存緩存
    test_data = {'SAT-123': np.array([1, 2, 3])}
    cache.save(test_data, 'test_cache')

    assert cache.exists('test_cache')

    # 清除緩存
    assert cache.invalidate('test_cache')
    assert not cache.exists('test_cache')
```

**集成測試**: 驗證 Stage 2/3 實際使用

```bash
# 測試 Stage 2 雙格式輸出
./run.sh --stage 2
ls data/outputs/stage2/*.json  # JSON 應該存在
ls data/outputs/stage2/*.h5    # HDF5 應該存在（如果配置 output_format='both'）

# 測試 Stage 3 緩存加速
rm -rf data/cache/stage3/       # 清除緩存
time ./run.sh --stage 3         # 第一次運行（~25分鐘）
time ./run.sh --stage 3         # 第二次運行（~2分鐘，使用緩存）
```

---

## ✅ 驗收標準

### 功能性標準

- ✅ **HDF5 handler 完整**: BaseHDF5Handler + 2種策略實作
- ✅ **Stage 2 遷移**: 使用 HDF5OutputStrategy，保持雙格式輸出
- ✅ **Stage 3 遷移**: 使用 HDF5CacheStrategy，保持緩存加速
- ✅ **向後相容**: Stage 2/3 現有接口不變
- ✅ **測試覆蓋**: HDF5 handler 單元測試覆蓋率 ≥ 80%

### 性能標準

- ✅ **Stage 2 輸出性能**: JSON + HDF5 保存時間 ≤ 原實作 +5%
- ✅ **Stage 3 緩存加速**: 緩存命中時執行時間 ≤ 3分鐘（原 2分鐘基準）
- ✅ **HDF5 壓縮率**: gzip 壓縮後檔案大小 ≤ 原實作 +10%

### 代碼質量標準

- ✅ **代碼減少**: Stage 2/3 HDF5 操作代碼減少 ~50行
- ✅ **重複消除**: HDF5 read/write 邏輯統一抽取
- ✅ **文檔完整**: 所有 HDF5 strategy 包含使用範例

---

## 📊 預期收益

### 量化收益

| 維度 | 改進前 | 改進後 | 提升幅度 |
|-----|-------|-------|---------|
| **HDF5 操作代碼行數** | ~120行 | ~70行 | -42% |
| **代碼重複** | 2處實作 | 統一策略 | -50% |
| **測試覆蓋率** | ~30% | ≥80% | +167% |
| **新階段 HDF5 添加時間** | ~2小時 | ~30分鐘 | -75% |

### 質化收益

1. **擴展性**:
   - 未來新階段需要 HDF5 時，直接使用現有策略
   - 可輕鬆添加新策略（如 HDF5ReadOnlyStrategy）

2. **維護性**:
   - HDF5 操作邏輯集中管理
   - Bug 修復只需修改一處

3. **測試性**:
   - 統一的 HDF5 測試框架
   - Mock HDF5 操作更容易

---

## ⚠️ 風險與緩解

| 風險 | 等級 | 緩解措施 |
|-----|------|---------|
| **HDF5 重構影響性能** | 🟢 低 | 保持原有壓縮參數（gzip level 4） |
| **緩存策略變更破壞現有緩存** | 🟡 中 | 保留 Stage3HDF5Cache 接口，內部委託給 strategy |
| **HDF5 檔案格式不相容** | 🟢 低 | 使用相同的 dataset 命名和結構 |

---

## 🔗 相關文件

- [00_OVERVIEW.md](00_OVERVIEW.md) - Phase 4 總覽
- [01_CURRENT_STATUS.md](01_CURRENT_STATUS.md) - 當前架構狀態
- [Phase 3 Progress Report](../phase3_result_manager_refactor/PHASE3_PROGRESS_REPORT.md) - BaseResultManager 設計

---

**下一步**: 閱讀 [05_P2_TESTING_FRAMEWORK.md](05_P2_TESTING_FRAMEWORK.md) 了解測試框架完善方案
