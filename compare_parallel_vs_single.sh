#!/bin/bash
# 比對 Stage 4 單線程 vs 多核並行執行結果
# 驗證並行處理是否影響精度

if [ $# -ne 1 ]; then
    echo "用法: $0 <baseline_directory>"
    echo "範例: $0 baselines/baseline_single_thread_20251005_083000"
    exit 1
fi

BASELINE_DIR=$1

if [ ! -d "$BASELINE_DIR" ]; then
    echo "❌ 基準目錄不存在: $BASELINE_DIR"
    exit 1
fi

echo "========================================"
echo "Stage 4 並行處理精度驗證"
echo "========================================"
echo ""
echo "基準 (單線程): $BASELINE_DIR"
echo "比對 (多核): 當前執行結果"
echo ""

python3 << EOF
import json
import sys
from pathlib import Path
import glob

# 讀取基準統計
baseline_stats_path = Path("$BASELINE_DIR") / "baseline_stats.json"
if not baseline_stats_path.exists():
    print("❌ 基準統計文件不存在")
    sys.exit(1)

with open(baseline_stats_path) as f:
    baseline_stats = json.load(f)

# 讀取當前執行結果
stage4_files = sorted(glob.glob('data/outputs/stage4/stage4_link_analysis_*.json'), reverse=True)
if not stage4_files:
    print("❌ 找不到當前 Stage 4 輸出")
    sys.exit(1)

with open(stage4_files[0]) as f:
    current_data = json.load(f)

# 提取當前指標
metadata = current_data.get('metadata', {})
summary = current_data.get('summary', {})
starlink_pool = current_data.get('starlink_pool', {})
oneweb_pool = current_data.get('oneweb_pool', {})

current_stats = {
    'execution_time_seconds': metadata.get('execution_time_seconds', 0),
    'total_satellites_processed': metadata.get('total_satellites_processed', 0),
    'total_visible_satellites': summary.get('total_visible_satellites', 0),
    'starlink_pool_size': len(starlink_pool.get('satellites', [])),
    'oneweb_pool_size': len(oneweb_pool.get('satellites', [])),
}

# ========== 1. 效能比較 ==========
print("📊 效能比較")
print("=" * 60)
baseline_time = baseline_stats['execution_time_seconds']
current_time = current_stats['execution_time_seconds']
speedup = baseline_time / current_time if current_time > 0 else 0

print(f"執行時間:")
print(f"  單線程: {baseline_time:.2f} 秒")
print(f"  多核:   {current_time:.2f} 秒")
print(f"  加速比: {speedup:.2f}x")
print()

# ========== 2. 數量一致性檢查 ==========
print("🔍 數量一致性檢查")
print("=" * 60)

checks = [
    ('處理衛星數', 'total_satellites_processed'),
    ('可見衛星數', 'total_visible_satellites'),
    ('Starlink 池大小', 'starlink_pool_size'),
    ('OneWeb 池大小', 'oneweb_pool_size'),
]

all_identical = True
for name, key in checks:
    baseline_val = baseline_stats[key]
    current_val = current_stats[key]
    match = "✅" if baseline_val == current_val else "❌"
    print(f"{match} {name}:")
    print(f"    單線程: {baseline_val}")
    print(f"    多核:   {current_val}")

    if baseline_val != current_val:
        all_identical = False
        diff = current_val - baseline_val
        print(f"    差異:   {diff:+d}")
    print()

# ========== 3. 精度比較（前 5 顆衛星） ==========
print("🎯 精度比較 (前 5 顆可見衛星)")
print("=" * 60)

baseline_samples = baseline_stats.get('sample_satellites', [])
current_samples = summary.get('visible_satellites', [])[:5]

if len(baseline_samples) > 0 and len(current_samples) > 0:
    # 建立衛星 ID 對照表
    baseline_dict = {sat['satellite_id']: sat for sat in baseline_samples}

    max_elevation_diffs = []
    visibility_time_diffs = []

    for current_sat in current_samples:
        sat_id = current_sat['satellite_id']

        if sat_id in baseline_dict:
            baseline_sat = baseline_dict[sat_id]

            # 比較最大仰角
            baseline_elev = baseline_sat.get('max_elevation', 0)
            current_elev = current_sat.get('max_elevation', 0)
            elev_diff = abs(current_elev - baseline_elev)
            max_elevation_diffs.append(elev_diff)

            # 比較可見時間
            baseline_time = baseline_sat.get('total_visible_time_seconds', 0)
            current_time = current_sat.get('total_visible_time_seconds', 0)
            time_diff = abs(current_time - baseline_time)
            visibility_time_diffs.append(time_diff)

            print(f"衛星 {sat_id}:")
            print(f"  最大仰角: {baseline_elev:.6f}° → {current_elev:.6f}° (差異 {elev_diff:.9f}°)")
            print(f"  可見時間: {baseline_time:.2f}s → {current_time:.2f}s (差異 {time_diff:.2f}s)")

    print()
    print("統計摘要:")
    if max_elevation_diffs:
        print(f"  最大仰角差異: 最大 {max(max_elevation_diffs):.9f}°, 平均 {sum(max_elevation_diffs)/len(max_elevation_diffs):.9f}°")
    if visibility_time_diffs:
        print(f"  可見時間差異: 最大 {max(visibility_time_diffs):.2f}s, 平均 {sum(visibility_time_diffs)/len(visibility_time_diffs):.2f}s")
else:
    print("⚠️ 樣本數據不足，無法進行精度比較")

print()

# ========== 4. 最終判定 ==========
print("=" * 60)
print("🎓 精度驗證結果")
print("=" * 60)

# 判定標準
PRECISION_THRESHOLD_ELEVATION = 1e-6  # 仰角差異容忍度 (度)
PRECISION_THRESHOLD_TIME = 0.1  # 時間差異容忍度 (秒)

if all_identical:
    if max_elevation_diffs and max(max_elevation_diffs) < PRECISION_THRESHOLD_ELEVATION:
        print("✅ 多核並行處理不影響精度！")
        print(f"   - 數量完全一致")
        print(f"   - 最大仰角差異 < {PRECISION_THRESHOLD_ELEVATION}° (機器精度範圍內)")
        print(f"   - 加速比: {speedup:.2f}x")
        print()
        print("🚀 建議: 可以安全啟用 Stage 4 並行處理")
    else:
        print("⚠️ 數量一致，但存在精度差異")
        print(f"   最大差異: {max(max_elevation_diffs) if max_elevation_diffs else 0:.9f}°")
else:
    print("❌ 並行處理導致結果不一致")
    print("   建議保持單線程執行")

print("=" * 60)
EOF
