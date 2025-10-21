#!/bin/bash
# RL 訓練數據生成專用腳本
# 使用環境變數覆寫配置，與前端渲染模式互不干擾

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

# 設置輸出路徑
OUTPUT_DIR="$PROJECT_ROOT/data/outputs/rl_training"

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}   🎯 RL 訓練數據生成模式${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}   模式: RL 訓練數據生成（環境變數模式）${NC}"
echo -e "${CYAN}   輸出目錄: $OUTPUT_DIR${NC}"
echo ""

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
echo -e "${CYAN}   參數                      前端渲染        RL 訓練（1天測試）${NC}"
echo -e "${CYAN}   ────────────────────      ──────────      ─────────────${NC}"
echo -e "${CYAN}   時間範圍                  94 分鐘         1 天${NC}"
echo -e "${CYAN}   coverage_cycles           1.0             15.2${NC}"
echo -e "${CYAN}   時間間隔                  30 秒           60 秒${NC}"
echo -e "${CYAN}   時間點數/衛星             220             1,440${NC}"
echo -e "${CYAN}   處理池                    優化池          候選池${NC}"
echo -e "${CYAN}   衛星取樣                  auto            disabled${NC}"
echo -e "${CYAN}   預期輸出大小              ~75 MB          ~500 MB${NC}"
echo -e "${CYAN}   預估時間                  30-40 分鐘      1-1.5 小時${NC}"
echo ""

# 設置環境變數（RL 訓練模式 - 1天測試）
export ORBIT_ENGINE_OUTPUT_DIR="$OUTPUT_DIR"

# 測試模式（允許在非容器環境運行）
export ORBIT_ENGINE_TEST_MODE=1

# 🔧 CRITICAL: 明確禁用取樣模式（處理全部 9087 顆衛星）
# 預設情況下 TEST_MODE=1 會啟用取樣（只處理 50 顆）
# 必須明確設置 SAMPLING_MODE=0 來處理全部衛星
export ORBIT_ENGINE_SAMPLING_MODE=0

# Stage 1: 不取樣，處理全部衛星
export ORBIT_ENGINE_STAGE1_SAMPLING___MODE=disabled

# Stage 2: 1天數據 + 1分鐘間隔
export ORBIT_ENGINE_STAGE2_TIME_SERIES___COVERAGE_CYCLES=15.2
export ORBIT_ENGINE_STAGE2_TIME_SERIES___INTERVAL_SECONDS=60

# Stage 5: 使用候選池（RL 訓練模式）
export ORBIT_ENGINE_STAGE5_USE_CANDIDATE_POOL=true

echo -e "${BLUE}🔧 環境變數設置:${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_OUTPUT_DIR=$ORBIT_ENGINE_OUTPUT_DIR${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_SAMPLING_MODE=$ORBIT_ENGINE_SAMPLING_MODE (0=禁用, 處理全部衛星)${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_STAGE1_SAMPLING___MODE=$ORBIT_ENGINE_STAGE1_SAMPLING___MODE${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_STAGE2_TIME_SERIES___COVERAGE_CYCLES=$ORBIT_ENGINE_STAGE2_TIME_SERIES___COVERAGE_CYCLES${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_STAGE2_TIME_SERIES___INTERVAL_SECONDS=$ORBIT_ENGINE_STAGE2_TIME_SERIES___INTERVAL_SECONDS${NC}"
echo -e "${CYAN}   ORBIT_ENGINE_STAGE5_USE_CANDIDATE_POOL=$ORBIT_ENGINE_STAGE5_USE_CANDIDATE_POOL${NC}"
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
        if [[ ! "$key" =~ ^ORBIT_ENGINE_(OUTPUT_DIR|STAGE1_SAMPLING_MODE|STAGE2_TIME_SERIES|STAGE5_USE_CANDIDATE_POOL)$ ]]; then
            export "$key=$value"
        fi
    done < .env
else
    echo -e "${YELLOW}⚠️  未找到 .env 文件，使用預設配置${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🚀 開始 RL 訓練數據生成（1天測試）...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⚠️  預計處理時間: 1-1.5 小時${NC}"
echo -e "${YELLOW}⚠️  預計輸出大小: ~500 MB${NC}"
echo -e "${CYAN}💡  測試目標: 驗證候選池數量和換手事件品質${NC}"
echo ""

# 執行主程式（傳遞所有參數）
python scripts/run_six_stages_with_validation.py "$@"

# 保存退出碼
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}   ✅ RL 訓練數據生成完成（1天測試）！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}   輸出位置:${NC}"
    echo -e "${CYAN}   - Stage 6: $OUTPUT_DIR/stage6/ ← RL 訓練數據（A4/D2 事件）${NC}"
    echo ""

    # 顯示 Stage 6 輸出統計
    if [ -d "$OUTPUT_DIR/stage6" ]; then
        latest_stage6=$(ls -t "$OUTPUT_DIR/stage6"/stage6_research_optimization_*.json 2>/dev/null | head -1)
        if [ -n "$latest_stage6" ]; then
            echo -e "${BLUE}   📊 Stage 6 輸出統計:${NC}"
            echo -e "${CYAN}      文件: $(basename "$latest_stage6")${NC}"

            # 提取關鍵統計
            if command -v jq &> /dev/null; then
                candidate_count=$(jq -r '.connectable_satellites_candidate.starlink | length' "$latest_stage6" 2>/dev/null || echo "N/A")
                optimized_count=$(jq -r '.connectable_satellites.starlink | length' "$latest_stage6" 2>/dev/null || echo "N/A")
                a4_count=$(jq -r '.gpp_events.a4_events | length' "$latest_stage6" 2>/dev/null || echo "N/A")
                d2_count=$(jq -r '.gpp_events.d2_events | length' "$latest_stage6" 2>/dev/null || echo "N/A")

                echo -e "${CYAN}      候選池衛星數: $candidate_count${NC}"
                echo -e "${CYAN}      優化池衛星數: $optimized_count${NC}"
                echo -e "${CYAN}      A4 換手事件: $a4_count${NC}"
                echo -e "${CYAN}      D2 換手事件: $d2_count${NC}"
            fi

            file_size=$(ls -lh "$latest_stage6" | awk '{print $5}')
            echo -e "${CYAN}      文件大小: $file_size${NC}"
        fi
        echo ""
    fi

    echo -e "${CYAN}   📈 數據品質檢查:${NC}"
    echo -e "${CYAN}      - 候選池是否 > 500 顆？${NC}"
    echo -e "${CYAN}      - 換手事件是否 > 100 個？${NC}"
    echo -e "${CYAN}      - 平均可見衛星數是多少？${NC}"
    echo ""
    echo -e "${CYAN}   下一步（如果數據 OK）:${NC}"
    echo -e "${CYAN}      1. 設置 7天完整數據生成:${NC}"
    echo -e "${CYAN}         export ORBIT_ENGINE_STAGE2_TIME_SERIES___COVERAGE_CYCLES=106.1${NC}"
    echo -e "${CYAN}      2. 預估時間: 8-10 小時${NC}"
    echo ""
else
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}   ⚠️  RL 訓練數據生成結束（退出碼: $EXIT_CODE）${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}   請檢查錯誤訊息，必要時查看:${NC}"
    echo -e "${YELLOW}   - 輸出目錄: $OUTPUT_DIR/${NC}"
    echo -e "${YELLOW}   - 日誌文件（如有）${NC}"
    echo ""
fi

exit $EXIT_CODE
