#!/usr/bin/env python3
"""
Debug script to analyze A4 vs D2 score magnitudes
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ml_training_data_generator.core.json_parser import Stage6OutputParser

# Load Stage 6 data
parser = Stage6OutputParser()
stage6_outputs = parser.parse_batch("data/outputs/stage6", pattern="stage6_research*.json")

if not stage6_outputs:
    print("❌ No Stage 6 data found")
    sys.exit(1)

stage6 = stage6_outputs[0]

# Analyze score magnitudes
print("=" * 70)
print("A4 vs D2 Score Magnitude Analysis")
print("=" * 70)

# A4 scores
a4_events = stage6.data['gpp_events']['a4_events']
a4_margins = [e['measurements']['trigger_margin_db'] for e in a4_events[:100]]

print(f"\n📊 A4 RSRP Margins (first 100 events):")
print(f"   Min: {min(a4_margins):.2f} dB")
print(f"   Max: {max(a4_margins):.2f} dB")
print(f"   Avg: {sum(a4_margins)/len(a4_margins):.2f} dB")
print(f"   ")
print(f"   With weight 0.6:")
print(f"   Min score: {min(a4_margins) * 0.6:.2f}")
print(f"   Max score: {max(a4_margins) * 0.6:.2f}")
print(f"   Avg score: {sum(a4_margins)/len(a4_margins) * 0.6:.2f}")

# D2 scores
d2_events = stage6.data['gpp_events']['d2_events']
d2_improvements = [e['measurements']['ground_distance_improvement_km'] for e in d2_events]

print(f"\n📊 D2 Distance Improvements (all {len(d2_events)} events):")
print(f"   Min: {min(d2_improvements):.2f} km")
print(f"   Max: {max(d2_improvements):.2f} km")
print(f"   Avg: {sum(d2_improvements)/len(d2_improvements):.2f} km")
print(f"   ")
print(f"   With normalization /200 and weight 0.4:")
print(f"   Min score: {min(d2_improvements)/200 * 0.4:.2f}")
print(f"   Max score: {max(d2_improvements)/200 * 0.4:.2f}")
print(f"   Avg score: {sum(d2_improvements)/len(d2_improvements)/200 * 0.4:.2f}")

print(f"\n" + "=" * 70)
print(f"PROBLEM DIAGNOSIS:")
print(f"=" * 70)

a4_avg_score = sum(a4_margins)/len(a4_margins) * 0.6
d2_avg_score = sum(d2_improvements)/len(d2_improvements)/200 * 0.4

print(f"\n平均 A4 分數: {a4_avg_score:.2f}")
print(f"平均 D2 分數: {d2_avg_score:.2f}")
print(f"比例: A4/D2 = {a4_avg_score/d2_avg_score:.1f}x")

print(f"\n❌ D2 分數太小，無法翻轉 A4 的候選排名！")
print(f"")
print(f"💡 可能的解決方案:")
print(f"   1. 增加 D2 權重: 0.4 → 0.6 或更高")
print(f"   2. 減少距離歸一化: 200 km → 100 km 或 50 km")
print(f"   3. 兩者結合調整")

print(f"\n" + "=" * 70)
