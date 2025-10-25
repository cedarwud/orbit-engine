# orbit-engine 環境遷移檢查清單

**檢查日期**: 2025-10-25
**目的**: 確保 orbit-engine 可在新環境中正常運行
**狀態**: ✅ 已驗證完成

---

## 📋 檢查摘要

| 項目 | 狀態 | 說明 |
|------|------|------|
| **Git 追蹤狀況** | ✅ 完整 | 所有重要檔案已追蹤，執行產生的數據已忽略 |
| **.gitignore 配置** | ✅ 完整 | 已涵蓋所有數據檔案、模型、快取 |
| **requirements.txt** | ✅ 齊全 | 僅包含 orbit-engine 必要套件，已移除 RL 相關 |
| **.env.example** | ✅ 存在 | 提供清晰的環境配置範例 |
| **README.md** | ✅ 完整 | 包含安裝和執行指引 |
| **職責劃分** | ✅ 明確 | orbit-engine = 數據生成 |

---

## 1️⃣ Git 追蹤狀況 ✅

### 已追蹤的重要檔案

```
✅ src/                        # 所有源代碼
✅ scripts/                    # 執行器和驗證器
✅ tools/                      # 開發工具
  ✅ ml_training_data_generator/  # HDF5 數據生成器
  ✅ archive/                      # 歸檔的舊代碼（保留歷史）
✅ config/                     # 所有配置檔案
✅ docs/                       # 所有文檔
✅ .env.example               # 環境配置範例
✅ requirements.txt           # Python 依賴
✅ Dockerfile                 # Docker 配置
✅ run.sh                     # 執行腳本
✅ Makefile                   # Make 命令
✅ README.md                  # 專案說明
```

### 已忽略的數據檔案（可重新生成）

```
❌ data/outputs/              # Stage 1-6 輸出（執行生成）
❌ data/ml_training/*.h5      # HDF5 訓練數據（執行生成）
❌ data/cache/                # 快取檔案（自動生成）
❌ data/validation_snapshots/ # 驗證快照（執行生成）
❌ data/models/               # 模型檔案（不應存在於 orbit-engine）
❌ data/evaluation_reports/   # 評估報告（不應存在於 orbit-engine）
❌ venv/                      # 虛擬環境（pip install 重建）
```

---

## 2️⃣ .gitignore 配置 ✅

### 核心忽略項目

```gitignore
# 🐍 Python 環境
venv/
.venv/
__pycache__/
*.pyc

# 🔐 敏感配置
.env
*.env

# 📊 數據文件（大型，可重新生成）
data/outputs/
data/cache/
data/validation_snapshots/
data/ml_training/*.h5
data/ml_training/*.bak

# 🤖 RL 訓練產物（不應存在，若誤生成則忽略）
data/models/
data/evaluation_reports/

# 📊 星歷數據（自動下載）
data/ephemeris/*.bsp
```

### 保留的目錄結構

```
data/outputs/.gitkeep
data/cache/.gitkeep
data/validation_snapshots/.gitkeep
data/tle_data/.gitkeep
```

---

## 3️⃣ requirements.txt 齊全性 ✅

### 已清理的套件（2025-10-25）

**移除的 RL 相關套件**（屬於 handover-rl）:
```
❌ stable-baselines3>=2.0.0    # RL 訓練
❌ gymnasium>=0.29.0           # RL 環境
❌ torch>=2.0.0                # 深度學習
❌ tensorboard>=2.10.0         # 訓練監控
❌ tabulate>=0.9.0             # 評估報告
```

**移除的 GPU 套件**（orbit-engine 不使用 GPU）:
```
❌ cupy-cuda11x>=11.0.0        # CUDA 11.x
❌ cupy-cuda12x>=12.0.0        # CUDA 12.x
```

### 保留的核心套件

**🚀 核心計算**:
```
numpy>=1.24.0
scipy>=1.10.0
pandas>=2.0.0
```

**🛰️ 天體力學與軌道計算**:
```
skyfield>=1.45                 # SGP4 官方實現
sgp4>=2.20                     # Vallado SGP4/SDP4
astropy>=7.0.0                 # 天文計算標準庫
h5py>=3.9.0                    # HDF5 數據格式
```

**📡 ITU-R 無線電傳播模型**:
```
itur>=0.4.0                    # ITU-R P.676-13 大氣衰減
```

**📊 數據處理**:
```
PyYAML>=6.0
pydantic>=2.0.0
requests>=2.31.0
httpx>=0.25.0
Pillow>=10.0.0
python-dateutil>=2.8.0
pytz>=2023.3
psutil>=5.9.0
tqdm>=4.65.0
```

**🧪 開發與測試**:
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0
pytest-bdd>=7.0.0
pytest-html>=4.0.0
pytest-json-report>=1.5.0
pytest-xdist>=3.1.0
allure-pytest>=2.13.0
```

**📈 日誌與監控**:
```
structlog>=23.1.0
rich>=13.5.0
python-dotenv>=1.0.0
aiohttp>=3.8.0
```

**📊 數值計算增強**:
```
matplotlib>=3.7.0
seaborn>=0.12.0
numba>=0.58.0                  # CPU JIT 編譯加速
```

**🎯 多目標優化**:
```
pymoo>=0.6.1                   # NSGA-II 多目標優化
```

**性能分析工具**:
```
memory-profiler>=0.60.0
line-profiler>=4.0.0
py-spy>=0.3.14
multiprocessing-logging>=0.3.4
```

**數據庫支援（可選）**:
```
psycopg2-binary>=2.9.0
SQLAlchemy>=2.0.0
```

---

## 4️⃣ 環境配置 ✅

### .env.example 範例

```bash
# TLE Data Directory Configuration
# Copy this file to .env and customize for your environment

# Relative path to sibling tle_data directory (RECOMMENDED)
SATELLITE_TLE_DATA_DIR=../tle_data

# Test and Sampling Modes
ORBIT_ENGINE_TEST_MODE=0
ORBIT_ENGINE_SAMPLING_MODE=0
```

### 目錄結構要求

```
parent_directory/
├── orbit-engine/     # orbit-engine 專案
├── handover-rl/      # handover-rl 專案（RL 訓練）
└── tle_data/         # TLE 數據（共享）
```

---

## 5️⃣ README.md 安裝指引 ✅

### 快速開始（已包含在 README.md）

```bash
# 1. 克隆專案
git clone <repository-url>
cd orbit-engine

# 2. 複製環境配置
cp .env.example .env

# 3. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 執行六階段處理
./run.sh
```

### Docker 執行（已包含在 README.md）

```bash
# 方式 1: 使用 run-docker.sh
./run-docker.sh

# 方式 2: 使用 Make
make docker

# 方式 3: 手動構建
docker build -t orbit-engine .
docker run -v $(pwd)/data:/app/data orbit-engine
```

---

## 6️⃣ 職責劃分 ✅

### orbit-engine 職責（數據生成）

```
✅ Stage 1: TLE 數據載入
✅ Stage 2: 軌道傳播（SGP4/Skyfield）
✅ Stage 3: 座標轉換（TEME → WGS84）
✅ Stage 4: 鏈路可行性分析
✅ Stage 5: 信號品質分析（RSRP/RSRQ/SINR + ITU-R）
✅ Stage 6: 換手事件生成（A3/A4/A5/D2）
✅ HDF5 訓練數據生成（77-dim temporal features）
```

**輸出位置**:
- `data/outputs/stage{1..6}/` - 六階段 JSON 輸出
- `data/ml_training/rl_training_dataset_temporal.h5` - HDF5 訓練數據

### handover-rl 職責（RL 訓練）

```
✅ 讀取 orbit-engine 生成的 HDF5 數據
✅ DQN/A3C/PPO/SAC 訓練
✅ 訓練監控（TensorBoard）
✅ 模型評估與測試
```

---

## 7️⃣ 新環境部署步驟 ✅

### 步驟 1: 克隆專案

```bash
# 克隆 orbit-engine
git clone <orbit-engine-repo-url>
cd orbit-engine

# 確認分支
git branch
git log --oneline -5
```

### 步驟 2: 設置環境

```bash
# 複製環境配置
cp .env.example .env

# 編輯 .env（如需修改）
vim .env
```

### 步驟 3: 虛擬環境設置

```bash
# 創建虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 驗證安裝
pip list | grep -E "skyfield|astropy|itur|pymoo"
```

### 步驟 4: 驗證環境

```bash
# 檢查 Python 版本
python --version  # 應該 >= 3.12

# 檢查目錄結構
ls -la data/
ls -la config/
ls -la src/

# 測試導入核心模組
python -c "import skyfield; import astropy; import itur; print('✅ Core modules OK')"
```

### 步驟 5: 執行測試

```bash
# 方式 1: 執行所有六階段
./run.sh

# 方式 2: 執行單一階段（測試）
./run.sh --stage 1

# 方式 3: 使用 Docker
./run-docker.sh
```

### 步驟 6: 驗證輸出

```bash
# 檢查 Stage 1 輸出
ls -lh data/outputs/stage1/

# 檢查 HDF5 數據集
ls -lh data/ml_training/*.h5

# 驗證 JSON 結構
jq . data/outputs/stage1/stage1_*.json | head -50
```

---

## 8️⃣ 常見問題處理 ✅

### 問題 1: pip install 失敗

**症狀**: 某些套件安裝失敗

**解決方法**:
```bash
# 升級 pip
pip install --upgrade pip

# 分批安裝
pip install numpy scipy pandas
pip install skyfield sgp4 astropy
pip install h5py itur pymoo
pip install -r requirements.txt
```

### 問題 2: TLE 數據路徑錯誤

**症狀**: `FileNotFoundError: ../tle_data`

**解決方法**:
```bash
# 確認目錄結構
cd ..
ls -la  # 應該看到 orbit-engine, handover-rl, tle_data

# 修改 .env
cd orbit-engine
vim .env
# 設置: SATELLITE_TLE_DATA_DIR=../tle_data
```

### 問題 3: 缺少 .env 檔案

**症狀**: `Warning: .env file not found`

**解決方法**:
```bash
cp .env.example .env
```

### 問題 4: Docker 構建失敗

**症狀**: Docker build error

**解決方法**:
```bash
# 清理舊容器
docker system prune -a

# 重新構建
docker build --no-cache -t orbit-engine .
```

---

## 9️⃣ 驗證清單 ✅

### Git 驗證

- [x] `git status` 顯示 clean working tree
- [x] 所有重要檔案已追蹤
- [x] 數據檔案已正確忽略
- [x] `.gitignore` 包含所有必要項目

### 環境驗證

- [x] `requirements.txt` 僅包含必要套件
- [x] `.env.example` 存在且完整
- [x] `README.md` 包含安裝指引
- [x] `Dockerfile` 可正常構建

### 功能驗證

- [x] `./run.sh` 可正常執行
- [x] 六階段處理可完整運行
- [x] HDF5 數據生成成功
- [x] Docker 容器可正常運行

### 職責驗證

- [x] orbit-engine 不包含 RL 訓練代碼
- [x] requirements.txt 不包含 torch/gymnasium/stable-baselines3
- [x] 所有 RL 相關檔案已移除或歸檔

---

## 🔟 遷移後驗證步驟

### 在新環境執行以下命令

```bash
# 1. 克隆並設置
git clone <orbit-engine-repo>
cd orbit-engine
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 驗證核心模組
python -c "
import skyfield
import astropy
import itur
import pymoo
import h5py
print('✅ All core modules imported successfully')
"

# 3. 執行單階段測試
./run.sh --stage 1

# 4. 檢查輸出
ls -lh data/outputs/stage1/

# 5. 執行完整流程（可選）
./run.sh
```

### 預期結果

```
✅ Git clone 成功
✅ venv 創建成功
✅ pip install 無錯誤
✅ 核心模組導入成功
✅ Stage 1 執行成功
✅ data/outputs/stage1/ 產生 JSON 檔案
✅ 六階段完整執行（如執行完整流程）
✅ data/ml_training/ 產生 HDF5 檔案
```

---

## 📚 相關文檔

- **README.md** - 專案說明和快速開始
- **CLEANUP_EXECUTION_REPORT_20251025.md** - 清理執行報告
- **ORBIT_ENGINE_AUDIT_REPORT_20251024.md** - 完整審計報告
- **TOOLS_CLEANUP_REPORT_20251024.md** - tools/ 目錄清理報告
- **docs/ACADEMIC_STANDARDS.md** - 學術合規性標準

---

## ✅ 環境遷移準備狀態

| 項目 | 狀態 |
|------|------|
| **Git 追蹤** | ✅ 完整 |
| **.gitignore** | ✅ 完整 |
| **requirements.txt** | ✅ 齊全（已清理 RL 套件） |
| **.env.example** | ✅ 存在 |
| **README.md** | ✅ 完整 |
| **Docker 配置** | ✅ 可用 |
| **職責劃分** | ✅ 明確 |
| **代碼清理** | ✅ 完成（移除 RL 代碼） |
| **環境可重現性** | ✅ 保證 |

---

**遷移準備狀態**: ✅ 完全就緒
**檢查日期**: 2025-10-25
**下一步**: 可以在新環境執行 `git clone` 並按照 README.md 安裝

---

**備註**:
1. 新環境需確保 Python 3.12+ 已安裝
2. 需要 4GB+ RAM 和 2GB+ 磁碟空間
3. Docker 執行需要 Docker Engine 已安裝
4. TLE 數據目錄結構需符合 .env.example 說明
