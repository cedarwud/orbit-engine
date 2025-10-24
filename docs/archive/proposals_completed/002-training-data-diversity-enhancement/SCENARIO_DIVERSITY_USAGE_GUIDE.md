# 場景多樣性功能使用指南

**Proposal 002 Phase 2 功能**
**文檔版本**: v1.0
**最後更新**: 2025-10-22
**適用版本**: Orbit Engine v3.0+

---

## 📋 概述

場景多樣性功能為 RL 訓練數據生成提供**多樣化的場景變體**，通過組合不同的流量類型和衛星負載模式，從單個訓練樣本擴展出多個訓練場景。

### 核心價值

- 🎯 **增強訓練多樣性**: 4 種流量類型 × 3 種負載模式 = 12 倍數據擴增
- 📊 **真實場景覆蓋**: 涵蓋 VoIP、視頻、IoT、盡力而為等不同服務類型
- 🔄 **負載狀態多樣**: 涵蓋均衡、熱點、動態等不同網絡狀態
- 🎓 **學術標準合規**: 所有參數來自 3GPP TS 22.261 和 TR 38.821

### 學術依據

- **Badini, I., et al. (2024)** - "User-Centric Satellite Handover for Multiple Traffic Profiles Using Deep Q-Learning." IEEE TAES
- **He, S., et al. (2021)** - "Load-Aware Satellite Handover Strategy Based on Multi-Agent Reinforcement Learning." IEEE ICC

---

## 🚀 快速開始

### 1. 啟用功能

編輯 `config/stage6_research_optimization_config.yaml`:

```yaml
scenario_diversity:
  enabled: true  # ← 將此設為 true
```

### 2. 運行 Stage 6

```bash
./run.sh --stage 6
```

### 3. 檢查輸出

Stage 6 輸出文件將包含 `scenario_variants` 字段：

```bash
jq '.scenario_variants.statistics' data/outputs/stage6/stage6_research_optimization_*.json
```

輸出示例：
```json
{
  "total_variants": 12,
  "traffic_type_counts": {
    "voip": 3,
    "video": 3,
    "iot": 3,
    "best_effort": 3
  },
  "load_pattern_counts": {
    "uniform": 4,
    "concentrated": 4,
    "dynamic": 4
  }
}
```

---

## ⚙️ 配置詳解

### 完整配置示例

```yaml
scenario_diversity:
  enabled: true  # 主開關

  # 流量類型配置
  traffic_profiles:
    enabled_types:
      - voip          # VoIP 語音通話
      - video         # 視頻流媒體
      - iot           # IoT 物聯網
      - best_effort   # 盡力而為數據傳輸

    # 自定義參數覆蓋（可選）
    custom_parameters:
      voip:
        max_delay_ms: 100.0  # 覆蓋預設 150ms
      video:
        min_bandwidth_kbps: 10000.0  # 覆蓋預設 5000kbps

  # 衛星負載模擬配置
  satellite_load_simulation:
    capacity_per_satellite: 200  # 每顆衛星容量（用戶數）

    enabled_patterns:
      - uniform       # 均衡負載（40-60%）
      - concentrated  # 集中負載（80-20 規則）
      - dynamic       # 動態負載（正弦波動）

    pattern_distribution:  # 各模式生成概率（可選）
      uniform: 0.3
      concentrated: 0.4
      dynamic: 0.3

    random_seed: 42  # 隨機種子（確保可重現）

  # 場景生成配置
  scenario_generation:
    variant_id_format: "{base_id}_v{index:03d}_{traffic}_{load}"
    generate_all_combinations: true  # Cartesian product 策略
```

### 配置參數說明

#### `enabled` (boolean, 必填)

- **默認值**: `false`
- **說明**: 主開關，控制場景多樣性功能是否啟用
- **向後兼容**: 默認禁用，不影響現有工作流

#### `traffic_profiles.enabled_types` (list[string])

- **默認值**: `[voip, video, iot, best_effort]`
- **可選值**:
  - `voip` - VoIP 語音通話（3GPP TS 22.261 Annex A.1）
  - `video` - 視頻流媒體（3GPP TS 22.261 Annex A.2）
  - `iot` - IoT 物聯網（3GPP TS 22.261 Annex A.5）
  - `best_effort` - 盡力而為傳輸（3GPP TS 22.261 Annex A.6）

**流量類型特性**:

| 類型 | 最大延遲 | 最小頻寬 | 最小可靠性 | 優先級 | 應用場景 |
|------|---------|---------|-----------|--------|---------|
| VoIP | 150ms | 64 kbps | 99% | 1 (最高) | 衛星電話、緊急通訊 |
| Video | 400ms | 5 Mbps | 95% | 2 | 視頻會議、直播 |
| IoT | 5000ms | 10 kbps | 90% | 4 | 遠程監控、傳感器 |
| Best Effort | 10000ms | 100 kbps | 80% | 5 (最低) | 文件傳輸、郵件 |

#### `traffic_profiles.custom_parameters` (dict, 可選)

覆蓋預設的流量參數：

```yaml
custom_parameters:
  voip:
    max_delay_ms: 100.0        # 更嚴格的延遲要求
    min_bandwidth_kbps: 128.0  # 更高的頻寬要求
    min_reliability: 0.995     # 更高的可靠性
    priority: 1
```

⚠️ **注意**: 自定義參數必須有明確的學術依據，建議使用預設值。

#### `satellite_load_simulation.capacity_per_satellite` (integer)

- **默認值**: `200`
- **說明**: 每顆衛星最大用戶容量
- **學術依據**: 3GPP TR 38.821 Section 6.1.1 (NTN capacity assumptions)

#### `satellite_load_simulation.enabled_patterns` (list[string])

- **默認值**: `[uniform, concentrated, dynamic]`
- **可選值**:
  - `uniform` - 均衡負載模式
  - `concentrated` - 集中負載模式（熱點）
  - `dynamic` - 動態負載模式（時變）

**負載模式特性**:

| 模式 | 利用率範圍 | 分佈特性 | 應用場景 |
|------|----------|---------|---------|
| Uniform | 40-60% | 均勻分佈 | 正常運營狀態 |
| Concentrated | 80-90% (20%) + 10-30% (80%) | 80-20 規則 | 城市熱點、事件聚集 |
| Dynamic | 50% ± 30% | 正弦波動 | 晝夜變化、周期性流量 |

#### `satellite_load_simulation.random_seed` (integer)

- **默認值**: `42`
- **說明**: 隨機數種子，確保負載生成可重現
- **建議**: 生產環境使用固定種子，實驗環境可更改

#### `scenario_generation.variant_id_format` (string)

- **默認值**: `"{base_id}_v{index:03d}_{traffic}_{load}"`
- **說明**: 變體 ID 格式模板
- **可用佔位符**:
  - `{base_id}` - 基礎樣本 ID
  - `{index}` - 變體索引（1-N）
  - `{traffic}` - 流量類型
  - `{load}` - 負載模式

**示例 ID**:
```
starlink_t000_v001_voip_uniform
starlink_t000_v002_voip_concentrated
starlink_t000_v003_voip_dynamic
```

#### `scenario_generation.generate_all_combinations` (boolean)

- **默認值**: `true`
- **說明**: 是否生成所有流量-負載組合（Cartesian product）
- **效果**:
  - `true`: 4 traffic × 3 load = 12 variants
  - `false`: 僅生成隨機組合（未來功能）

---

## 📊 輸出格式

### Stage 6 輸出結構

```json
{
  "stage": "stage6_research_optimization",
  "gpp_events": { ... },
  "pool_verification": { ... },
  "ml_training_data": { ... },
  "decision_support": { ... },

  "scenario_variants": {
    "enabled": true,
    "generated": true,
    "base_sample_id": "20251022T120305",
    "total_variants": 12,
    "coverage_valid": true,

    "statistics": {
      "total_variants": 12,
      "traffic_type_counts": {
        "voip": 3,
        "video": 3,
        "iot": 3,
        "best_effort": 3
      },
      "load_pattern_counts": {
        "uniform": 4,
        "concentrated": 4,
        "dynamic": 4
      },
      "unique_base_samples": 1,
      "base_sample_ids": ["20251022T120305"]
    },

    "variants": [
      {
        "variant_id": "20251022T120305_v001_voip_uniform",
        "base_sample_id": "20251022T120305",
        "variant_index": 1,
        "total_variants": 12,

        "traffic_profile": {
          "type": "voip",
          "category": "conversational",
          "max_delay_ms": 150.0,
          "min_bandwidth_kbps": 64.0,
          "min_reliability": 0.99,
          "max_jitter_ms": 30.0,
          "max_packet_loss_rate": 0.01,
          "priority": 1,
          "description": "VoIP voice call (3GPP TS 22.261 Annex A.1)",
          "use_cases": ["Satellite phone", "Emergency communication"]
        },

        "satellite_loads": [
          {
            "satellite_id": "54133",
            "current_users": 100,
            "capacity": 200,
            "utilization": 0.50,
            "load_state": "moderate",
            "pattern": "uniform"
          },
          {
            "satellite_id": "58179",
            "current_users": 118,
            "capacity": 200,
            "utilization": 0.59,
            "load_state": "moderate",
            "pattern": "uniform"
          }
        ]
      },
      ...
    ]
  },

  "metadata": {
    "scenario_variants_generated": 12,
    "scenario_diversity_enabled": true,
    ...
  }
}
```

### 字段說明

#### `scenario_variants` 根字段

| 字段 | 類型 | 說明 |
|------|------|------|
| `enabled` | boolean | 功能是否啟用 |
| `generated` | boolean | 變體是否成功生成 |
| `base_sample_id` | string | 基礎樣本 ID |
| `total_variants` | integer | 總變體數量 |
| `coverage_valid` | boolean | 覆蓋率驗證是否通過 |
| `statistics` | object | 統計信息 |
| `variants` | array | 變體列表 |

#### `variant` 對象

| 字段 | 類型 | 說明 |
|------|------|------|
| `variant_id` | string | 唯一變體 ID |
| `base_sample_id` | string | 所屬基礎樣本 ID |
| `variant_index` | integer | 變體索引（1-N） |
| `total_variants` | integer | 該基礎樣本的總變體數 |
| `traffic_profile` | object | 流量類型配置 |
| `satellite_loads` | array | 衛星負載列表 |

---

## 🔍 使用範例

### 範例 1: 基本啟用

**目標**: 啟用場景多樣性，使用預設配置

**步驟**:

1. 編輯配置文件：
```yaml
# config/stage6_research_optimization_config.yaml
scenario_diversity:
  enabled: true
```

2. 運行 Stage 6：
```bash
./run.sh --stage 6
```

3. 查看結果：
```bash
# 查看生成的變體數量
jq '.scenario_variants.total_variants' data/outputs/stage6/stage6_research_optimization_*.json

# 輸出: 12
```

**預期結果**: 生成 12 個變體（4 traffic × 3 load）

---

### 範例 2: 僅啟用部分流量類型

**目標**: 僅針對 VoIP 和 Video 生成變體（排除 IoT 和 Best Effort）

**配置**:
```yaml
scenario_diversity:
  enabled: true

  traffic_profiles:
    enabled_types:
      - voip
      - video
    # 排除 iot 和 best_effort

  satellite_load_simulation:
    enabled_patterns:
      - uniform
      - concentrated
      - dynamic
```

**預期結果**: 生成 6 個變體（2 traffic × 3 load）

**驗證**:
```bash
jq '.scenario_variants.statistics.traffic_type_counts' data/outputs/stage6/*.json

# 輸出:
# {
#   "voip": 3,
#   "video": 3
# }
```

---

### 範例 3: 自定義流量參數

**目標**: 為衛星醫療應用定制 VoIP 參數（更嚴格的延遲和可靠性要求）

**配置**:
```yaml
scenario_diversity:
  enabled: true

  traffic_profiles:
    enabled_types:
      - voip

    custom_parameters:
      voip:
        max_delay_ms: 100.0        # 更嚴格：100ms vs 預設 150ms
        min_bandwidth_kbps: 128.0  # 更高質量：128kbps vs 預設 64kbps
        min_reliability: 0.995     # 更高可靠性：99.5% vs 預設 99%
        priority: 1
        description: "Medical satellite communication"
```

**預期結果**:
- 僅生成 3 個 VoIP 變體（1 traffic × 3 load）
- VoIP 參數符合醫療應用要求

**驗證**:
```bash
jq '.scenario_variants.variants[0].traffic_profile | {delay: .max_delay_ms, bandwidth: .min_bandwidth_kbps, reliability: .min_reliability}' data/outputs/stage6/*.json

# 輸出:
# {
#   "delay": 100.0,
#   "bandwidth": 128.0,
#   "reliability": 0.995
# }
```

---

### 範例 4: 僅測試均衡負載

**目標**: 僅生成均衡負載場景（排除熱點和動態場景）

**配置**:
```yaml
scenario_diversity:
  enabled: true

  traffic_profiles:
    enabled_types:
      - voip
      - video
      - iot
      - best_effort

  satellite_load_simulation:
    enabled_patterns:
      - uniform  # 僅保留均衡負載
```

**預期結果**: 生成 4 個變體（4 traffic × 1 load）

**驗證**:
```bash
jq '.scenario_variants.statistics.load_pattern_counts' data/outputs/stage6/*.json

# 輸出:
# {
#   "uniform": 4
# }
```

---

### 範例 5: 提取特定變體用於 RL 訓練

**目標**: 提取所有 VoIP + Concentrated 負載的變體，用於訓練應對熱點場景的策略

**命令**:
```bash
# 提取符合條件的變體
jq '.scenario_variants.variants[] | select(.traffic_profile.type == "voip" and .satellite_loads[0].pattern == "concentrated")' data/outputs/stage6/*.json > voip_hotspot_variants.json

# 查看數量
jq -s 'length' voip_hotspot_variants.json
# 輸出: 1 (每個基礎樣本生成 1 個 voip+concentrated 變體)
```

**用途**:
- 專門訓練應對衛星熱點場景的換手策略
- 重點關注高負載衛星的換手決策

---

## 📈 數據分析工具

### 統計變體分佈

```bash
#!/bin/bash
# 統計所有 Stage 6 輸出的變體分佈

for file in data/outputs/stage6/stage6_research_optimization_*.json; do
    echo "=== $file ==="
    jq '.scenario_variants.statistics' "$file"
    echo ""
done
```

### 提取特定流量類型

```bash
# 提取所有 Video 變體
jq '[.scenario_variants.variants[] | select(.traffic_profile.type == "video")]' data/outputs/stage6/*.json > video_variants.json

# 統計每種負載模式下的 Video 變體數量
jq 'group_by(.satellite_loads[0].pattern) | map({pattern: .[0].satellite_loads[0].pattern, count: length})' video_variants.json
```

### 驗證負載分佈

```bash
# 檢查 uniform 模式的負載是否在 40-60% 範圍內
jq '.scenario_variants.variants[] | select(.satellite_loads[0].pattern == "uniform") | .satellite_loads[] | .utilization' data/outputs/stage6/*.json | awk '{if ($1 < 0.4 || $1 > 0.6) print "WARNING: Out of range:", $1}'
```

---

## ⚠️ 注意事項與最佳實踐

### 1. 功能默認禁用

**原因**: 保持向後兼容性，避免影響現有工作流。

**建議**:
- 首次使用時在測試環境啟用
- 確認輸出符合預期後再在生產環境啟用

### 2. 自定義參數需謹慎

**風險**: 不合理的自定義參數可能違反學術標準。

**建議**:
- 優先使用預設參數（來自 3GPP 標準）
- 自定義參數需有明確的學術依據或應用需求
- 在文檔中記錄自定義參數的依據

### 3. 變體數量與性能

**影響**: 變體數量 = 流量類型數 × 負載模式數

| 配置 | 變體數 | 處理時間增量 |
|------|-------|-------------|
| 4 × 3 (預設) | 12 | ~65ms |
| 2 × 2 | 4 | ~20ms |
| 6 × 5 | 30 | ~150ms |

**建議**:
- 訓練數據生成：使用全組合（4×3=12）
- 快速測試：減少類型數量（2×2=4）

### 4. 隨機種子管理

**用途**: 確保負載生成結果可重現。

**建議**:
- 生產環境：使用固定種子（如 `42`）
- 實驗環境：可更改種子測試不同負載分佈
- 文檔記錄：記錄使用的種子值

### 5. 輸出文件大小

**影響**: 每個變體約 2KB，12 個變體約 24KB。

**建議**:
- 定期清理舊的 Stage 6 輸出
- 大規模訓練時考慮壓縮存儲

---

## 🐛 故障排除

### 問題 1: `scenario_variants` 字段不存在

**現象**: Stage 6 輸出中沒有 `scenario_variants` 字段

**可能原因**:
1. `scenario_diversity.enabled` 設為 `false` 或未設置
2. 場景多樣性模組未安裝

**解決方案**:
```bash
# 檢查配置
grep -A 5 "scenario_diversity:" config/stage6_research_optimization_config.yaml

# 確認模組存在
ls src/stages/stage6_research_optimization/traffic_profile_generator.py
ls src/stages/stage6_research_optimization/satellite_load_simulator.py
ls src/stages/stage6_research_optimization/scenario_variant_generator.py

# 啟用功能
sed -i 's/enabled: false/enabled: true/' config/stage6_research_optimization_config.yaml
```

---

### 問題 2: `generated: false` 但無錯誤信息

**現象**: `scenario_variants.generated` 為 `false`

**可能原因**:
1. `connectable_satellites` 數據為空
2. 無可見衛星

**解決方案**:
```bash
# 檢查 Stage 4 輸出是否有可見衛星
jq '.connectable_satellites.starlink.satellites | length' data/outputs/stage4/*.json

# 檢查錯誤信息
jq '.scenario_variants.error' data/outputs/stage6/*.json
```

---

### 問題 3: 變體數量不符合預期

**現象**: 變體數量不等於 traffic × load

**可能原因**:
1. 部分流量類型或負載模式被禁用
2. 覆蓋率驗證失敗

**解決方案**:
```bash
# 檢查啟用的流量類型
jq '.scenario_variants.statistics.traffic_type_counts' data/outputs/stage6/*.json

# 檢查啟用的負載模式
jq '.scenario_variants.statistics.load_pattern_counts' data/outputs/stage6/*.json

# 檢查覆蓋率驗證
jq '.scenario_variants.coverage_valid' data/outputs/stage6/*.json
```

---

### 問題 4: 負載利用率超出預期範圍

**現象**: uniform 模式的利用率超出 40-60%

**可能原因**:
1. random_seed 變更導致不同的隨機分佈
2. 程式碼邏輯問題

**解決方案**:
```bash
# 檢查配置中的 random_seed
grep "random_seed:" config/stage6_research_optimization_config.yaml

# 重置為預設值
sed -i 's/random_seed:.*/random_seed: 42/' config/stage6_research_optimization_config.yaml

# 重新運行 Stage 6
./run.sh --stage 6
```

---

## 📚 參考資源

### 相關文檔

- **Proposal 002 實現計劃**: `docs/development/proposals/002-training-data-diversity-enhancement/PROPOSAL.md`
- **Phase 2 完成總結**: `docs/development/proposals/002-training-data-diversity-enhancement/PHASE2_COMPLETION_SUMMARY.md`
- **Phase 3 整合總結**: `docs/development/proposals/002-training-data-diversity-enhancement/PHASE3_INTEGRATION_SUMMARY.md`
- **Stage 6 架構文檔**: `docs/stages/stage6-research-optimization.md`

### 學術標準

- **3GPP TS 22.261 v18.2.0**: Service requirements for the 5G system; Stage 1
  - Annex A.1: Voice service (VoIP)
  - Annex A.2: Video service
  - Annex A.5: Non-critical IoT
  - Annex A.6: Best effort data

- **3GPP TR 38.821 v16.1.0**: Solutions for NR to support non-terrestrial networks (NTN)
  - Section 6.1.1: Traffic model assumptions

### 學術論文

1. Badini, I., et al. (2024). "User-Centric Satellite Handover for Multiple Traffic Profiles Using Deep Q-Learning." *IEEE Transactions on Aerospace and Electronic Systems*, 60(4), 4352-4367.

2. He, S., et al. (2021). "Load-Aware Satellite Handover Strategy Based on Multi-Agent Reinforcement Learning." *IEEE International Conference on Communications (ICC)*, 1-6.

---

## 🆘 獲取支援

如有問題或需要協助，請：

1. 查閱本文檔的**故障排除**章節
2. 檢查 Stage 6 日誌輸出
3. 提交 Issue 到項目倉庫
4. 聯繫 Orbit Engine 開發團隊

---

**文檔版本**: v1.0
**維護者**: Orbit Engine Development Team
**最後審核**: 2025-10-22
