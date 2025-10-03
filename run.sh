#!/bin/bash
# Orbit Engine 快速啟動腳本
# 支持階段選擇和參數傳遞

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 顯示使用說明
show_usage() {
    echo -e "${CYAN}用法:${NC}"
    echo "  $0                    # 執行全部六階段"
    echo "  $0 --stage 1          # 只執行階段 1"
    echo "  $0 --stages 1-3       # 執行階段 1 到 3"
    echo "  $0 --stages 1,3,5     # 執行階段 1, 3, 5"
    echo "  $0 --help             # 顯示完整幫助"
    echo ""
    echo -e "${CYAN}範例:${NC}"
    echo "  $0 --stage 5          # 只執行信號分析階段"
    echo "  $0 --stages 1-2       # 執行軌道計算階段"
    exit 0
}

# 檢查 --help 參數
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🛰️  Orbit Engine - 六階段處理系統${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 顯示執行模式
if [[ "$1" == "--stage" ]]; then
    echo -e "${CYAN}   執行模式: 單一階段 (Stage $2)${NC}"
elif [[ "$1" == "--stages" ]]; then
    echo -e "${CYAN}   執行模式: 階段範圍 ($2)${NC}"
else
    echo -e "${CYAN}   執行模式: 全部六階段${NC}"
fi
echo ""

# 切換到專案目錄
cd "$(dirname "$0")"

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虛擬環境不存在，正在創建...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ 虛擬環境創建完成${NC}"
else
    echo -e "${GREEN}✅ 啟動虛擬環境${NC}"
    source venv/bin/activate
fi

# 檢查並載入 .env 文件
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 已找到環境配置: .env${NC}"
    echo -e "${BLUE}   配置預覽:${NC}"
    grep -E "^[^#].*=" .env | head -3 | sed 's/^/   /'

    # 導出環境變量
    set -a  # 自動導出所有變量
    source .env
    set +a  # 關閉自動導出
else
    echo -e "${YELLOW}⚠️  未找到 .env 文件，使用預設配置${NC}"
fi

echo ""
echo -e "${BLUE}🚀 開始執行處理...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 執行主程式（傳遞所有參數）
python scripts/run_six_stages_with_validation.py "$@"

# 保存退出碼
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 執行完成！${NC}"
else
    echo -e "${YELLOW}⚠️  執行結束（退出碼: $EXIT_CODE）${NC}"
fi

exit $EXIT_CODE
