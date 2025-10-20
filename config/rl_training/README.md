# RL 訓練配置文件

**創建日期**: 2025-10-20
**用途**: 為 handover-rl 強化學習訓練生成專用數據

---

## 📁 配置文件說明

這些配置文件是 orbit-engine 原始配置的**調整版本**，專為 RL 訓練優化：

| 文件 | 主要差異 | 說明 |
|------|---------|------|
| `stage1_rl_config.yaml` | 無變更 | 使用相同的 TLE 加載邏輯 |
| `stage2_rl_config.yaml` | ✅ **`coverage_cycles: 106.1`** | **7天時間範圍**（vs 前端渲染的 94分鐘） |
| `stage3_rl_config.yaml` | 無變更 | 使用相同的坐標轉換 |
| `stage4_rl_config.yaml` | ✅ **池優化目標調整** | **800-1000 衛星池**，**4-6 顆並發可見** |
| `stage5_rl_config.yaml` | 無變更 | 使用相同的信號分析 |
| `stage6_rl_config.yaml` | 無變更 | 使用相同的事件檢測（A3/A4/A5/D2） |

---

## 🎯 關鍵參數差異

### Stage 2: 時間範圍擴展

```yaml
# 前端渲染模式（原始）
coverage_cycles: 1.0  # 94 分鐘（1 軌道週期）→ 220 時間點

# RL 訓練模式（本配置）
coverage_cycles: 106.1  # 7 天（106 軌道週期）→ 20,160 時間點
```

**學術依據**:
- SOURCE: handover-rl 需求 - 7天訓練數據
- 計算: 7天 = 10,080分鐘 / 95分鐘軌道週期 = 106.1 週期
- 時間點: 10,080分鐘 / 30秒間隔 = 20,160 個時間點/衛星

### Stage 4: 池優化目標調整

```yaml
# 前端渲染模式（原始）
starlink:
  expected_visible_satellites: [10, 15]  # 10-15 顆並發可見
  min_pool_size: 10                      # 最小池: 10 衛星
  max_pool_size: 15                      # 最大池: 15 衛星

# RL 訓練模式（本配置）
starlink:
  expected_visible_satellites: [4, 6]    # 4-6 顆並發可見
  min_pool_size: 800                     # 最小池: 800 衛星
  max_pool_size: 1000                    # 最大池: 1000 衛星
```

**學術依據**:
- SOURCE: handover-rl A4/D2 baseline 比較研究需求
- 4-6 顆並發可見: 提供充足的換手機會（≥30% handover rate）
- 800-1000 衛星池: 確保 7 天內持續有換手機會

---

## 📊 預期輸出差異

| 維度 | 前端渲染模式 | RL 訓練模式 |
|------|-------------|------------|
| 衛星數量 | 101 顆 | 800-1000 顆 |
| 時間範圍 | 94 分鐘 | 7 天（10,080 分鐘） |
| 時間點數/衛星 | 220 個 | 20,160 個 |
| 並發可見衛星 | 10-15 顆 | 4-6 顆 |
| Stage 2 輸出大小 | ~50 MB | ~4 GB |
| Stage 4 輸出大小 | ~20 MB | ~1.5 GB |
| Stage 6 輸出大小 | ~4 MB | ~300 MB |
| **總輸出大小** | **~75 MB** | **~6 GB** |

---

## 🚀 使用方式

### 方法 1: 使用環境變數（推薦）

```bash
# 設置 RL 訓練模式
export ORBIT_ENGINE_CONFIG_DIR="/home/sat/satellite/orbit-engine/config/rl_training"
export ORBIT_ENGINE_OUTPUT_DIR="/home/sat/satellite/orbit-engine/data/outputs/rl_training"

# 執行六階段處理
./run.sh --stages 1-6
```

### 方法 2: 使用專用腳本（Phase 2 實施後）

```bash
# 執行 RL 訓練數據生成
./scripts/generate_rl_training_data.sh --stages 1-6
```

---

## ⚙️ 配置驗證

驗證所有配置文件語法正確：

```bash
python3 -c "
import yaml
for i in range(1, 7):
    with open(f'config/rl_training/stage{i}_rl_config.yaml') as f:
        yaml.safe_load(f)
    print(f'✅ Stage {i} 配置正確')
"
```

---

## 🔄 與前端渲染模式的關係

**完全獨立，互不干擾**：

```
orbit-engine/
├── config/                  ← 前端渲染配置（原始，不變）
│   ├── stage1_*.yaml
│   └── ...
│
├── config/rl_training/      ← RL 訓練配置（本目錄）
│   ├── stage1_rl_config.yaml
│   └── ...
│
├── data/outputs/            ← 前端渲染輸出（101 衛星，94 分鐘）
│   └── stage6/
│
└── data/outputs/rl_training/ ← RL 訓練輸出（800 衛星，7 天）
    └── stage6/
```

**優勢**:
- ✅ 修改 RL 配置不影響前端渲染
- ✅ 兩種輸出可以並存
- ✅ 配置清晰，易於維護

---

## 📚 學術合規性

所有參數調整都有明確的學術依據：

- **7天時間範圍**: handover-rl 需求規格（充足的訓練數據）
- **4-6 顆並發可見**: Yu et al. 2022 - LEO NTN handover 需求
- **800-1000 衛星池**: 確保 ≥30% handover opportunity rate
- **30秒時間解析度**: Vallado 2013 - SGP4 精度要求
- **95% 覆蓋率**: ITU-T E.800 (2008) - 研究原型系統門檻

---

## 🔍 故障排除

### 問題: 配置加載失敗

```bash
# 檢查環境變數
echo $ORBIT_ENGINE_CONFIG_DIR
# 應輸出: /home/sat/satellite/orbit-engine/config/rl_training

# 驗證配置文件存在
ls -lh config/rl_training/
```

### 問題: 輸出目錄錯誤

```bash
# 檢查輸出環境變數
echo $ORBIT_ENGINE_OUTPUT_DIR
# 應輸出: /home/sat/satellite/orbit-engine/data/outputs/rl_training

# 創建輸出目錄
mkdir -p data/outputs/rl_training/{stage1,stage2,stage3,stage4,stage5,stage6}
```

---

## 📝 變更歷史

| 日期 | 變更 | 說明 |
|------|------|------|
| 2025-10-20 | 初始創建 | 複製原始配置並調整 RL 訓練參數 |
| 2025-10-20 | Stage 2 調整 | `coverage_cycles: 1.0 → 106.1`（7天） |
| 2025-10-20 | Stage 4 調整 | 池優化目標 `[10,15] → [4,6]`, `10-15 → 800-1000` |

---

**相關文檔**:
- `/home/sat/satellite/DUAL_MODE_ARCHITECTURE.md` - 雙模式架構完整設計
- `/home/sat/satellite/RL_VS_ORBIT_ENGINE_COMPARISON.md` - RL vs orbit-engine 對比分析
