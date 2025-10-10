# Contributing to Orbit Engine

**欢迎参与 Orbit Engine 学术研究项目！**

本指南整合了代码标准、文档同步流程、审查清单，确保所有贡献符合学术研究标准。

---

## 📋 目录

1. [学术合规性原则](#学术合规性原则)
2. [代码注释标准](#代码注释标准)
3. [文档同步流程](#文档同步流程)
4. [代码审查清单](#代码审查清单)
5. [提交流程](#提交流程)

---

## 🎓 学术合规性原则

### 核心原则（来自 ACADEMIC_STANDARDS.md）

**FORBIDDEN（绝对禁止）**：
- ❌ 简化/模拟算法或"基础模型"
- ❌ 随机/伪造数据生成（`np.random()`, `random.normal()`）
- ❌ 估计/假设值（无官方来源）
- ❌ 占位符实现或"临时"代码

**REQUIRED（必须遵守）**：
- ✅ 官方标准：ITU-R, 3GPP, IEEE, NASA JPL 精确规范
- ✅ 真实数据源：Space-Track.org TLE, 官方 API, 硬件接口
- ✅ 完整实现（包含学术引用）
- ✅ 所有参数可追溯到官方来源（使用 SOURCE 注释）

**代码编写前自检**：
1. ❓ 这是精确的官方规范吗？
2. ❓ 我使用的是真实数据还是生成伪数据？
3. ❓ 这能通过科学期刊的同行评审吗？
4. ❓ 每个参数都有文档记录其官方来源吗？

---

## 💬 代码注释标准

### 1. SOURCE 注释（必需）

**所有硬编码参数必须标注来源：**

```python
# ✅ 正确示例
elevation_threshold_deg = 5.0
# SOURCE: 3GPP TR 38.821 Section 6.1.2 - NTN minimum elevation for Starlink

atmospheric_scale_height_km = 8.5
# SOURCE: US Standard Atmosphere 1976, Table 1
# JUSTIFICATION: 指数大气模型标准参数

# ❌ 错误示例
elevation_threshold_deg = 5.0  # Starlink 门槛
# 问题：没有具体标准引用
```

### 2. 算法实现注释

```python
def calculate_atmospheric_attenuation(self, frequency_ghz: float, elevation_deg: float) -> float:
    """
    计算大气衰减

    SOURCE: ITU-R P.676-13 (2022) - Attenuation by atmospheric gases
    IMPLEMENTATION: Simplified oxygen/water vapor absorption model
    ACCURACY: ±0.5 dB for elevation > 10°
    ASSUMPTIONS:
      - Standard atmospheric conditions (US Standard Atmosphere 1976)
      - Dry air + water vapor partial pressure 7.5 g/m³

    Args:
        frequency_ghz: 频率 (GHz), valid range [1, 100]
        elevation_deg: 仰角 (degrees), valid range [5, 90]

    Returns:
        float: 大气衰减 (dB)
    """
```

### 3. 配置文件注释

```yaml
# config/stage5_signal_analysis_config.yaml

atmospheric_model:
  oxygen_absorption:
    a0: 7.19e-3  # dB/km
    # SOURCE: ITU-R P.676-13 Table 1, sea level, 20°C
    # UNIT: dB/km per GHz²

  water_vapor_absorption:
    b0: 0.05     # dB/km
    # SOURCE: ITU-R P.676-13 Section 2.2.2
    # CONDITIONS: 7.5 g/m³ water vapor density (standard atmosphere)
```

### 4. 禁止的注释模式

```python
# ❌ 使用禁止词
value = 100.0  # 假設值
value = 100.0  # 估計值
value = 100.0  # 簡化模型
value = 100.0  # 約 100

# ✅ 正确替代
value = 100.0  # SOURCE: Measured from hardware specification sheet
value = 100.0  # SOURCE: 3GPP TS 38.214 Section 5.1.2.1 Table 5.1.2.1-1
```

---

## 📚 文档同步流程

### 单一真相来源原则

**验证状态的唯一真相来源：**
- Stage 4: `docs/stages/STAGE4_VERIFICATION_MATRIX.md`
- Stage 6: `docs/stages/STAGE6_COMPLIANCE_CHECKLIST.md`

**规则：**
- ✅ 检查验证状态时**必须先读取矩阵文件**
- ❌ 禁止假设主文档声称的功能都已实现
- ✅ 修改验证状态时必须更新矩阵文件

### 添加新验证项目

**步骤：**

1. **更新验证矩阵**
   ```markdown
   | 7 | new_validation | processor.py:100-150 | ❌ 无 | ❌ | ⚠️ **未验证** | - |
   ```

2. **实现验证逻辑**（在 `scripts/run_six_stages_with_validation.py`）
   ```python
   def validate_new_feature(data):
       # ...验证逻辑
   ```

3. **更新脚本注释**
   ```python
   # ✅ 已实现: #7 new_validation (本段代码 850-900 行)
   ```

4. **更新矩阵状态**
   ```markdown
   | 7 | new_validation | processor.py:100-150 | validation.py:850-900 | ✅ | ✅ **已实现** | 2025-10-10 |
   ```

### 文档更新清单

每次修改代码后：
- [ ] 更新相关 stage 文档（如果架构改变）
- [ ] 更新验证矩阵（如果验证项目改变）
- [ ] 运行 `python3 tools/verify_documentation_sync.py --stage N`（如果可用）
- [ ] 确认所有引用的行号仍然正确

---

## ✅ 代码审查清单

### 提交前自查（必需）

**学术合规性：**
- [ ] ✅ 所有硬编码数字都有 SOURCE 标记
- [ ] ✅ 没有使用禁用词（假设、估计、简化、模拟）
- [ ] ✅ 所有算法实现有文献引用或标准引用
- [ ] ✅ 配置参数有来源说明

**代码质量：**
- [ ] ✅ 函数有完整 docstring（包含 SOURCE, ACCURACY 等）
- [ ] ✅ 复杂算法有实现说明和精度声明
- [ ] ✅ 边界条件有处理和验证
- [ ] ✅ 单位在注释中明确标注（km, degrees, dB 等）

**文档同步：**
- [ ] ✅ 验证矩阵已更新（如果适用）
- [ ] ✅ Stage 文档已同步（如果架构改变）
- [ ] ✅ CHANGELOG.md 已更新（如果是重大改动）

**测试：**
- [ ] ✅ 单元测试已添加/更新
- [ ] ✅ 集成测试通过
- [ ] ✅ 验证脚本通过（`./run.sh --stage N`）

### Code Review 时检查

**审查者清单：**

1. **检查 SOURCE 标记**
   ```bash
   # 查找所有硬编码数字
   grep -n "=\s*[0-9]" src/stages/stageN_*/*.py | grep -v "SOURCE\|来源"
   ```

2. **检查禁用词**
   ```bash
   # 中文禁用词
   grep -rn "假設\|估計\|約\|模擬\|簡化" src/stages/stageN_*/ --include="*.py"

   # 英文禁用词
   grep -rn "estimated\|assumed\|roughly\|simplified\|mock" src/stages/stageN_*/ --include="*.py"
   ```

3. **检查文档同步**
   - 验证矩阵中的行号是否正确
   - 主文档声称的功能是否真的实现
   - 配置文件是否与代码一致

4. **运行自动化工具**
   ```bash
   python tools/academic_compliance_checker.py src/stages/stageN_*/
   ```

---

## 🚀 提交流程

### 1. 开发阶段

```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 编写代码（遵循上述标准）
# ...

# 本地测试
./run.sh --stage N

# 自查清单（使用上述审查清单）
```

### 2. 提交前检查

```bash
# 运行合规性检查
python tools/academic_compliance_checker.py src/stages/stageN_*/

# 检查禁用词
grep -rn "假設\|估計\|約\|模擬\|簡化\|estimated\|assumed" src/stages/stageN_*/ --include="*.py"

# 运行完整测试（如果改动较大）
python scripts/run_six_stages_with_validation.py
```

### 3. Commit Message 格式

```
<type>(<scope>): <subject>

<body>

SOURCE: <官方标准引用>
VERIFICATION: <如何验证>
```

**示例：**
```
fix(stage5): Correct atmospheric attenuation calculation

- Replace simplified model with ITU-R P.676-13 exact formula
- Add 44+35 spectral line absorption (oxygen + water vapor)
- Update unit tests with ITU-R reference values

SOURCE: ITU-R P.676-13 (2022) Section 1, Annex 1
VERIFICATION: Validated against ITU-R test cases (±0.1 dB accuracy)
```

### 4. Pull Request

**PR Description 必须包含：**
- **目的**：解决什么问题或添加什么功能
- **变更内容**：代码和文档的主要变更
- **学术依据**：引用的官方标准或文献
- **验证方法**：如何验证正确性
- **审查清单**：勾选上述代码审查清单

**PR Template:**
```markdown
## 目的
[描述 PR 目的]

## 变更内容
- [ ] 代码变更：...
- [ ] 文档更新：...
- [ ] 测试添加：...

## 学术依据
SOURCE: [引用官方标准]
- [具体章节和页码]

## 验证方法
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 合规性检查通过

## 审查清单
- [ ] 所有参数有 SOURCE 标记
- [ ] 无禁用词
- [ ] 文档已同步
- [ ] 验证矩阵已更新
```

---

## 🛠️ 开发工具

### 自动化检查工具

1. **学术合规性检查器**
   ```bash
   python tools/academic_compliance_checker.py <directory>
   ```

2. **文档同步验证器**（如果可用）
   ```bash
   python tools/verify_documentation_sync.py --stage N
   ```

3. **Pre-commit Hook**（推荐安装）
   ```bash
   cp tools/pre-commit-academic.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

### 快速参考

**常用标准文档：**
- 3GPP TS 38.331: RRC protocol (handover events)
- 3GPP TR 38.821: NTN solutions
- ITU-R P.676: Atmospheric attenuation
- ITU-R P.525: Free-space propagation
- NASA JPL: DE421 ephemeris

**在线资源：**
- 3GPP Portal: https://portal.3gpp.org/
- ITU-R Recommendations: https://www.itu.int/rec/R-REC/
- Space-Track.org: https://www.space-track.org/

---

## 📞 获取帮助

**问题优先级：**
1. **CRITICAL 违规**：立即停止，优先修正
2. **学术合规性疑问**：查阅 `docs/ACADEMIC_STANDARDS.md`
3. **实现技术问题**：查阅相关 `docs/stages/stageN-*.md`
4. **流程问题**：本文档或询问维护者

**联系方式：**
- GitHub Issues: [项目 Issues 页面]
- 文档：`docs/` 目录下各主题文档

---

## 🎯 核心原则总结

> **学术研究的严谨性不能依赖"人的自觉"，**
> **必须建立在"系统性的强制检查"之上。**

**记住：**
- 一个"估计"值 = 整个研究可能被质疑
- 零容忍 = 零质疑
- SOURCE 注释 = 学术可信度

---

**维护**: Orbit Engine Team
**版本**: v1.0
**最后更新**: 2025-10-10

**相关文档：**
- [ACADEMIC_STANDARDS.md](../ACADEMIC_STANDARDS.md) - 详细学术标准
- [STAGE4_VERIFICATION_MATRIX.md](../stages/STAGE4_VERIFICATION_MATRIX.md) - Stage 4 验证状态
- [STAGE6_COMPLIANCE_CHECKLIST.md](../stages/STAGE6_COMPLIANCE_CHECKLIST.md) - Stage 6 合规清单
