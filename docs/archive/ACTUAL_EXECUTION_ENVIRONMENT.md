# 實際執行環境診斷報告

**診斷日期**: 2025-10-02
**目的**: 搞清楚 run_six_stages_with_validation.py 實際是怎麼執行的

---

## ✅ 診斷結果總結

### 您的實際執行方式

```bash
# 就這麼簡單！
cd /home/sat/orbit-engine
python scripts/run_six_stages_with_validation.py
```

**不需要**:
- ❌ 不需要 `export ORBIT_ENGINE_TEST_MODE=1`（可選）
- ❌ 不需要 `export PYTHONPATH=...`（腳本自己處理）
- ❌ 不需要虛擬環境（直接用系統 Python）
- ❌ 不需要激活任何環境

---

## 📊 環境詳情

### Python 環境
```
實際使用: Python 3.12.3 (/usr/bin/python)
套件位置: /home/sat/.local/lib/python3.12/site-packages/
安裝方式: pip install --user <package>
```

**驗證**:
```bash
$ python --version
Python 3.12.3

$ python -c "import skyfield; print(skyfield.__file__)"
/home/sat/.local/lib/python3.12/site-packages/skyfield/__init__.py
```

### 腳本自動處理路徑

**腳本內建邏輯** (run_six_stages_with_validation.py):
```python
# 腳本自己會設定 Python 路徑！
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
```

**這就是為什麼不需要 export PYTHONPATH！**

### 沒有虛擬環境

```bash
$ ls -la | grep venv
(沒有輸出)

$ echo $VIRTUAL_ENV
(空的)
```

**結論**: 直接使用系統 Python 3.12.3

### 沒有環境變數設定

```bash
$ grep ORBIT_ENGINE ~/.bashrc ~/.profile
(沒有結果)
```

**結論**: 沒有自動設定環境變數

---

## 🔴 問題診斷：為什麼之前安裝 itur 失敗？

### 問題根源

```bash
# 之前執行的命令
$ pip install itur
Successfully installed ... itur-0.4.0

# 但是 pip 指向 Python 3.8！
$ pip --version
pip 25.0.1 from /home/sat/.local/lib/python3.8/site-packages/pip (python 3.8)

# 而實際執行用的是 Python 3.12！
$ python --version
Python 3.12.3
```

**結果**: itur 安裝到 Python 3.8，但腳本用 Python 3.12 → import 失敗！

---

## ✅ 正確的安裝方式

### 方法 1: 使用 python3 -m pip（推薦）

```bash
# 確保安裝到正確的 Python 版本
python3 -m pip install --user itur

# 驗證
python3 -c "import itur; print(f'✅ ITU-Rpy {itur.__version__}')"
```

### 方法 2: 使用 python -m pip

```bash
# python 和 python3 是同一個（3.12.3）
python -m pip install --user itur

# 驗證
python -c "import itur; print(f'✅ ITU-Rpy {itur.__version__}')"
```

### ❌ 錯誤方式

```bash
# 不要這樣做！pip 可能指向錯誤的 Python 版本
pip install itur  # ← 這個安裝到 Python 3.8
```

---

## 🎯 完整執行流程

### 安裝依賴（一次性）

```bash
cd /home/sat/orbit-engine

# 安裝所有依賴（包括 itur）
python3 -m pip install --user -r requirements.txt
python3 -m pip install --user itur

# 驗證
python3 -c "import itur; print('✅ itur 安裝成功')"
python3 -c "import skyfield; print('✅ skyfield OK')"
```

### 日常執行

```bash
cd /home/sat/orbit-engine

# 方式 1: 完整六階段
python scripts/run_six_stages_with_validation.py

# 方式 2: 指定階段
python scripts/run_six_stages_with_validation.py --stage 5

# 方式 3: 階段範圍
python scripts/run_six_stages_with_validation.py --stages "1-3"

# 可選：測試模式（使用採樣數據，速度更快）
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py
```

---

## 📋 容器執行（備用）

### 當前容器狀態

```bash
$ docker ps --filter "name=orbit-engine"
orbit-engine-dev - Up 42 hours (unhealthy)
```

### 容器執行方式

```bash
# 在容器內執行
docker exec orbit-engine-dev python /orbit-engine/scripts/run_six_stages_with_validation.py

# 容器內需要先安裝 itur
docker exec orbit-engine-dev pip install itur

# 或者更新 Dockerfile + requirements.txt 後重建
```

---

## 🔍 診斷清單

### ✅ 已確認

- [x] Python 版本: 3.12.3
- [x] 執行方式: 直接 `python scripts/...`
- [x] 不需要虛擬環境
- [x] 不需要 export 環境變數
- [x] 腳本自己處理 sys.path
- [x] 依賴安裝位置: ~/.local/lib/python3.12/

### ❌ 問題根源

- [x] pip 指向 Python 3.8
- [x] itur 安裝到錯誤的 Python 版本
- [x] 需要用 `python3 -m pip` 而非 `pip`

---

## 🚀 立即執行的正確命令

```bash
# 1. 安裝 itur 到正確的 Python 版本
python3 -m pip install --user itur

# 2. 驗證安裝
python3 -c "import itur; print(f'✅ ITU-Rpy {itur.__version__} 已安裝')"

# 3. 執行腳本
python scripts/run_six_stages_with_validation.py --stage 5

# 完成！
```

---

## 📝 常見問題

### Q1: 為什麼 README 說要 export ORBIT_ENGINE_TEST_MODE=1？

**A**: 這是**可選的**測試模式：
- 設定後：使用採樣數據（10 顆衛星），速度快
- 不設定：使用完整數據（9041 顆衛星），完整驗證

```bash
# 測試模式（快速）
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py

# 正式模式（完整）
python scripts/run_six_stages_with_validation.py
```

### Q2: 需要設定 PYTHONPATH 嗎？

**A**: **不需要**！腳本自己會處理：
```python
# 腳本內建
sys.path.insert(0, str(project_root / 'src'))
```

### Q3: 要用虛擬環境嗎？

**A**: **不需要**！您已經用系統 Python 3.12.3 且運行正常。
- 虛擬環境的好處：隔離依賴
- 您的情況：系統 Python 用戶安裝 (--user) 已經夠用

### Q4: 容器執行和本地執行哪個好？

**A**: 看您的需求：
- **本地執行**：速度快，方便調試（您目前在用）
- **容器執行**：環境一致，適合生產部署

---

## 🎯 總結

### 您的實際環境（非常簡單）

```
工作目錄: /home/sat/orbit-engine
Python: 3.12.3 (系統)
依賴安裝: pip install --user (用戶目錄)
執行方式: python scripts/run_six_stages_with_validation.py
環境變數: 不需要！
```

### ITU-Rpy 安裝（一行搞定）

```bash
python3 -m pip install --user itur
```

### 為什麼之前混亂？

1. ❌ `pip` 指向 Python 3.8（錯的）
2. ✅ `python3` 是 Python 3.12（對的）
3. 🔧 解決方案：用 `python3 -m pip` 而不是 `pip`

---

*診斷完成，環境已清楚*
*下一步：正確安裝 itur 並繼續優化*
