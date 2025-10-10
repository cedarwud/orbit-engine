# 📋 Orbit Engine 学术合规性重构详细计划

**版本**: 1.0
**日期**: 2025-10-10
**作者**: Orbit Engine Team

---

## 🎯 重构目标

### 核心原则
1. **完全符合学术标准**: 移除所有违反 `ACADEMIC_STANDARDS.md` 的代码
2. **功能正确性**: 修复所有根本性错误（如 D2 距离测量）
3. **可追溯性**: 所有参数和算法有明确来源
4. **保持向后兼容**: 不破坏现有管道的正常运行

### 成功标准
- ✅ 通过 `make compliance` 学术合规性检查
- ✅ D2 事件使用正确的地面距离测量
- ✅ 所有预设值替换为 Fail-Fast 机制
- ✅ 3GPP 事件总数 > 1,250（满足 `final.md` 要求）
- ✅ 所有单元测试通过

---

## 🚨 问题分析

### P0-1: NTPUVisibilityCalculator 使用球形地球模型

**文件位置**: `src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py`

**问题描述**:
```python
# Lines 5-8
⚠️ 幾何簡化說明:
- 使用球形地球模型（忽略 WGS84 扁率）
- 適用於快速估算，精度約 ±0.2° 仰角
```

**违反条款**: `ACADEMIC_STANDARDS.md` Lines 15-17
> "不使用簡化版、基礎版、示範版算法，必須使用完整的學術標準算法"

**修复方案**:
1. 删除 `ntpu_visibility_calculator.py`
2. 更新所有引用为 `SkyfieldVisibilityCalculator`（已有完整实现）
3. 确保使用 WGS84 椭球模型（精度 < 0.01°）

**影响范围**: Stage 4 可见性计算

**工作量**: 30分钟

---

### P0-2: Stage 6 使用保守估计预设值

**文件位置**: `src/stages/stage6_research_optimization/stage6_research_optimization_processor.py`

**问题描述**:
```python
# Lines 99-121
DEFAULT_ELEVATION_DEG = 45.0        # 保守估计
DISTANCE_UNREACHABLE = 9999.0       # 标记值
DEFAULT_LINK_MARGIN_DB = 10.0       # 保守估计

# Lines 461-479 使用预设值
elevation_deg = visibility_metrics.get('elevation_deg', self.DEFAULT_ELEVATION_DEG)
```

**违反条款**: `ACADEMIC_STANDARDS.md` Lines 265-274
> "系統參數（頻寬、噪聲係數等）禁止使用預設值"
> "❌ 錯誤: self.config.get('noise_figure_db', 7.0)"
> "✅ 正確: 必須在配置中提供，或拋出錯誤"

**修复方案**:
```python
# ✅ Fail-Fast 实现
if 'elevation_deg' not in visibility_metrics:
    raise ValueError(
        f"衛星 {satellite_id} 缺少 elevation_deg 數據\n"
        f"Grade A 標準禁止使用預設值（ACADEMIC_STANDARDS.md Lines 265-274）\n"
        f"請確保 Stage 5 提供完整數據"
    )
elevation_deg = visibility_metrics['elevation_deg']
```

**影响范围**: Stage 6 数据快照提取

**工作量**: 1小时

---

### P0-3: D2 事件使用错误的距离测量

**文件位置**: `src/stages/stage6_research_optimization/gpp_event_detector.py`

**问题描述**:
```python
# Lines 463, 476 - 当前实现
serving_distance = serving_satellite['physical_parameters']['distance_km']
neighbor_distance = neighbor['physical_parameters']['distance_km']
# ❌ 这是 3D 斜距（UE → 卫星直线距离）
```

**3GPP 标准要求** (`docs/ts.md` Lines 145-150):
```
Ml1 = distance between UE and a **moving reference location**
      └─ Moving reference location 基于:
         ├─ movingReferenceLocation 参数
         ├─ Epoch time
         └─ 服务小区的**卫星星历** (broadcast in SIB19)

Ml2 = distance between UE and a **moving reference location**
      └─ 基于 referenceLocation 和卫星星历
```

**正确实现**:
1. 计算卫星的地面投影点（sub-satellite point）
2. 使用 Haversine 公式计算 UE 到地面投影点的大圆距离
3. 单位：米（不是公里）

**场景对比**:
| 场景 | 3D 斜距（错误） | 2D 地面距离（正确） | 误差 |
|------|----------------|-------------------|------|
| 卫星在头顶 (90° 仰角) | 550 km | ~0 km | 550 km |
| 地平线附近 (5° 仰角) | ~2300 km | ~2000 km | 300 km |

**修复方案**:
1. 实现 ECEF → Geodetic 坐标转换
2. 实现 Haversine 地面距离计算
3. 修改 `detect_d2_events` 使用正确的距离

**影响范围**: Stage 6 D2 事件检测

**工作量**: 2-3天

---

### P1-1: GeometricPrefilter 缺少学术警告

**文件位置**: `src/stages/stage3_coordinate_transformation/geometric_prefilter.py`

**问题描述**:
虽然有学术辩护（Lines 20-52），但缺少明确的使用限制说明

**修复方案**:
添加更明确的警告标注：
```python
"""
⚠️ 【禁止用途 - Grade A 标准】
- ❌ 不可用于论文中的精确座标计算
- ❌ 不可用于学术发表的可见性结果
- ✅ 僅用於性能優化（減少 77.5% 計算量）
"""
```

**影响范围**: 文档完善

**工作量**: 15分钟

---

## 📅 实施时间表

### 第 1 天: P0-1 移除简化算法
- [ ] 8:00-8:30  - 删除 `ntpu_visibility_calculator.py`
- [ ] 8:30-9:00  - 更新引用为 `SkyfieldVisibilityCalculator`
- [ ] 9:00-9:15  - 添加 `GeometricPrefilter` 警告标注
- [ ] 9:15-9:30  - 运行测试验证

### 第 1 天: P0-2 修复 Stage 6 预设值
- [ ] 9:30-10:00 - 分析所有使用预设值的位置
- [ ] 10:00-11:00 - 实现 Fail-Fast 机制
- [ ] 11:00-11:30 - 编写单元测试
- [ ] 11:30-12:00 - 运行 Stage 6 验证

### 第 2-4 天: P0-3 完整实现 D2 事件

**第 2 天**: 基础组件开发
- [ ] 9:00-10:30 - 实现 `coordinate_converter.py`
- [ ] 10:30-12:00 - 实现 `ground_distance_calculator.py`
- [ ] 14:00-16:00 - 编写单元测试
- [ ] 16:00-17:00 - 验证测试通过

**第 3 天**: D2 检测器重构
- [ ] 9:00-12:00 - 重构 `detect_d2_events` 方法
- [ ] 14:00-16:00 - 集成地面距离计算
- [ ] 16:00-17:00 - 编写集成测试

**第 4 天**: 验证与文档
- [ ] 9:00-11:00 - 运行完整管道测试
- [ ] 11:00-12:00 - 验证 D2 事件正确性
- [ ] 14:00-16:00 - 更新文档
- [ ] 16:00-17:00 - 学术合规性检查

### 第 5 天: 集成与发布
- [ ] 9:00-11:00 - 集成所有修改
- [ ] 11:00-12:00 - 运行完整测试套件
- [ ] 14:00-16:00 - 编写迁移指南
- [ ] 16:00-17:00 - 准备发布

---

## 🔧 技术实施细节

### P0-1 实施步骤

```bash
# 1. 删除简化算法文件
rm src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py

# 2. 检查所有引用
grep -r "NTPUVisibilityCalculator" src/

# 3. 更新为 Skyfield
# 如果有引用，全部改为 SkyfieldVisibilityCalculator

# 4. 验证
./run.sh --stage 4
```

### P0-2 实施步骤

修改位置：
1. `stage6_research_optimization_processor.py:99-121` - 删除预设值常量
2. `stage6_research_optimization_processor.py:461-479` - 实现 Fail-Fast

```python
# 修改前
elevation_deg = visibility_metrics.get('elevation_deg', self.DEFAULT_ELEVATION_DEG)

# 修改后
if 'elevation_deg' not in visibility_metrics:
    raise ValueError(f"缺少 elevation_deg，违反 Grade A 标准")
elevation_deg = visibility_metrics['elevation_deg']
```

### P0-3 实施步骤

新增文件：
1. `refactoring/03_d2_event_implementation/coordinate_converter.py`
2. `refactoring/03_d2_event_implementation/ground_distance_calculator.py`
3. `refactoring/03_d2_event_implementation/d2_event_detector_refactored.py`

修改文件：
1. `src/stages/stage6_research_optimization/gpp_event_detector.py`

---

## ✅ 验证清单

### 学术合规性验证
- [ ] 无简化算法（`grep -r "simplified\|簡化" src/`）
- [ ] 无预设值（`grep -r "get.*default\|預設" src/`）
- [ ] 无硬编码（所有数值有 SOURCE 标记）
- [ ] 通过 `make compliance` 检查

### 功能正确性验证
- [ ] D2 事件使用地面距离（2D）
- [ ] 3GPP 事件总数 > 1,250
- [ ] Stage 4 可见性计算精度 < 0.01°
- [ ] Stage 6 数据缺失时正确抛出错误

### 测试覆盖率验证
- [ ] 所有新函数有单元测试
- [ ] 集成测试通过
- [ ] 回归测试通过

---

## 📊 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| D2 实现复杂度超预期 | 中 | 高 | 提前 1 天，分阶段实施 |
| Stage 5 数据不完整 | 低 | 中 | Fail-Fast 会暴露问题，及时修复 |
| 性能下降（移除简化算法） | 低 | 低 | 离线计算，性能影响可接受 |
| 破坏现有功能 | 低 | 高 | 完整测试套件保障 |

---

## 📚 参考资料

- 3GPP TS 38.331 v18.5.1 - D2 事件标准定义
- WGS84 NIMA TR8350.2 - 椭球模型参数
- Haversine formula - 地面大圆距离计算
- Vincenty formula - 高精度地面距离（可选）

---

**下一步**: 开始执行 [P0-1: 移除简化算法](01_remove_simplified_algorithms/)
