# P3: 模塊重組

**優先級**: 🟡 P3 - 低優先級（可選執行）
**預估時間**: 2-3天
**依賴**: Phase 1-4 完成
**影響範圍**: `src/shared/` 目錄結構，全專案 import 路徑

---

## 📊 問題分析

### 當前目錄結構

```
src/shared/
├── __init__.py
├── base_processor.py                    # BaseStageProcessor 基類
├── base_result_manager.py               # BaseResultManager 基類
└── utils/
    ├── __init__.py
    ├── coordinate_converter.py          # 坐標轉換工具
    ├── file_utils.py                    # 文件操作工具
    ├── ground_distance_calculator.py    # 地面距離計算
    ├── math_utils.py                    # 數學工具函數
    └── time_utils.py                    # 時間工具函數

scripts/stage_executors/
├── base_executor.py                     # StageExecutor 基類
└── stageN_executor.py                   # 各階段 Executor

scripts/stage_validators/
├── base_validator.py                    # StageValidator 基類
└── stageN_validator.py                  # 各階段 Validator
```

---

### 問題描述

**1. 基類分散在不同目錄**:
- `base_processor.py`, `base_result_manager.py` 在 `src/shared/`
- `base_executor.py` 在 `scripts/stage_executors/`
- `base_validator.py` 在 `scripts/stage_validators/`
- **問題**: 邏輯上相關的基類物理分離，不易理解架構

**2. `utils/` 目錄缺少分類**:
- 5個工具模組平鋪在同一目錄
- 缺少領域劃分（坐標、時間、數學）
- **問題**: 隨著工具增加，目錄會越來越混亂

**3. import 路徑不一致**:
```python
# 不同的 import 風格
from shared.base_processor import BaseStageProcessor
from shared.utils.coordinate_converter import ecef_to_geodetic
from scripts.stage_executors.base_executor import StageExecutor
```

**4. 新增模組位置不明確**:
- Phase 4 新增的模組應該放哪裡？
  - `exceptions.py` → `src/shared/` or `src/shared/core/`?
  - `hdf5_handler.py` → `src/shared/` or `src/shared/storage/`?
  - `logging_config.py` → `src/shared/` or `src/shared/utils/`?

---

### 影響分析

| 影響維度 | 嚴重程度 | 具體影響 |
|---------|---------|---------|
| **代碼理解性** | 🟡 中 | 新開發者難以快速理解架構層級 |
| **擴展性** | 🟡 中 | 不知道新模組應該放哪裡 |
| **維護成本** | 🟢 低 | 當前結構尚可接受 |
| **功能性** | 🟢 無 | 不影響運行 |

**結論**: 非緊急問題，但隨著項目成長會逐漸顯現。適合作為 Phase 4 的可選優化項目。

---

## 🎯 設計目標

### 主要目標

1. **統一基類位置** - 所有基類集中管理
2. **領域驅動分類** - 按功能領域組織工具模組
3. **清晰的命名空間** - import 路徑反映架構層級
4. **向後相容** - 保留舊 import 路徑別名
5. **漸進式遷移** - 允許新舊路徑共存

### 成功指標

- ✅ 基類集中在 `src/shared/base/` 目錄
- ✅ utils 按領域分類（geometry, time, io, math）
- ✅ 提供向後相容的 import 別名
- ✅ 所有測試 100% 通過（無破壞性變更）
- ✅ 文檔清晰定義模組組織規則

---

## 🏗️ 設計方案

### 目標目錄結構

```
src/
├── shared/                              # 共享模組根目錄
│   ├── __init__.py                      # 模組入口（提供向後相容別名）
│   │
│   ├── base/                            # 🆕 基類目錄
│   │   ├── __init__.py
│   │   ├── executor.py                  # StageExecutor (moved from scripts/)
│   │   ├── validator.py                 # StageValidator (moved from scripts/)
│   │   ├── processor.py                 # BaseStageProcessor (moved from base_processor.py)
│   │   └── result_manager.py            # BaseResultManager (moved from base_result_manager.py)
│   │
│   ├── core/                            # 🆕 核心功能模組
│   │   ├── __init__.py
│   │   ├── exceptions.py                # 異常定義（Phase 4 新增）
│   │   ├── logging_config.py            # 日誌配置（Phase 4 新增）
│   │   └── config_manager.py            # 配置管理器（Phase 4 新增）
│   │
│   ├── storage/                         # 🆕 儲存相關模組
│   │   ├── __init__.py
│   │   ├── hdf5_handler.py              # HDF5 處理（Phase 4 新增）
│   │   └── file_utils.py                # 文件工具（moved from utils/）
│   │
│   ├── geometry/                        # 🆕 幾何計算模組
│   │   ├── __init__.py
│   │   ├── coordinate_converter.py      # 坐標轉換（moved from utils/）
│   │   └── ground_distance_calculator.py # 地面距離（moved from utils/）
│   │
│   ├── time/                            # 🆕 時間處理模組
│   │   ├── __init__.py
│   │   └── time_utils.py                # 時間工具（moved from utils/）
│   │
│   ├── math/                            # 🆕 數學工具模組
│   │   ├── __init__.py
│   │   └── math_utils.py                # 數學工具（moved from utils/）
│   │
│   └── utils/                           # 🔄 保留為向後相容別名目錄
│       ├── __init__.py                  # 重新導出所有工具（向後相容）
│       ├── coordinate_converter.py      # Deprecated alias
│       ├── file_utils.py                # Deprecated alias
│       ├── ground_distance_calculator.py # Deprecated alias
│       ├── math_utils.py                # Deprecated alias
│       └── time_utils.py                # Deprecated alias
│
└── scripts/
    ├── stage_executors/
    │   ├── base_executor.py             # 🔄 Deprecated alias → shared.base.executor
    │   └── stageN_executor.py           # 各階段 Executor（保持不變）
    │
    └── stage_validators/
        ├── base_validator.py            # 🔄 Deprecated alias → shared.base.validator
        └── stageN_validator.py          # 各階段 Validator（保持不變）
```

---

### 領域驅動分類原則

**`shared/base/`** - 基類和框架
- 所有基類（Executor, Validator, Processor, ResultManager）
- Template Method Pattern 實作
- 階段無關的通用框架

**`shared/core/`** - 核心功能
- 異常定義（exceptions.py）
- 日誌配置（logging_config.py）
- 配置管理（config_manager.py）
- 應用級別的核心模組

**`shared/storage/`** - 儲存和 I/O
- HDF5 處理（hdf5_handler.py）
- 文件操作（file_utils.py）
- JSON/YAML 讀寫工具

**`shared/geometry/`** - 幾何和坐標
- 坐標轉換（coordinate_converter.py）
- 距離計算（ground_distance_calculator.py）
- 未來可擴展：姿態計算、軌道幾何

**`shared/time/`** - 時間處理
- 時間工具（time_utils.py）
- 未來可擴展：時區轉換、Epoch 處理

**`shared/math/`** - 數學工具
- 數學工具（math_utils.py）
- 未來可擴展：矩陣運算、統計函數

---

## 💻 實作細節

### 1. 向後相容機制

**核心策略**: Adapter Pattern + Deprecation Warnings

**範例 1: `src/shared/__init__.py` 向後相容導出**:

```python
"""
📦 Shared Module - Backward Compatibility Layer

This module provides backward-compatible imports for legacy code.
All imports redirect to new locations with deprecation warnings.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)
"""

import warnings

# ==================== New Recommended Imports ====================

# Base classes (new location)
from .base.executor import StageExecutor
from .base.validator import StageValidator
from .base.processor import BaseStageProcessor
from .base.result_manager import BaseResultManager

# Core functionality
from .core.exceptions import (
    OrbitEngineError,
    ConfigurationError,
    DataError,
    ProcessingError,
)
from .core.logging_config import get_logger, configure_logging
from .core.config_manager import BaseConfigManager

# Storage
from .storage.hdf5_handler import HDF5OutputStrategy, HDF5CacheStrategy
from .storage.file_utils import find_latest_output_file

# Geometry
from .geometry.coordinate_converter import ecef_to_geodetic, geodetic_to_ecef
from .geometry.ground_distance_calculator import calculate_ground_distance

# Time
from .time.time_utils import utc_now, format_timestamp

# Math
from .math.math_utils import deg_to_rad, rad_to_deg


# ==================== Deprecated Backward Compatibility ====================

def _deprecation_warning(old_import, new_import):
    """Issue deprecation warning for old import paths"""
    warnings.warn(
        f"⚠️ Import from '{old_import}' is deprecated. "
        f"Use '{new_import}' instead.",
        DeprecationWarning,
        stacklevel=3
    )


class _BackwardCompatibilityMeta(type):
    """Metaclass for backward compatibility with deprecation warnings"""

    def __getattr__(cls, name):
        # Map old attribute names to new imports
        _deprecated_imports = {
            'base_processor': ('base.processor', BaseStageProcessor),
            'base_result_manager': ('base.result_manager', BaseResultManager),
        }

        if name in _deprecated_imports:
            new_module, obj = _deprecated_imports[name]
            _deprecation_warning(f'shared.{name}', f'shared.{new_module}')
            return obj

        raise AttributeError(f"module 'shared' has no attribute '{name}'")


class _BackwardCompatibility(metaclass=_BackwardCompatibilityMeta):
    """Backward compatibility helper"""
    pass


# Enable backward compatibility
__all__ = [
    # Base classes
    'StageExecutor',
    'StageValidator',
    'BaseStageProcessor',
    'BaseResultManager',
    # Core
    'OrbitEngineError',
    'ConfigurationError',
    'DataError',
    'ProcessingError',
    'get_logger',
    'configure_logging',
    'BaseConfigManager',
    # Storage
    'HDF5OutputStrategy',
    'HDF5CacheStrategy',
    'find_latest_output_file',
    # Geometry
    'ecef_to_geodetic',
    'geodetic_to_ecef',
    'calculate_ground_distance',
    # Time
    'utc_now',
    'format_timestamp',
    # Math
    'deg_to_rad',
    'rad_to_deg',
]
```

---

**範例 2: `src/shared/utils/__init__.py` 向後相容**:

```python
"""
⚠️ Deprecated Module - Use Specific Submodules

This module is deprecated. Please import from specific submodules:
- Geometry: from shared.geometry import ...
- Time: from shared.time import ...
- Math: from shared.math import ...
- Storage: from shared.storage import ...

This compatibility layer will be removed in Phase 5.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "⚠️ Importing from 'shared.utils' is deprecated. "
    "Use specific submodules: shared.geometry, shared.time, shared.math, shared.storage",
    DeprecationWarning,
    stacklevel=2
)

# Redirect to new locations
from ..geometry.coordinate_converter import (
    ecef_to_geodetic,
    geodetic_to_ecef,
    teme_to_ecef,
    ecef_to_lla
)

from ..geometry.ground_distance_calculator import (
    calculate_ground_distance,
    haversine_distance
)

from ..time.time_utils import (
    utc_now,
    format_timestamp,
    parse_epoch
)

from ..math.math_utils import (
    deg_to_rad,
    rad_to_deg,
    normalize_angle
)

from ..storage.file_utils import (
    find_latest_output_file,
    ensure_directory_exists
)


__all__ = [
    # Geometry
    'ecef_to_geodetic',
    'geodetic_to_ecef',
    'teme_to_ecef',
    'ecef_to_lla',
    'calculate_ground_distance',
    'haversine_distance',
    # Time
    'utc_now',
    'format_timestamp',
    'parse_epoch',
    # Math
    'deg_to_rad',
    'rad_to_deg',
    'normalize_angle',
    # Storage
    'find_latest_output_file',
    'ensure_directory_exists',
]
```

---

**範例 3: `scripts/stage_executors/base_executor.py` 向後相容**:

```python
"""
⚠️ Deprecated Import Path

This file is deprecated. Please use:
    from shared.base.executor import StageExecutor

This compatibility layer will be removed in Phase 5.
"""

import warnings

warnings.warn(
    "⚠️ Importing from 'scripts.stage_executors.base_executor' is deprecated. "
    "Use 'from shared.base.executor import StageExecutor' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Redirect to new location
from src.shared.base.executor import StageExecutor

__all__ = ['StageExecutor']
```

---

### 2. 漸進式遷移策略

**階段 1: 創建新目錄結構（不破壞現有代碼）**

```bash
# 創建新目錄
mkdir -p src/shared/{base,core,storage,geometry,time,math}

# 複製（不移動）檔案到新位置
cp src/shared/base_processor.py src/shared/base/processor.py
cp src/shared/base_result_manager.py src/shared/base/result_manager.py
cp scripts/stage_executors/base_executor.py src/shared/base/executor.py
cp scripts/stage_validators/base_validator.py src/shared/base/validator.py

# 複製 utils 檔案
cp src/shared/utils/coordinate_converter.py src/shared/geometry/
cp src/shared/utils/ground_distance_calculator.py src/shared/geometry/
cp src/shared/utils/time_utils.py src/shared/time/
cp src/shared/utils/math_utils.py src/shared/math/
cp src/shared/utils/file_utils.py src/shared/storage/
```

**階段 2: 添加向後相容層**

```bash
# 修改舊檔案為重定向（如上述範例）
# 這樣舊 import 路徑仍然有效
```

**階段 3: 漸進式遷移 import 語句**

```python
# ❌ 舊寫法（仍然有效，但會有 DeprecationWarning）
from shared.base_processor import BaseStageProcessor
from shared.utils.coordinate_converter import ecef_to_geodetic

# ✅ 新寫法（推薦）
from shared.base.processor import BaseStageProcessor
from shared.geometry.coordinate_converter import ecef_to_geodetic
```

**階段 4: 批量遷移和測試**

```bash
# 使用工具批量替換 import 語句
# (提供 Python 腳本自動化)

python tools/migrate_imports.py --dry-run   # 預覽變更
python tools/migrate_imports.py --execute   # 執行遷移

# 運行全量測試
./run.sh --stages 1-6
pytest tests/
```

**階段 5: 移除向後相容層（Phase 5）**

```bash
# 在 Phase 5 中移除舊檔案
# 此時所有 import 已遷移完成
rm src/shared/base_processor.py
rm src/shared/base_result_manager.py
# ...
```

---

### 3. Import 遷移工具

**檔案位置**: `tools/migrate_imports.py`

```python
"""
Import Path Migration Tool

Automatically migrates import statements from old paths to new paths.

Usage:
    python tools/migrate_imports.py --dry-run   # Preview changes
    python tools/migrate_imports.py --execute   # Apply changes
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple


# Define import mapping rules
IMPORT_MAPPING = {
    # Base classes
    r'from shared\.base_processor import': 'from shared.base.processor import',
    r'from shared\.base_result_manager import': 'from shared.base.result_manager import',
    r'from scripts\.stage_executors\.base_executor import': 'from shared.base.executor import',
    r'from scripts\.stage_validators\.base_validator import': 'from shared.base.validator import',

    # Utils → Geometry
    r'from shared\.utils\.coordinate_converter import': 'from shared.geometry.coordinate_converter import',
    r'from shared\.utils\.ground_distance_calculator import': 'from shared.geometry.ground_distance_calculator import',

    # Utils → Time
    r'from shared\.utils\.time_utils import': 'from shared.time.time_utils import',

    # Utils → Math
    r'from shared\.utils\.math_utils import': 'from shared.math.math_utils import',

    # Utils → Storage
    r'from shared\.utils\.file_utils import': 'from shared.storage.file_utils import',
}


def migrate_file(file_path: Path, dry_run: bool = True) -> List[Tuple[int, str, str]]:
    """
    Migrate import statements in a single file

    Args:
        file_path: Path to Python file
        dry_run: If True, only preview changes

    Returns:
        List of (line_number, old_line, new_line) tuples
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changes = []
    new_lines = []

    for line_num, line in enumerate(lines, 1):
        new_line = line
        for old_pattern, new_import in IMPORT_MAPPING.items():
            if re.search(old_pattern, line):
                new_line = re.sub(old_pattern, new_import, line)
                changes.append((line_num, line.strip(), new_line.strip()))
                break

        new_lines.append(new_line)

    if not dry_run and changes:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return changes


def main():
    parser = argparse.ArgumentParser(description='Migrate import paths')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--execute', action='store_true', help='Apply changes')
    args = parser.parse_args()

    if not (args.dry_run or args.execute):
        print("Please specify --dry-run or --execute")
        return

    # Find all Python files
    python_files = list(Path('src').rglob('*.py')) + list(Path('scripts').rglob('*.py'))

    total_changes = 0

    print(f"{'🔍 DRY RUN MODE' if args.dry_run else '✏️ EXECUTING CHANGES'}\n")

    for file_path in python_files:
        changes = migrate_file(file_path, dry_run=args.dry_run)

        if changes:
            print(f"📄 {file_path}")
            for line_num, old_line, new_line in changes:
                print(f"  Line {line_num}:")
                print(f"    ❌ {old_line}")
                print(f"    ✅ {new_line}")
            print()
            total_changes += len(changes)

    print(f"\n📊 Summary: {total_changes} import statements {'would be' if args.dry_run else 'were'} migrated")

    if args.dry_run:
        print("\n⚠️ Run with --execute to apply changes")


if __name__ == '__main__':
    main()
```

---

## 📋 實施計劃

### 階段劃分

| 階段 | 任務 | 預估時間 | 依賴 |
|-----|------|---------|------|
| **Step 1** | 創建新目錄結構並複製檔案 | 2小時 | Phase 1-3 完成 |
| **Step 2** | 實作向後相容層（alias 檔案） | 3小時 | Step 1 |
| **Step 3** | 創建 import 遷移工具 | 2小時 | Step 1 |
| **Step 4** | 執行 import 遷移（dry-run + execute） | 2小時 | Step 2-3 |
| **Step 5** | 執行全量測試驗證 | 2小時 | Step 4 |
| **Step 6** | 更新文檔和 import 指引 | 2小時 | Step 5 |
| **Step 7** | 移除舊檔案（Phase 5）| 1小時 | 6個月後 |

**總計**: 13小時（約 2天）+ 1小時（Phase 5 清理）

---

## ✅ 驗收標準

### 功能性標準

- ✅ **新目錄結構完整**: 所有模組正確分類到 base, core, storage, geometry, time, math
- ✅ **向後相容性 100%**: 舊 import 路徑仍然有效（帶 DeprecationWarning）
- ✅ **所有測試通過**: 單元測試、集成測試、E2E 測試 100% 通過
- ✅ **Import 遷移工具**: 可正確遷移 90%+ import 語句

### 文檔標準

- ✅ **模組組織規則**: 文檔清晰定義新模組應該放哪個目錄
- ✅ **Import 指引**: 提供新舊 import 路徑對照表
- ✅ **遷移指南**: 開發者可按步驟完成遷移

### 代碼質量標準

- ✅ **Deprecation 警告**: 舊 import 路徑觸發清晰警告
- ✅ **__init__.py 完整**: 所有新目錄包含完整的 __init__.py
- ✅ **__all__ 定義**: 所有模組定義 __all__ 導出列表

---

## 📊 預期收益

### 量化收益

| 維度 | 改進前 | 改進後 | 提升幅度 |
|-----|-------|-------|---------|
| **模組組織清晰度** | 60% | 95% | +58% |
| **新模組添加決策時間** | ~10分鐘 | ~1分鐘 | -90% |
| **Import 路徑長度（平均）** | 35字符 | 28字符 | -20% |

### 質化收益

1. **架構理解性**:
   - 新開發者可快速理解模組組織
   - IDE 自動補全更準確
   - 架構圖更清晰

2. **擴展性**:
   - 新模組位置明確
   - 領域驅動設計更清晰
   - 未來添加新領域更容易（如 `shared/optimization/`）

3. **維護性**:
   - 相關模組集中管理
   - 減少循環依賴風險
   - 代碼審查更容易

---

## ⚠️ 風險與緩解

| 風險 | 等級 | 緩解措施 |
|-----|------|---------|
| **Import 遷移破壞現有代碼** | 🟠 中高 | 保留向後相容層，漸進式遷移 |
| **開發者不適應新結構** | 🟡 中 | 提供詳細文檔和遷移指引 |
| **工具無法處理所有 import** | 🟡 中 | 提供 dry-run 模式，手動檢查遺漏 |
| **CI/CD 流程受影響** | 🟢 低 | 向後相容層確保現有流程不變 |

---

## 🔗 相關文件

- [00_OVERVIEW.md](00_OVERVIEW.md) - Phase 4 總覽
- [Phase 1-3 Completion Reports](../) - 基類遷移歷史

---

**下一步**: 閱讀 [08_IMPLEMENTATION_ROADMAP.md](08_IMPLEMENTATION_ROADMAP.md) 了解 Phase 4 完整實施路線圖
