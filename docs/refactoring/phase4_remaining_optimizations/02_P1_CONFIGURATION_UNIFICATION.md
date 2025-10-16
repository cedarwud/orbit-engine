# P1: Configuration管理統一

**優先級**: 🔴 P1 - 高（必須執行）
**預估時間**: 1天
**依賴**: Phase 1 完成
**影響範圍**: Stage 1, 3, 6 + 全局配置管理

---

## 🎯 目標

建立統一的配置管理系統，將所有階段的參數外部化到 YAML 配置檔案，並創建 `BaseConfigManager` 基類統一配置載入邏輯。

### 成功指標

- ✅ Stage 1, 3, 6 都有 YAML 配置檔案
- ✅ 所有階段使用統一的配置載入方式
- ✅ `BaseConfigManager` 提供配置合併、驗證工具
- ✅ 100% 向後相容（預設值與原行為一致）
- ✅ 所有測試通過

---

## 📊 當前問題分析

### 配置分散問題

| Stage | 當前狀態 | 問題 | 行數 |
|-------|---------|------|------|
| Stage 1 | 隱式配置（executor內） | ❌ 無法外部調整 | ~15行硬編碼 |
| Stage 2 | ✅ YAML配置 | ✅ 良好 | 0 |
| Stage 3 | 隱式配置（executor內） | ❌ 無法外部調整 | ~20行硬編碼 |
| Stage 4 | ✅ YAML配置 | ✅ 良好（但合併複雜） | 0 |
| Stage 5 | ✅ YAML配置 | ✅ 良好 | 0 |
| Stage 6 | ❌ 無配置檔 | ❌ 參數散佈代碼中 | ~30行硬編碼 |

**總計**: ~65行配置代碼需要外部化

---

## 🏗️ 解決方案設計

### 1. 創建 BaseConfigManager

**位置**: `src/shared/config_manager.py`（新增）

```python
"""
統一配置管理基類

提供功能:
- 配置載入（YAML文件）
- 配置合併（上游 + 本地，本地優先）
- 配置驗證（Fail-Fast）
- 環境變數覆蓋
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import os


class BaseConfigManager(ABC):
    """
    配置管理基類 - Template Method Pattern

    使用範例:
    ```python
    class Stage1ConfigManager(BaseConfigManager):
        def get_config_path(self) -> Path:
            return Path('config/stage1_orbital_calculation.yaml')

        def get_default_config(self) -> Dict[str, Any]:
            return {
                'sample_mode': False,
                'sample_size': 50,
                ...
            }

    # 使用
    config_manager = Stage1ConfigManager()
    config = config_manager.load_config()
    ```
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    # ===== Template Method =====

    def load_config(self, custom_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        載入配置（Template Method）

        流程:
        1. 獲取配置檔案路徑
        2. 載入 YAML 配置（如果存在）
        3. 與預設配置合併
        4. 環境變數覆蓋
        5. 驗證配置完整性

        Args:
            custom_path: 自訂配置檔案路徑（可選）

        Returns:
            完整的配置字典
        """
        # Step 1: 獲取配置路徑
        config_path = custom_path or self.get_config_path()

        # Step 2: 載入 YAML 配置
        yaml_config = self._load_yaml(config_path)

        # Step 3: 與預設配置合併
        default_config = self.get_default_config()
        merged_config = self.merge_configs(default_config, yaml_config)

        # Step 4: 環境變數覆蓋
        final_config = self._apply_env_overrides(merged_config)

        # Step 5: 驗證配置
        self.validate_config(final_config)

        return final_config

    def merge_configs(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        遞歸合併配置（override優先）

        Args:
            base: 基礎配置（預設值）
            override: 覆蓋配置（YAML或上游）

        Returns:
            合併後的配置

        Example:
            base = {'a': 1, 'b': {'c': 2}}
            override = {'b': {'c': 3, 'd': 4}}
            result = {'a': 1, 'b': {'c': 3, 'd': 4}}
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)
            ):
                # 遞歸合併嵌套字典
                result[key] = self.merge_configs(result[key], value)
            else:
                # 直接覆蓋
                result[key] = value

        return result

    # ===== 抽象方法（子類必須實現） =====

    @abstractmethod
    def get_config_path(self) -> Path:
        """
        返回配置檔案路徑

        Returns:
            配置檔案的 Path 對象

        Example:
            return Path('config/stage1_orbital_calculation.yaml')
        """
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        返回預設配置（回退值）

        Returns:
            預設配置字典

        Example:
            return {
                'sample_mode': False,
                'sample_size': 50,
                'epoch_analysis': {'enabled': True}
            }
        """
        pass

    # ===== 可覆寫方法 =====

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        驗證配置完整性（Fail-Fast）

        子類可覆寫此方法添加專用驗證。

        Args:
            config: 待驗證的配置

        Raises:
            ValueError: 配置驗證失敗

        Example:
            def validate_config(self, config):
                if 'sample_size' not in config:
                    raise ValueError("缺少 sample_size 配置")
                if config['sample_size'] <= 0:
                    raise ValueError("sample_size 必須 > 0")
        """
        # 基類默認不驗證（子類可覆寫）
        pass

    def get_env_overrides(self) -> Dict[str, str]:
        """
        返回環境變數覆蓋映射

        子類可覆寫此方法定義環境變數映射。

        Returns:
            環境變數名 → 配置路徑的映射

        Example:
            return {
                'ORBIT_ENGINE_SAMPLE_SIZE': 'sample_size',
                'ORBIT_ENGINE_SAMPLE_MODE': 'sample_mode'
            }
        """
        return {}

    # ===== 內部輔助方法 =====

    def _load_yaml(self, config_path: Path) -> Dict[str, Any]:
        """載入 YAML 配置檔案"""
        if not config_path.exists():
            self.logger.warning(f"⚠️ 配置檔案不存在: {config_path}，使用預設配置")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
            self.logger.info(f"✅ 已載入配置: {config_path}")
            return yaml_config
        except Exception as e:
            self.logger.error(f"❌ 載入配置失敗: {config_path}, {e}")
            raise ValueError(f"無法載入配置檔案: {config_path}") from e

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """應用環境變數覆蓋"""
        env_overrides = self.get_env_overrides()
        result = config.copy()

        for env_var, config_path in env_overrides.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 設置嵌套配置（支持 'a.b.c' 路徑）
                self._set_nested_value(result, config_path, env_value)
                self.logger.info(f"🔧 環境變數覆蓋: {env_var} → {config_path} = {env_value}")

        return result

    def _set_nested_value(self, config: Dict, path: str, value: Any):
        """設置嵌套配置值（支持 'a.b.c' 路徑）"""
        keys = path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 類型轉換
        current[keys[-1]] = self._convert_type(value)

    def _convert_type(self, value: str) -> Any:
        """環境變數類型轉換"""
        # 布林值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # 整數
        try:
            return int(value)
        except ValueError:
            pass

        # 浮點數
        try:
            return float(value)
        except ValueError:
            pass

        # 字符串
        return value
```

---

### 2. 創建 Stage 1 配置檔案

**位置**: `config/stage1_orbital_calculation.yaml`（新增）

```yaml
# Stage 1: TLE 數據載入與軌道初始化
#
# 配置說明:
# - sample_mode: 取樣模式（自動檢測或強制開啟）
# - sample_size: 取樣數量（測試模式使用）
# - epoch_analysis: Epoch 動態分析配置
# - epoch_filter: Epoch 篩選配置

# 取樣模式配置
sample_mode: auto  # auto | true | false
  # auto: 自動檢測（基於 ORBIT_ENGINE_TEST_MODE）
  # true: 強制開啟取樣模式
  # false: 強制關閉取樣模式

sample_size: 50  # 取樣數量（僅在 sample_mode=true 時生效）

# Epoch 分析配置
epoch_analysis:
  enabled: true  # 啟用 epoch 動態分析（找出最新日期）
  log_statistics: true  # 記錄 epoch 統計信息

# Epoch 篩選配置
epoch_filter:
  enabled: true  # 啟用 epoch 篩選
  mode: latest_date  # 篩選模式: latest_date | all
    # latest_date: 保留最新日期衛星（容差範圍內）
    # all: 不篩選，保留所有衛星
  tolerance_hours: 24  # 容差範圍（小時）
    # 例: tolerance_hours=24 表示保留距離最新日期 ±24h 內的衛星
    # SOURCE: TLE 數據時效性標準，通常 24-48h 內為有效數據

# TLE 數據源配置
tle_sources:
  directory: data/tle_data  # TLE 文件目錄
  file_patterns:
    - "*.tle"
    - "*.txt"

# 星座配置（可覆寫預設值）
constellation_configs:
  starlink:
    elevation_threshold: 5.0  # 仰角門檻（度）
      # SOURCE: 3GPP TR 38.821 Section 6.1.2
    frequency_ghz: 12.5  # 下行頻率（GHz）
      # SOURCE: Starlink Gen 2 Ku-band specification

  oneweb:
    elevation_threshold: 10.0  # 仰角門檻（度）
      # SOURCE: OneWeb constellation design requirements
    frequency_ghz: 12.75  # 下行頻率（GHz）
      # SOURCE: OneWeb Ku-band specification

# 研究配置
research_configuration:
  observation_location:
    name: NTPU  # 觀測站名稱
    latitude_deg: 24.94388888  # 緯度（度）
      # SOURCE: GPS surveyed coordinates
    longitude_deg: 121.37083333  # 經度（度）
    altitude_m: 36  # 海拔（米）
```

---

### 3. 創建 Stage 3 配置檔案

**位置**: `config/stage3_coordinate_transformation.yaml`（已存在，需補充）

```yaml
# Stage 3: 座標系統轉換層
#
# 配置說明:
# - geometric_prefilter: 幾何預篩選配置（v3.1已禁用）
# - coordinate_config: 座標轉換配置
# - precision_config: 精度配置
# - cache_config: HDF5緩存配置
# - parallel_config: 並行處理配置

# 幾何預篩選（v3.1 已禁用）
geometric_prefilter:
  enabled: false  # v3.1: 禁用幾何預篩選
  # REASON: 保留所有衛星數據，避免過早篩選

# 座標轉換配置
coordinate_config:
  source_frame: TEME  # 源座標系
    # True Equator Mean Equinox
  target_frame: WGS84  # 目標座標系
    # World Geodetic System 1984

  time_corrections: true  # 啟用時間修正
  polar_motion: true  # 啟用極移修正
    # SOURCE: IERS Earth Orientation Parameters

  nutation_model: IAU2000A  # 歲差章動模型
    # SOURCE: IAU 2000A precession-nutation model

# 精度配置
precision_config:
  target_accuracy_m: 0.5  # 目標精度（米）
    # 亞米級精度要求
    # SOURCE: Academic research requirements

# HDF5 緩存配置
cache_config:
  enabled: true  # 啟用 HDF5 緩存
  cache_dir: data/cache/stage3  # 緩存目錄
  compression: gzip  # 壓縮算法
  compression_opts: 6  # 壓縮級別（1-9）
  max_cache_size_mb: 500  # 最大緩存大小（MB）
  cache_expiry_hours: 168  # 緩存過期時間（小時，默認7天）

# 並行處理配置
parallel_config:
  enabled: true  # 啟用並行處理
  max_workers: 30  # 最大工作進程數
    # 可通過環境變數 ORBIT_ENGINE_MAX_WORKERS 覆蓋
  chunk_size: 100  # 批次大小
```

---

### 4. 創建 Stage 6 配置檔案

**位置**: `config/stage6_research_optimization_config.yaml`（新增）

```yaml
# Stage 6: 研究數據生成層
#
# 配置說明:
# - event_detection: 3GPP 事件檢測配置
# - handover_decision: 換手決策配置
# - research_data: 研究數據生成配置

# 3GPP 事件檢測配置
event_detection:
  # A3: 鄰居信號優於服務衛星（相對偏移）
  a3_offset_db: 3.0  # A3 偏移門檻（dB）
    # SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.4

  # A4: 鄰居信號超過絕對門檻
  a4_threshold_dbm: -110  # A4 絕對門檻（dBm）
    # SOURCE: 3GPP TS 38.133 Section 9.2.2.3

  # A5: 服務信號劣化且鄰居良好
  a5_threshold1_dbm: -110  # A5 服務門檻（dBm）
    # SOURCE: 3GPP TS 38.331 Section 5.5.4.5
  a5_threshold2_dbm: -95  # A5 鄰居門檻（dBm）

  # 遲滯和時間觸發
  hysteresis_db: 2.0  # 遲滯餘量（dB）
    # SOURCE: 3GPP TS 38.331 hysteresis parameter
  time_to_trigger_ms: 640  # 觸發時間（毫秒）
    # SOURCE: 3GPP TS 38.331 timeToTrigger values

  # D2: 地面基站切換事件（未來實現）
  d2_enabled: false  # D2 事件檢測（預留）

# 換手決策配置
handover_decision:
  evaluation_mode: batch  # 評估模式: batch | realtime
    # batch: 批次評估模式（學術研究用）
    # realtime: 實時評估模式（未來實現）

  # 服務衛星選擇策略
  serving_selection_strategy: median  # median | max_rsrp | random
    # median: 選擇中位數 RSRP 衛星（推薦）
    # max_rsrp: 選擇最高 RSRP 衛星
    # random: 隨機選擇

  # 候選衛星排序策略
  candidate_ranking: rsrp  # rsrp | elevation | distance
    # rsrp: 按 RSRP 排序（推薦）
    # elevation: 按仰角排序
    # distance: 按距離排序

  # 性能監控（學術研究禁用）
  enable_performance_metrics: false  # 禁用性能監控
    # REASON: 學術研究聚焦數據重現，不需要實時性能指標

  # 自適應門檻（學術研究禁用）
  enable_adaptive_thresholds: false  # 禁用自適應門檻
    # REASON: 使用 3GPP 標準固定值，確保學術可重現性

# 研究數據生成配置
research_data:
  # RL 訓練數據生成
  generate_rl_training_data: true  # 生成 RL 訓練數據

  # 狀態-動作-獎勵對
  state_features:
    - serving_rsrp  # 服務衛星 RSRP
    - neighbor_rsrp  # 鄰居衛星 RSRP
    - elevation  # 仰角
    - azimuth  # 方位角
    - distance  # 距離

  # 獎勵函數配置
  reward_function:
    rsrp_weight: 0.6  # RSRP 權重
    stability_weight: 0.3  # 穩定性權重
    efficiency_weight: 0.1  # 效率權重

  # 輸出格式
  output_format: json  # json | csv | both
```

---

## 🔧 實施步驟

### Step 1: 創建 BaseConfigManager（1小時）

```bash
# 1. 創建基類文件
touch src/shared/config_manager.py

# 2. 實現 BaseConfigManager（參考上面的設計）

# 3. 創建單元測試
touch tests/unit/shared/test_config_manager.py
```

**測試覆蓋**:
- ✅ YAML 載入
- ✅ 配置合併（遞歸）
- ✅ 環境變數覆蓋
- ✅ 配置驗證（Fail-Fast）
- ✅ 預設值回退

---

### Step 2: 創建 Stage 1/3/6 配置檔案（1小時）

```bash
# 1. 創建配置檔案
touch config/stage1_orbital_calculation.yaml
# （Stage 3 已存在，補充內容）
touch config/stage6_research_optimization_config.yaml

# 2. 填寫配置內容（參考上面的設計）

# 3. 驗證 YAML 語法
python -c "import yaml; yaml.safe_load(open('config/stage1_orbital_calculation.yaml'))"
```

---

### Step 3: 實現階段專用 ConfigManager（2小時）

**Stage 1**:
```python
# src/stages/stage1_orbital_calculation/config_manager.py
from shared.config_manager import BaseConfigManager

class Stage1ConfigManager(BaseConfigManager):
    def get_config_path(self) -> Path:
        return Path('config/stage1_orbital_calculation.yaml')

    def get_default_config(self) -> Dict[str, Any]:
        return {
            'sample_mode': 'auto',
            'sample_size': 50,
            'epoch_analysis': {'enabled': True},
            'epoch_filter': {
                'enabled': True,
                'mode': 'latest_date',
                'tolerance_hours': 24
            }
        }

    def validate_config(self, config: Dict[str, Any]):
        # Fail-Fast 驗證
        if config['sample_size'] <= 0:
            raise ValueError("sample_size 必須 > 0")
        if config['epoch_filter']['tolerance_hours'] < 0:
            raise ValueError("tolerance_hours 必須 >= 0")

    def get_env_overrides(self) -> Dict[str, str]:
        return {
            'ORBIT_ENGINE_SAMPLE_MODE': 'sample_mode',
            'ORBIT_ENGINE_SAMPLE_SIZE': 'sample_size'
        }
```

**Stage 3/6**: 類似實現

---

### Step 4: 更新 Executor 使用 ConfigManager（2小時）

**Before** (`scripts/stage_executors/stage1_executor.py`):
```python
def load_config(self) -> Dict[str, Any]:
    # ❌ 硬編碼配置
    config = {
        'sample_mode': use_sampling,
        'sample_size': 50,
        ...
    }
    return config
```

**After**:
```python
def load_config(self) -> Dict[str, Any]:
    # ✅ 使用 ConfigManager
    from stages.stage1_orbital_calculation.config_manager import Stage1ConfigManager

    config_manager = Stage1ConfigManager()
    config = config_manager.load_config()

    # 顯示配置摘要
    print(f"📋 配置摘要:")
    print(f"   取樣模式: {config['sample_mode']}")
    print(f"   Epoch 篩選: {config['epoch_filter']['mode']}")

    return config
```

---

### Step 5: 測試與驗證（2小時）

```bash
# 1. 單元測試
pytest tests/unit/shared/test_config_manager.py -v

# 2. 集成測試（Stage 1-6）
export ORBIT_ENGINE_TEST_MODE=1
./run.sh --stages 1-6

# 3. 配置覆蓋測試
export ORBIT_ENGINE_SAMPLE_SIZE=100
./run.sh --stage 1
# 驗證: sample_size 應該是 100

# 4. 向後相容測試
# 刪除配置檔案，確認使用預設值
mv config/stage1_orbital_calculation.yaml config/stage1_orbital_calculation.yaml.bak
./run.sh --stage 1
# 驗證: 應該使用預設值且正常執行
```

---

## ✅ 驗收標準

### 功能驗收

- [ ] BaseConfigManager 創建完成（~150行）
- [ ] Stage 1/3/6 配置檔案創建完成
- [ ] 所有階段使用 ConfigManager 載入配置
- [ ] 環境變數覆蓋功能正常
- [ ] 配置驗證（Fail-Fast）正常

### 測試驗收

- [ ] BaseConfigManager 單元測試（≥15個測試，80%覆蓋率）
- [ ] Stage 1-6 完整管道測試通過
- [ ] 配置覆蓋測試通過
- [ ] 向後相容測試通過（無配置檔時使用預設值）

### 質量驗收

- [ ] 所有測試通過
- [ ] 性能無退化（< 5%）
- [ ] 代碼風格檢查通過（pylint, mypy）
- [ ] 文檔更新（CLAUDE.md, README.md）

---

## 📊 預期收益

### 代碼質量

- ✅ 消除 ~65行硬編碼配置
- ✅ 統一配置管理方式（100%）
- ✅ 配置外部化（100%）

### 可維護性

- ✅ 參數調整無需修改代碼
- ✅ 環境變數覆蓋支持
- ✅ 配置驗證（Fail-Fast）

### 靈活性

- ✅ 快速測試不同配置
- ✅ 多環境部署支持
- ✅ 配置繼承和覆蓋

---

## ⚠️ 注意事項

### 向後相容

- ✅ 預設值必須與原行為一致
- ✅ 保留所有環境變數檢查
- ✅ 配置檔案不存在時回退到預設值

### 學術合規

- ✅ 所有參數必須有 SOURCE 註解
- ✅ 不允許隨意修改標準值
- ✅ 配置變更需要文檔記錄

### 測試要求

- ✅ 配置載入失敗時 Fail-Fast
- ✅ 環境變數覆蓋優先級正確
- ✅ 配置合併邏輯正確（遞歸合併）

---

**下一步**: 閱讀 [03_P2_ERROR_HANDLING.md](03_P2_ERROR_HANDLING.md)
