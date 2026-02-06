#!/bin/bash
# Monitor orbit-engine 6-stage progress

echo "=========================================="
echo "🛰️  Orbit-Engine Progress Monitor"
echo "=========================================="
echo ""

# Check if running
if ps aux | grep -q "[r]un.sh"; then
    echo "✅ Status: Running"
else
    echo "⚠️  Status: Not running"
fi
echo ""

# Check log for current stage
echo "=== Current Progress ==="
if [ -f orbit-engine-run.log ]; then
    # Get latest stage info
    CURRENT_STAGE=$(tail -100 orbit-engine-run.log | grep -E "階段[0-9]|Stage [0-9]" | tail -1)
    echo "$CURRENT_STAGE"
    echo ""

    # Get latest progress
    LATEST_PROGRESS=$(tail -50 orbit-engine-run.log | grep -E "進度|完成|Progress|Complete" | tail -5)
    echo "$LATEST_PROGRESS"
    echo ""
fi

# Check outputs
echo "=== Stage Outputs ==="
for i in {1..6}; do
    OUTPUT_COUNT=$(ls data/outputs/stage$i/*.json 2>/dev/null | wc -l)
    if [ $OUTPUT_COUNT -gt 0 ]; then
        LATEST=$(ls -t data/outputs/stage$i/*.json 2>/dev/null | head -1)
        SIZE=$(du -h "$LATEST" 2>/dev/null | cut -f1)
        echo "✅ Stage $i: $OUTPUT_COUNT files (latest: $SIZE)"
    else
        echo "⏳ Stage $i: Not completed"
    fi
done
echo ""

# Estimated time remaining
echo "=== Time Info ==="
ELAPSED=$(($(date +%s) - $(stat -c %Y orbit-engine-run.log 2>/dev/null || echo 0)))
ELAPSED_MIN=$((ELAPSED / 60))
echo "Elapsed: ${ELAPSED_MIN} minutes"
echo "Expected total: 61-68 minutes (first run without cache)"
echo ""

echo "=========================================="
echo "Run: ./monitor_progress.sh to check again"
echo "Log: tail -f orbit-engine-run.log"
echo "=========================================="
