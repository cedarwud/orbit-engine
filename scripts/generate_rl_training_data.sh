#!/bin/bash
# RL 訓練數據生成專用腳本
# 使用獨立配置，輸出到獨立目錄，與前端渲染模式互不干擾

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 獲取腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 設置路徑
CONFIG_DIR="$PROJECT_ROOT/config/rl_training"
OUTPUT_DIR="$PROJECT_ROOT/data/outputs/rl_training"

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}   🎯 RL 訓練數據生成模式${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}   模式: RL 訓練數據生成${NC}"
echo -e "${CYAN}   配置目錄: $CONFIG_DIR${NC}"
echo -e "${CYAN}   輸出目錄: $OUTPUT_DIR${NC}"
echo ""

# 驗證配置目錄存在
if [ ! -d "$CONFIG_DIR" ]; then
    echo -e "${YELLOW}❌ 錯誤: RL 訓練配置目錄不存在${NC}"
    echo -e "${YELLOW}   路徑: $CONFIG_DIR${NC}"
    echo -e "${YELLOW}   請先執行 Phase 1（創建 RL 配置文件）${NC}"
    exit 1
fi

# 創建輸出目錄
echo -e "${BLUE}📁 創建輸出目錄...${NC}"
mkdir -p "$OUTPUT_DIR"/{stage1,stage2,stage3,stage4,stage5,stage6}
mkdir -p "$OUTPUT_DIR/cache"
mkdir -p "$OUTPUT_DIR/validation_snapshots"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 輸出目錄創建完成${NC}"
else
    echo -e "${YELLOW}❌ 輸出目錄創建失敗${NC}"
    exit 1
fi

# 顯示關鍵參數差異
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   📊 RL 訓練模式 vs 前端渲染模式${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}   參數                      前端渲染        RL 訓練${NC}"
echo -e "${CYAN}   ────────────────────      ──────────      ─────────${NC}"
echo -e "${CYAN}   時間範圍                  94 分鐘         7 天${NC}"
echo -e "${CYAN}   coverage_cycles           1.0             106.1${NC}"
echo -e "${CYAN}   時間點數/衛星             220             20,160${NC}"
echo -e "${CYAN}   目標可見衛星              10-15 顆        4-6 顆${NC}"
echo -e "${CYAN}   衛星池大小                10-15           800-1000${NC}"
echo -e "${CYAN}   預期輸出大小              ~75 MB          ~6 GB${NC}"
echo ""

# 設置環境變數（RL 訓練模式）
export ORBIT_ENGINE_CONFIG_DIR="$CONFIG_DIR"
export ORBIT_ENGINE_OUTPUT_DIR="$OUTPUT_DIR"

echo -e "${BLUE}🔧 環境變數設置:${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_CONFIG_DIR=$ORBIT_ENGINE_CONFIG_DIR${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_OUTPUT_DIR=$ORBIT_ENGINE_OUTPUT_DIR${NC}"
echo ""

# 切換到專案目錄
cd "$PROJECT_ROOT"

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

# 檢查並載入 .env 文件（如果存在）
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 已找到環境配置: .env${NC}"
    echo -e "${BLUE}   配置預覽:${NC}"
    grep -E "^[^#].*=" .env | head -3 | sed 's/^/   /'

    # 導出環境變量（但不覆蓋已設置的 RL 訓練變數）
    while IFS='=' read -r key value; do
        # 跳過註釋和空行
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # 跳過已設置的 RL 訓練變數
        if [ "$key" != "ORBIT_ENGINE_CONFIG_DIR" ] && [ "$key" != "ORBIT_ENGINE_OUTPUT_DIR" ]; then
            export "$key=$value"
        fi
    done < .env
else
    echo -e "${YELLOW}⚠️  未找到 .env 文件，使用預設配置${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🚀 開始 RL 訓練數據生成...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⚠️  預計處理時間: 2-4 小時（800 衛星 × 7 天）${NC}"
echo -e "${YELLOW}⚠️  預計輸出大小: ~6 GB${NC}"
echo -e "${YELLOW}⚠️  建議保留至少 10 GB 磁碟空間${NC}"
echo ""

# 執行主程式（傳遞所有參數）
python scripts/run_six_stages_with_validation.py "$@"

# 保存退出碼
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}   ✅ RL 訓練數據生成完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}   輸出位置:${NC}"
    echo -e "${CYAN}   - Stage 1: $OUTPUT_DIR/stage1/${NC}"
    echo -e "${CYAN}   - Stage 2: $OUTPUT_DIR/stage2/${NC}"
    echo -e "${CYAN}   - Stage 3: $OUTPUT_DIR/stage3/${NC}"
    echo -e "${CYAN}   - Stage 4: $OUTPUT_DIR/stage4/${NC}"
    echo -e "${CYAN}   - Stage 5: $OUTPUT_DIR/stage5/${NC}"
    echo -e "${CYAN}   - Stage 6: $OUTPUT_DIR/stage6/ ← RL 訓練數據（A4/D2 事件）${NC}"
    echo ""

    # 顯示輸出文件大小
    if [ -d "$OUTPUT_DIR/stage6" ]; then
        echo -e "${BLUE}   📊 Stage 6 輸出:${NC}"
        ls -lh "$OUTPUT_DIR/stage6/" | tail -n +2 | sed 's/^/   /'
        echo ""
    fi

    echo -e "${CYAN}   下一步:${NC}"
    echo -e "${CYAN}   - 在 handover-rl 中讀取 Stage 6 輸出${NC}"
    echo -e "${CYAN}   - 提取 A4/D2 事件數據${NC}"
    echo -e "${CYAN}   - 開始 RL agent 訓練${NC}"
    echo ""
else
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}   ⚠️  RL 訓練數據生成結束（退出碼: $EXIT_CODE）${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}   請檢查錯誤訊息，必要時查看:${NC}"
    echo -e "${YELLOW}   - 配置文件: $CONFIG_DIR/${NC}"
    echo -e "${YELLOW}   - 輸出目錄: $OUTPUT_DIR/${NC}"
    echo -e "${YELLOW}   - 日誌文件（如有）${NC}"
    echo ""
fi

exit $EXIT_CODE
