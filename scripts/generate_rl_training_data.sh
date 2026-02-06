#!/bin/bash
# RL 訓練數據生成專用腳本 (恢復版本 - 僅使用優化池)
#
# 目的: 為 handover-rl 生成 30 天軌道數據，與前端渲染模式互不干擾
#
# 設計原則:
# 1. 使用環境變數覆寫配置，無需修改主配置文件
# 2. 輸出到獨立目錄 (data/outputs/rl_training/)
# 3. 使用優化池 (101 顆衛星)，保證 10-15 顆可見衛星
# 4. 生成 30 天完整軌道數據 (coverage_cycles=455)

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
echo -e "${MAGENTA}   🎯 RL 訓練數據生成模式 (30 天)${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}   模式: RL 訓練數據生成${NC}"
echo -e "${CYAN}   輸出目錄: $OUTPUT_DIR${NC}"
echo -e "${CYAN}   衛星池: Stage 4 優化池 (101 顆衛星)${NC}"
echo -e "${CYAN}   時間跨度: 30 天 (coverage_cycles=455)${NC}"
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
echo -e "${CYAN}   參數                      前端渲染        RL 訓練${NC}"
echo -e "${CYAN}   ────────────────────      ──────────      ─────────${NC}"
echo -e "${CYAN}   時間範圍                  95 分鐘         30 天${NC}"
echo -e "${CYAN}   coverage_cycles           1.0             455${NC}"
echo -e "${CYAN}   時間點數/衛星             190             86,400${NC}"
echo -e "${CYAN}   衛星池                    101 (優化池)    101 (優化池)${NC}"
echo -e "${CYAN}   目標可見衛星              10-15 顆        10-15 顆${NC}"
echo -e "${CYAN}   預期輸出大小 (Stage 2)    ~15 MB          ~6.5 GB${NC}"
echo ""

# 臨時修改配置文件（因為環境變數會被 processor 重新加載的 YAML 覆蓋）
echo -e "${BLUE}🔧 臨時修改 Stage 2 配置文件:${NC}"

STAGE2_CONFIG="$PROJECT_ROOT/config/stage2_orbital_computing_config.yaml"
STAGE2_CONFIG_BACKUP="$PROJECT_ROOT/config/stage2_orbital_computing_config.yaml.rl_backup"

# 備份原始配置
cp "$STAGE2_CONFIG" "$STAGE2_CONFIG_BACKUP"
echo -e "${CYAN}   ✓ 已備份原始配置: ${STAGE2_CONFIG_BACKUP}${NC}"

# 修改配置：coverage_cycles 從 1.0 改為 455（30天）
sed -i 's/coverage_cycles: 1\.0/coverage_cycles: 455/g' "$STAGE2_CONFIG"
echo -e "${CYAN}   ✓ time_series.coverage_cycles: 1.0 → 455${NC}"
echo -e "${CYAN}   ✓ orbital_calculation.coverage_cycles: 1.0 → 455${NC}"

# 修改配置：interval_seconds 從 30 改為 60（降低數據量）
sed -i 's/interval_seconds: 30/interval_seconds: 60/g' "$STAGE2_CONFIG"
echo -e "${CYAN}   ✓ interval_seconds: 30 → 60${NC}"

# 顯示修改後的關鍵配置
echo ""
echo -e "${BLUE}📋 驗證配置修改:${NC}"
grep -E "coverage_cycles|interval_seconds" "$STAGE2_CONFIG" | head -6 | sed 's/^/   /'

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
        if [ "$key" != "ORBIT_ENGINE_OUTPUT_DIR" ]; then
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
echo -e "${YELLOW}⚠️  預計處理時間: 2-4 小時 (101 衛星 × 30 天)${NC}"
echo -e "${YELLOW}⚠️  預計輸出大小: ~10 GB (所有 6 階段)${NC}"
echo -e "${YELLOW}⚠️  建議保留至少 20 GB 磁碟空間${NC}"
echo ""

# 執行主程式（傳遞所有參數，默認執行 Stage 1-4）
if [ $# -eq 0 ]; then
    # 默認執行 Stage 1-4 (RL 訓練只需要 Stage 4 的衛星池數據)
    echo -e "${CYAN}   執行階段: Stage 1-4 (預設)${NC}"
    echo -e "${CYAN}   理由: handover-rl 只需要 Stage 4 優化池數據${NC}"
    echo ""
    python scripts/run_six_stages_with_validation.py --stages 1-4
else
    # 傳遞用戶指定的參數
    python scripts/run_six_stages_with_validation.py "$@"
fi

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
    echo -e "${CYAN}   - Stage 2: $OUTPUT_DIR/stage2/ ← 30 天軌道數據${NC}"
    echo -e "${CYAN}   - Stage 3: $OUTPUT_DIR/stage3/${NC}"
    echo -e "${CYAN}   - Stage 4: $OUTPUT_DIR/stage4/ ← RL 訓練衛星池 (101 顆)${NC}"
    echo ""

    # 顯示輸出文件大小
    if [ -d "$OUTPUT_DIR/stage2" ]; then
        echo -e "${BLUE}   📊 Stage 2 輸出 (30 天軌道數據):${NC}"
        ls -lh "$OUTPUT_DIR/stage2/" | tail -n +2 | sed 's/^/   /'
        echo ""
    fi

    if [ -d "$OUTPUT_DIR/stage4" ]; then
        echo -e "${BLUE}   📊 Stage 4 輸出 (優化池):${NC}"
        ls -lh "$OUTPUT_DIR/stage4/" | tail -n +2 | sed 's/^/   /'
        echo ""
    fi

    echo -e "${CYAN}   下一步:${NC}"
    echo -e "${CYAN}   1. 在 handover-rl 中重新生成預計算表:${NC}"
    echo -e "${CYAN}      cd ../handover-rl${NC}"
    echo -e "${CYAN}      python scripts/generate_orbit_precompute.py \\\\${NC}"
    echo -e "${CYAN}        --start-time \"2025-10-26 00:00:00\" \\\\${NC}"
    echo -e "${CYAN}        --end-time \"2025-11-25 23:59:59\" \\\\${NC}"
    echo -e "${CYAN}        --output data/orbit_precompute_30days_optimized.h5 \\\\${NC}"
    echo -e "${CYAN}        --config configs/diagnostic_config.yaml \\\\${NC}"
    echo -e "${CYAN}        --processes 30 \\\\${NC}"
    echo -e "${CYAN}        --yes${NC}"
    echo ""
    echo -e "${CYAN}   2. 修改 satellite_utils.py 使用 RL 訓練數據:${NC}"
    echo -e "${CYAN}      use_rl_training_data=True${NC}"
    echo ""
    echo -e "${CYAN}   3. 驗證 Level 1 訓練:${NC}"
    echo -e "${CYAN}      python train.py --config configs/diagnostic_config.yaml${NC}"
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

# 恢復原始配置文件
echo ""
echo -e "${BLUE}🔄 恢復原始配置...${NC}"
if [ -f "$STAGE2_CONFIG_BACKUP" ]; then
    mv "$STAGE2_CONFIG_BACKUP" "$STAGE2_CONFIG"
    echo -e "${GREEN}✅ 已恢復原始 Stage 2 配置${NC}"
else
    echo -e "${YELLOW}⚠️  未找到備份文件${NC}"
fi

exit $EXIT_CODE
