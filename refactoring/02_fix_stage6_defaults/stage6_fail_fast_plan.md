# P0-2: Stage 6 预设值改为 Fail-Fast

**优先级**: P0（立即修复）
**工作量**: 1小时
**依据**: `ACADEMIC_STANDARDS.md` Lines 265-274

---

## 🚨 问题分析

### 违反条款

**ACADEMIC_STANDARDS.md Lines 265-274**:
> ### 🚫 **預設值使用限制**（新增）
> - [ ] 系統參數（頻寬、噪聲係數等）**禁止使用預設值**
>   - ❌ 錯誤: `self.config.get('noise_figure_db', 7.0)`
>   - ✅ 正確: 必須在配置中提供，或拋出錯誤

### 当前实现问题

**文件**: `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py`

#### 问题 1: 预设值常量定义 (Lines 99-121)

```python
# 仰角預設值（保守估計）
DEFAULT_ELEVATION_DEG = 45.0
# 說明: 45° 是 0-90° 的中點，用於數據缺失時的保守估計

# 距離不可達標記
DISTANCE_UNREACHABLE = 9999.0  # km
# 說明: 9999.0 km 作為「數據缺失」的明確標記

# 鏈路裕度預設值（保守估計）
DEFAULT_LINK_MARGIN_DB = 10.0
# 說明: 10 dB 對應 CQI 9-11，適合保守估計
```

**违反原因**:
- ❌ 使用"保守估計"预设值
- ❌ 数据缺失时不报错，而是使用假设值
- ❌ 违反 Grade A 标准

#### 问题 2: 使用预设值 (Lines 449-479)

```python
# ❌ 违反 Grade A 标准
if 'distance_km' not in physical_parameters:
    self.logger.warning(f"衛星 {satellite_id} 缺少 distance_km")
    physical_parameters['distance_km'] = self.DISTANCE_UNREACHABLE

elevation_deg = visibility_metrics.get('elevation_deg', self.DEFAULT_ELEVATION_DEG)
link_margin_db = self.DEFAULT_LINK_MARGIN_DB
```

---

## ✅ 解决方案

### 原则：Fail-Fast 机制

数据缺失时**立即抛出错误**，而非使用预设值：

```python
# ✅ Grade A 标准实现
if 'elevation_deg' not in visibility_metrics:
    raise ValueError(
        f"衛星 {satellite_id} 缺少 elevation_deg 數據\n"
        f"Grade A 標準禁止使用預設值（ACADEMIC_STANDARDS.md Lines 265-274）\n"
        f"請確保 Stage 5 提供完整數據"
    )
elevation_deg = visibility_metrics['elevation_deg']
```

---

## 🔧 实施步骤

### 步骤 1: 删除预设值常量（10分钟）

**修改位置**: Lines 99-121

```python
# ❌ 删除以下常量
# DEFAULT_ELEVATION_DEG = 45.0
# DISTANCE_UNREACHABLE = 9999.0
# DEFAULT_LINK_MARGIN_DB = 10.0
```

**原因**: 这些常量的存在本身就违反学术标准

### 步骤 2: 重构 `_extract_latest_snapshot` 方法（30分钟）

**修改位置**: Lines 412-508

**修改内容**:

1. **elevation_deg** (Lines 461-462):
```python
# ❌ 当前
elevation_deg = self.DEFAULT_ELEVATION_DEG

# ✅ 修正
# elevation_deg 应该从 physical_parameters 获取
# 如果 Stage 5 没有提供，应该报错
if 'elevation_deg' not in latest_point:
    raise ValueError(
        f"衛星 {satellite_id} time_series 缺少 elevation_deg\n"
        f"Grade A 標準要求所有時間點必須包含仰角數據\n"
        f"請檢查 Stage 5 輸出完整性"
    )
```

2. **distance_km** (Lines 449-455):
```python
# ❌ 当前
if 'distance_km' not in physical_parameters:
    self.logger.warning(...)
    physical_parameters['distance_km'] = self.DISTANCE_UNREACHABLE

# ✅ 修正
if 'distance_km' not in physical_parameters:
    raise ValueError(
        f"衛星 {satellite_id} physical_parameters 缺少 distance_km\n"
        f"Grade A 標準禁止使用預設值或標記值\n"
        f"請確保 Stage 5 提供完整的物理參數數據"
    )
```

3. **link_margin_db** (Lines 477-479):
```python
# ❌ 当前
link_margin_db = self.DEFAULT_LINK_MARGIN_DB

# ✅ 修正
# link_margin_db 应该从 Stage 5 计算得出
# 如果没有，需要从 signal_quality 推导或报错
if 'link_margin_db' not in summary:
    raise ValueError(
        f"衛星 {satellite_id} summary 缺少 link_margin_db\n"
        f"Grade A 標準要求明確計算鏈路裕度\n"
        f"請確保 Stage 5 包含完整的信號品質評估"
    )
link_margin_db = summary['link_margin_db']
```

### 步骤 3: 修改 `_provide_decision_support` 方法（10分钟）

**修改位置**: Lines 543-545

```python
# ❌ 当前
candidate_snapshot = self._extract_latest_snapshot(sat_id, sat_data)

# ✅ 修正（添加错误处理）
try:
    candidate_snapshot = self._extract_latest_snapshot(sat_id, sat_data)
    candidate_satellites.append(candidate_snapshot)
except ValueError as e:
    # 候选卫星数据不完整，跳过（但记录警告）
    self.logger.warning(f"候选衛星 {sat_id} 數據不完整，跳過: {e}")
    continue
```

### 步骤 4: 运行测试验证（10分钟）

```bash
# 1. 运行 Stage 6
./run.sh --stage 6

# 2. 如果出现 ValueError，检查 Stage 5 输出
jq '.signal_analysis | to_entries | .[0] | .value.time_series[0]' data/outputs/stage5/*.json

# 3. 确认 Stage 5 提供了所有必需字段
# 必需字段: elevation_deg, distance_km, link_margin_db
```

---

## 📊 预期行为变化

### 修改前（使用预设值）
```python
# 数据缺失时静默使用预设值
elevation_deg = 45.0  # 默认值
distance_km = 9999.0  # 标记值
link_margin_db = 10.0  # 保守估计

# ❌ 问题：数据不完整但不报错，结果不可靠
```

### 修改后（Fail-Fast）
```python
# 数据缺失时立即报错
raise ValueError(
    "衛星 12345 缺少 elevation_deg 數據\n"
    "Grade A 標準禁止使用預設值\n"
    "請確保 Stage 5 提供完整數據"
)

# ✅ 优点：强制数据完整性，符合学术标准
```

---

## 🔍 潜在问题与解决方案

### 问题 1: Stage 5 可能没有提供 link_margin_db

**症状**: 运行 Stage 6 时抛出 ValueError

**解决方案**:
1. 检查 Stage 5 输出结构
2. 如果 Stage 5 没有计算，需要修复 Stage 5
3. 或者在 Stage 6 中基于 RSRP/RSRQ 计算

### 问题 2: elevation_deg 在哪个字段？

**当前数据结构** (需要验证):
```json
{
  "time_series": [{
    "timestamp": "...",
    "signal_quality": {...},
    "physical_parameters": {
      "distance_km": 1234,
      "elevation_deg": 45  // ← 可能在这里
    }
  }]
}
```

**修复方法**: 从 `physical_parameters` 或 `visibility_metrics` 获取

---

## ✅ 验证清单

完成后检查：

- [ ] 删除所有预设值常量 (Lines 99-121)
- [ ] `_extract_latest_snapshot` 实现 Fail-Fast
- [ ] `_provide_decision_support` 添加错误处理
- [ ] Stage 6 运行成功（或明确报错数据缺失）
- [ ] 学术合规性检查通过（`make compliance`）
- [ ] Git 提交完成

---

## 📚 参考资料

- `ACADEMIC_STANDARDS.md` Lines 265-274 - 预设值使用限制
- `docs/final.md` Lines 157-159 - 研究环境完整性要求

---

**下一步**: 根据实际测试结果，可能需要修复 Stage 5 输出结构
**完成后**: 继续执行 [P0-3: D2 事件完整实现](../03_d2_event_implementation/)
