# 🚀 Orbit Engine 快速啟動指南

**更新日期**: 2025-10-03  
**版本**: 零配置執行版

---

## 📋 目錄
- [最簡單的執行方式](#最簡單的執行方式)
- [三種執行方式](#三種執行方式)
- [環境配置說明](#環境配置說明)
- [常見問題](#常見問題)

---

## 🎯 最簡單的執行方式

### 方式一：一鍵執行（推薦）

```bash
cd /home/sat/orbit-engine

# 執行全部六階段
./run.sh

# 執行單一階段
./run.sh --stage 1          # 只執行階段 1
./run.sh --stage 5          # 只執行階段 5（信號分析）

# 執行階段範圍
./run.sh --stages 1-3       # 執行階段 1 到 3
./run.sh --stages 1,3,5     # 執行階段 1, 3, 5

# 顯示幫助
./run.sh --help
```

**就這麼簡單！** 腳本會自動：
- ✅ 啟動虛擬環境
- ✅ 加載 `.env` 配置
- ✅ 執行指定階段
- ✅ 顯示執行狀態

### 方式二：手動執行

```bash
cd /home/sat/orbit-engine
source venv/bin/activate

# 執行全部階段
python scripts/run_six_stages_with_validation.py

# 執行單一階段
python scripts/run_six_stages_with_validation.py --stage 1

# 執行階段範圍
python scripts/run_six_stages_with_validation.py --stages 1-3
python scripts/run_six_stages_with_validation.py --stages 1,3,5
```

**無需 export！** 腳本會自動從 `.env` 讀取配置。

### 方式三：Docker 容器執行

```bash
# 方式 3A: 使用快捷腳本（推薦）
./run-docker.sh                    # 執行全部六階段
./run-docker.sh --stage 5          # 只執行階段 5
./run-docker.sh --stages 1-3       # 執行階段 1-3
./run-docker.sh --build            # 重新構建容器
./run-docker.sh --shell            # 進入容器 shell

# 方式 3B: 使用 Makefile（最簡潔）
make docker                        # 執行全部六階段
make docker-stage STAGE=5          # 只執行階段 5
make docker-stages STAGES=1-3      # 執行階段 1-3
make docker-build                  # 重新構建容器
make docker-shell                  # 進入容器 shell

# 方式 3C: 原生 Docker 命令
docker build -t orbit-engine .
docker run --rm -v $(pwd)/data:/orbit-engine/data orbit-engine
docker run --rm orbit-engine python scripts/run_six_stages_with_validation.py --stage 5
```

**容器特性**:
- ✅ 自動讀取 `.env` 配置（本地 `.env` 會覆蓋容器內建）
- ✅ 數據持久化（`data/` 目錄掛載）
- ✅ 環境隔離（不影響主機）

---

## 🔧 執行方式完整對比

| 方式 | 快捷命令 | 原生命令 | 優點 | 適用場景 |
|------|---------|---------|------|---------|
| **本地一鍵** | `./run.sh --stage 5` | - | 全自動，最簡單 | 日常開發 |
| **本地手動** | - | `source venv/bin/activate && python ...` | 靈活控制 | 調試/開發 |
| **容器腳本** | `./run-docker.sh --stage 5` | - | 自動化容器執行 | 快速驗證 |
| **Makefile** | `make docker-stage STAGE=5` | - | 最簡潔 | 標準化流程 |
| **原生 Docker** | - | `docker run orbit-engine ...` | 完全控制 | 生產/CI/CD |

---

## 📊 階段選擇說明

### 六階段功能概覽

| 階段 | 名稱 | 功能 | 輸出 | 執行時間 |
|------|------|------|------|---------|
| **1** | TLE 加載與軌道初始化 | 載入衛星 TLE 數據，初始化 SGP4 | `stage1_orbital_data.json` | ~5秒 |
| **2** | 軌道傳播計算 | 95分鐘時間序列軌道計算 | `stage2_propagation.json` | ~30秒 |
| **3** | 坐標轉換 | TEME → ECEF → Geodetic | `stage3_coordinates.json` | ~15秒 |
| **4** | 鏈路可行性分析 | 可見性、Pool 優化、換手分析 | `stage4_link_analysis.json` | ~45秒 |
| **5** | 信號質量分析 | RSRP/RSRQ/SINR、大氣衰減 | `stage5_signal.json` | ~20秒 |
| **6** | 研究優化 | 換手優化、3GPP 事件分析 | `stage6_research.json` | ~10秒 |

### 常用執行場景

**場景 1: 完整流程**
```bash
./run.sh                    # 執行全部六階段（測試模式 ~2分鐘）
```

**場景 2: 只驗證 ITU-Rpy 大氣衰減（Stage 5）**
```bash
./run.sh --stage 5          # 只執行信號分析階段
```

**場景 3: 軌道計算部分（Stage 1-2）**
```bash
./run.sh --stages 1-2       # TLE 加載 + 軌道傳播
```

**場景 4: 換手分析流程（Stage 4,6）**
```bash
./run.sh --stages 4,6       # 鏈路分析 + 換手優化
```

**場景 5: 調試特定階段**
```bash
# 只執行 Stage 4（需要 Stage 1-3 的輸出已存在）
./run.sh --stage 4
```

---

## ⚙️ 環境配置說明

### .env 文件配置

專案根目錄的 `.env` 文件會被自動讀取：

```bash
# /home/sat/orbit-engine/.env

# 🧪 執行模式
ORBIT_ENGINE_TEST_MODE=1        # 1=測試模式(50衛星), 0=完整模式(9039衛星)

# 📊 取樣模式
ORBIT_ENGINE_SAMPLING_MODE=0    # 0=關閉, 1=啟用

# 🖥️ Python 輸出
PYTHONUNBUFFERED=1              # 1=即時輸出日誌
```

### 修改配置

**要處理全部衛星？** 編輯 `.env`：

```bash
# 改為完整模式
ORBIT_ENGINE_TEST_MODE=0
```

**要更快速測試？** 保持預設：

```bash
# 測試模式（約1-2分鐘）
ORBIT_ENGINE_TEST_MODE=1
```

---

## 📊 執行模式對比

| 模式 | 衛星數量 | 處理時間 | 配置 |
|------|---------|---------|------|
| **測試模式** | 50 顆 | ~1-2 分鐘 | `ORBIT_ENGINE_TEST_MODE=1` |
| **完整模式** | 9039 顆 | ~15-20 分鐘 | `ORBIT_ENGINE_TEST_MODE=0` |

---

## 🔍 常見問題

### Q1: 還需要手動 export 環境變數嗎？

**A:** ❌ 不需要！腳本會自動從 `.env` 讀取。

**舊方式（不再需要）**:
```bash
export ORBIT_ENGINE_TEST_MODE=1  # ❌ 不用了
export ORBIT_ENGINE_SAMPLING_MODE=0  # ❌ 不用了
```

**新方式（自動）**:
```bash
./run.sh  # ✅ 自動讀取 .env
```

### Q2: Docker 容器如何讀取配置？

**A:** 容器啟動時自動讀取內建的 `.env` 文件。

如需覆蓋配置：
```bash
docker run -e ORBIT_ENGINE_TEST_MODE=0 orbit-engine  # 完整模式
```

### Q3: 虛擬環境在哪裡？

**A:** 專案根目錄的 `venv/`：

```bash
/home/sat/orbit-engine/
├── venv/              # Python 3.12 虛擬環境
├── .env               # 環境配置（自動讀取）
├── run.sh             # 一鍵啟動腳本
├── scripts/
│   └── run_six_stages_with_validation.py
└── ...
```

### Q4: 如何驗證配置已加載？

**A:** 執行時會顯示配置資訊：

```
✅ 已自動加載環境配置: /home/sat/orbit-engine/.env
   ORBIT_ENGINE_TEST_MODE = 1
```

### Q5: 如何切換測試/完整模式？

**A:** 編輯 `.env` 文件，修改 `ORBIT_ENGINE_TEST_MODE` 即可：

```bash
# 測試模式（50衛星）
vim .env  # 改為 ORBIT_ENGINE_TEST_MODE=1

# 完整模式（9039衛星）
vim .env  # 改為 ORBIT_ENGINE_TEST_MODE=0
```

---

## 🚀 典型工作流程

### 開發/測試

```bash
cd /home/sat/orbit-engine

# 確保 .env 為測試模式
grep TEST_MODE .env
# 應顯示: ORBIT_ENGINE_TEST_MODE=1

# 一鍵執行
./run.sh
```

### 完整處理

```bash
cd /home/sat/orbit-engine

# 修改為完整模式
sed -i 's/TEST_MODE=1/TEST_MODE=0/' .env

# 執行
./run.sh

# 恢復測試模式
sed -i 's/TEST_MODE=0/TEST_MODE=1/' .env
```

### CI/CD 流程

```bash
# 容器構建
docker build -t orbit-engine .

# 測試模式（快速驗證）
docker run -e ORBIT_ENGINE_TEST_MODE=1 orbit-engine

# 完整模式（正式處理）
docker run -e ORBIT_ENGINE_TEST_MODE=0 orbit-engine
```

---

## 📚 相關文檔

- [ITU-Rpy 整合報告](ITU_RPY_INTEGRATION_SUMMARY.md)
- [Stage 5 信號分析](stages/stage5-signal-analysis.md)
- [Final 需求規格](final.md)

---

## ✅ 檢查清單

執行前確認：

- [ ] 虛擬環境已建立（`venv/` 存在）
- [ ] `.env` 文件已配置
- [ ] ITU-Rpy 已安裝（`venv/bin/python -c "import itur"`）
- [ ] TLE 數據已準備（`data/tle_data/` 有數據）

**全部 OK？直接執行 `./run.sh` 即可！** 🚀

---

**更新日期**: 2025-10-03  
**維護者**: Orbit Engine Project
