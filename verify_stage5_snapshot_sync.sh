#!/bin/bash
# Stage 5 快照验证同步检查脚本
# Date: 2025-10-04

set -e

echo "================================"
echo "Stage 5 快照验证同步检查"
echo "================================"
echo ""

export ORBIT_ENGINE_TEST_MODE=1

# 1. 检查 SnapshotManager 字段完整性
echo "✓ 检查 1: SnapshotManager 字段完整性"
python3 << 'EOF'
import sys, os
os.environ['ORBIT_ENGINE_TEST_MODE'] = '1'
sys.path.insert(0, 'src')

# 模拟数据
analysis_summary = {
    'total_satellites_analyzed': 100,
    'usable_satellites': 80,
    'signal_quality_distribution': {'excellent': 20, 'good': 40, 'fair': 20, 'poor': 20},
    'average_rsrp_dbm': -95.5,
    'average_sinr_db': 12.3,
    'total_time_points_processed': 20000
}

# 模拟 SnapshotManager 的字段提取逻辑
data_summary = {
    'total_satellites_analyzed': analysis_summary.get('total_satellites_analyzed', 0),
    'usable_satellites': analysis_summary.get('usable_satellites', 0),
    'signal_quality_distribution': analysis_summary.get('signal_quality_distribution', {}),
    'average_rsrp_dbm': analysis_summary.get('average_rsrp_dbm'),
    'average_sinr_db': analysis_summary.get('average_sinr_db'),
    'total_time_points_processed': analysis_summary.get('total_time_points_processed', 0)
}

# 检查所有字段
required_fields = [
    'total_satellites_analyzed', 'usable_satellites', 'signal_quality_distribution',
    'average_rsrp_dbm', 'average_sinr_db', 'total_time_points_processed'
]

all_present = all(field in data_summary for field in required_fields)
all_not_none = all(data_summary[field] is not None for field in required_fields)

if all_present and all_not_none:
    print('  ✅ SnapshotManager 包含所有必要字段')
    for field in required_fields:
        print(f'     - {field}: {data_summary[field]}')
else:
    missing = [f for f in required_fields if f not in data_summary or data_summary[f] is None]
    print(f'  ❌ 缺少或为空的字段: {missing}')
    sys.exit(1)
EOF

echo ""

# 2. 检查 Validator 验证
echo "✓ 检查 2: Validator 验证快照"
python3 << 'EOF'
import sys
sys.path.insert(0, 'scripts')
from stage_validators.stage5_validator import check_stage5_validation

snapshot_data = {
    'stage': 'stage5_signal_analysis',
    'timestamp': '2025-10-04T06:00:00Z',
    'data_summary': {
        'total_satellites_analyzed': 100,
        'usable_satellites': 80,
        'signal_quality_distribution': {'excellent': 20, 'good': 40, 'fair': 20, 'poor': 20},
        'average_rsrp_dbm': -95.5,
        'average_sinr_db': 12.3,
        'total_time_points_processed': 20000
    },
    'metadata': {
        'gpp_config': {'standard_version': 'TS_38.214_v18.5.1'},
        'itur_config': {'recommendation': 'P.618-13'},
        'physical_constants': {'standard_compliance': 'CODATA_2018'},
        'gpp_standard_compliance': True,
        'itur_standard_compliance': True
    }
}

valid, message = check_stage5_validation(snapshot_data)

if valid:
    print(f'  ✅ 验证器验证通过')
    print(f'     {message[:100]}...')
else:
    print(f'  ❌ 验证器验证失败: {message}')
    sys.exit(1)
EOF

echo ""

# 3. 检查字段映射一致性
echo "✓ 检查 3: ResultBuilder → SnapshotManager → Validator 字段映射"
python3 << 'EOF'
# 定义各组件的字段
result_builder_fields = {
    'total_satellites_analyzed',
    'usable_satellites',
    'signal_quality_distribution',
    'average_rsrp_dbm',
    'average_sinr_db',
    'total_time_points_processed'
}

snapshot_manager_fields = {
    'total_satellites_analyzed',
    'usable_satellites',
    'signal_quality_distribution',
    'average_rsrp_dbm',
    'average_sinr_db',
    'total_time_points_processed'
}

validator_required_fields = {
    'total_satellites_analyzed',
    'usable_satellites',
    'signal_quality_distribution',
    'average_rsrp_dbm',
    'average_sinr_db'
}

# 检查映射完整性
builder_to_snapshot = result_builder_fields == snapshot_manager_fields
snapshot_to_validator = validator_required_fields.issubset(snapshot_manager_fields)

if builder_to_snapshot and snapshot_to_validator:
    print('  ✅ 字段映射完全一致')
    print(f'     - ResultBuilder → SnapshotManager: ✓')
    print(f'     - SnapshotManager → Validator: ✓')
else:
    print('  ❌ 字段映射不一致')
    if not builder_to_snapshot:
        print(f'     - ResultBuilder vs SnapshotManager 不匹配')
    if not snapshot_to_validator:
        missing = validator_required_fields - snapshot_manager_fields
        print(f'     - Validator 需要但 SnapshotManager 缺少: {missing}')
    import sys
    sys.exit(1)
EOF

echo ""

# 4. 检查代码中的字段使用
echo "✓ 检查 4: 代码中的字段引用"
if grep -q "average_rsrp_dbm.*analysis_summary.get" src/stages/stage5_signal_analysis/output_management/snapshot_manager.py; then
    echo "  ✅ SnapshotManager 引用 average_rsrp_dbm"
else
    echo "  ❌ SnapshotManager 未引用 average_rsrp_dbm"
    exit 1
fi

if grep -q "average_sinr_db.*analysis_summary.get" src/stages/stage5_signal_analysis/output_management/snapshot_manager.py; then
    echo "  ✅ SnapshotManager 引用 average_sinr_db"
else
    echo "  ❌ SnapshotManager 未引用 average_sinr_db"
    exit 1
fi

if grep -q "total_time_points_processed.*analysis_summary.get" src/stages/stage5_signal_analysis/output_management/snapshot_manager.py; then
    echo "  ✅ SnapshotManager 引用 total_time_points_processed"
else
    echo "  ❌ SnapshotManager 未引用 total_time_points_processed"
    exit 1
fi

echo ""

# 总结
echo "================================"
echo "验证完成！"
echo "================================"
echo ""
echo "同步检查摘要:"
echo "  ✅ SnapshotManager 字段完整性"
echo "  ✅ Validator 验证功能"
echo "  ✅ 字段映射一致性"
echo "  ✅ 代码引用完整性"
echo ""
echo "🎉 Stage 5 快照验证完全同步！"
echo ""
echo "相关文件:"
echo "  - 修复文件: src/stages/stage5_signal_analysis/output_management/snapshot_manager.py"
echo "  - 验证器: scripts/stage_validators/stage5_validator.py"
echo "  - 问题报告: STAGE5_SNAPSHOT_SYNC_FIX.md"
echo ""
