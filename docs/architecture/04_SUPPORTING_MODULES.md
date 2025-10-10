# 支持模塊與檔案清單

本文檔補充說明 Orbit Engine 中所有支持性模塊和檔案，這些是六階段執行系統依賴的底層實現。

---

## 目錄

- [scripts/ 目錄下的工具腳本](#scripts-目錄下的工具腳本)
- [src/shared/ 共用模塊](#srcshared-共用模塊)
- [Stage 1 子模塊](#stage-1-子模塊)
- [Stage 2 子模塊](#stage-2-子模塊)
- [Stage 3 子模塊](#stage-3-子模塊)
- [Stage 4 子模塊](#stage-4-子模塊)
- [Stage 5 子模塊](#stage-5-子模塊)
- [Stage 6 子模塊](#stage-6-子模塊)

---

## scripts/ 目錄下的工具腳本

### 核心執行腳本

| 檔案 | 說明 | 備註 |
|------|------|------|
| `run_six_stages_with_validation.py` | 主執行腳本 (332 行) | 已記錄於 02_STAGES_DETAIL.md |

### 工具腳本

| 檔案 | 說明 | 用途 |
|------|------|------|
| **generate_validation_snapshot.py** | 驗證快照生成工具 | 獨立生成驗證快照（調試用） |
| **run_parameter_sweep.py** | 參數掃描工具 | 用於 Stage 6 的參數優化實驗 |

#### generate_validation_snapshot.py

**用途**: 獨立生成各階段的驗證快照，無需完整執行管道。

**使用場景**:
- 調試驗證邏輯
- 重新生成驗證快照
- 驗證快照格式檢查

**執行方式**:
```bash
python scripts/generate_validation_snapshot.py --stage 1
python scripts/generate_validation_snapshot.py --stage 5
```

#### run_parameter_sweep.py

**用途**: 自動化參數掃描實驗，用於研究優化階段 (Stage 6)。

**使用場景**:
- A3/A4/A5 門檻值優化
- 遲滯餘量 (hysteresis) 調整
- 時間觸發 (time-to-trigger) 調整

**執行方式**:
```bash
python scripts/run_parameter_sweep.py --constellation starlink --event-type a3
```

**輸出**:
- `results/parameter_sweep_*/sweep_results.json`
- `results/parameter_sweep_*/optimal_parameters.json`

---

## src/shared/ 共用模塊

### 概覽

`src/shared/` 包含所有階段共用的基礎設施代碼。

```
src/shared/
├── base_processor.py                         # 基礎處理器類
├── base_stage_processor.py                   # 階段處理器基類
├── constants/                                # 常數定義模塊
├── coordinate_systems/                       # 座標系統模塊
├── interfaces/                               # 接口定義
├── utils/                                    # 工具函數
└── validation_framework/                     # 驗證框架
```

---

### 1. 基礎處理器類

#### base_processor.py

**說明**: 所有處理器的基類，定義通用接口。

**關鍵類**:
```python
class BaseProcessor:
    """所有處理器的基類"""
    def execute(self, input_data):
        """執行處理邏輯"""
        pass

    def validate(self, data):
        """驗證數據"""
        pass
```

**使用者**: 所有 Stage 處理器繼承此類。

#### base_stage_processor.py

**說明**: 階段處理器專用基類，擴展 BaseProcessor。

**關鍵類**:
```python
class BaseStageProcessor(BaseProcessor):
    """階段處理器基類"""
    def save_validation_snapshot(self, data):
        """保存驗證快照"""
        pass

    def run_validation_checks(self, data):
        """執行驗證檢查"""
        pass
```

**使用者**: Stage 1-6 的主處理器。

---

### 2. constants/ - 常數定義模塊

#### 模塊結構

```
src/shared/constants/
├── __init__.py
├── academic_standards.py           # 學術標準常數
├── astropy_physics_constants.py    # Astropy 物理常數
├── constellation_constants.py      # 星座配置常數
├── handover_constants.py           # 換手事件常數
├── physics_constants.py            # 物理常數
├── system_constants.py             # 系統配置常數
└── tle_constants.py                # TLE 格式常數
```

#### academic_standards.py

**說明**: 學術標準相關常數（ITU-R, 3GPP, NASA JPL）。

**關鍵常數**:
```python
# 3GPP TS 38.214 RSRP 測量範圍
RSRP_MIN_DBM = -140.0
RSRP_MAX_DBM = -44.0  # 報告範圍，非物理限制

# ITU-R P.676-13 大氣模型參數
ITU_R_P676_VERSION = "13"
STANDARD_TEMPERATURE_K = 288.15
STANDARD_PRESSURE_HPA = 1013.25

# NASA JPL 星曆表
EPHEMERIS_FILE = "de421.bsp"
EPHEMERIS_ACCURACY_M = 0.5
```

**使用階段**: Stage 5 (信號品質分析)

#### constellation_constants.py

**說明**: Starlink 和 OneWeb 星座配置常數。

**關鍵常數**:
```python
# Starlink 配置
STARLINK_ALTITUDE_KM = 550
STARLINK_ELEVATION_THRESHOLD_DEG = 5.0
STARLINK_FREQUENCY_GHZ = 12.5
STARLINK_TARGET_POOL_SIZE = 12

# OneWeb 配置
ONEWEB_ALTITUDE_KM = 1200
ONEWEB_ELEVATION_THRESHOLD_DEG = 10.0
ONEWEB_FREQUENCY_GHZ = 12.75
ONEWEB_TARGET_POOL_SIZE = 5
```

**使用階段**: Stage 1, Stage 4

#### handover_constants.py

**說明**: 3GPP 換手事件常數。

**關鍵常數**:
```python
# 3GPP TS 38.331 Section 5.5.4
A3_OFFSET_DB = 3.0              # A3 事件偏移門檻
A4_THRESHOLD_DBM = -110.0       # A4 絕對門檻
A5_THRESHOLD1_DBM = -110.0      # A5 服務門檻
A5_THRESHOLD2_DBM = -95.0       # A5 鄰居門檻

HYSTERESIS_DB = 2.0             # 遲滯餘量
TIME_TO_TRIGGER_MS = 640        # 觸發時間
```

**使用階段**: Stage 6 (研究數據生成)

#### physics_constants.py

**說明**: 物理常數（光速、波爾茲曼常數等）。

**關鍵常數**:
```python
SPEED_OF_LIGHT_M_S = 299792458.0        # 光速 (m/s)
BOLTZMANN_CONSTANT_J_K = 1.380649e-23   # 波爾茲曼常數 (J/K)
EARTH_RADIUS_KM = 6371.0                # 地球半徑 (km)
```

**使用階段**: Stage 2, Stage 3, Stage 5

#### system_constants.py

**說明**: 系統配置常數（並行處理、緩存等）。

**關鍵常數**:
```python
DEFAULT_MAX_WORKERS = 30        # 預設並行工作進程數
CACHE_DIR = "data/cache"        # 緩存目錄
OUTPUT_DIR = "data/outputs"     # 輸出目錄
SNAPSHOT_DIR = "data/validation_snapshots"  # 驗證快照目錄
```

**使用階段**: 所有階段

#### tle_constants.py

**說明**: TLE 格式常數（NORAD 標準）。

**關鍵常數**:
```python
TLE_LINE_LENGTH = 69            # TLE 標準行長度
TLE_LINE1_PREFIX = "1 "         # TLE Line 1 前綴
TLE_LINE2_PREFIX = "2 "         # TLE Line 2 前綴

# TLE 字段位置
NORAD_ID_START = 2
NORAD_ID_END = 7
EPOCH_START = 18
EPOCH_END = 32
```

**使用階段**: Stage 1 (TLE 數據載入)

---

### 3. coordinate_systems/ - 座標系統模塊

#### 模塊結構

```
src/shared/coordinate_systems/
├── __init__.py
├── iers_data_manager.py             # IERS 地球定向參數管理
├── skyfield_coordinate_engine.py    # Skyfield 座標轉換引擎
└── wgs84_manager.py                 # WGS84 座標管理
```

#### iers_data_manager.py

**說明**: 管理 IERS (國際地球自轉服務) 地球定向參數。

**主要功能**:
- 下載和緩存 IERS finals2000A.all 數據
- 提供極移 (Polar Motion) 和 UT1-UTC 修正
- 自動更新過期數據

**關鍵類**:
```python
class IERSDataManager:
    def get_polar_motion(self, utc_time):
        """獲取極移參數 (x, y)"""
        pass

    def get_ut1_utc(self, utc_time):
        """獲取 UT1-UTC 時間修正"""
        pass
```

**使用階段**: Stage 3 (座標轉換)

**緩存位置**: `data/cache/iers/`

#### skyfield_coordinate_engine.py

**說明**: 基於 Skyfield 的座標轉換引擎。

**主要功能**:
- TEME → ECEF 轉換
- ECEF → Geodetic WGS84 轉換
- 時間系統轉換 (UTC → TT → UT1)
- IAU 2000A 歲差章動模型

**關鍵類**:
```python
class SkyfieldCoordinateEngine:
    def teme_to_ecef(self, teme_coords, utc_time):
        """TEME → ECEF 轉換"""
        pass

    def ecef_to_geodetic(self, ecef_coords):
        """ECEF → Geodetic WGS84 轉換"""
        pass
```

**使用階段**: Stage 3 (座標轉換)

**學術標準**: IAU 2000A/2006, IERS Conventions 2010

#### wgs84_manager.py

**說明**: WGS84 座標系統管理。

**主要功能**:
- 計算仰角 (Elevation)
- 計算方位角 (Azimuth)
- 計算斜距 (Slant Range)
- 地表距離計算

**關鍵類**:
```python
class WGS84Manager:
    def calculate_elevation(self, satellite_position, observer_position):
        """計算仰角"""
        pass

    def calculate_azimuth(self, satellite_position, observer_position):
        """計算方位角"""
        pass

    def calculate_slant_range(self, satellite_position, observer_position):
        """計算斜距"""
        pass
```

**使用階段**: Stage 3, Stage 4

---

### 4. interfaces/ - 接口定義

#### processor_interface.py

**說明**: 定義處理器標準接口和數據結構。

**關鍵類**:

```python
class ProcessingStatus(Enum):
    """處理狀態枚舉"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

class ProcessingResult:
    """處理結果標準格式"""
    def __init__(self, status, data, errors=None, metrics=None):
        self.status = status
        self.data = data
        self.errors = errors or []
        self.metrics = metrics or {}
```

**使用者**: 所有階段處理器返回 `ProcessingResult`

---

### 5. utils/ - 工具函數

#### 模塊結構

```
src/shared/utils/
├── __init__.py
├── file_utils.py        # 檔案操作工具
├── math_utils.py        # 數學計算工具
└── time_utils.py        # 時間處理工具
```

#### file_utils.py

**說明**: 檔案 I/O 工具函數。

**主要函數**:
```python
def save_json(data, file_path):
    """保存 JSON 文件"""
    pass

def load_json(file_path):
    """載入 JSON 文件"""
    pass

def ensure_directory(dir_path):
    """確保目錄存在"""
    pass

def find_latest_file(directory, pattern):
    """找到最新的文件"""
    pass
```

**使用階段**: 所有階段

#### math_utils.py

**說明**: 數學計算工具函數。

**主要函數**:
```python
def calculate_distance_3d(point1, point2):
    """計算 3D 歐幾里得距離"""
    pass

def deg_to_rad(degrees):
    """角度轉弧度"""
    pass

def rad_to_deg(radians):
    """弧度轉角度"""
    pass

def normalize_angle(angle_deg):
    """正規化角度到 [0, 360)"""
    pass
```

**使用階段**: Stage 3, Stage 4, Stage 5

#### time_utils.py

**說明**: 時間處理工具函數。

**主要函數**:
```python
def parse_tle_epoch(tle_epoch_string):
    """解析 TLE epoch 字符串"""
    pass

def utc_to_julian_date(utc_time):
    """UTC 轉儒略日"""
    pass

def format_iso8601(datetime_obj):
    """格式化為 ISO 8601 字符串"""
    pass
```

**使用階段**: Stage 1, Stage 2, Stage 3

---

### 6. validation_framework/ - 驗證框架

#### 模塊結構

```
src/shared/validation_framework/
├── __init__.py
├── academic_validation_framework.py     # 學術標準驗證框架
├── real_time_snapshot_system.py         # 實時快照系統
├── stage4_validator.py                  # Stage 4 驗證器 (共用)
├── stage5_signal_validator.py           # Stage 5 信號驗證器 (共用)
└── validation_engine.py                 # 驗證引擎
```

#### academic_validation_framework.py

**說明**: 學術標準驗證框架（ITU-R, 3GPP 合規性檢查）。

**主要功能**:
- 檢查算法是否符合官方標準
- 檢查參數是否有 SOURCE 注釋
- 檢查是否使用 mock/simplified 算法

**關鍵類**:
```python
class AcademicValidationFramework:
    def validate_algorithm_compliance(self, algorithm_name, implementation):
        """驗證算法合規性"""
        pass

    def check_source_annotations(self, code_module):
        """檢查 SOURCE 注釋"""
        pass
```

**使用階段**: 所有階段（開發時檢查）

#### real_time_snapshot_system.py

**說明**: 實時快照系統，用於驗證快照生成和管理。

**主要功能**:
- 生成驗證快照
- 管理快照版本
- 比對快照差異

**關鍵類**:
```python
class RealTimeSnapshotSystem:
    def generate_snapshot(self, stage_num, data):
        """生成驗證快照"""
        pass

    def compare_snapshots(self, snapshot1, snapshot2):
        """比對快照差異"""
        pass
```

**使用階段**: 所有階段

#### stage4_validator.py (共用)

**說明**: Stage 4 專用驗證器（共用模塊）。

**主要功能**:
- 池優化結果驗證
- 覆蓋率計算驗證
- 服務窗口完整性檢查

**使用階段**: Stage 4

**備註**: 與 `scripts/stage_validators/stage4_validator.py` 不同，此為處理器內部使用的驗證邏輯。

#### stage5_signal_validator.py (共用)

**說明**: Stage 5 專用信號品質驗證器（共用模塊）。

**主要功能**:
- RSRP/RSRQ/SINR 範圍檢查
- ITU-R 模型參數驗證
- 3GPP 標準合規性檢查

**使用階段**: Stage 5

#### validation_engine.py

**說明**: 通用驗證引擎。

**主要功能**:
- 數據類型檢查
- 數值範圍檢查
- 必要字段檢查
- 統計特性檢查

**關鍵類**:
```python
class ValidationEngine:
    def validate_required_fields(self, data, required_fields):
        """驗證必要字段"""
        pass

    def validate_value_range(self, value, min_val, max_val):
        """驗證數值範圍"""
        pass

    def validate_statistical_properties(self, data, expected_stats):
        """驗證統計特性"""
        pass
```

**使用階段**: 所有階段

---

## Stage 1 子模塊

### 目錄結構

```
src/stages/stage1_orbital_calculation/
├── __init__.py
├── stage1_main_processor.py          # 主處理器 (已記錄)
├── tle_data_loader.py                # TLE 數據載入器
├── epoch_analyzer.py                 # Epoch 分析器
├── time_reference_manager.py         # 時間基準管理器
├── data_validator.py                 # 數據驗證器
├── checkers/                         # 檢查器子模塊
│   ├── __init__.py
│   ├── academic_checker.py           # 學術標準檢查器
│   └── requirement_checker.py        # 需求檢查器
├── validators/                       # 驗證器子模塊
│   ├── __init__.py
│   ├── format_validator.py           # TLE 格式驗證器
│   └── checksum_validator.py         # TLE 校驗和驗證器
├── metrics/                          # 指標計算子模塊
│   ├── __init__.py
│   ├── accuracy_calculator.py        # 精度計算器
│   └── consistency_calculator.py     # 一致性計算器
└── reports/                          # 報告生成子模塊
    ├── __init__.py
    └── statistics_reporter.py        # 統計報告生成器
```

### 關鍵子模塊說明

#### tle_data_loader.py

**主要功能**:
- 讀取 `.tle` 文件
- 解析 NORAD TLE 格式
- 分類衛星（Starlink, OneWeb）

**關鍵類**:
```python
class TLEDataLoader:
    def load_tle_files(self, tle_directory):
        """載入 TLE 文件"""
        pass

    def parse_tle(self, tle_line1, tle_line2):
        """解析 TLE 兩行元素"""
        pass
```

#### epoch_analyzer.py

**主要功能**:
- 分析 TLE epoch 分佈
- 找出最新日期
- 計算容差範圍

**關鍵類**:
```python
class EpochAnalyzer:
    def analyze_epoch_distribution(self, satellites):
        """分析 epoch 分佈"""
        pass

    def find_latest_date(self, satellites):
        """找出最新日期"""
        pass

    def filter_by_tolerance(self, satellites, latest_date, tolerance_hours):
        """根據容差篩選衛星"""
        pass
```

**學術依據**: SGP4 精度分析（±24 小時容差）

#### time_reference_manager.py

**主要功能**:
- 管理每顆衛星的獨立時間基準
- 確保不存在統一時間基準
- 提供 epoch 相關計算

**關鍵類**:
```python
class TimeReferenceManager:
    def get_satellite_epoch(self, satellite_id):
        """獲取衛星 epoch"""
        pass

    def validate_no_unified_time_base(self, metadata):
        """驗證不存在統一時間基準"""
        pass
```

**學術合規性**: 禁止統一時間基準（CLAUDE.md 要求）

#### checkers/academic_checker.py

**主要功能**:
- 檢查是否使用 simplified 算法
- 檢查是否使用 mock 數據
- 檢查參數是否有 SOURCE 注釋

**關鍵類**:
```python
class AcademicChecker:
    def check_no_simplified_algorithms(self, code_module):
        """檢查無簡化算法"""
        pass

    def check_source_annotations(self, parameters):
        """檢查 SOURCE 注釋"""
        pass
```

#### validators/format_validator.py

**主要功能**:
- 驗證 TLE 格式 (69 字符)
- 驗證行號 ('1 ', '2 ')
- 驗證 NORAD ID 格式

**關鍵類**:
```python
class FormatValidator:
    def validate_tle_line_length(self, tle_line):
        """驗證 TLE 行長度"""
        pass

    def validate_tle_line_number(self, tle_line, expected_line_num):
        """驗證 TLE 行號"""
        pass
```

**學術標準**: NORAD Two-Line Element Set Format

#### validators/checksum_validator.py

**主要功能**:
- 驗證 TLE 校驗和
- 確保數據完整性

**關鍵類**:
```python
class ChecksumValidator:
    def validate_checksum(self, tle_line):
        """驗證 TLE 校驗和"""
        pass
```

---

## Stage 2 子模塊

### 目錄結構

```
src/stages/stage2_orbital_computing/
├── __init__.py
├── stage2_orbital_computing_processor.py    # 主處理器 (已記錄)
├── sgp4_calculator.py                       # SGP4 計算器
├── unified_time_window_manager.py           # 統一時間窗口管理器
├── stage2_result_manager.py                 # 結果管理器
└── stage2_validator.py                      # 驗證器
```

### 關鍵子模塊說明

#### sgp4_calculator.py

**主要功能**:
- 使用 Skyfield 執行 SGP4 軌道傳播
- 計算 TEME 座標
- 計算軌道週期

**關鍵類**:
```python
class SGP4Calculator:
    def propagate_orbit(self, tle, time_series):
        """傳播軌道"""
        pass

    def calculate_orbital_period(self, tle):
        """計算軌道週期"""
        pass
```

**學術標準**: NASA GSFC SGP4 implementation via Skyfield

#### unified_time_window_manager.py

**主要功能**:
- 管理時間序列生成
- 計算覆蓋軌道週期數
- 確保星座統一的時間窗口（用於可比性）

**關鍵類**:
```python
class UnifiedTimeWindowManager:
    def generate_time_series(self, start_time, orbital_period, num_periods):
        """生成時間序列"""
        pass

    def calculate_coverage_duration(self, orbital_period, coverage_periods):
        """計算覆蓋時長"""
        pass
```

**設計理念**: 每顆衛星有獨立 epoch，但使用統一觀測時間窗口（用於研究可比性）

#### stage2_result_manager.py

**主要功能**:
- 管理 HDF5 輸出
- 管理 JSON 元數據
- 壓縮和優化存儲

**關鍵類**:
```python
class Stage2ResultManager:
    def save_to_hdf5(self, satellite_data, h5_file_path):
        """保存到 HDF5"""
        pass

    def save_metadata(self, metadata, json_file_path):
        """保存元數據"""
        pass
```

---

## Stage 3 子模塊

### 目錄結構

```
src/stages/stage3_coordinate_transformation/
├── __init__.py
├── stage3_coordinate_transform_processor.py    # 主處理器 (已記錄)
├── stage3_transformation_engine.py             # 轉換引擎
├── geometric_prefilter.py                      # 幾何預篩選器 (已禁用)
├── stage3_data_extractor.py                    # 數據提取器
├── stage3_data_validator.py                    # 數據驗證器
├── stage3_results_manager.py                   # 結果管理器
└── stage3_compliance_validator.py              # 合規性驗證器
```

### 關鍵子模塊說明

#### stage3_transformation_engine.py

**主要功能**:
- TEME → ECEF → Geodetic WGS84 轉換
- IAU 2000A 歲差章動模型
- IERS 極移修正

**關鍵類**:
```python
class Stage3TransformationEngine:
    def transform_teme_to_geodetic(self, teme_coords, utc_time):
        """TEME → Geodetic WGS84"""
        pass

    def calculate_observer_relative_coords(self, satellite_geo, observer_geo):
        """計算觀測者相對座標（仰角、方位角、斜距）"""
        pass
```

**學術標準**: IAU 2000A/2006, IERS Conventions 2010

#### geometric_prefilter.py (已禁用 v3.1)

**主要功能**: 幾何預篩選（已禁用，由 Stage 1 的 epoch 篩選替代）

**狀態**: v3.1 版本已禁用，保留代碼供參考

#### stage3_data_extractor.py

**主要功能**:
- 從 Stage 2 HDF5 文件提取數據
- 批次讀取優化

**關鍵類**:
```python
class Stage3DataExtractor:
    def extract_teme_from_hdf5(self, h5_file_path, satellite_id):
        """從 HDF5 提取 TEME 座標"""
        pass
```

#### stage3_results_manager.py

**主要功能**:
- 管理 Stage 3 輸出
- HDF5 緩存管理
- JSON 結果保存

---

## Stage 4 子模塊

### 目錄結構

```
src/stages/stage4_link_feasibility/
├── __init__.py
├── stage4_link_feasibility_processor.py        # 主處理器 (已記錄)
├── skyfield_visibility_calculator.py           # Skyfield 可見性計算器
├── pool_optimizer.py                           # 動態池優化器
├── link_budget_analyzer.py                     # 鏈路預算分析器
├── constellation_filter.py                     # 星座篩選器
├── dynamic_threshold_analyzer.py               # 動態門檻分析器
├── epoch_validator.py                          # Epoch 驗證器
├── poliastro_validator.py                      # Poliastro 交叉驗證器
├── filtering/                                  # 篩選子模塊
│   ├── __init__.py
│   └── satellite_filter.py                     # 衛星篩選器
├── data_processing/                            # 數據處理子模塊
│   ├── __init__.py
│   ├── coordinate_extractor.py                 # 座標提取器
│   └── service_window_calculator.py            # 服務窗口計算器
└── output_management/                          # 輸出管理子模塊
    ├── __init__.py
    ├── result_builder.py                       # 結果建構器
    └── snapshot_manager.py                     # 快照管理器
```

### 關鍵子模塊說明

#### skyfield_visibility_calculator.py

**主要功能**:
- 基於 Skyfield 的可見性計算
- 仰角門檻判斷
- 遮蔽檢查

**關鍵類**:
```python
class SkyfieldVisibilityCalculator:
    def is_visible(self, satellite_elevation, threshold_deg):
        """判斷是否可見"""
        pass

    def calculate_visibility_windows(self, satellite_positions, observer):
        """計算可見性窗口"""
        pass
```

#### pool_optimizer.py

**主要功能**:
- 動態衛星池優化
- 覆蓋率計算
- 池大小自適應調整

**關鍵類**:
```python
class PoolOptimizer:
    def optimize_satellite_pool(self, visible_satellites, target_coverage_rate):
        """優化衛星池"""
        pass

    def calculate_coverage_rate(self, pool_satellites, time_series):
        """計算覆蓋率"""
        pass
```

**學術依據**: 3GPP TR 38.821 Section 6.1.2

#### link_budget_analyzer.py

**主要功能**:
- 鏈路預算分析
- 自由空間路徑損耗計算

**關鍵類**:
```python
class LinkBudgetAnalyzer:
    def calculate_free_space_loss(self, distance_km, frequency_ghz):
        """計算自由空間路徑損耗"""
        pass
```

**公式**: FSPL(dB) = 20 log₁₀(d) + 20 log₁₀(f) + 92.45

#### data_processing/service_window_calculator.py

**主要功能**:
- 服務窗口計算
- 連續可見時段識別
- 最大仰角計算

**關鍵類**:
```python
class ServiceWindowCalculator:
    def calculate_service_windows(self, visibility_time_series):
        """計算服務窗口"""
        pass

    def find_max_elevation(self, window_elevations):
        """找到最大仰角"""
        pass
```

---

## Stage 5 子模塊

### 目錄結構

```
src/stages/stage5_signal_analysis/
├── __init__.py
├── stage5_signal_analysis_processor.py         # 主處理器 (已記錄)
├── gpp_ts38214_signal_calculator.py            # 3GPP 信號計算器 (已記錄)
├── itur_official_atmospheric_model.py          # ITU-R 大氣模型 (已記錄)
├── itur_physics_calculator.py                  # ITU-R 物理計算器
├── doppler_calculator.py                       # 多普勒計算器
├── coordinate_converter.py                     # 座標轉換器
├── time_series_analyzer.py                     # 時間序列分析器
├── stage5_compliance_validator.py              # 合規性驗證器
├── data_processing/                            # 數據處理子模塊
│   ├── __init__.py
│   ├── config_manager.py                       # 配置管理器
│   └── input_extractor.py                      # 輸入提取器
├── output_management/                          # 輸出管理子模塊
│   ├── __init__.py
│   ├── result_builder.py                       # 結果建構器
│   └── snapshot_manager.py                     # 快照管理器
└── parallel_processing/                        # 並行處理子模塊
    ├── __init__.py
    ├── cpu_optimizer.py                        # CPU 優化器
    └── worker_manager.py                       # 工作進程管理器
```

### 關鍵子模塊說明

#### itur_physics_calculator.py

**主要功能**:
- 大氣參數計算（溫度、壓力、水汽密度）
- 基於 ITU-R P.835-6 標準

**關鍵類**:
```python
class ITURPhysicsCalculator:
    def calculate_atmospheric_parameters(self, altitude_m, latitude_deg):
        """計算大氣參數"""
        pass
```

**學術標準**: ITU-R P.835-6

#### doppler_calculator.py

**主要功能**:
- 多普勒頻移計算
- 衛星相對速度計算

**關鍵類**:
```python
class DopplerCalculator:
    def calculate_doppler_shift(self, satellite_velocity, observer_position, frequency_ghz):
        """計算多普勒頻移"""
        pass
```

**公式**: Δf = (v/c) × f₀

#### time_series_analyzer.py

**主要功能**:
- 時間序列信號品質分析
- 統計特性計算
- 異常檢測

**關鍵類**:
```python
class TimeSeriesAnalyzer:
    def analyze_signal_quality_time_series(self, rsrp_time_series):
        """分析信號品質時間序列"""
        pass

    def detect_anomalies(self, signal_data):
        """檢測異常值"""
        pass
```

#### parallel_processing/cpu_optimizer.py

**主要功能**:
- CPU 核心數檢測
- 工作進程數優化
- 負載平衡

**關鍵類**:
```python
class CPUOptimizer:
    def get_optimal_worker_count(self):
        """獲取最佳工作進程數"""
        pass
```

**預設**: 30 個工作進程 (可通過 ORBIT_ENGINE_MAX_WORKERS 環境變量調整)

---

## Stage 6 子模塊

### 目錄結構

```
src/stages/stage6_research_optimization/
├── __init__.py
├── stage6_research_optimization_processor.py   # 主處理器 (已記錄)
├── gpp_event_detector.py                       # 3GPP 事件檢測器 (已記錄)
├── handover_decision_evaluator.py              # 換手決策評估器 (已記錄)
├── coordinate_converter.py                     # 座標轉換器
├── ground_distance_calculator.py               # 地面距離計算器
├── satellite_pool_verifier.py                  # 衛星池驗證器
├── stage6_academic_compliance.py               # 學術合規性檢查器
├── stage6_input_output_validator.py            # 輸入輸出驗證器
├── stage6_snapshot_manager.py                  # 快照管理器
└── stage6_validation_framework.py              # 驗證框架
```

### 關鍵子模塊說明

#### coordinate_converter.py

**主要功能**:
- WGS84 → ECEF 轉換
- 地心座標計算

**關鍵類**:
```python
class CoordinateConverter:
    def geodetic_to_ecef(self, lat_deg, lon_deg, alt_m):
        """WGS84 → ECEF"""
        pass
```

#### ground_distance_calculator.py

**主要功能**:
- 計算地面距離（Haversine 公式）
- D2 事件檢測依據

**關鍵類**:
```python
class GroundDistanceCalculator:
    def calculate_haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算地面距離"""
        pass
```

**學術標準**: Haversine formula

#### satellite_pool_verifier.py

**主要功能**:
- 驗證 Stage 4 的衛星池結果
- 檢查候選衛星有效性

**關鍵類**:
```python
class SatellitePoolVerifier:
    def verify_candidate_satellites(self, candidates, pool_satellites):
        """驗證候選衛星"""
        pass
```

#### stage6_academic_compliance.py

**主要功能**:
- 檢查 3GPP 標準合規性
- 檢查事件定義正確性

**關鍵類**:
```python
class Stage6AcademicCompliance:
    def check_3gpp_event_compliance(self, events):
        """檢查 3GPP 事件合規性"""
        pass
```

**學術標準**: 3GPP TS 38.331 v18.5.1 Section 5.5.4

---

## 檔案統計總結

### scripts/ 目錄

| 類別 | 檔案數 | 說明 |
|------|--------|------|
| 主執行腳本 | 1 | `run_six_stages_with_validation.py` |
| 工具腳本 | 2 | `generate_validation_snapshot.py`, `run_parameter_sweep.py` |
| 執行器 | 6 + 1 | 6個階段執行器 + 1個工具模塊 |
| 驗證器 | 6 | 6個階段驗證器 |
| **總計** | **16** | |

### src/shared/ 目錄

| 模塊 | 檔案數 | 說明 |
|------|--------|------|
| 基礎類 | 2 | `base_processor.py`, `base_stage_processor.py` |
| constants/ | 8 | 常數定義 |
| coordinate_systems/ | 3 | 座標系統 |
| interfaces/ | 1 | 接口定義 |
| utils/ | 3 | 工具函數 |
| validation_framework/ | 5 | 驗證框架 |
| **總計** | **22** | |

### src/stages/ 目錄

| 階段 | 主處理器 | 子模塊檔案數 | 說明 |
|------|---------|------------|------|
| Stage 1 | 1 | 13 | TLE 載入、Epoch 分析、格式驗證 |
| Stage 2 | 1 | 4 | SGP4 計算、HDF5 管理 |
| Stage 3 | 1 | 6 | 座標轉換、IERS 數據 |
| Stage 4 | 1 | 13 | 可見性計算、池優化 |
| Stage 5 | 1 | 14 | 信號計算、ITU-R 模型 |
| Stage 6 | 1 | 9 | 事件檢測、換手評估 |
| **總計** | **6** | **59** | |

### 總計

- **scripts/**: 16 個檔案
- **src/shared/**: 22 個檔案
- **src/stages/**: 65 個檔案（6 個主處理器 + 59 個子模塊）
- **總計**: **103 個 Python 檔案**

---

## 相關文檔

- **主執行流程**: [01_EXECUTION_FLOW.md](./01_EXECUTION_FLOW.md)
- **六階段詳細**: [02_STAGES_DETAIL.md](./02_STAGES_DETAIL.md)
- **驗證系統**: [03_VALIDATION_SYSTEM.md](./03_VALIDATION_SYSTEM.md)

---

**文檔版本**: v1.0
**創建日期**: 2025-10-10
**補充說明**: 本文檔記錄了所有支持性模塊，補充主文檔中未詳細記錄的部分。
