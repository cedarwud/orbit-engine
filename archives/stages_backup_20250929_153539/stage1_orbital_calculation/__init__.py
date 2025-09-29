"""
🔄 Stage 1: TLE數據載入層 (v2.0重構版)

📋 符合 @orbit-engine/docs/stages/stage1-tle-loading.md 規範

🏗️ v2.0 核心架構組件:
┌─────────────────────────────────────────────────────────────┐
│                    Stage 1: 數據載入層                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  TLE Loader │  │Data Validator│  │Time Reference│       │
│  │             │  │             │  │Manager       │       │
│  │ • 檔案讀取    │  │ • 格式驗證   │  │ • Epoch提取   │       │
│  │ • 解析TLE    │  │ • 數據完整性  │  │ • 基準時間    │       │
│  │ • 批次處理    │  │ • 品質檢查   │  │ • 時區處理    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│           │              │               │                │
│           └──────────────┼───────────────┘                │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │     Stage1 Main Processor      │            │
│           │                                 │            │
│           │ • 協調三個組件                   │            │
│           │ • 數據流控制                     │            │
│           │ • 錯誤處理與回報                 │            │
│           │ • 性能監控                       │            │
│           └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘

✅ v2.0 職責 (純數據載入):
- TLE檔案載入和解析
- 數據格式驗證和品質檢查
- 個別時間基準保持 (每筆TLE保持獨立 epoch_datetime)
- 為Stage 2提供清潔的TLE數據

❌ 不再包含 (已移至Stage 2):
- SGP4軌道計算
- 位置和速度計算
- 可見性分析
- 座標系統轉換

⚡ 性能目標:
- 處理時間: < 30秒 (vs 原來2.8分鐘)
- 記憶體使用: < 200MB (vs 原來500MB)
"""

# 🔄 v2.0 主處理器 (符合文檔設計)
from .stage1_main_processor import Stage1RefactoredProcessor, create_stage1_refactored_processor
# Backward compatibility alias
Stage1MainProcessor = Stage1RefactoredProcessor
create_stage1_main_processor = create_stage1_refactored_processor

# 🏗️ v2.0 核心組件 (四個組件)
from .tle_data_loader import TLEDataLoader
from .data_validator import DataValidator
from .time_reference_manager import TimeReferenceManager

# 🔄 v2.0 簡化處理器 (向後兼容)
# 過時的 stage1_data_loading_processor 已移除，使用 stage1_main_processor 中的重構版本

# ❌ 舊版TLE處理器已移除 (違反v2.0規範)
# from .tle_orbital_calculation_processor import Stage1TLEProcessor

# 🧪 驗證組件 (已歸檔到專案根目錄 _archived_stage1_files/)
# from .orbital_validation_engine import OrbitalValidationEngine

__all__ = [
    # 🔄 v2.0 主要介面
    'Stage1MainProcessor',         # 主處理器 (文檔標準)
    'create_stage1_main_processor', # 工廠函數

    # 🏗️ v2.0 核心組件
    'TLEDataLoader',               # TLE檔案載入器
    'DataValidator',               # 數據格式驗證器
    'TimeReferenceManager',        # 時間基準管理器

    # 🔄 向後兼容處理器
    'Stage1DataLoadingProcessor',  # 簡化版處理器
    # 'Stage1TLEProcessor',          # 舊版處理器已移除

    # 🧪 驗證組件
    # 'OrbitalValidationEngine'      # 驗證引擎 (已歸檔)
]

# 🎯 預設主處理器 (文檔推薦)
Stage1Processor = Stage1MainProcessor
create_stage1_processor = create_stage1_main_processor