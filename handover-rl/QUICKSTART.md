# Handover-RL 快速開始指南

## 📋 前置需求

1. **orbit-engine 已運行完 Stage 6**
   ```bash
   cd /home/sat/orbit-engine
   ./run.sh  # 或確保 data/outputs/stage6/ 有輸出文件
   ```

2. **Python 3.8+** 已安裝

## 🚀 快速開始（5 分鐘）

### 步驟 1: 創建虛擬環境並安裝依賴

```bash
cd /home/sat/orbit-engine/handover-rl

# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 步驟 2: 驗證數據連接

```bash
# 檢查 orbit-engine 路徑配置
cat config/data_config.yaml

# 確認 Stage 6 輸出存在
ls -lh /home/sat/orbit-engine/data/outputs/stage6/
```

### 步驟 3: 執行完整流程

```bash
# 方法 1: 使用一鍵腳本（推薦）
./run_all.sh

# 方法 2: 逐步執行
python phase1_data_loader.py      # 數據載入
python phase2_baseline_methods.py # Baseline 評估
python phase3_rl_environment.py   # RL 環境驗證
python phase4_rl_training.py      # DQN 訓練（耗時較長）
python phase5_evaluation.py       # 最終評估
```

## 📊 預期輸出

### Phase 1: 數據載入
```
✅ handover_events.json (4,695 樣本)
✅ train_data.json (3,521 樣本)
✅ val_data.json (587 樣本)
✅ test_data.json (587 樣本)
```

### Phase 2: Baseline 評估
```
results/baseline_results.json
results/baseline_comparison.txt
```

### Phase 3: 環境驗證
```
✅ 環境驗證通過
✅ 隨機策略測試通過
```

### Phase 4: DQN 訓練
```
results/models/dqn_best.pth          (最佳模型)
results/models/dqn_final.pth         (最終模型)
results/training_log.json            (訓練日誌)
results/plots/training_curve.png     (訓練曲線)
```

訓練時間：約 10-30 分鐘（取決於 `episodes` 配置）

### Phase 5: 最終評估
```
results/final_evaluation.json
results/comparison_report.txt
results/plots/performance_comparison.png
```

## 🎯 查看結果

### 1. 查看比較報告（文本）
```bash
cat results/comparison_report.txt
```

預期輸出：
```
方法                 換手頻率        Ping-Pong率     平均QoS(dBm)
------------------------------------------------------------------------
DQN (Best)           0.120          3.50%           -85.23
RSRP-based           0.180          12.30%          -87.45
A3-triggered         0.150          8.20%           -86.12
Always-handover      0.850          45.60%          -92.30
```

### 2. 查看評估結果（JSON）
```bash
cat results/final_evaluation.json | jq '.'
```

### 3. 查看訓練曲線
```bash
# 在本地查看（如果有 GUI）
xdg-open results/plots/training_curve.png

# 或複製到本地
scp user@server:/home/sat/orbit-engine/handover-rl/results/plots/*.png ./
```

## ⚙️ 調整配置

### 修改訓練參數

編輯 `config/rl_config.yaml`:

```yaml
training:
  episodes: 5000        # 減少到 1000 可加快測試
  save_interval: 100
  log_interval: 10
```

### 修改獎勵權重

```yaml
environment:
  reward_weights:
    qos_improvement: 1.0      # 增加可更重視信號品質
    handover_penalty: -0.2    # 減少可允許更多換手
    signal_quality: 0.3
    ping_pong_penalty: -0.5   # 增加可更嚴格懲罰 Ping-Pong
```

### 修改 DQN 超參數

```yaml
dqn:
  learning_rate: 0.001   # 增加可加快學習
  epsilon_decay: 0.995   # 減少可增加探索
  batch_size: 128        # 增加可穩定訓練
```

## 🔧 常見問題

### Q1: 找不到 Stage 6 輸出文件

**A**: 確認 orbit-engine 已運行完成：
```bash
cd /home/sat/orbit-engine
./run.sh --stages 6
ls -lh data/outputs/stage6/
```

### Q2: 訓練太慢

**A**: 減少訓練 episodes：
```yaml
# config/rl_config.yaml
training:
  episodes: 1000  # 改為 1000（原本 5000）
```

### Q3: 記憶體不足

**A**: 減少經驗回放緩衝區：
```yaml
# config/rl_config.yaml
dqn:
  memory_size: 5000  # 改為 5000（原本 10000）
```

### Q4: 想要更快看到結果

**A**: 使用小數據集測試：
```bash
# 編輯 phase1_data_loader.py
# 在 main() 中添加：
# samples = samples[:500]  # 只使用 500 個樣本
```

## 📈 下一步

### 1. 論文撰寫

使用 `results/final_evaluation.json` 和 `results/comparison_report.txt` 的數據：

- **Table 1**: 方法比較（換手頻率、Ping-Pong 率、QoS）
- **Figure 1**: 訓練曲線 (`results/plots/training_curve.png`)
- **Figure 2**: 性能比較 (`results/plots/performance_comparison.png`)

### 2. 實驗擴展

- 調整獎勵權重做消融實驗
- 測試不同 DQN 超參數
- 實作 PPO 算法（複製 Phase 4 修改）

### 3. 添加新的 Baseline

編輯 `phase2_baseline_methods.py`，添加新的 `BaselineMethod` 類。

## 💡 提示

1. **先小規模測試**：使用 1000 episodes 快速驗證流程
2. **定期保存**：訓練會自動保存 checkpoints
3. **多次運行**：改變隨機種子可得到統計平均
4. **調整獎勵**：這是影響性能的關鍵

## 📞 需要幫助？

查看完整文檔：
- `README.md` - 專案概述
- `phase*.py` - 各階段詳細註釋
- `config/*.yaml` - 配置參數說明
