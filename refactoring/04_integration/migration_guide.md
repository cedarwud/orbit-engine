# 🚀 学术合规性重构迁移指南

**版本**: 1.0
**日期**: 2025-10-10

---

## 📋 迁移概览

本指南帮助您将学术合规性重构集成到主代码库。

###总体变更
- ❌ 删除: `ntpu_visibility_calculator.py` (球形地球模型)
- ✅ 修改: `stage6_research_optimization_processor.py` (Fail-Fast)
- ✅ 修改: `gpp_event_detector.py` (D2 地面距离)
- ✅ 新增: `coordinate_converter.py`, `ground_distance_calculator.py`
- ✅ 文档: `geometric_prefilter.py` (添加警告)

---

## 🔄 迁移步骤（按顺序）

### 步骤 1: P0-1 移除简化算法 (30分钟)

```bash
# 1. 删除球形地球模型
rm src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py

# 2. 检查无残留引用
grep -r "NTPUVisibilityCalculator" src/

# 3. 运行 Stage 4 验证
./run.sh --stage 4

# 4. 添加 GeometricPrefilter 警告（见下文代码）
```

**编辑**: `src/stages/stage3_coordinate_transformation/geometric_prefilter.py`

在文件开头 docstring 添加：
```python
⚠️ 【禁止用途 - Grade A 標準】
==========================================
本模組僅用於性能優化，**禁止用於學術發表的結果計算**

❌ 禁止用途:
- 不可用於論文中的精確座標計算
- 不可用於學術發表的可見性結果
- 不可引用本模組作為座標轉換方法

✅ 正確用途:
- 僅用於預篩選（減少後續計算量）
- 論文應引用 Skyfield + IERS 完整算法結果
==========================================
```

### 步骤 2: P0-2 修复 Stage 6 预设值 (1小时)

**编辑**: `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py`

**修改 1**: 删除预设值常量 (Lines 99-121)
```python
# ❌ 删除这些行
# DEFAULT_ELEVATION_DEG = 45.0
# DISTANCE_UNREACHABLE = 9999.0
# DEFAULT_LINK_MARGIN_DB = 10.0
```

**修改 2**: `_extract_latest_snapshot` Fail-Fast (Lines 449-479)
```python
# ✅ 修改所有预设值使用为 Fail-Fast
if 'distance_km' not in physical_parameters:
    raise ValueError(
        f"衛星 {satellite_id} physical_parameters 缺少 distance_km\n"
        f"Grade A 標準禁止使用預設值（ACADEMIC_STANDARDS.md Lines 265-274）\n"
        f"請確保 Stage 5 提供完整數據"
    )
```

**修改 3**: 添加错误处理 (Line 548)
```python
try:
    candidate_snapshot = self._extract_latest_snapshot(sat_id, sat_data)
    candidate_satellites.append(candidate_snapshot)
except ValueError as e:
    self.logger.warning(f"候选衛星 {sat_id} 數據不完整，跳過: {e}")
    continue
```

**测试**:
```bash
./run.sh --stage 6
# 如果出错，检查 Stage 5 输出是否包含所有必需字段
```

### 步骤 3: P0-3 D2 事件完整实现 (2-3天)

#### 3.1 复制新模块到 Stage 6
```bash
cp refactoring/03_d2_event_implementation/coordinate_converter.py \
   src/stages/stage6_research_optimization/

cp refactoring/03_d2_event_implementation/ground_distance_calculator.py \
   src/stages/stage6_research_optimization/
```

#### 3.2 修改 `gpp_event_detector.py`

**添加导入** (在文件开头):
```python
from .coordinate_converter import ecef_to_geodetic
from .ground_distance_calculator import haversine_distance
```

**重构 `detect_d2_events`** (Lines 431-510):
```python
def detect_d2_events(self, serving_satellite, neighbor_satellites):
    \"\"\"檢測 D2 事件: 基於地面距離的換手觸發\"\"\"

    # NTPU 地面站座標 - SOURCE: GPS Survey 2025-10-02
    UE_LAT = 24.94388888  # 24°56'38"N
    UE_LON = 121.37083333  # 121°22'15"E

    # 3GPP 標準參數 (單位：米)
    threshold1_m = self.config['d2_threshold1_km'] * 1000
    threshold2_m = self.config['d2_threshold2_km'] * 1000
    hysteresis_m = self.config['hysteresis_km'] * 1000

    # 計算服務衛星地面距離
    serving_ecef = serving_satellite['physical_parameters']['position_ecef_m']
    serving_lat, serving_lon, _ = ecef_to_geodetic(*serving_ecef)
    serving_ground_dist_m = haversine_distance(UE_LAT, UE_LON, serving_lat, serving_lon)

    # D2-1 條件檢查
    if (serving_ground_dist_m - hysteresis_m) <= threshold1_m:
        return []  # 服務衛星距離尚可

    # 檢查鄰居衛星
    d2_events = []
    for neighbor in neighbor_satellites:
        neighbor_ecef = neighbor['physical_parameters']['position_ecef_m']
        neighbor_lat, neighbor_lon, _ = ecef_to_geodetic(*neighbor_ecef)
        neighbor_ground_dist_m = haversine_distance(UE_LAT, UE_LON, neighbor_lat, neighbor_lon)

        # D2-2 條件
        if (neighbor_ground_dist_m + hysteresis_m) < threshold2_m:
            # 觸發 D2 事件...
```

#### 3.3 确保 Stage 5 提供 ECEF 位置

**检查**: Stage 5 是否输出 `position_ecef_m`？

```bash
jq '.signal_analysis | to_entries[0].value.time_series[0].physical_parameters' \
   data/outputs/stage5/*.json
```

**如果没有**: 需要修改 Stage 5 添加 ECEF 位置字段。

### 步骤 4: 完整测试 (1天)

```bash
# 1. 运行完整管道
./run.sh

# 2. 检查所有 6 个阶段输出
ls -lh data/outputs/stage{1..6}/

# 3. 验证 D2 事件
jq '.gpp_events | {
  a3: (.a3_events | length),
  a4: (.a4_events | length),
  a5: (.a5_events | length),
  d2: (.d2_events | length)
}' data/outputs/stage6/*.json

# 4. 学术合规性检查
make compliance

# 5. 验证事件总数 > 1,250
jq '.gpp_events.total_events' data/outputs/stage6/*.json
```

---

## ✅ 验证清单

迁移完成后确认：

### 功能正确性
- [ ] Stage 4 使用 WGS84 椭球模型（无球形地球）
- [ ] Stage 6 数据缺失时正确抛出 ValueError
- [ ] D2 事件使用地面距离（2D，单位：米）
- [ ] 所有 6 个阶段正常运行

### 学术合规性
- [ ] 无简化算法（`grep -r "simplified\|簡化" src/`）
- [ ] 无预设值（`grep -r "DEFAULT_.*=" src/ | grep -v "# "`）
- [ ] 通过 `make compliance` 检查
- [ ] 所有参数有 SOURCE 标记

### 输出质量
- [ ] 3GPP 事件总数 > 1,250
- [ ] D2 事件距离合理（服务 > 2000m，鄰居 < 1500m）
- [ ] 无异常值或错误数据

---

## 🐛 常见问题

### Q1: Stage 6 报错"缺少 elevation_deg"
**原因**: Stage 5 没有提供仰角数据
**解决**: 检查 Stage 5 输出，确保包含 `physical_parameters.elevation_deg`

### Q2: D2 事件报错"缺少 position_ecef_m"
**原因**: Stage 5 没有提供 ECEF 位置
**解决**: 修改 Stage 5 添加 ECEF 位置字段，或从现有数据推导

### Q3: 学术合规性检查失败
**原因**: 仍有简化算法或预设值残留
**解决**: 运行 `grep -r "estimated\|assumed\|DEFAULT" src/` 检查

---

## 📊 预期性能影响

| 指标 | 修改前 | 修改后 | 变化 |
|------|--------|--------|------|
| **Stage 4 精度** | ±0.2° | <0.01° | +20倍 |
| **Stage 4 速度** | 基准 | +5-10% | 可接受 |
| **D2 事件数** | ~438 (错误) | ~200-300 (正确) | 正常 |
| **学术合规** | ❌ 部分违反 | ✅ 完全符合 | +100% |

---

## 🚀 部署建议

### 开发环境
1. 在独立分支测试所有修改
2. 运行完整测试套件
3. 验证输出质量

### 生产环境
1. 备份现有输出数据
2. 分阶段迁移（P0-1 → P0-2 → P0-3）
3. 每阶段验证后再继续

---

## 📞 支持

遇到问题请参考：
- `refactoring/00_refactoring_plan.md` - 详细技术计划
- `docs/ACADEMIC_STANDARDS.md` - 学术标准要求
- `docs/final.md` - 研究目标

---

**最后更新**: 2025-10-10
**维护者**: Orbit Engine Team
