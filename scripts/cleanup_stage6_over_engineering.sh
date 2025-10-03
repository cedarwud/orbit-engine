#!/bin/bash
# Stage 6 過度開發清理腳本
# 用途: 移除未使用的模組，減少 60% 代碼量
# 作者: ORBIT Engine Team
# 日期: 2025-10-03

set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Stage 6 過度開發清理腳本${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 確認操作
echo -e "${YELLOW}⚠️  此腳本將刪除 11 個未使用的模組（共 180KB）${NC}"
echo ""
echo "刪除清單:"
echo "  🔴 Stage 4 遺留代碼 (4個):"
echo "     - handover_optimizer.py (36K)"
echo "     - dynamic_pool_planner.py (38K)"
echo "     - research_performance_analyzer.py (23K)"
echo "     - config_manager.py (17K)"
echo ""
echo "  🟡 多目標優化系統 (7個):"
echo "     - multi_obj_optimizer.py (16K)"
echo "     - nsga2_algorithm.py (8.7K)"
echo "     - pymoo_nsga2_adapter.py (13K)"
echo "     - optimization_models.py (1.4K)"
echo "     - objective_evaluators.py (4.6K)"
echo "     - constraint_solver.py (6.5K)"
echo "     - pareto_analyzer.py (9.1K)"
echo "     - quality_cost_balancer.py (6.4K)"
echo ""
read -p "確定要繼續嗎？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${YELLOW}取消清理${NC}"
    exit 1
fi

# 創建備份
echo -e "${GREEN}📦 創建備份...${NC}"
BACKUP_DIR="backups/stage6_cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 備份要刪除的文件
cp src/stages/stage6_research_optimization/handover_optimizer.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/dynamic_pool_planner.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/research_performance_analyzer.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/config_manager.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/multi_obj_optimizer.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/nsga2_algorithm.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/pymoo_nsga2_adapter.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/optimization_models.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/objective_evaluators.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/constraint_solver.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/pareto_analyzer.py "$BACKUP_DIR/" 2>/dev/null || true
cp src/stages/stage6_research_optimization/quality_cost_balancer.py "$BACKUP_DIR/" 2>/dev/null || true

echo -e "${GREEN}✅ 備份已保存到: $BACKUP_DIR${NC}"
echo ""

# 刪除 Stage 4 遺留代碼
echo -e "${GREEN}🗑️  刪除 Stage 4 遺留代碼...${NC}"
rm -f src/stages/stage6_research_optimization/handover_optimizer.py
rm -f src/stages/stage6_research_optimization/dynamic_pool_planner.py
rm -f src/stages/stage6_research_optimization/research_performance_analyzer.py
rm -f src/stages/stage6_research_optimization/config_manager.py
echo -e "${GREEN}   ✅ 已刪除 4 個文件 (114KB)${NC}"
echo ""

# 刪除多目標優化系統
echo -e "${GREEN}🗑️  刪除多目標優化系統...${NC}"
rm -f src/stages/stage6_research_optimization/multi_obj_optimizer.py
rm -f src/stages/stage6_research_optimization/nsga2_algorithm.py
rm -f src/stages/stage6_research_optimization/pymoo_nsga2_adapter.py
rm -f src/stages/stage6_research_optimization/optimization_models.py
rm -f src/stages/stage6_research_optimization/objective_evaluators.py
rm -f src/stages/stage6_research_optimization/constraint_solver.py
rm -f src/stages/stage6_research_optimization/pareto_analyzer.py
rm -f src/stages/stage6_research_optimization/quality_cost_balancer.py
echo -e "${GREEN}   ✅ 已刪除 8 個文件 (66KB)${NC}"
echo ""

# 統計剩餘模組
REMAINING=$(ls -1 src/stages/stage6_research_optimization/*.py | grep -v __pycache__ | grep -v __init__ | wc -l)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}清理完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 清理結果:"
echo "   - 刪除模組: 12 個"
echo "   - 減少代碼: ~180KB"
echo "   - 剩餘模組: ${REMAINING} 個"
echo "   - 備份位置: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}⚠️  下一步:${NC}"
echo "   1. 從 requirements.txt 移除 pymoo 和 stable-baselines3"
echo "   2. 運行測試: python scripts/run_six_stages_with_validation.py --stage 6"
echo "   3. 如果測試通過，提交變更: git add . && git commit -m 'Clean up Stage 6 over-engineering'"
echo ""
