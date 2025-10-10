# P0-1: 移除 NTPUVisibilityCalculator（球形地球模型）

**优先级**: P0（立即修复）
**工作量**: 30分钟
**依据**: `ACADEMIC_STANDARDS.md` Lines 15-17

---

## 🚨 问题分析

### 违反条款
**ACADEMIC_STANDARDS.md Lines 15-17**:
> "不使用簡化版、基礎版、示範版算法，必須使用完整的學術標準算法"

### 当前实现问题
**文件**: `src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py`

```python
# Lines 5-8
⚠️ 幾何簡化說明:
- 使用球形地球模型（忽略 WGS84 扁率）
- 適用於快速估算，精度約 ±0.2° 仰角（台北地區）
```

### 精度对比

| 模型 | 实现 | 精度 | 学术标准 |
|------|------|------|----------|
| **球形地球** | NTPUVisibilityCalculator | ±0.2° | ❌ 简化算法 |
| **WGS84 椭球** | SkyfieldVisibilityCalculator | <0.01° | ✅ IAU 标准 |

---

## ✅ 解决方案

### 方案：移除简化实现，统一使用 Skyfield

**理由**:
1. ✅ 项目中已有完整实现（`SkyfieldVisibilityCalculator`）
2. ✅ 精度提升 20 倍（±0.2° → ±0.01°）
3. ✅ 符合学术标准（IAU SOFA）
4. ✅ 性能影响可接受（离线计算）

---

## 🔧 实施步骤

### 步骤 1: 检查引用（5分钟）

```bash
# 检查是否有文件引用 NTPUVisibilityCalculator
grep -r "NTPUVisibilityCalculator" src/ --include="*.py"
grep -r "from.*ntpu_visibility_calculator" src/ --include="*.py"
```

**预期结果**: 应该无引用或仅在测试中引用

### 步骤 2: 删除文件（1分钟）

```bash
# 删除简化实现
rm src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py
```

### 步骤 3: 更新文档（5分钟）

如果 Stage 4 文档中提到 `NTPUVisibilityCalculator`，更新为：

```markdown
## 可见性计算

使用 `SkyfieldVisibilityCalculator` 进行精确可见性计算：
- 完整 WGS84 椭球模型
- IAU SOFA 标准
- 精度 < 0.01° 仰角
```

### 步骤 4: 运行验证（15分钟）

```bash
# 1. 运行 Stage 4
./run.sh --stage 4

# 2. 检查输出是否正常
ls -lh data/outputs/stage4/

# 3. 验证可见性数据
jq '.metadata.visible_satellites_count' data/outputs/stage4/*.json

# 4. 运行学术合规性检查
make compliance
```

### 步骤 5: 提交修改（5分钟）

```bash
git add -A
git commit -m "refactor: Remove NTPUVisibilityCalculator (simplified spherical Earth model)

移除球形地球模型，统一使用 WGS84 椭球标准实现

- 删除: src/stages/stage4_link_feasibility/ntpu_visibility_calculator.py
- 原因: 违反 ACADEMIC_STANDARDS.md Lines 15-17（禁止简化算法）
- 替代: SkyfieldVisibilityCalculator（IAU 标准，精度 <0.01°）
- 依据: docs/ACADEMIC_STANDARDS.md, docs/final.md

学术合规性:
✅ 移除简化算法
✅ 使用官方 WGS84 椭球模型
✅ 精度提升 20 倍 (±0.2° → ±0.01°)
✅ 符合 Grade A 标准

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 📊 影响评估

### 代码变更
- ❌ 删除文件: `ntpu_visibility_calculator.py` (431 lines)
- ✅ 无需替换: 已使用 Skyfield 实现
- ✅ 无破坏性更改

### 性能影响
- 计算时间: 可能增加 5-10%（可接受）
- 精度提升: 20 倍
- 学术合规: 完全符合

### 风险评估
- **风险**: 无
- **理由**: SkyfieldVisibilityCalculator 已经过完整测试

---

## ✅ 验证清单

完成后检查：

- [ ] 文件已删除（`ntpu_visibility_calculator.py`）
- [ ] 无引用残留（`grep -r "NTPUVisibilityCalculator" src/`）
- [ ] Stage 4 运行正常（`./run.sh --stage 4`）
- [ ] 输出文件生成（`ls data/outputs/stage4/`）
- [ ] 学术合规性检查通过（`make compliance`）
- [ ] 文档已更新（如适用）
- [ ] Git 提交完成

---

## 📚 参考资料

- **WGS84 标准**: NIMA TR8350.2 (2000)
- **IAU SOFA**: Standards of Fundamental Astronomy
- **Skyfield 文档**: https://rhodesmill.org/skyfield/

---

**完成后**: 继续执行 [P1-1: 添加 GeometricPrefilter 警告标注](annotate_geometric_prefilter.md)
