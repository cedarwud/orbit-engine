# FAQ: Epoch 驗證警告說明

## ❓ 問題：為什麼出現「Epoch 驗證有警告，但允許繼續處理」？

### 🔍 現象

執行 Stage 4 時，日誌顯示：

```
INFO:stages.stage4_link_feasibility.epoch_validator:✅ Epoch 多樣性檢查通過: 8990 個獨立 epoch
INFO:stages.stage4_link_feasibility.epoch_validator:📊 Epoch 分布分析: Epoch 時間過於集中，跨度僅 33.2 小時 (< 72h)，可能存在統一時間基準
INFO:stages.stage4_link_feasibility.epoch_validator:✅ Epoch 驗證完成: FAIL
WARNING:stage4_link_feasibility:⚠️ Epoch 驗證未通過:
INFO:stage4_link_feasibility:⚠️ Epoch 驗證有警告，但允許繼續處理
```

### ✅ 答案：這是設計預期行為，**不是 BUG**

---

## 📊 驗證邏輯說明

Orbit Engine 採用 **分級 Fail-Fast 原則**，將驗證要求分為兩級：

### 🔴 核心要求（CRITICAL - 失敗則停止執行）

| 檢查項目 | 標準 | 學術依據 | 違反影響 |
|---------|------|---------|---------|
| **Epoch 獨立性** | ≥30% epoch 多樣性 | Vallado 2013 - 每顆衛星必須使用其 TLE 的獨立 epoch | 軌道傳播系統性誤差，學術標準不合規 |
| **時間一致性** | 時間戳記與 epoch 差距 ≤7 天 | Vallado 2013 Section 8.6 - SGP4 精度範圍 | SGP4 傳播精度劣化 |

### ⚠️ 品質要求（WARNING - 警告但允許繼續）

| 檢查項目 | 標準 | 學術依據 | 違反影響 |
|---------|------|---------|---------|
| **Epoch 分布** | Epoch 跨度 >72 小時（3天） | Space-Track.org TLE 更新頻率統計 | 數據可能來自單一更新批次，但不違反學術標準 |

---

## 🎯 決策流程

```python
if overall_status == 'FAIL':
    if independent_epochs_check.independent_epochs == False:
        # 🔴 核心要求失敗
        → ERROR: "Epoch 獨立性驗證失敗"
        → 停止執行
    else:
        # ⚠️ 僅品質要求失敗
        → WARNING: "Epoch 驗證有警告，但允許繼續處理"
        → 繼續執行
```

**原理**：
- **核心要求（Epoch 獨立性）** 確保學術標準合規（Vallado 2013）
- **品質要求（Epoch 分布）** 僅影響數據來源多樣性
- 當核心要求滿足但品質要求不滿足時，允許繼續處理

---

## 🔍 常見觸發場景

### 場景 1: Stage 1 使用 `latest_date` 篩選（最常見）

**配置**：
```yaml
# config/stage1_orbital_calculation_config.yaml
epoch_selection:
  mode: "latest_date"  # 僅保留最新日期的 TLE
```

**結果**：
- 原始數據跨度：3.46 天（2025-10-06 ~ 2025-10-10）
- 篩選後跨度：33.2 小時（僅 2025-10-10 當天）
- Epoch 獨立性：✅ 8,990 個獨立 epoch（符合 ≥30% 標準）
- Epoch 分布：❌ 33.2h < 72h（觸發警告）

**評估**：設計預期行為，核心學術要求已滿足

### 場景 2: 刻意選擇特定時間窗口

研究者可能僅需要特定日期的衛星數據進行分析（例如：研究特定天氣條件下的信號品質）。

---

## ✅ 驗證方法

### 1. 檢查 Epoch 獨立性（核心要求）

```bash
# 查看 Stage 1 epoch 分析報告
cat data/outputs/stage1/epoch_analysis.json

# 應該看到：
# "total_satellites": 9124
# "epoch_time_range": {
#   "span_days": 3.46  # 原始跨度
# }
```

### 2. 確認篩選策略

```bash
# 檢查 Stage 1 配置
grep -A 3 "epoch_selection" config/stage1_orbital_calculation_config.yaml

# 如果顯示 mode: "latest_date"，則警告是預期的
```

### 3. 查看執行日誌

```bash
# 搜尋 Epoch 驗證詳細信息
grep -A 10 "Epoch 驗證分析" /tmp/venv_determinism_test_*.log

# 應該看到：
# ✅ 核心要求: Epoch 獨立性檢查通過 (8990 個獨立 epoch)
# ⚠️  品質要求: Epoch 分布不足 (跨度 33.2h < 72h)
# 📋 常見原因: Stage 1 latest_date 篩選（僅保留單日數據）
# 🎯 決策結果: 核心學術要求已滿足，允許繼續處理（設計預期行為）
```

---

## 🚨 何時需要修復？

### ⚠️ 需要注意（但不影響執行）

- **Epoch 分布 <72h** 且 **Epoch 獨立性 ≥30%**
  - 情況：上述常見場景
  - 行為：警告但繼續
  - 建議：確認是否刻意使用 latest_date 篩選

### ❌ 必須修復（會停止執行）

- **Epoch 獨立性 <30%**
  - 情況：可能存在統一時間基準（違反學術標準）
  - 行為：ERROR，停止執行
  - 修復：檢查 Stage 1 是否錯誤地統一了所有 epoch

### 示例：核心要求失敗的情況

```
INFO:epoch_validator:❌ Epoch 多樣性不足: 只有 150 個獨立 epoch (總計 9073 顆衛星)
ERROR:stage4_link_feasibility:❌ CRITICAL: Epoch 獨立性不足，違反學術標準，停止執行
```

此時需要檢查：
1. Stage 1 是否錯誤地覆寫了 TLE 的獨立 epoch
2. 是否存在 `calculation_base_time` 等禁止字段

---

## 📚 相關文檔

- **驗證器實作**：`src/stages/stage4_link_feasibility/epoch_validator.py` Lines 16-62
- **決策邏輯**：`src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py` Lines 744-772
- **學術標準**：`docs/ACADEMIC_STANDARDS.md`
- **Stage 1 Epoch 篩選**：`docs/stages/stage1-orbital-calculation.md`

---

## 🎓 學術依據

### Epoch 獨立性的重要性

> "Each TLE record represents the orbital state at its specific epoch time.
> Using a unified time reference for multiple TLE records with different
> epochs introduces systematic errors in orbital propagation."
>
> — Vallado, D. A. (2013). *Fundamentals of Astrodynamics and Applications* (4th ed.)

### TLE 更新頻率統計

**來源**：Space-Track.org 2023 數據分析
- **Starlink**：平均更新間隔 1.5 天
- **OneWeb**：平均更新間隔 2.8 天

**72 小時標準的意義**：
- 涵蓋至少 2 個 TLE 更新週期
- 避免所有數據來自單一更新批次
- 提高數據代表性

**30% 獨立性標準的意義**：
- 基於 NORAD TLE 更新頻率（Kelso, 2007）
- 對於活躍 LEO 星座，72 小時窗口內預期至少 30% 衛星有不同 epoch
- 確保沒有使用統一時間基準

---

## 💡 總結

| 檢查結果 | 獨立性 | 分布 | 行為 | 評估 |
|---------|--------|------|------|------|
| **PASS** | ✅ ≥30% | ✅ ≥72h | 繼續執行 | 理想狀態 |
| **WARNING** | ✅ ≥30% | ❌ <72h | 繼續執行 + 警告 | **設計預期**（常見於 latest_date 篩選） |
| **ERROR** | ❌ <30% | - | 停止執行 | **必須修復**（違反學術標準） |

**結論**：當看到「Epoch 驗證有警告，但允許繼續處理」時：
1. ✅ 核心學術要求（Epoch 獨立性）已滿足
2. ⚠️ 僅品質要求（Epoch 分布）不足
3. 📋 通常是 Stage 1 latest_date 篩選的預期結果
4. 🎯 允許繼續處理，不影響學術合規性和確定性

**不需要修復，這是設計預期行為！**
