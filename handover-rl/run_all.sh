#!/bin/bash
# 完整執行所有階段的腳本

set -e  # 遇到錯誤立即退出

echo "════════════════════════════════════════════════════════════"
echo "🚀 Handover-RL 完整執行流程"
echo "════════════════════════════════════════════════════════════"

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "❌ 未找到虛擬環境"
    echo "請先執行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Phase 1: 數據載入
echo ""
echo "=" * 70
echo "Phase 1: 數據載入與處理"
echo "=" * 70
python phase1_data_loader.py

# Phase 2: Baseline 評估
echo ""
echo "=" * 70
echo "Phase 2: Baseline 方法評估"
echo "=" * 70
python phase2_baseline_methods.py

# Phase 3: 環境驗證
echo ""
echo "=" * 70
echo "Phase 3: RL 環境驗證"
echo "=" * 70
python phase3_rl_environment.py

# Phase 4: RL 訓練
echo ""
echo "=" * 70
echo "Phase 4: DQN 訓練"
echo "=" * 70
python phase4_rl_training.py

# Phase 5: 最終評估
echo ""
echo "=" * 70
echo "Phase 5: 最終評估與比較"
echo "=" * 70
python phase5_evaluation.py

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ 所有階段執行完成！"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📁 查看結果:"
echo "   results/final_evaluation.json      - 完整評估結果"
echo "   results/comparison_report.txt      - 比較報告"
echo "   results/plots/                     - 所有圖表"
