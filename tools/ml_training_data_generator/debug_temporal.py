#!/usr/bin/env python3
"""Debug script to understand temporal data structure"""

import json
from pathlib import Path
from collections import defaultdict

# Load Stage 6 data
stage6_file = Path('data/outputs/stage6').glob('stage6_research*.json').__next__()
with open(stage6_file) as f:
    data = json.load(f)

gpp_events = data['gpp_events']
signal_analysis = data['signal_analysis']

a4_events = gpp_events['a4_events']
d2_events = gpp_events['d2_events']

print(f"Total A4 events: {len(a4_events)}")
print(f"Total D2 events: {len(d2_events)}")

# Sample A4 event
if a4_events:
    print(f"\n📋 Sample A4 event:")
    print(json.dumps(a4_events[0], indent=2))

# Sample D2 event
if d2_events:
    print(f"\n📋 Sample D2 event:")
    print(json.dumps(d2_events[0], indent=2))

# Check concurrent events
events_by_time = defaultdict(lambda: {'a4': [], 'd2': []})

for event in a4_events:
    ts = event.get('timestamp')
    if ts:
        events_by_time[ts]['a4'].append(event)

for event in d2_events:
    ts = event.get('timestamp')
    if ts:
        events_by_time[ts]['d2'].append(event)

print(f"\n📊 Time points with both A4 and D2 events:")
both_count = 0
for ts, events in events_by_time.items():
    if events['a4'] and events['d2']:
        both_count += 1
        if both_count <= 3:
            print(f"   {ts}: {len(events['a4'])} A4, {len(events['d2'])} D2")

print(f"   Total: {both_count} time points with both A4 and D2")

# Check if any A4 and D2 events have different satellite choices
print(f"\n🔍 Checking satellite choices:")
different_choices = 0
for ts, events in events_by_time.items():
    if events['a4'] and events['d2']:
        a4_sats = {e.get('neighbor_satellite_id') for e in events['a4']}
        d2_sats = {e.get('neighbor_satellite_id') for e in events['d2']}

        if a4_sats != d2_sats:
            different_choices += 1
            if different_choices <= 3:
                print(f"   {ts}:")
                print(f"      A4 candidates: {a4_sats}")
                print(f"      D2 candidates: {d2_sats}")
                print(f"      Difference: {d2_sats - a4_sats}")

print(f"   Total: {different_choices} time points with different satellite choices")

# Check signal analysis structure
sample_sat = list(signal_analysis.keys())[0]
print(f"\n📊 Sample signal analysis for satellite {sample_sat}:")
print(f"   Time series length: {len(signal_analysis[sample_sat]['time_series'])}")
print(f"   First entry timestamp: {signal_analysis[sample_sat]['time_series'][0]['timestamp']}")
print(f"   Last entry timestamp: {signal_analysis[sample_sat]['time_series'][-1]['timestamp']}")
