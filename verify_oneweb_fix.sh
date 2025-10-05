#!/bin/bash
# OneWeb 軌道週期修復驗證腳本
# 檢查 Stage 2 時間點生成和 Stage 6 軌道週期驗證

echo "========================================"
echo "OneWeb 軌道週期修復驗證"
echo "========================================"
echo ""

# 1. 檢查 Stage 2 驗證快照
echo "📊 Stage 2: 時間點生成驗證"
echo "----------------------------------------"

STAGE2_VALIDATION="data/validation_snapshots/stage2_validation.json"

if [ ! -f "$STAGE2_VALIDATION" ]; then
    echo "❌ Stage 2 驗證快照不存在: $STAGE2_VALIDATION"
    exit 1
fi

# 提取 Starlink 和 OneWeb 時間點數量
echo "計算各星座時間點數..."
python3 << 'EOF'
import json

with open('data/validation_snapshots/stage2_validation.json') as f:
    data = json.load(f)

# 從 metadata 獲取統計
metadata = data.get('metadata', {})
total_points = metadata.get('total_time_points', 0)
total_sats = metadata.get('total_satellites', 0)

# 從 constellation_summary 獲取星座統計
summary = data.get('constellation_summary', {})
starlink_sats = summary.get('starlink', {}).get('satellite_count', 0)
oneweb_sats = summary.get('oneweb', {}).get('satellite_count', 0)

# 計算平均時間點數
avg_points = total_points / total_sats if total_sats > 0 else 0

print(f"  總衛星數: {total_sats}")
print(f"  總時間點: {total_points:,}")
print(f"  平均點數/衛星: {avg_points:.1f}")
print()
print(f"  Starlink: {starlink_sats} 顆")
print(f"  OneWeb: {oneweb_sats} 顆")
print()

# 計算預期值
expected_starlink_points = starlink_sats * 190
expected_oneweb_points = oneweb_sats * 220
expected_total = expected_starlink_points + expected_oneweb_points

print(f"🔍 預期時間點分配 (修正後):")
print(f"  Starlink: {starlink_sats} × 190 = {expected_starlink_points:,}")
print(f"  OneWeb: {oneweb_sats} × 220 = {expected_oneweb_points:,}")
print(f"  預期總計: {expected_total:,}")
print()

# 驗證
if abs(total_points - expected_total) < 100:
    print(f"✅ 時間點分配正確！")
    print(f"   實際 {total_points:,} ≈ 預期 {expected_total:,}")
else:
    print(f"❌ 時間點分配錯誤！")
    print(f"   實際 {total_points:,} vs 預期 {expected_total:,}")
    print(f"   誤差: {abs(total_points - expected_total):,}")
EOF

echo ""
echo "========================================"
echo ""

# 2. 檢查 Stage 6 軌道週期驗證
echo "📊 Stage 6: 軌道週期覆蓋驗證"
echo "----------------------------------------"

STAGE6_VALIDATION="data/validation_snapshots/stage6_validation.json"

if [ ! -f "$STAGE6_VALIDATION" ]; then
    echo "❌ Stage 6 驗證快照不存在: $STAGE6_VALIDATION"
    exit 1
fi

# 提取軌道週期驗證結果
echo "檢查軌道週期驗證結果..."
python3 << 'EOF'
import json

with open('data/validation_snapshots/stage6_validation.json') as f:
    data = json.load(f)

# 提取 pool_verification 數據
pool_verif = data.get('pool_verification', {})

# Starlink 驗證
starlink_pool = pool_verif.get('starlink_pool', {})
starlink_orbital = starlink_pool.get('orbital_period_validation', {})

print("🔵 Starlink 軌道週期驗證:")
print(f"  時間跨度: {starlink_orbital.get('time_span_minutes', 0):.1f} 分鐘")
print(f"  預期週期: {starlink_orbital.get('expected_period_minutes', 0):.1f} 分鐘")
print(f"  覆蓋比率: {starlink_orbital.get('coverage_ratio', 0):.1%}")
print(f"  完整週期: {'✅ 是' if starlink_orbital.get('is_complete_period') else '❌ 否'}")
print(f"  驗證通過: {'✅ 通過' if starlink_orbital.get('validation_passed') else '❌ 失敗'}")
print()

# OneWeb 驗證
oneweb_pool = pool_verif.get('oneweb_pool', {})
oneweb_orbital = oneweb_pool.get('orbital_period_validation', {})

print("🟢 OneWeb 軌道週期驗證:")
print(f"  時間跨度: {oneweb_orbital.get('time_span_minutes', 0):.1f} 分鐘")
print(f"  預期週期: {oneweb_orbital.get('expected_period_minutes', 0):.1f} 分鐘")
print(f"  覆蓋比率: {oneweb_orbital.get('coverage_ratio', 0):.1%}")
print(f"  完整週期: {'✅ 是' if oneweb_orbital.get('is_complete_period') else '❌ 否'}")
print(f"  驗證通過: {'✅ 通過' if oneweb_orbital.get('validation_passed') else '❌ 失敗'}")
print()

# 最終判定
starlink_pass = starlink_orbital.get('validation_passed', False)
oneweb_pass = oneweb_orbital.get('validation_passed', False)

print("=" * 40)
if starlink_pass and oneweb_pass:
    print("🎉 所有驗證通過！OneWeb 軌道週期問題已修復！")
    exit(0)
else:
    print("❌ 仍有驗證失敗！")
    if not starlink_pass:
        print("  - Starlink 驗證失敗")
    if not oneweb_pass:
        print("  - OneWeb 驗證失敗")
    exit(1)
EOF

RESULT=$?

echo ""
echo "========================================"
echo ""

if [ $RESULT -eq 0 ]; then
    echo "✅ OneWeb 軌道週期修復驗證完成！"
else
    echo "❌ 驗證未完全通過，請檢查詳細結果"
fi

exit $RESULT
