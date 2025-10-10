# 🔧 Orbit Engine 学术合规性重构项目

**创建日期**: 2025-10-10
**目标**: 修复所有违反 `docs/ACADEMIC_STANDARDS.md` 的代码，实现完整的 D2 事件检测
**依据**: `docs/final.md` 研究目标和 3GPP TS 38.331 标准

---

## 📋 重构总览

### 🎯 核心目标

1. **符合学术标准**: 移除所有简化算法、预设值、硬编码参数
2. **完整实现 D2**: 基于地面距离（2D）而非 3D 斜距
3. **保持可追溯性**: 所有参数和算法有明确 SOURCE 标记
4. **达成研究目标**: 满足 `final.md` 的 3GPP 事件检测要求

### 🚨 需要修复的问题（按优先级）

| 优先级 | 问题 | 违反条款 | 影响 | 预估工作量 |
|--------|------|----------|------|-----------|
| **P0-1** | NTPUVisibilityCalculator 球形地球模型 | ACADEMIC_STANDARDS.md Lines 15-17 | 学术合规 | 30分钟 |
| **P0-2** | Stage 6 使用预设值 | ACADEMIC_STANDARDS.md Lines 265-274 | 学术合规 | 1小时 |
| **P0-3** | D2 事件距离测量错误 | 3GPP TS 38.331 Section 5.5.4.15a | 功能错误 | 2-3天 |
| **P1-1** | GeometricPrefilter 缺少警告 | 文档完善 | 可维护性 | 15分钟 |

### 📁 文件结构

```
refactoring/
├── README.md                                    # 本文件
├── 00_refactoring_plan.md                      # 详细重构计划
│
├── 01_remove_simplified_algorithms/             # P0-1, P1-1
│   ├── remove_ntpu_visibility_calculator.md    # 移除球形地球模型
│   └── annotate_geometric_prefilter.md         # 添加学术警告
│
├── 02_fix_stage6_defaults/                      # P0-2
│   ├── stage6_fail_fast_plan.md                # Fail-Fast 实现计划
│   └── stage6_processor_refactored.py          # 重构后的处理器
│
├── 03_d2_event_implementation/                  # P0-3
│   ├── d2_implementation_plan.md               # D2 实现计划
│   ├── coordinate_converter.py                  # ECEF → Geodetic 转换
│   ├── ground_distance_calculator.py            # Haversine/Vincenty 算法
│   ├── d2_event_detector_refactored.py         # 重构后的 D2 检测器
│   └── test_d2_implementation.py               # 单元测试
│
└── 04_integration/                              # 集成指南
    ├── integration_plan.md                      # 集成步骤
    ├── migration_guide.md                       # 迁移指南
    └── validation_checklist.md                  # 验证清单
```

---

## 🔄 重构执行顺序

### 阶段 1: P0-1 移除简化算法（30分钟）
1. 删除 `ntpu_visibility_calculator.py`
2. 更新所有引用为 `SkyfieldVisibilityCalculator`
3. 添加 `GeometricPrefilter` 学术警告标注

**输出**: 移除所有球形地球模型，统一使用 WGS84 椭球

### 阶段 2: P0-2 修复 Stage 6 预设值（1小时）
1. 重构 `stage6_research_optimization_processor.py`
2. 移除 `DEFAULT_ELEVATION_DEG`, `DISTANCE_UNREACHABLE`, `DEFAULT_LINK_MARGIN_DB`
3. 实现 Fail-Fast 机制（数据缺失时抛出错误）

**输出**: 符合 Grade A 标准的 Stage 6 处理器

### 阶段 3: P0-3 完整实现 D2 事件（2-3天）
1. 实现 ECEF → Geodetic 坐标转换
2. 实现 Haversine 地面距离计算
3. 重构 D2 事件检测器
4. 编写单元测试验证正确性

**输出**: 符合 3GPP TS 38.331 标准的 D2 事件检测

### 阶段 4: 集成与验证（1天）
1. 集成所有修改
2. 运行完整管道测试
3. 验证学术合规性
4. 更新文档

**输出**: 完全符合学术标准的 Orbit Engine

---

## ✅ 验证标准

### 学术合规性检查
```bash
# 运行学术合规性检查器
make compliance

# 或手动检查
python tools/academic_compliance_checker.py src/
```

### 功能正确性检查
```bash
# 运行完整管道
./run.sh

# 验证 D2 事件输出
jq '.gpp_events.d2_events | length' data/outputs/stage6/*.json
```

### 预期结果
- ✅ 所有简化算法已移除
- ✅ 所有预设值已替换为 Fail-Fast
- ✅ D2 事件使用正确的地面距离测量
- ✅ 通过 `make compliance` 检查
- ✅ 3GPP 事件总数 > 1,250（符合 final.md 要求）

---

## 📚 参考文档

- `docs/ACADEMIC_STANDARDS.md` - 学术合规性标准
- `docs/final.md` - 研究目标和验收标准
- `docs/ts.md` - 3GPP TS 38.331 标准摘录
- `docs/stages/stage6-research-optimization.md` - Stage 6 详细文档

---

## 🔗 快速导航

- [详细重构计划](00_refactoring_plan.md)
- [P0-1: 移除简化算法](01_remove_simplified_algorithms/)
- [P0-2: 修复预设值](02_fix_stage6_defaults/)
- [P0-3: D2 事件实现](03_d2_event_implementation/)
- [集成指南](04_integration/)

---

**维护者**: Orbit Engine Team
**最后更新**: 2025-10-10
