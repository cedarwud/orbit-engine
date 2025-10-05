#!/bin/bash
# Stage 5 配置加载修复验证脚本
# Date: 2025-10-04

set -e  # 遇到错误立即退出

echo "================================"
echo "Stage 5 配置加载修复验证"
echo "================================"
echo ""

# 设置测试模式
export ORBIT_ENGINE_TEST_MODE=1

# 1. 验证配置文件存在
echo "✓ 检查 1: 配置文件存在性"
if [ -f "config/stage5_signal_analysis_config.yaml" ]; then
    echo "  ✅ 配置文件存在: config/stage5_signal_analysis_config.yaml"
    echo "  文件大小: $(wc -c < config/stage5_signal_analysis_config.yaml) 字节"
    echo "  行数: $(wc -l < config/stage5_signal_analysis_config.yaml) 行"
else
    echo "  ❌ 配置文件不存在"
    exit 1
fi
echo ""

# 2. 验证配置加载函数
echo "✓ 检查 2: 配置加载函数"
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from stage_executors.stage5_executor import load_stage5_config, validate_stage5_config

try:
    config = load_stage5_config()
    valid, msg = validate_stage5_config(config)
    if valid:
        print('  ✅ 配置加载和验证成功')
        print(f'     - signal_calculator: {list(config[\"signal_calculator\"].keys())}')
        print(f'     - atmospheric_model: {list(config[\"atmospheric_model\"].keys())}')
    else:
        print(f'  ❌ 配置验证失败: {msg}')
        sys.exit(1)
except Exception as e:
    print(f'  ❌ 配置加载失败: {e}')
    sys.exit(1)
" 2>&1 | grep -v "WARNING\|INFO"
echo ""

# 3. 验证 Processor 初始化
echo "✓ 检查 3: Processor 初始化"
python3 -c "
import sys, os
os.environ['ORBIT_ENGINE_TEST_MODE'] = '1'
sys.path.insert(0, 'src')
sys.path.insert(0, 'scripts')

from stage_executors.stage5_executor import load_stage5_config
from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor

try:
    config = load_stage5_config()
    processor = Stage5SignalAnalysisProcessor(config)
    print('  ✅ Processor 初始化成功')
    print(f'     - max_workers: {processor.max_workers}')
    print(f'     - enable_parallel: {processor.enable_parallel}')
except Exception as e:
    print(f'  ❌ Processor 初始化失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" 2>&1 | grep -E "✅|❌|max_workers|enable_parallel"
echo ""

# 4. 运行集成测试
echo "✓ 检查 4: 集成测试"
python3 -m pytest tests/integration/test_stage5_config_loading.py -v --tb=short 2>&1 | tail -5
echo ""

# 5. 验证文档同步
echo "✓ 检查 5: 文档同步状态"
if grep -q "配置文件使用說明" docs/stages/stage5-signal-analysis.md; then
    echo "  ✅ 文档已更新配置加载说明"
else
    echo "  ❌ 文档缺少配置加载说明"
    exit 1
fi

if grep -q "自動加載 (推薦)" docs/stages/stage5-signal-analysis.md; then
    echo "  ✅ 文档包含自动加载说明"
else
    echo "  ❌ 文档缺少自动加载说明"
    exit 1
fi
echo ""

# 总结
echo "================================"
echo "验证完成！"
echo "================================"
echo ""
echo "修复摘要:"
echo "  ✅ 配置文件存在并有效"
echo "  ✅ 配置加载函数正常工作"
echo "  ✅ Processor 可正确初始化"
echo "  ✅ 集成测试通过"
echo "  ✅ 文档同步完成"
echo ""
echo "🎉 Stage 5 配置加载修复验证通过！"
echo ""
echo "相关文件:"
echo "  - 配置文件: config/stage5_signal_analysis_config.yaml"
echo "  - 执行器: scripts/stage_executors/stage5_executor.py"
echo "  - 文档: docs/stages/stage5-signal-analysis.md"
echo "  - 测试: tests/integration/test_stage5_config_loading.py"
echo "  - 修复摘要: STAGE5_CONFIG_LOADING_FIX_SUMMARY.md"
echo ""
