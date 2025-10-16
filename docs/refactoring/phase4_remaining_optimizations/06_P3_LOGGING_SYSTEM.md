# P3: 日誌系統統一化

**優先級**: 🟡 P3 - 低優先級（可選執行）
**預估時間**: 0.5天
**依賴**: 無
**影響範圍**: 全專案（6個階段 + shared utilities）

---

## 📊 問題分析

### 當前狀態

**日誌使用現況**:

| 問題類型 | 具體表現 | 影響階段 | 嚴重程度 |
|---------|---------|---------|---------|
| **日誌級別不一致** | INFO vs DEBUG 使用混亂 | 全階段 | 🟡 中 |
| **格式不統一** | Emoji、中英文混用 | 全階段 | 🟡 中 |
| **結構化不足** | 缺少關鍵字段（stage, operation） | 全階段 | 🟢 低 |
| **日誌量過大** | DEBUG 日誌過多 | Stage 2, 3, 5 | 🟢 低 |

---

### 日誌級別混亂

**問題示例**:

```python
# ❌ 不一致的日誌級別使用

# Stage 2: 正常處理使用 DEBUG
logger.debug(f"處理衛星 {sat_id}")

# Stage 4: 相同場景使用 INFO
logger.info(f"處理衛星 {sat_id}")

# Stage 5: 關鍵錯誤使用 WARNING（應該用 ERROR）
logger.warning(f"信號計算失敗: {sat_id}")

# Stage 6: 調試信息使用 INFO（應該用 DEBUG）
logger.info(f"候選衛星: {candidates}")
```

**影響**:
- 日誌過濾困難（INFO 日誌過多）
- 生產環境日誌噪音大
- 告警配置不準確

---

### 日誌格式不統一

**問題示例**:

```python
# ❌ 不同的格式風格

# 風格 1: Emoji + 中文
logger.info("✅ 階段 2 執行完成")

# 風格 2: 純英文
logger.info("Stage 3 processing completed")

# 風格 3: 中英混合
logger.info("Stage 4 處理完成 | Processing completed")

# 風格 4: 無 Emoji
logger.info("階段 5 完成")

# 風格 5: 過多 Emoji
logger.info("🚀✨🎉 Stage 6 finished successfully! 🎊🎈")
```

**影響**:
- 日誌解析困難（正則匹配失敗）
- 國際化困難
- 監控工具配置複雜

---

### 缺少結構化日誌

**問題示例**:

```python
# ❌ 非結構化日誌

logger.info("處理了 150 個衛星，耗時 30.5 秒")

# ✅ 應該使用結構化格式

logger.info(
    "衛星處理完成",
    extra={
        'stage': 5,
        'operation': 'signal_analysis',
        'satellites_processed': 150,
        'processing_time_seconds': 30.5
    }
)
```

**影響**:
- 無法自動化日誌分析
- 監控指標難以提取
- 告警規則難以配置

---

## 🎯 設計目標

### 主要目標

1. **統一日誌級別** - 明確定義何時使用何種級別
2. **標準化格式** - 統一 Emoji 和中英文使用
3. **結構化日誌** - 添加關鍵字段便於解析
4. **配置化控制** - 環境變數控制日誌級別和格式
5. **向後相容** - 現有日誌輸出不受影響

### 成功指標

- ✅ 定義清晰的日誌級別使用指引
- ✅ 統一日誌格式規範（Emoji + 中文 | English）
- ✅ 關鍵操作添加結構化字段
- ✅ 提供配置化日誌級別控制
- ✅ 日誌格式一致性 ≥ 90%

---

## 🏗️ 設計方案

### 日誌級別標準化

**級別定義**:

| 級別 | 使用場景 | 範例 | 生產環境可見 |
|-----|---------|------|------------|
| **DEBUG** | 詳細調試信息、循環內日誌、中間變量 | `logger.debug(f"處理衛星 {sat_id}")` | ❌ 關閉 |
| **INFO** | 階段開始/結束、關鍵里程碑、成功消息 | `logger.info("✅ 階段 5 完成")` | ✅ 開啟 |
| **WARNING** | 非致命錯誤、降級處理、性能警告 | `logger.warning("⚠️ Epoch 分布不足")` | ✅ 開啟 |
| **ERROR** | 處理失敗但可恢復、數據錯誤 | `logger.error("❌ 衛星計算失敗")` | ✅ 開啟 |
| **CRITICAL** | 系統級錯誤、階段完全失敗 | `logger.critical("💥 階段執行失敗")` | ✅ 開啟 |

---

### 日誌格式標準

**統一格式規範**:

```python
# ✅ 標準格式: Emoji + 中文 | English（雙語）

# 1. 階段開始/結束
logger.info("🚀 開始執行階段 5 | Starting Stage 5 execution")
logger.info("✅ 階段 5 執行完成 | Stage 5 execution completed")

# 2. 處理進度
logger.info(f"📊 處理進度: {progress}% | Processing progress: {progress}%")

# 3. 數據統計
logger.info(f"📋 處理了 {count} 個衛星 | Processed {count} satellites")

# 4. 警告訊息
logger.warning(f"⚠️ 警告: {message} | Warning: {message}")

# 5. 錯誤訊息
logger.error(f"❌ 錯誤: {error} | Error: {error}")
```

**Emoji 使用規範**:

| Emoji | 含義 | 使用場景 |
|-------|------|---------|
| 🚀 | 開始執行 | 階段/操作開始 |
| ✅ | 成功完成 | 階段/操作成功結束 |
| ⚠️ | 警告 | 非致命問題 |
| ❌ | 錯誤 | 處理失敗 |
| 💥 | 嚴重錯誤 | 系統級失敗 |
| 📊 | 進度統計 | 處理進度 |
| 📋 | 數據摘要 | 統計信息 |
| 💾 | 文件操作 | 保存/載入 |
| 🔍 | 搜尋/檢查 | 檢查操作 |
| 🔄 | 重試/循環 | 重試操作 |

---

### 結構化日誌設計

**結構化字段定義**:

```python
# ✅ 標準結構化日誌格式

logger.info(
    "階段處理完成 | Stage processing completed",
    extra={
        'stage': 5,                          # 階段編號
        'stage_name': 'signal_analysis',     # 階段名稱
        'operation': 'rsrp_calculation',     # 具體操作
        'satellites_processed': 150,         # 處理數量
        'processing_time_seconds': 30.5,     # 處理時間
        'success': True,                     # 成功狀態
        'error_count': 0                     # 錯誤數量
    }
)
```

**關鍵操作結構化範例**:

```python
# 階段執行開始
logger.info(
    "🚀 開始執行階段 | Starting stage execution",
    extra={
        'stage': stage_num,
        'stage_name': stage_name,
        'upstream_stage': upstream_stage,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
)

# 處理進度
logger.info(
    f"📊 處理進度: {progress}% | Processing progress: {progress}%",
    extra={
        'stage': stage_num,
        'operation': 'processing',
        'progress_percent': progress,
        'items_processed': processed_count,
        'items_total': total_count
    }
)

# 階段執行完成
logger.info(
    "✅ 階段執行完成 | Stage execution completed",
    extra={
        'stage': stage_num,
        'processing_time_seconds': elapsed_time,
        'satellites_processed': sat_count,
        'output_file': output_path,
        'success': True
    }
)
```

---

## 💻 實作細節

### 1. 統一日誌配置器

**檔案位置**: `src/shared/logging_config.py` (新建)

```python
"""
📝 Orbit Engine 統一日誌配置

Standardized logging configuration for all stages and utilities.
Provides structured logging, configurable formats, and log level control.

Author: Orbit Engine Refactoring Team
Date: 2025-10-15 (Phase 4 Refactoring)

Usage:
    from shared.logging_config import get_logger

    logger = get_logger(__name__, stage=5)
    logger.info("✅ 處理完成", extra={'satellites': 150})
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter with Orbit Engine conventions

    Features:
    - Emoji support for visual scanning
    - Bilingual messages (中文 | English)
    - Structured extra fields
    - Consistent timestamp format
    """

    # ANSI color codes for terminal output
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'
    }

    def __init__(self, use_color=True):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_color = use_color

    def format(self, record):
        """Format log record with color and structured fields"""
        # Add color for terminal output
        if self.use_color and record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        # Format base message
        formatted = super().format(record)

        # Append structured fields if present
        if hasattr(record, 'stage'):
            formatted += f" | stage={record.stage}"
        if hasattr(record, 'operation'):
            formatted += f" | operation={record.operation}"
        if hasattr(record, 'processing_time_seconds'):
            formatted += f" | duration={record.processing_time_seconds:.2f}s"
        if hasattr(record, 'satellites_processed'):
            formatted += f" | satellites={record.satellites_processed}"

        return formatted


def get_logger(
    name: str,
    stage: Optional[int] = None,
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Get configured logger instance

    Args:
        name: Logger name (typically __name__)
        stage: Optional stage number for context
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__, stage=5)
        logger.info("✅ 處理完成 | Processing completed", extra={'satellites': 150})

    Environment Variables:
        ORBIT_ENGINE_LOG_LEVEL: Override default log level (default: INFO)
        ORBIT_ENGINE_LOG_FILE: Write logs to file
        ORBIT_ENGINE_LOG_NO_COLOR: Disable color output
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Determine log level
    if level is None:
        level = os.getenv('ORBIT_ENGINE_LOG_LEVEL', 'INFO').upper()

    logger.setLevel(getattr(logging, level, logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    use_color = os.getenv('ORBIT_ENGINE_LOG_NO_COLOR') is None
    console_handler.setFormatter(StructuredFormatter(use_color=use_color))
    logger.addHandler(console_handler)

    # File handler (optional)
    log_file = log_file or os.getenv('ORBIT_ENGINE_LOG_FILE')
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredFormatter(use_color=False))
        logger.addHandler(file_handler)

    # Add stage context if provided
    if stage is not None:
        logger = logging.LoggerAdapter(logger, {'stage': stage})

    return logger


def configure_logging(
    level: str = 'INFO',
    log_file: Optional[Path] = None,
    enable_debug_stages: Optional[list] = None
):
    """
    Configure global logging settings

    Args:
        level: Default log level
        log_file: Optional log file path
        enable_debug_stages: List of stages to enable DEBUG logging

    Example:
        # In main script
        configure_logging(
            level='INFO',
            log_file=Path('logs/orbit_engine.log'),
            enable_debug_stages=[2, 3]  # Debug only Stage 2 and 3
        )
    """
    # Set root logger level
    logging.root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Configure stage-specific debug logging
    if enable_debug_stages:
        for stage_num in enable_debug_stages:
            stage_logger = logging.getLogger(f'src.stages.stage{stage_num}_*')
            stage_logger.setLevel(logging.DEBUG)
```

---

### 2. 遷移指引

**各階段遷移模式**:

```python
# ❌ 舊寫法

import logging
logger = logging.getLogger(__name__)

def process_satellites(satellites):
    logger.info("開始處理衛星")
    for sat in satellites:
        logger.info(f"處理 {sat}")
    logger.info("處理完成")


# ✅ 新寫法

from shared.logging_config import get_logger

logger = get_logger(__name__, stage=5)

def process_satellites(satellites):
    logger.info(
        "🚀 開始處理衛星 | Starting satellite processing",
        extra={'total_satellites': len(satellites)}
    )

    for i, sat in enumerate(satellites, 1):
        logger.debug(f"處理衛星 {sat} | Processing satellite {sat}")

        if i % 100 == 0:
            progress = (i / len(satellites)) * 100
            logger.info(
                f"📊 處理進度: {progress:.1f}% | Progress: {progress:.1f}%",
                extra={
                    'progress_percent': progress,
                    'satellites_processed': i,
                    'satellites_total': len(satellites)
                }
            )

    logger.info(
        "✅ 衛星處理完成 | Satellite processing completed",
        extra={'satellites_processed': len(satellites)}
    )
```

---

### 3. 日誌級別遷移矩陣

**決策矩陣**:

| 原日誌內容 | 原級別 | 新級別 | 理由 |
|-----------|-------|-------|------|
| `處理衛星 {sat_id}` | INFO | DEBUG | 循環內詳細信息 |
| `階段 N 開始執行` | INFO | INFO | 關鍵里程碑 |
| `載入配置檔案` | INFO | DEBUG | 內部操作細節 |
| `找到 N 個衛星` | INFO | INFO | 重要統計信息 |
| `Epoch 分布不足` | INFO | WARNING | 非致命問題 |
| `信號計算失敗` | WARNING | ERROR | 處理錯誤 |
| `配置檔案不存在` | ERROR | CRITICAL | 致命錯誤 |

---

## 📋 實施計劃

### 階段劃分

| 階段 | 任務 | 預估時間 | 依賴 |
|-----|------|---------|------|
| **Step 1** | 創建 `src/shared/logging_config.py` | 1小時 | 無 |
| **Step 2** | 定義日誌級別和格式規範文檔 | 0.5小時 | Step 1 |
| **Step 3** | 遷移 Stage 2-6 日誌調用 | 1.5小時 | Step 1 |
| **Step 4** | 更新 shared utilities 日誌 | 0.5小時 | Step 1 |
| **Step 5** | 執行全量測試驗證輸出格式 | 0.5小時 | Step 3-4 |

**總計**: 4小時（約 0.5天）

---

### 環境變數配置

**新增環境變數**:

```bash
# .env 檔案

# 日誌級別控制
ORBIT_ENGINE_LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 日誌文件輸出
ORBIT_ENGINE_LOG_FILE=logs/orbit_engine.log

# 禁用彩色輸出（CI 環境）
ORBIT_ENGINE_LOG_NO_COLOR=1

# 階段級別調試（逗號分隔）
ORBIT_ENGINE_DEBUG_STAGES=2,3        # 僅 Stage 2 和 3 輸出 DEBUG 日誌
```

---

## ✅ 驗收標準

### 格式一致性標準

- ✅ **Emoji 使用**: 90%+ 日誌使用標準 Emoji
- ✅ **雙語格式**: 80%+ 關鍵日誌包含中英文
- ✅ **結構化字段**: 所有階段開始/結束日誌包含 extra 字段

### 功能性標準

- ✅ **級別控制**: 環境變數正確控制日誌級別
- ✅ **文件輸出**: 日誌可正確寫入文件（UTF-8 編碼）
- ✅ **彩色輸出**: 終端輸出包含正確 ANSI 顏色
- ✅ **結構化解析**: extra 字段可被 JSON 日誌解析器解析

### 性能標準

- ✅ **日誌量**: INFO 級別日誌減少 50%（移至 DEBUG）
- ✅ **性能影響**: 結構化日誌開銷 < 1%

---

## 📊 預期收益

### 量化收益

| 維度 | 改進前 | 改進後 | 提升幅度 |
|-----|-------|-------|---------|
| **日誌格式一致性** | 40% | 90%+ | +125% |
| **生產環境日誌量** | 10MB/run | 5MB/run | -50% |
| **日誌解析成功率** | 60% | 95%+ | +58% |
| **調試效率** | 需搜尋 | 結構化查詢 | +200% |

### 質化收益

1. **運維支援**:
   - 日誌聚合工具（ELK, Splunk）更容易配置
   - 告警規則更精確
   - 性能分析更容易

2. **開發體驗**:
   - 彩色輸出提升可讀性
   - 結構化字段便於調試
   - 環境變數控制級別更靈活

3. **國際化**:
   - 雙語日誌支援國際協作
   - 便於生成英文技術文檔

---

## ⚠️ 風險與緩解

| 風險 | 等級 | 緩解措施 |
|-----|------|---------|
| **結構化日誌影響性能** | 🟢 低 | 僅關鍵操作添加 extra，循環內使用簡單日誌 |
| **日誌文件過大** | 🟢 低 | 使用 RotatingFileHandler（10MB 輪換） |
| **彩色輸出在 CI 中異常** | 🟢 低 | 提供 ORBIT_ENGINE_LOG_NO_COLOR 環境變數 |

---

## 🔗 相關文件

- [00_OVERVIEW.md](00_OVERVIEW.md) - Phase 4 總覽
- [03_P2_ERROR_HANDLING.md](03_P2_ERROR_HANDLING.md) - 錯誤處理標準化（異常訊息格式）

---

**下一步**: 閱讀 [07_P3_MODULE_REORGANIZATION.md](07_P3_MODULE_REORGANIZATION.md) 了解模塊重組方案
