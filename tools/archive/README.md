# Tools Archive

**归档日期**: 2025-10-10
**原因**: 工具未被项目文档引用或与其他工具功能重复

---

## 📦 归档结构

```
archive/
├── experimental/     # 实验性/增强版工具
└── deployment/       # 生产部署相关工具
```

---

## 🗂️ 归档工具清单

### experimental/ - 实验性工具

**deep_compliance_scanner.py** (20KB)
- **用途**: 深度学术合规扫描器
- **功能**:
  - AST 语法树分析
  - 配置文件检查（YAML/JSON）
  - 依赖关系分析
  - 语义分析
  - 交叉引用检查
- **归档原因**: 功能与 `academic_compliance_checker.py` 重复，为增强版但未被文档引用
- **状态**: 完整可用，可随时恢复
- **恢复方式**: `cp archive/experimental/deep_compliance_scanner.py ../`

**特点**:
- 更高级的检测能力（AST 分析）
- 检测隐藏的 mock 使用、测试模块泄漏
- 配置文件深度扫描
- 生成 JSON 格式详细报告

**如果需要更强大的合规检查**:
1. 恢复此工具到 tools/ 目录
2. 更新 CONTRIBUTING.md 引用此工具
3. 可选择替换 `academic_compliance_checker.py`

---

### deployment/ - 生产部署工具

**startup_optimizer.py** (13KB)
- **用途**: 容器启动性能优化器
- **功能**:
  - 预加载关键数据
  - 优化内存使用
  - 创建就绪探针（readiness probe）
  - 生成启动性能报告
- **归档原因**: 为 Docker/生产环境设计，当前项目为学术研究性质
- **状态**: 完整可用，可随时恢复
- **恢复方式**: `cp archive/deployment/startup_optimizer.py ../`

**适用场景**:
- Docker 容器化部署
- Kubernetes 环境
- 需要快速启动时间（<30s）
- 生产环境监控

**如果未来需要部署到生产环境**:
1. 恢复此工具
2. 更新 Dockerfile 集成此优化器
3. 配置 Kubernetes readiness/liveness probes

---

## ✅ 当前活跃工具

### tools/ 主目录（4个工具）

1. **academic_compliance_checker.py** (11KB)
   - 学术合规性自动检查
   - 被引用于: CONTRIBUTING.md, STAGE6_COMPLIANCE_CHECKLIST.md
   - 状态: ✅ 活跃使用

2. **validate_metadata_consistency.py** (11KB)
   - 元数据一致性验证
   - 被引用于: CODE_REVIEW_CHECKLIST.md, METADATA_CONSISTENCY_GUIDE.md
   - 状态: ✅ 活跃使用

3. **verify_documentation_sync.py** (8.5KB)
   - 文档与代码同步验证
   - 被引用于: CONTRIBUTING.md
   - 状态: ✅ 活跃使用

4. **pre-commit-academic.sh** (1.7KB)
   - Git pre-commit hook
   - 被引用于: CONTRIBUTING.md
   - 状态: ✅ 活跃使用

---

## 🔄 恢复归档工具

### 恢复单个工具
```bash
# 恢复深度合规扫描器
cp tools/archive/experimental/deep_compliance_scanner.py tools/

# 恢复启动优化器
cp tools/archive/deployment/startup_optimizer.py tools/
```

### 批量恢复
```bash
# 恢复所有实验性工具
cp tools/archive/experimental/*.py tools/

# 恢复所有部署工具
cp tools/archive/deployment/*.py tools/
```

---

## ⚠️ 使用建议

### deep_compliance_scanner.py vs academic_compliance_checker.py

**何时使用基础版（academic_compliance_checker.py）**:
- 日常开发检查
- Pre-commit hook
- 快速扫描

**何时使用增强版（deep_compliance_scanner.py）**:
- 发布前全面检查
- 代码审计
- 配置文件深度验证
- 需要详细 JSON 报告

**建议**: 可以两者并存
- 基础版用于日常开发
- 增强版用于重要里程碑检查

---

## 📝 维护记录

| 日期 | 操作 | 文件 | 原因 |
|------|------|------|------|
| 2025-10-10 | 归档 | deep_compliance_scanner.py | 未被文档引用 |
| 2025-10-10 | 归档 | startup_optimizer.py | 非学术研究需求 |
| 2025-10-10 | 删除 | QUICK_START.md | 与 docs/ 重复 |

---

**维护**: 定期检查（每 6 个月），评估是否需要恢复或永久删除
**联系**: 如有疑问，参考 `docs/development/CONTRIBUTING.md`
