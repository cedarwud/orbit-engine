# P1-1: 添加 GeometricPrefilter 学术警告标注

**优先级**: P1（重要优化）
**工作量**: 15分钟
**依据**: 文档完善，防止误用

---

## 🎯 目标

为 `GeometricPrefilter` 添加明确的使用限制说明，防止在学术发表中误用简化算法结果。

---

## 📋 当前状态

**文件**: `src/stages/stage3_coordinate_transformation/geometric_prefilter.py`

**现有说明** (Lines 20-52):
```python
✅ 學術合規說明 (Grade A 標準):
==========================================
【簡化算法使用聲明】

本模組使用簡化 GMST 算法（Meeus 1998），而非完整 IAU SOFA 標準。
這是唯一的簡化項，並有明確的學術依據：

1. 模組定位: 優化預篩選器，非精確座標轉換
2. 誤差預算: ~60m RMS
3. 精確計算保證: 通過預篩選的衛星 100% 使用 Skyfield
```

**问题**: 虽有辩护，但缺少明确的**禁止用途**声明

---

## ✅ 解决方案

### 添加明确的禁止用途警告

在文件开头（Lines 1-10）添加：

```python
#!/usr/bin/env python3
"""
Stage 3 幾何預篩選器 - 快速可見性初步判斷

🎯 核心目標：
- 在精密 Skyfield 轉換前快速篩選明顯不可見的衛星
- 減少 77.5% 無效座標計算浪費（基於 Stage 4 基準數據）
- 使用快速幾何計算，無需完整 IERS/Skyfield 處理

⚠️ 重要原則：
- 寬鬆篩選，使用安全緩衝，避免誤篩可見衛星（false negatives）
- 只排除明顯不可見的衛星（地平線以下、距離過遠）
- 精確可見性判斷仍在 Stage 4 進行

🔬 幾何判斷方法：
1. 距離檢查：衛星是否在地面站合理通訊範圍內
2. 地平線檢查：衛星是否在地球背面（粗略幾何角度）
3. 高度檢查：排除明顯過低/過高的軌道異常

⚠️ 【禁止用途 - Grade A 標準】
==========================================
本模組僅用於性能優化，**禁止用於學術發表的結果計算**

❌ 禁止用途:
- 不可用於論文中的精確座標計算
- 不可用於學術發表的可見性結果
- 不可用於需要高精度的仰角/距離計算
- 不可引用本模組作為座標轉換方法

✅ 正確用途:
- 僅用於預篩選（減少後續計算量）
- 論文應引用 Skyfield + IERS 完整算法結果
- 可在「性能優化」章節說明預篩選機制

學術依據:
- 精確座標轉換: Skyfield v1.49 + IERS Bulletin A
- 預篩選誤差: ±60m RMS（在 3000km 閾值下可忽略 < 0.002%）
- 最終結果精度: < 0.5m (Grade A 標準)
==========================================
"""
```

---

## 🔧 实施步骤

### 步骤 1: 修改文件开头（10分钟）

```bash
# 编辑文件
vi src/stages/stage3_coordinate_transformation/geometric_prefilter.py

# 或使用 Edit 工具
```

将上述警告添加到文件开头的 docstring 中。

### 步骤 2: 验证语法（2分钟）

```bash
# 检查 Python 语法
python3 -m py_compile src/stages/stage3_coordinate_transformation/geometric_prefilter.py

# 运行 Stage 3 验证
./run.sh --stage 3
```

### 步骤 3: 提交修改（3分钟）

```bash
git add src/stages/stage3_coordinate_transformation/geometric_prefilter.py
git commit -m "docs: Add academic usage restrictions to GeometricPrefilter

添加明确的学术使用限制警告

修改内容:
- 添加「禁止用途」警告（不可用于学术发表结果）
- 明确「正确用途」（仅用于性能优化）
- 强调论文应引用 Skyfield 完整算法

学术合规性:
✅ 防止误用简化算法结果
✅ 明确模块定位（优化工具，非学术结果依据）
✅ 保持学术透明度

依据: docs/ACADEMIC_STANDARDS.md

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 📊 影响评估

### 代码变更
- ✅ 仅文档修改（无功能变更）
- ✅ 无破坏性更改
- ✅ 提升学术透明度

### 风险评估
- **风险**: 无
- **收益**: 防止误用，符合学术规范

---

## ✅ 验证清单

完成后检查：

- [ ] 警告已添加到文件开头
- [ ] Python 语法检查通过
- [ ] Stage 3 运行正常
- [ ] Git 提交完成

---

**完成后**: P0-1 阶段全部完成，继续执行 [P0-2: 修复 Stage 6 预设值](../02_fix_stage6_defaults/)
