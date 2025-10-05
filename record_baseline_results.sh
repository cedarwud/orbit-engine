#!/bin/bash
# 記錄 Stage 4 單線程執行基準結果
# 用於後續與多核並行結果比對

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASELINE_DIR="baseline_single_thread_$TIMESTAMP"

echo "========================================"
echo "記錄 Stage 4 單線程執行基準結果"
echo "========================================"
echo ""

# 創建基準結果目錄
mkdir -p "baselines/$BASELINE_DIR"

echo "📊 複製輸出文件..."

# 複製 Stage 4 輸出
if [ -f data/outputs/stage4/stage4_link_analysis_*.json ]; then
    STAGE4_OUTPUT=$(ls -t data/outputs/stage4/stage4_link_analysis_*.json | head -1)
    cp "$STAGE4_OUTPUT" "baselines/$BASELINE_DIR/stage4_output.json"
    echo "  ✅ Stage 4 輸出: $STAGE4_OUTPUT"
else
    echo "  ❌ Stage 4 輸出不存在"
fi

# 複製驗證快照
if [ -f data/validation_snapshots/stage4_validation.json ]; then
    cp data/validation_snapshots/stage4_validation.json "baselines/$BASELINE_DIR/stage4_validation.json"
    echo "  ✅ Stage 4 驗證快照"
fi

# 複製 Stage 6 輸出（包含軌道週期驗證）
if [ -f data/validation_snapshots/stage6_validation.json ]; then
    cp data/validation_snapshots/stage6_validation.json "baselines/$BASELINE_DIR/stage6_validation.json"
    echo "  ✅ Stage 6 驗證快照"
fi

echo ""
echo "📈 提取關鍵統計指標..."

# 提取 Stage 4 統計
python3 << 'EOF'
import json
from pathlib import Path
import glob

# 找到最新的 Stage 4 輸出
stage4_files = sorted(glob.glob('data/outputs/stage4/stage4_link_analysis_*.json'), reverse=True)
if not stage4_files:
    print("❌ 找不到 Stage 4 輸出")
    exit(1)

with open(stage4_files[0]) as f:
    stage4_data = json.load(f)

# 提取關鍵指標
metadata = stage4_data.get('metadata', {})
summary = stage4_data.get('summary', {})
starlink_pool = stage4_data.get('starlink_pool', {})
oneweb_pool = stage4_data.get('oneweb_pool', {})

print("🔍 Stage 4 基準指標 (單線程):")
print(f"  執行時間: {metadata.get('execution_time_seconds', 0):.2f} 秒")
print(f"  處理衛星數: {metadata.get('total_satellites_processed', 0)}")
print(f"  可見衛星數: {summary.get('total_visible_satellites', 0)}")
print(f"  Starlink 池大小: {len(starlink_pool.get('satellites', []))}")
print(f"  OneWeb 池大小: {len(oneweb_pool.get('satellites', []))}")
print()

# 提取前 5 顆衛星的詳細數據作為精度基準
print("📊 前 5 顆可見衛星詳細數據 (精度基準):")
visible_sats = summary.get('visible_satellites', [])[:5]
for sat in visible_sats:
    print(f"  - {sat.get('satellite_id')}: "
          f"max_elevation={sat.get('max_elevation', 0):.6f}°, "
          f"total_visible_time={sat.get('total_visible_time_seconds', 0):.2f}s")

# 保存統計到文件
baseline_stats = {
    'execution_time_seconds': metadata.get('execution_time_seconds', 0),
    'total_satellites_processed': metadata.get('total_satellites_processed', 0),
    'total_visible_satellites': summary.get('total_visible_satellites', 0),
    'starlink_pool_size': len(starlink_pool.get('satellites', [])),
    'oneweb_pool_size': len(oneweb_pool.get('satellites', [])),
    'sample_satellites': visible_sats[:5]  # 前 5 顆作為精度樣本
}

# 找到基準目錄
import os
baseline_dirs = sorted([d for d in os.listdir('baselines') if d.startswith('baseline_single_thread_')])
if baseline_dirs:
    latest_baseline = f"baselines/{baseline_dirs[-1]}"
    with open(f"{latest_baseline}/baseline_stats.json", 'w') as f:
        json.dump(baseline_stats, f, indent=2)
    print()
    print(f"✅ 統計已保存至: {latest_baseline}/baseline_stats.json")
EOF

echo ""
echo "========================================"
echo "✅ 基準結果記錄完成！"
echo ""
echo "基準目錄: baselines/$BASELINE_DIR"
echo ""
echo "下一步："
echo "1. 修改 Stage 4 配置啟用並行處理"
echo "2. 重新執行 Stage 4-6"
echo "3. 比對結果差異"
echo "========================================"
