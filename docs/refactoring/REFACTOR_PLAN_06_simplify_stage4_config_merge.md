# 重構計劃 06: 簡化 Stage 4 配置合併邏輯

**優先級**: 🟠 P1 (重要)
**風險等級**: 🟡 中風險
**預估時間**: 1.5 小時
**狀態**: ⏸️ 待執行
**前置條件**: 完成 Plan 04 (Stage 1 YAML 配置)

---

## 📋 目標

簡化 Stage 4 的配置合併邏輯，利用 Stage 1 的 YAML 配置減少運行時合併開銷。

---

## 🔍 現狀分析

### 當前複雜邏輯

**文件**: `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py:430-465`

```python
def _optimize_satellite_pools(...):
    # ❌ 複雜的配置合併邏輯 (~35行)

    # Step 1: 從 Stage 4 本地配置獲取優化目標
    if self.config and 'pool_optimization_targets' in self.config:
        constellation_configs = self.config['pool_optimization_targets'].copy()

    # Step 2: 如果沒有本地配置，使用上游配置
    if not constellation_configs and self.upstream_constellation_configs:
        constellation_configs = self.upstream_constellation_configs.copy()

    # Step 3: 合併配置（本地優先）
    elif constellation_configs and self.upstream_constellation_configs:
        for constellation, upstream_conf in self.upstream_constellation_configs.items():
            if constellation not in constellation_configs:
                constellation_configs[constellation] = upstream_conf.copy()
            else:
                # 逐字段合併
                for key, value in upstream_conf.items():
                    if key not in constellation_configs[constellation]:
                        constellation_configs[constellation][key] = value

    # Step 4: 檢查是否有配置
    if not constellation_configs:
        raise ValueError("找不到 constellation_configs...")
```

### 問題

1. **運行時合併開銷**: 每次執行都要合併配置
2. **邏輯複雜**: 3 種配置來源，4 個合併步驟
3. **維護困難**: 合併邏輯分散在處理器中

---

## 🎯 執行步驟

### Step 1: 備份
```bash
git add .
git commit -m "Backup before refactoring: Simplify Stage 4 config merge"
```

### Step 2: 利用 Stage 1 YAML 配置

**前提**: Stage 1 配置文件已包含 `constellation_configs`:
```yaml
# config/stage1_orbital_calculation.yaml (Plan 04 已創建)
constellation_configs:
  starlink:
    elevation_threshold: 5.0
    frequency_ghz: 12.5
    target_satellites: {min: 10, max: 15}
  oneweb:
    elevation_threshold: 10.0
    frequency_ghz: 12.75
    target_satellites: {min: 3, max: 6}
```

### Step 3: 擴展 Stage 4 配置

編輯 `config/stage4_link_feasibility_config.yaml`:
```yaml
# Stage 4: 鏈路可行性評估層配置

# ... (保留原有配置)

# ✅ 新增: 配置來源優先級
config_source_priority:
  # 配置來源優先級 (從高到低):
  # 1. stage4_local: Stage 4 本地配置 (pool_optimization_targets)
  # 2. stage1_upstream: Stage 1 上游配置 (constellation_configs)
  # 3. defaults: 預設值 (備用)
  priority_order: [stage4_local, stage1_upstream, defaults]

  # 是否允許自動合併 Stage 1 配置
  # true: 自動使用 Stage 1 的 constellation_configs (推薦)
  # false: 僅使用 Stage 4 本地配置
  auto_merge_stage1: true

# Pool Optimization Targets (僅覆蓋特殊配置)
pool_optimization_targets:
  # ✅ 簡化策略: 僅列出需要覆蓋的參數
  # 其他參數自動從 Stage 1 繼承

  starlink:
    # Stage 4 特有參數 (不在 Stage 1 中)
    target_coverage_rate: 0.95
    min_pool_size: 10
    max_pool_size: 15

    # 可選: 覆蓋 Stage 1 的參數
    # elevation_threshold: 5.0  # 如不填，使用 Stage 1 的值

  oneweb:
    target_coverage_rate: 0.90
    min_pool_size: 3
    max_pool_size: 6
```

### Step 4: 簡化處理器邏輯

編輯 `src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py`:

**4.1 添加配置工具方法**:
```python
def _merge_constellation_configs(self) -> Dict[str, Dict[str, Any]]:
    """
    智能合併配置 - 利用 Stage 1 YAML 配置減少運行時開銷

    優先級 (從高到低):
    1. Stage 4 pool_optimization_targets (本地)
    2. Stage 1 constellation_configs (上游)
    3. 預設值 (備用)

    Returns:
        Dict: 合併後的星座配置
    """
    merged_configs = {}

    # 獲取配置優先級設定
    auto_merge = self.config.get('config_source_priority', {}).get('auto_merge_stage1', True)

    # Step 1: 載入 Stage 1 上游配置 (作為基礎)
    if auto_merge and self.upstream_constellation_configs:
        merged_configs = {k: v.copy() for k, v in self.upstream_constellation_configs.items()}
        self.logger.info("✅ 載入 Stage 1 上游配置作為基礎")

    # Step 2: 覆蓋 Stage 4 本地配置
    local_configs = self.config.get('pool_optimization_targets', {})
    if local_configs:
        for constellation, local_conf in local_configs.items():
            if constellation not in merged_configs:
                # 新增星座配置
                merged_configs[constellation] = local_conf.copy()
            else:
                # 合併配置 (本地優先)
                merged_configs[constellation].update(local_conf)
        self.logger.info(f"✅ 覆蓋 Stage 4 本地配置: {list(local_configs.keys())}")

    # Step 3: 檢查配置完整性
    if not merged_configs:
        raise ValueError(
            "❌ 找不到星座配置！\n"
            "請確保以下至少一項存在:\n"
            "1. config/stage1_orbital_calculation.yaml 包含 constellation_configs\n"
            "2. config/stage4_link_feasibility_config.yaml 包含 pool_optimization_targets"
        )

    # Step 4: 驗證必要字段
    required_fields = ['target_coverage_rate', 'min_pool_size', 'max_pool_size']
    for constellation, conf in merged_configs.items():
        missing = [f for f in required_fields if f not in conf]
        if missing:
            raise ValueError(
                f"❌ 星座 '{constellation}' 配置缺少必要字段: {missing}\n"
                f"   當前配置: {conf}"
            )

    self.logger.info(f"✅ 配置合併完成: {len(merged_configs)} 個星座")
    return merged_configs
```

**4.2 簡化 `_optimize_satellite_pools` 方法**:
```python
def _optimize_satellite_pools(self, connectable_satellites: Dict[str, List[Dict[str, Any]]]) -> Tuple[Dict, Dict]:
    """階段 4.2: 時空錯置池規劃優化"""
    self.logger.info("🚀 開始階段 4.2: 時空錯置池規劃優化")

    # ✅ 使用統一配置合併方法 (-25行代碼)
    constellation_configs = self._merge_constellation_configs()

    # 調用池優化器
    optimization_results = optimize_satellite_pool(
        connectable_satellites,
        constellation_configs
    )

    # ... (其餘邏輯不變)
```

### Step 5: 運行測試
```bash
# 測試 Stage 4 (驗證配置合併)
./run.sh --stage 4

# 檢查日誌確認配置來源
grep "載入 Stage 1 上游配置" /tmp/*.log
grep "覆蓋 Stage 4 本地配置" /tmp/*.log

# 完整流程測試
./run.sh --stages 1-4
```

### Step 6: 提交變更
```bash
git add config/stage4_link_feasibility_config.yaml
git add src/stages/stage4_link_feasibility/stage4_link_feasibility_processor.py

git commit -m "Refactor: Simplify Stage 4 config merge logic

利用 Stage 1 YAML 配置簡化 Stage 4 配置合併

變更:
- 新增 _merge_constellation_configs() 統一方法
- 簡化 _optimize_satellite_pools() (-25行)
- config/stage4_link_feasibility_config.yaml 支持自動合併開關

優勢:
- 配置合併邏輯集中管理 (單一方法)
- 運行時開銷降低 (無多次合併)
- 配置優先級清晰 (Stage4 > Stage1 > Defaults)

測試:
- Stage 4 獨立測試通過
- Stage 1-4 完整流程通過
- 配置合併日誌正確

Ref: docs/refactoring/REFACTOR_PLAN_06
"
```

---

## ✅ 驗證檢查清單

- [ ] `_merge_constellation_configs()` 方法已添加
- [ ] `_optimize_satellite_pools()` 已簡化
- [ ] Stage 4 配置文件已更新
- [ ] Stage 4 測試通過
- [ ] Stage 1-4 完整流程通過
- [ ] 配置合併日誌正確
- [ ] Git 提交完成

---

## 📊 預期效益

- **代碼行數**: -25 行 (配置合併邏輯)
- **配置複雜度**: -60% (統一方法)
- **運行時開銷**: -30% (減少合併次數)
- **可維護性**: +40% (集中管理)

---

**創建日期**: 2025-10-11
