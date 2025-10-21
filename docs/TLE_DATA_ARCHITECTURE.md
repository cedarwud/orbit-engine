# TLE Data Architecture - Three Independent Repositories

## 📁 Repository Structure

```
parent_directory/              ← Can be renamed (e.g., satellite → ntn-system)
├─ orbit-engine/               ← Git repo 1 (前端渲染專案)
│  ├─ .git/
│  ├─ .env                     ← SATELLITE_TLE_DATA_DIR=../tle_data
│  ├─ .env.example             ← Template (committed to Git)
│  └─ config/
│     └─ stage1_tle_loader_config.yaml
│
├─ handover-rl/                ← Git repo 2 (RL 訓練專案)
│  ├─ .git/
│  ├─ .env                     ← SATELLITE_TLE_DATA_DIR=../tle_data
│  ├─ .env.example             ← Template (committed to Git)
│  └─ config/
│     └─ data_gen_config.yaml
│
└─ tle_data/                   ← Git repo 3 (共享 TLE 數據)
   ├─ .git/
   ├─ starlink/tle/
   │  ├─ starlink_20251018.tle
   │  ├─ starlink_20251019.tle
   │  └─ ... (每日更新)
   ├─ oneweb/tle/
   │  └─ oneweb_*.tle
   ├─ scripts/
   │  └─ update_tle.sh         ← TLE 自動更新腳本
   └─ logs/
      └─ tle_download_*.log
```

## 🎯 設計原則

### 1. 三個獨立的 Git 倉庫
- ✅ 每個倉庫有自己的版本控制
- ✅ 可以獨立開發、測試、部署
- ✅ 不需要 Git submodules（避免複雜性）

### 2. 只使用相對路徑
- ✅ **orbit-engine** 訪問 tle_data: `../tle_data`
- ✅ **handover-rl** 訪問 tle_data: `../tle_data`
- ✅ **父目錄名稱可以改變**（satellite → ntn-system → 任何名稱）
- ✅ **父目錄位置可以改變**（/home/sat/ → /opt/ → /mnt/data/）
- ✅ **跨系統可移植**（開發機 → 伺服器 → Docker）

### 3. 環境變量配置
```bash
# .env 文件（本地配置，不提交到 Git）
SATELLITE_TLE_DATA_DIR=../tle_data

# .env.example 文件（模板，提交到 Git）
SATELLITE_TLE_DATA_DIR=../tle_data
```

## 🚀 新成員設置步驟

### Step 1: Clone 三個倉庫

```bash
# 創建父目錄（名稱任意）
mkdir -p ~/my-satellite-project
cd ~/my-satellite-project

# Clone 三個倉庫（放在同一層）
git clone https://github.com/your-org/orbit-engine.git
git clone https://github.com/your-org/handover-rl.git
git clone https://github.com/your-org/tle_data.git

# 目錄結構檢查
ls -la
# 應該看到：
# drwxr-xr-x  orbit-engine/
# drwxr-xr-x  handover-rl/
# drwxr-xr-x  tle_data/
```

### Step 2: 配置環境變量

```bash
# orbit-engine 配置
cd orbit-engine
cp .env.example .env
# 檢查 .env 內容（應該是 SATELLITE_TLE_DATA_DIR=../tle_data）
cat .env

# handover-rl 配置
cd ../handover-rl
cp .env.example .env
cat .env
```

### Step 3: 驗證 TLE 數據訪問

```bash
# 測試 orbit-engine
cd ~/my-satellite-project/orbit-engine
python3 -c "
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
tle_dir = os.getenv('SATELLITE_TLE_DATA_DIR', '../tle_data')
tle_path = Path(tle_dir)
if not tle_path.is_absolute():
    tle_path = Path.cwd() / tle_path

print(f'TLE directory: {tle_path}')
print(f'Exists: {tle_path.exists()}')

if tle_path.exists():
    starlink_files = list((tle_path / 'starlink/tle').glob('*.tle'))
    print(f'Starlink TLE files: {len(starlink_files)}')
"

# 測試 handover-rl
cd ~/my-satellite-project/handover-rl
# 同樣的測試腳本
```

## 📊 TLE 數據自動更新

### Cron Job 配置

```bash
# TLE 每 6 小時自動更新（2:00, 8:00, 14:00, 20:00）
0 2,8,14,20 * * * /path/to/your/parent/tle_data/scripts/update_tle.sh
```

**重要**：
- Crontab 必須使用**絕對路徑**（因為 cron 沒有當前工作目錄）
- 但 `update_tle.sh` 腳本內部使用**相對路徑**
- 如果移動父目錄，只需更新 crontab 行

### 手動更新 TLE

```bash
cd ~/my-satellite-project/tle_data/scripts
./update_tle.sh

# 查看日誌
tail -f ../logs/tle_download_*.log
```

## 🔄 移動或重命名父目錄

### 完全可以！設計就是為此

```bash
# 原來的路徑
/home/sat/satellite/
├─ orbit-engine/
├─ handover-rl/
└─ tle_data/

# 移動到新位置
mv /home/sat/satellite /opt/ntn-system

# 新路徑
/opt/ntn-system/
├─ orbit-engine/    ← 仍然使用 ../tle_data（相對路徑，自動適應）
├─ handover-rl/     ← 仍然使用 ../tle_data
└─ tle_data/

# 唯一需要更新：crontab 中的絕對路徑
crontab -e
# 修改：
# 0 2,8,14,20 * * * /opt/ntn-system/tle_data/scripts/update_tle.sh
```

## 🐳 Docker 部署

### Dockerfile 示例

```dockerfile
FROM python:3.10

# 創建工作目錄
WORKDIR /app

# 複製三個倉庫（保持相對位置）
COPY orbit-engine/ /app/orbit-engine/
COPY handover-rl/ /app/handover-rl/
COPY tle_data/ /app/tle_data/

# 設置環境變量（相對路徑自動工作）
WORKDIR /app/orbit-engine
RUN cp .env.example .env

# 運行
CMD ["./run.sh"]
```

## 📝 .gitignore 配置

### orbit-engine/.gitignore
```
.env          ← 不要提交本地配置
*.log
data/outputs/
```

### handover-rl/.gitignore
```
.env          ← 不要提交本地配置
*.log
data/episodes/
results/
```

### tle_data/.gitignore
```
logs/         ← 日誌不提交
*.log
```

## ⚠️ 常見問題

### Q1: 為什麼不使用絕對路徑？
**A**: 絕對路徑會綁定特定系統路徑，無法跨系統移植：
```bash
# ❌ 不好：
SATELLITE_TLE_DATA_DIR=/home/sat/satellite/tle_data
# 如果移到另一台機器（/opt/），路徑會失效

# ✅ 好：
SATELLITE_TLE_DATA_DIR=../tle_data
# 在任何系統、任何位置都能工作
```

### Q2: 為什麼不使用 Git Submodules？
**A**: Submodules 增加複雜性：
- 需要 `git clone --recurse-submodules`
- 需要 `git submodule update`
- 容易出現版本不一致
- TLE 每天更新，Git 倉庫會快速膨脹

三個獨立倉庫更簡單、更靈活。

### Q3: 如何在不同機器之間同步？
**A**:
```bash
# 機器 A（開發機）
cd ~/satellite/tle_data
git add .
git commit -m "Update TLE data"
git push

# 機器 B（伺服器）
cd ~/production/tle_data
git pull
```

### Q4: 如何測試新的 TLE 數據？
**A**:
```bash
# 在 tle_data 倉庫創建測試分支
cd tle_data
git checkout -b test-new-tle
# 下載新 TLE 或修改
git commit -am "Test new TLE data"

# orbit-engine 和 handover-rl 不需要改動
# 自動使用 tle_data 的當前分支數據
```

## 📚 技術細節

### 環境變量解析邏輯

```python
# Python 配置加載器
import os
from pathlib import Path
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

# 獲取 TLE 目錄（默認相對路徑）
tle_dir = os.getenv('SATELLITE_TLE_DATA_DIR', '../tle_data')
tle_path = Path(tle_dir)

# 如果是相對路徑，相對於當前工作目錄
if not tle_path.is_absolute():
    tle_path = Path.cwd() / tle_path

# 現在 tle_path 是絕對路徑，可以安全使用
print(f"TLE directory: {tle_path}")
```

### Bash 腳本相對路徑導航

```bash
#!/bin/bash
# update_tle.sh

# 獲取腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 獲取 tle_data 根目錄（腳本在 scripts/ 子目錄）
TLE_DIR="$(dirname "$SCRIPT_DIR")"

# 現在可以安全使用 TLE_DIR
echo "TLE directory: $TLE_DIR"
ls "$TLE_DIR/starlink/tle"
```

## 🎓 總結

這個架構的核心優勢：
1. ✅ **可移植性**：父目錄可以任意移動、重命名
2. ✅ **獨立性**：三個倉庫各自維護，互不干擾
3. ✅ **簡單性**：不需要 submodules，不需要複雜配置
4. ✅ **靈活性**：可以單獨更新、測試、部署任一倉庫

**關鍵原則**：
- 🚫 絕不使用絕對路徑（除了 crontab 必須要）
- ✅ 始終使用相對路徑 `../tle_data`
- ✅ 三個倉庫放在同一層（sibling directories）
- ✅ 環境變量 + .env 文件管理配置

---

**文檔版本**: 1.0
**更新日期**: 2025-10-20
**維護者**: Claude Code
