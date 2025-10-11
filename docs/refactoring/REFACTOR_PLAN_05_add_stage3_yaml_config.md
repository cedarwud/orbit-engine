# 重構計劃 05: Stage 3 配置 YAML 化

**優先級**: 🟠 P1 (重要)
**風險等級**: 🟡 中風險
**預估時間**: 45 分鐘
**狀態**: ⏸️ 待執行
**前置條件**: 完成 Plan 04

---

## 📋 目標

將 Stage 3 的硬編碼配置遷移到 YAML 配置文件。

---

## 🔍 現狀分析

### 當前硬編碼位置

**文件**: `scripts/stage_executors/stage3_executor.py:23-37`

```python
def execute_stage3(previous_results):
    # ❌ 硬編碼配置 (15行)
    stage3_config = {
        'enable_geometric_prefilter': False,  # v3.1: 禁用預篩選
        'coordinate_config': {
            'source_frame': 'TEME',
            'target_frame': 'WGS84',
            'time_corrections': True,
            'polar_motion': True,
            'nutation_model': 'IAU2000A'
        },
        'precision_config': {
            'target_accuracy_m': 0.5  # 亞米級精度
        }
    }
```

---

## 🎯 執行步驟

### Step 1: 備份
```bash
cd /home/sat/orbit-engine
git add .
git commit -m "Backup before refactoring: Add Stage 3 YAML config"
```

### Step 2: 創建配置文件

創建 `config/stage3_coordinate_transformation.yaml`:
```yaml
# Stage 3: 座標系統轉換層配置
# SOURCE: Stage 3 執行器硬編碼參數遷移
# Date: 2025-10-11

# 幾何預篩選配置
geometric_prefilter:
  # 是否啟用幾何預篩選
  # v3.1: 已禁用預篩選，改為完整處理所有衛星
  # SOURCE: 架構優化決策 - 避免過早篩選導致數據丟失
  enabled: false

  # 預篩選參數 (僅在 enabled=true 時生效)
  # min_elevation_deg: 0.0  # 最小仰角 (度)
  # max_distance_km: 2000.0  # 最大距離 (km)

# 座標轉換配置
coordinate_config:
  # 源座標系統
  # SOURCE: Stage 2 輸出為 TEME 座標系統
  source_frame: TEME

  # 目標座標系統
  # SOURCE: WGS84 為標準地理座標系統 (GPS 標準)
  target_frame: WGS84

  # 是否啟用時間修正
  # SOURCE: IAU 標準要求 - UT1-UTC, TAI-UTC 修正
  # NOTE: 精確座標轉換必須考慮時間系統差異
  time_corrections: true

  # 是否啟用極移修正
  # SOURCE: IERS Bulletin A - 地球極移參數
  # NOTE: 極移影響座標轉換精度 (~10米量級)
  polar_motion: true

  # 歲差章動模型
  # OPTIONS:
  #   - IAU2000A: 高精度模型 (亞米級精度)
  #   - IAU2000B: 簡化模型 (米級精度)
  #   - IAU1980: 舊標準 (已棄用)
  # SOURCE: IAU SOFA Standards (2000A 為當前推薦標準)
  nutation_model: IAU2000A

# 精度配置
precision_config:
  # 目標精度 (米)
  # SOURCE: 研究需求 - 亞米級精度 (< 1m)
  # NOTE: 與 GNSS 精度相當 (RTK-GPS: 0.01-0.05m)
  target_accuracy_m: 0.5

  # 迭代收斂門檻 (米)
  # SOURCE: 座標轉換迭代算法收斂條件
  convergence_threshold_m: 0.001

  # 最大迭代次數
  # SOURCE: 防止無窮迴圈，通常 3-5 次即可收斂
  max_iterations: 10

# IERS 數據配置
iers_data:
  # IERS 數據緩存目錄
  cache_directory: data/cache/iers

  # 自動下載 IERS 數據
  # SOURCE: Astropy 自動下載 IERS Bulletin A
  auto_download: true

  # IERS 數據過期警告門檻 (天)
  # NOTE: IERS 數據每週更新，30天以上視為過期
  expiry_warning_days: 30

# 座標系統參考框架
reference_frames:
  # WGS84 橢球參數
  # SOURCE: NIMA TR8350.2 (2000)
  wgs84:
    semi_major_axis_m: 6378137.0       # 長半軸 (a)
    flattening: 0.00335281066474748    # 扁率 (f)
    # 計算值: semi_minor_axis = 6356752.314245 m

  # TEME 座標系統說明
  # SOURCE: NORAD SGP4/SDP4 Technical Report
  teme:
    description: "True Equator Mean Equinox of Epoch"
    note: "SGP4/SDP4 輸出的慣性座標系統，基於 TLE epoch 的真赤道平春分點"

# HDF5 緩存配置
cache_config:
  # 是否啟用 HDF5 緩存
  # PURPOSE: 加速重複執行 (首次 ~25min，緩存後 ~2min)
  enabled: true

  # 緩存目錄
  cache_directory: data/cache/stage3

  # 緩存檔案名稱模式
  filename_pattern: "stage3_cache_{hash}.h5"

  # 緩存過期時間 (小時)
  # NOTE: 如果輸入數據（Stage 2 output）未變化，可使用緩存
  expiry_hours: 24

  # 自動清理舊緩存
  auto_cleanup: true

  # 最大緩存大小 (MB)
  max_cache_size_mb: 500

# 並行處理配置
parallel_config:
  # 最大工作進程數
  # SOURCE: 動態配置基於 CPU 核心數
  # NOTE: 0 表示自動檢測 (使用 95% CPU 核心)
  max_workers: 0

  # 批次大小
  # SOURCE: 平衡內存使用和並行效率
  chunk_size: 100

  # 是否顯示進度條
  show_progress: true

# 輸出配置
output:
  # 輸出目錄
  directory: data/outputs/stage3

  # 檔案名稱模式
  filename_pattern: "stage3_coordinate_transformation_real_{timestamp}.json"

  # 是否保存驗證快照
  save_validation_snapshot: true

  # 輸出格式
  # - json: JSON 格式 (預設)
  # - hdf5: HDF5 格式 (大數據量)
  format: json

# 驗證配置
validation:
  # 座標範圍檢查
  coordinate_range_check: true

  # 座標範圍 (WGS84)
  valid_ranges:
    latitude_deg: [-90, 90]
    longitude_deg: [-180, 180]
    altitude_km: [200, 2000]  # LEO 衛星高度範圍

  # 數據完整性檢查
  data_integrity_check: true

  # 最小數據點數量 (每顆衛星)
  min_data_points: 180

# 性能配置
performance:
  # 內存限制 (MB)
  # NOTE: 處理 9,000 顆衛星約需 4GB 內存
  memory_limit_mb: 8192

  # 日誌等級
  log_level: INFO

  # 性能統計
  enable_profiling: false
```

### Step 3: 修改執行器

編輯 `scripts/stage_executors/stage3_executor.py`:
```python
import yaml
from pathlib import Path
from .executor_utils import project_root

def execute_stage3(previous_results):
    """執行 Stage 3: 座標系統轉換層"""
    try:
        print('\n🌍 階段三：座標系統轉換層')
        print('-' * 60)

        # 檢查前序階段
        if 'stage2' not in previous_results:
            print('❌ 缺少 Stage 2 結果')
            return False, None, None

        # 清理舊的輸出
        clean_stage_outputs(3)

        # ✅ 從 YAML 載入配置
        config_path = project_root / "config/stage3_coordinate_transformation.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                stage3_config = yaml.safe_load(f)
            print(f"✅ 已載入 Stage 3 配置: {config_path}")
        else:
            print(f"⚠️ 未找到配置文件: {config_path}")
            print("⚠️ 使用預設配置")
            stage3_config = {
                'geometric_prefilter': {'enabled': False},
                'coordinate_config': {
                    'source_frame': 'TEME',
                    'target_frame': 'WGS84',
                    'time_corrections': True,
                    'polar_motion': True,
                    'nutation_model': 'IAU2000A'
                },
                'precision_config': {'target_accuracy_m': 0.5}
            }

        # 向後兼容：扁平化配置結構 (適配處理器)
        config_compat = {
            'enable_geometric_prefilter': stage3_config.get('geometric_prefilter', {}).get('enabled', False),
            'coordinate_config': stage3_config.get('coordinate_config', {}),
            'precision_config': stage3_config.get('precision_config', {}),
            'cache_config': stage3_config.get('cache_config', {}),
            'parallel_config': stage3_config.get('parallel_config', {})
        }

        print(f"📋 配置摘要:")
        print(f"   源座標系: {config_compat['coordinate_config']['source_frame']}")
        print(f"   目標座標系: {config_compat['coordinate_config']['target_frame']}")
        print(f"   歲差章動模型: {config_compat['coordinate_config']['nutation_model']}")
        print(f"   目標精度: {config_compat['precision_config']['target_accuracy_m']}m")
        print(f"   幾何預篩選: {'啟用' if config_compat['enable_geometric_prefilter'] else '禁用'}")

        # 創建處理器
        from stages.stage3_coordinate_transformation.stage3_coordinate_transform_processor import Stage3CoordinateTransformProcessor
        stage3 = Stage3CoordinateTransformProcessor(config=config_compat)

        # 提取 Stage 2 數據
        stage2_data = extract_data_from_result(previous_results['stage2'])

        # 執行處理
        stage3_result = stage3.execute(stage2_data)

        # 檢查結果
        if not stage3_result or (hasattr(stage3_result, 'status') and stage3_result.status.value != 'success'):
            error_msg = '; '.join(stage3_result.errors) if hasattr(stage3_result, 'errors') and stage3_result.errors else "無結果"
            print(f'❌ Stage 3 執行失敗: {error_msg}')
            return False, stage3_result, stage3

        return True, stage3_result, stage3

    except Exception as e:
        print(f'❌ Stage 3 執行異常: {e}')
        import traceback
        traceback.print_exc()
        return False, None, None
```

### Step 4-7: 驗證、測試、提交
```bash
# 驗證 YAML
python3 -c "import yaml; yaml.safe_load(open('config/stage3_coordinate_transformation.yaml'))"

# 測試
./run.sh --stage 3
./run.sh --stages 1-3

# 提交
git add config/stage3_coordinate_transformation.yaml
git add scripts/stage_executors/stage3_executor.py
git commit -m "Refactor: Migrate Stage 3 config to YAML

Ref: docs/refactoring/REFACTOR_PLAN_05
"
```

---

## ✅ 驗證檢查清單

- [ ] 配置文件已創建
- [ ] YAML 語法正確
- [ ] Stage 3 測試通過
- [ ] Stage 1-3 完整流程通過
- [ ] Git 提交完成

---

**創建日期**: 2025-10-11
