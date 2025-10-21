# 🛰️ Orbit Engine - LEO衛星動態池研究系統

**學術研究用六階段衛星數據處理系統，支援 Starlink 和 OneWeb 動態衛星池分析與 3GPP NTN 切換優化研究。**

> 📚 **學術研究專用** - 此系統專為學術論文撰寫與研究而設計，符合 NASA JPL、IAU 和 3GPP 學術標準。

---

## ⚠️ 開發者必讀：學術合規性標準

**本專案遵循嚴格的學術研究標準**，確保所有代碼符合同行審查要求。

### 📚 全局標準指南

**📖 [學術合規性標準指南](docs/ACADEMIC_STANDARDS.md)** - 適用所有六個階段

**核心原則**：
- ❌ 禁止：估計值、假設參數、模擬數據、簡化算法
- ✅ 要求：實測數據、學術引用、官方來源、完整實現

### 🔍 需要檢查時

```bash
# 檢查整個專案
make compliance

# 檢查特定階段
python tools/academic_compliance_checker.py src/stages/stage4_link_feasibility/
```

詳見：[學術合規性標準指南](docs/ACADEMIC_STANDARDS.md)

---

## 🎯 研究目標

- **LEO衛星動態池規劃** - 支援時空錯位理論研究
- **3GPP NTN切換優化** - A4/A5/D2事件檢測與強化學習
- **星座感知計算** - Starlink vs OneWeb 軌道週期差異分析
- **學術標準合規** - NASA JPL(<10m)、IAU(<0.5m)、3GPP精度要求

## 🎓 雙模式架構：研究 vs RL 訓練

Orbit Engine 支援兩種輸出模式，滿足不同研究需求：

### 模式 1: 研究數據生成（預設）

**用途**: 完整的六階段學術研究數據

```bash
# 方式 1: 快速執行
./run.sh

# 方式 2: Make 命令
make run

# 方式 3: 容器執行
./run-docker.sh
```

**輸出特性**:
- ✅ 完整信號分析（RSRP/RSRQ/SINR + ITU-R 大氣衰減）
- ✅ 3GPP 事件完整報告（A3/A4/A5/D2）
- ✅ 驗證快照（JSON schema validation）
- ✅ 詳細 metadata（constellation configs, epoch analysis）
- 📊 **輸出位置**: `data/outputs/stage{1..6}/`

### 模式 2: RL 訓練數據生成

**用途**: 精簡的 episode-based 訓練數據

```bash
# 生成 RL 訓練數據
./scripts/generate_rl_training_data.sh

# 或使用環境變數控制
export ORBIT_ENGINE_RL_OUTPUT_DIR=/custom/path
./scripts/generate_rl_training_data.sh
```

**輸出特性**:
- ✅ 精簡狀態-動作對（state-action pairs）
- ✅ Episode 數據結構（適合 RL 算法）
- ✅ 候選衛星池（candidate pools）
- ✅ 換手事件觸發標記（handover triggers）
- 📊 **輸出位置**: `data/outputs/rl_training/stage{1..6}/`
- ⚙️ **配置位置**: `config/rl_training/stage*.yaml`

### 模式差異對比

| 項目 | 研究模式 | RL 訓練模式 |
|------|----------|-------------|
| **輸出目錄** | `data/outputs/` | `data/outputs/rl_training/` |
| **配置文件** | `config/stage*.yaml` | `config/rl_training/stage*.yaml` |
| **執行腳本** | `./run.sh` | `./scripts/generate_rl_training_data.sh` |
| **數據結構** | 完整分析報告 | Episode-based |
| **驗證快照** | ✅ 完整驗證 | ✅ RL 專用驗證 |
| **處理時間** | ~30-40分鐘（9,000+衛星） | ~30-40分鐘（可配置取樣） |
| **適用場景** | 學術論文、詳細分析 | DQN/PPO/SAC 訓練 |

### 配置切換

兩種模式使用獨立配置文件，互不干擾：

```bash
# 研究模式配置
config/
├── stage1_orbital_initialization_config.yaml
├── stage2_orbital_computing_config.yaml
└── ...

# RL 訓練模式配置
config/rl_training/
├── stage1_rl_config.yaml
├── stage2_rl_config.yaml
└── ...
```

詳見：[RL 訓練配置說明](config/rl_training/README.md)

## 🚀 快速開始

### 系統需求
- Python 3.12+ (虛擬環境)
- Docker (可選，容器執行)
- 4GB+ RAM (學術研究用途)
- 2GB+ 可用磁碟空間

### 執行方式（零配置）

#### 方式一：一鍵執行（推薦）
```bash
cd /home/sat/orbit-engine

# 執行全部六階段（自動讀取 .env 配置）
./run.sh

# 執行單一階段
./run.sh --stage 1           # TLE 加載
./run.sh --stage 5           # 信號分析（ITU-Rpy）

# 執行階段範圍
./run.sh --stages 1-3        # 軌道計算流程
./run.sh --stages 4,6        # 換手分析流程
```

#### 方式二：Makefile 命令（最簡潔）
```bash
make help                    # 查看所有命令

# 本地執行
make run                     # 執行全部階段
make run-stage STAGE=5       # 執行階段 5

# 容器執行
make docker                  # 容器執行全部階段
make docker-stage STAGE=5    # 容器執行階段 5
make docker-build            # 重新構建容器

# 測試與狀態
make test                    # 執行測試套件
make test-itur               # ITU-Rpy 驗證測試
make status                  # 查看環境狀態
```

#### 方式三：容器執行
```bash
# 使用快捷腳本
./run-docker.sh              # 執行全部階段
./run-docker.sh --stage 5    # 執行階段 5
./run-docker.sh --build      # 重新構建容器
./run-docker.sh --shell      # 進入容器 shell

# 或使用原生 Docker
docker build -t orbit-engine .
docker run --rm -v $(pwd)/data:/orbit-engine/data orbit-engine
```

**特性**:
- ✅ 自動讀取 `.env` 配置（無需手動 export）
- ✅ 虛擬環境自動啟動
- ✅ 支持階段選擇（單一/範圍/全部）
- ✅ 容器和本地執行統一接口

## 📋 學術研究六階段架構

### 現行系統架構（已實現）
```
🛰️ Stage 1: TLE加載與軌道初始化 (SGP4)
   ↓
🔄 Stage 2: 軌道傳播計算 (95分鐘時間序列)
   ↓
🌐 Stage 3: 坐標轉換 (TEME → ECEF → Geodetic)
   ↓
📡 Stage 4: 鏈路可行性分析 (Pool優化 + 3GPP換手)
   ↓
📶 Stage 5: 信號質量分析 (RSRP/RSRQ + ITU-Rpy大氣衰減) ✨ 新增
   ↓
🔬 Stage 6: 研究優化 (換手優化 + 時序分析)
```

### 六階段詳細說明

#### Stage 1: TLE 加載與軌道初始化
- **輸入**: Space-Track.org TLE 數據
- **處理**: SGP4 軌道模型初始化
- **輸出**: `stage1_orbital_data.json`
- **執行**: `./run.sh --stage 1`

#### Stage 2: 軌道傳播計算
- **輸入**: Stage 1 軌道數據
- **處理**: 95分鐘時間序列軌道計算
- **輸出**: `stage2_propagation.json`
- **執行**: `./run.sh --stage 2`

#### Stage 3: 坐標轉換
- **輸入**: Stage 2 傳播數據
- **處理**: TEME → ECEF → Geodetic 轉換
- **輸出**: `stage3_coordinates.json`
- **執行**: `./run.sh --stage 3`

#### Stage 4: 鏈路可行性分析
- **輸入**: Stage 3 坐標數據
- **處理**: 可見性分析、Pool 優化、3GPP 換手事件
- **輸出**: `stage4_link_analysis.json`
- **執行**: `./run.sh --stage 4`

#### Stage 5: 信號質量分析 ✨
- **輸入**: Stage 4 鏈路數據
- **處理**:
  - RSRP/RSRQ/SINR 計算
  - **ITU-Rpy 官方大氣衰減模型** (ITU-R P.676-13)
  - 都卜勒頻移分析
- **輸出**: `stage5_signal.json`
- **執行**: `./run.sh --stage 5`
- **學術優勢**:
  - ✅ ITU-R 官方認可實現
  - ✅ 維護成本降低 90%
  - ✅ 代碼量減少 97%
  - ✅ 自動同步標準更新

#### Stage 6: 研究優化
- **輸入**: Stage 5 信號數據
- **處理**: 換手優化、3GPP 事件分析、時序研究
- **輸出**: `stage6_research.json`
- **執行**: `./run.sh --stage 6`

## ✨ 最新更新（2025-10-03）

### ITU-Rpy 官方套件整合
- **階段**: Stage 5 信號質量分析
- **改進**: 替換自實現大氣衰減模型為 ITU-R 官方認可的 ITU-Rpy 套件
- **效益**:
  - 修正自實現版本計算錯誤（~50倍誤差）
  - 代碼量減少 97% (385行 → 10行)
  - 維護成本降低 90%
  - 學術可信度顯著提升
- **文檔**: [ITU-Rpy 整合報告](docs/ITU_RPY_INTEGRATION_SUMMARY.md)

### 零配置執行環境
- **新增**: 自動讀取 `.env` 配置（無需手動 export）
- **新增**: 一鍵執行腳本 `./run.sh` 和 `./run-docker.sh`
- **新增**: Makefile 快捷命令 (`make run`, `make docker`)
- **新增**: 虛擬環境自動管理
- **文檔**: [快速啟動指南](docs/QUICK_START.md)

## 📁 專案結構

```
orbit-engine/
├── 🚀 執行腳本（新增）
│   ├── run.sh                              # 本地一鍵執行
│   ├── run-docker.sh                       # 容器一鍵執行
│   ├── Makefile                            # Make 快捷命令
│   └── .env                                # 環境配置（自動讀取）
│
├── 🐍 Python 環境
│   ├── venv/                               # Python 3.12 虛擬環境
│   ├── requirements.txt                    # 依賴清單（含 itur>=0.4.0）
│   └── Dockerfile                          # 容器配置
│
├── 📜 執行腳本
│   └── scripts/
│       └── run_six_stages_with_validation.py  # 六階段執行腳本
│
├── 💻 核心代碼
│   └── src/
│       ├── stages/                         # 六階段處理器
│       │   ├── stage1_orbital_calculation/
│       │   ├── stage2_orbital_computing/
│       │   ├── stage3_coordinate_transformation/
│       │   ├── stage4_link_feasibility/    # Pool 優化 + 換手分析
│       │   ├── stage5_signal_analysis/     # ✨ ITU-Rpy 整合
│       │   │   ├── itur_official_atmospheric_model.py  # ITU-Rpy 封裝
│       │   │   └── deprecated/             # 已棄用的自實現版本
│       │   └── stage6_research_optimization/
│       └── shared/                         # 共享組件
│
├── 📊 數據與輸出
│   └── data/
│       ├── outputs/                        # 各階段輸出
│       │   ├── stage1/                    # TLE 數據
│       │   ├── stage2/                    # 軌道傳播
│       │   ├── stage3/                    # 坐標轉換
│       │   ├── stage4/                    # 鏈路分析
│       │   ├── stage5/                    # 信號質量
│       │   └── stage6/                    # 研究優化
│       ├── validation_snapshots/           # 驗證快照
│       └── tle_data/                      # TLE 原始數據
│
├── 📚 文檔
│   └── docs/
│       ├── QUICK_START.md                 # 🆕 快速啟動指南
│       ├── ITU_RPY_INTEGRATION_SUMMARY.md # 🆕 ITU-Rpy 整合報告
│       ├── final.md                       # 研究目標規格
│       ├── ACADEMIC_STANDARDS.md          # 學術標準指南
│       └── stages/                        # 各階段詳細文檔
│
└── 🧪 測試
    └── tests/
        ├── test_itur_official_validation.py  # 🆕 ITU-Rpy 驗證測試
        └── ...
```

## 🎓 學術標準合規

### 已實現標準
- **ITU-R P.676-13**: 大氣衰減模型（官方 ITU-Rpy 套件）✅
- **3GPP TS 38.300**: NTN 換手事件檢測 (A4/A5/D2) ✅
- **SGP4**: 軌道傳播精度驗證 ✅
- **逐時驗證**: 時間序列覆蓋率分析 ✅

### 學術引用
- **ITU-Rpy**: del Portillo, Í. (2024). ITU-Rpy: Python implementation of ITU-R Recommendations
- **SGP4**: Vallado, D. A., et al. (2006). Revisiting Spacetrack Report #3
- **3GPP NTN**: 3GPP TS 38.300 (Release 17), Non-Terrestrial Networks

## 🎨 視覺化功能 (學術展示用)

### 前端衛星池展示
- `visualization_demo.py` - 動態池概念視覺化
- `satellite_3d_demo.html` - 3D衛星軌道展示
- `satellite_dashboard_demo.html` - 學術儀表板

### 研究數據視覺化
- Starlink vs OneWeb 軌道週期對比
- 時空錯位理論視覺化展示
- 3GPP切換事件分析圖表
- RL訓練過程視覺化

## ⚙️ 開發設置

### 環境配置（零配置）
```bash
# 1. 克隆專案
git clone <repository>
cd orbit-engine

# 2. 直接執行（自動設置虛擬環境和配置）
./run.sh

# 或使用 Make 命令
make run

# 查看環境狀態
make status
```

### 配置文件說明
- **`.env`**: 環境變數配置（自動讀取，無需 export）
  ```bash
  ORBIT_ENGINE_TEST_MODE=1        # 測試模式（50衛星）
  ORBIT_ENGINE_SAMPLING_MODE=0    # 取樣模式
  PYTHONUNBUFFERED=1              # 即時輸出
  ```

- **`requirements.txt`**: Python 依賴（含 ITU-Rpy）
- **`Makefile`**: 快捷命令定義

### 開發流程
1. **修改代碼**: 編輯 `src/stages/` 中的處理器
2. **本地測試**: `./run.sh --stage <N>` 或 `make run-stage STAGE=<N>`
3. **容器驗證**: `./run-docker.sh --stage <N>` 或 `make docker-stage STAGE=<N>`
4. **執行測試**: `make test` 或 `make test-itur`

## 📊 學術研究指標

### 精度目標 (學術標準)
- **軌道精度**: <10m (NASA JPL要求)
- **座標轉換**: <0.5m (IAU標準)
- **時間處理**: 微秒級精度
- **覆蓋連續性**: >95% (動態池要求)

### 系統性能 (研究用途)
- **處理時間**: <60秒 (學術研究可接受)
- **記憶體使用**: <4GB (研究環境)
- **衛星支援**: Starlink(10-15顆) + OneWeb(3-6顆)
- **研究數據**: 支援論文撰寫與分析

### 星座差異分析
| 指標 | Starlink | OneWeb |
|------|----------|--------|
| 軌道週期 | 90-95分鐘 | 109-115分鐘 |
| 可見衛星 | 10-15顆 | 3-6顆 |
| 仰角閾值 | 5° | 10° |
| 研究重點 | 高密度切換 | 長期連接 |

## 🎯 快速開始指南

### 立即執行
```bash
cd /home/sat/orbit-engine

# 方式 1: 一鍵執行（最簡單）
./run.sh                    # 執行全部階段
./run.sh --stage 5          # 執行 Stage 5（驗證 ITU-Rpy）

# 方式 2: Makefile（最簡潔）
make help                   # 查看所有命令
make run                    # 執行全部階段
make docker-stage STAGE=5   # 容器執行 Stage 5

# 方式 3: 容器執行
./run-docker.sh             # 容器執行全部階段
./run-docker.sh --stage 5   # 容器執行 Stage 5
```

### 測試與驗證
```bash
# 執行 ITU-Rpy 驗證測試
make test-itur

# 執行完整測試套件
make test

# 查看環境狀態
make status

# 清理輸出
make clean
```

### 文檔導航
- 📚 [快速啟動指南](docs/QUICK_START.md) - 詳細執行說明
- 📡 [ITU-Rpy 整合報告](docs/ITU_RPY_INTEGRATION_SUMMARY.md) - 技術細節
- 🎯 [研究目標規格](docs/final.md) - 專案需求
- 📊 [Stage 5 信號分析](docs/stages/stage5-signal-analysis.md) - 階段文檔

---

**專案狀態**: 生產就緒 ✅
**版本**: v2.0 (ITU-Rpy 整合版)
**更新日期**: 2025-10-03
**核心特性**: 零配置執行 + ITU-R 官方套件 + 階段選擇控制