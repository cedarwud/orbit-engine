#!/usr/bin/env python3
"""
Debug Min-Max normalization to understand why D2 still has 0% impact
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ml_training_data_generator.core.json_parser import Stage6OutputParser

# Load Stage 6 data
parser = Stage6OutputParser()
outputs = parser.parse_batch("data/outputs/stage6", pattern="stage6_research*.json")

if not outputs:
    print("❌ No data found")
    sys.exit(1)

stage6 = outputs[0]

# Find cases where both A4 and D2 exist
print("=" * 70)
print("Analyzing A4+D2 Overlap Cases (Min-Max Normalized)")
print("=" * 70)

timestamps = sorted(set(
    e['timestamp'] for e in stage6.data['gpp_events']['a4_events']
) | set(
    e['timestamp'] for e in stage6.data['gpp_events']['d2_events']
))

cases_analyzed = 0
d2_wins = 0

for ts in timestamps[:20]:  # Analyze first 20 timestamps
    # Get events at this timestamp
    a4_events = [e for e in stage6.data['gpp_events']['a4_events'] if e['timestamp'] == ts]
    d2_events = [e for e in stage6.data['gpp_events']['d2_events'] if e['timestamp'] == ts]

    if not a4_events or not d2_events:
        continue

    # Assume serving satellite from first A4 event
    serving = a4_events[0]['serving_satellite']

    # Get events for this serving
    a4_for_serving = [e for e in a4_events if str(e['serving_satellite']) == str(serving)]
    d2_for_serving = [e for e in d2_events if str(e['serving_satellite']) == str(serving)]

    if not a4_for_serving or not d2_for_serving:
        continue

    cases_analyzed += 1
    print(f"\nCase {cases_analyzed}: Timestamp {ts[:19]}, Serving {serving}")

    # Collect raw values
    a4_raw = {}
    d2_raw = {}

    for e in a4_for_serving:
        neighbor = e['neighbor_satellite']
        a4_raw[neighbor] = e['measurements']['trigger_margin_db']

    for e in d2_for_serving:
        if e['distance_analysis']['handover_recommended']:
            neighbor = e['neighbor_satellite']
            d2_raw[neighbor] = e['measurements']['ground_distance_improvement_km']

    if not a4_raw or not d2_raw:
        print("  ⚠️  Skipped: Missing A4 or D2 raw values")
        continue

    # Min-Max normalization
    a4_min, a4_max = min(a4_raw.values()), max(a4_raw.values())
    d2_min, d2_max = min(d2_raw.values()), max(d2_raw.values())

    a4_norm = {}
    d2_norm = {}

    if a4_max > a4_min:
        for k, v in a4_raw.items():
            a4_norm[k] = (v - a4_min) / (a4_max - a4_min)
    else:
        a4_norm = {k: 0.5 for k in a4_raw}

    if d2_max > d2_min:
        for k, v in d2_raw.items():
            d2_norm[k] = (v - d2_min) / (d2_max - d2_min)
    else:
        d2_norm = {k: 0.5 for k in d2_raw}

    # Weighted scores
    all_neighbors = set(a4_norm.keys()) | set(d2_norm.keys())
    scores = {}
    a4_only_scores = {}

    for neighbor in all_neighbors:
        a4_score = a4_norm.get(neighbor, 0.0) * 0.6
        d2_score = d2_norm.get(neighbor, 0.0) * 0.4
        scores[neighbor] = a4_score + d2_score
        a4_only_scores[neighbor] = a4_score

    # Find winners
    best_combined = max(scores, key=scores.get)
    best_a4_only = max(a4_only_scores, key=a4_only_scores.get)

    print(f"  A4 raw range: {a4_min:.2f} - {a4_max:.2f} dB")
    print(f"  D2 raw range: {d2_min:.2f} - {d2_max:.2f} km")
    print(f"  ")
    print(f"  Best by A4-only: {best_a4_only} (score={a4_only_scores[best_a4_only]:.3f})")
    print(f"  Best by A4+D2:   {best_combined} (score={scores[best_combined]:.3f})")

    if best_combined != best_a4_only:
        d2_wins += 1
        print(f"  ✅ D2 CHANGED DECISION!")
        print(f"     A4-only would choose: {best_a4_only}")
        print(f"     A4+D2 chose: {best_combined}")
        print(f"     Reason: D2 score boosted {best_combined} enough to overtake")
    else:
        print(f"  ❌ D2 didn't change (both chose {best_combined})")
        # Show why D2 didn't help
        if best_combined in a4_norm and best_combined in d2_norm:
            print(f"     {best_combined}: A4_norm={a4_norm[best_combined]:.3f}, D2_norm={d2_norm[best_combined]:.3f}")

print(f"\n" + "=" * 70)
print(f"SUMMARY:")
print(f"=" * 70)
print(f"Cases analyzed: {cases_analyzed}")
print(f"D2 changed decision: {d2_wins} ({d2_wins/cases_analyzed*100 if cases_analyzed > 0 else 0:.1f}%)")
print(f"")
if d2_wins == 0:
    print(f"❌ D2 NEVER changed decisions even with Min-Max normalization!")
    print(f"")
    print(f"💡 Possible reasons:")
    print(f"   1. A4 and D2 events favor the SAME candidates")
    print(f"   2. Weight 0.6/0.4 still too biased toward A4")
    print(f"   3. D2 score variation too small after normalization")
