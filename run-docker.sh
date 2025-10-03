#!/bin/bash
# Orbit Engine 容器快速執行腳本

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 顯示使用說明
show_usage() {
    echo -e "${CYAN}用法:${NC}"
    echo "  $0                    # 執行全部六階段（容器）"
    echo "  $0 --stage 1          # 只執行階段 1（容器）"
    echo "  $0 --stages 1-3       # 執行階段 1-3（容器）"
    echo "  $0 --build            # 重新構建容器"
    echo "  $0 --shell            # 進入容器 shell"
    echo "  $0 --help             # 顯示幫助"
    echo ""
    echo -e "${CYAN}範例:${NC}"
    echo "  $0 --stage 5          # 容器中執行 Stage 5（驗證 ITU-Rpy）"
    echo "  $0 --build --stage 1  # 重新構建後執行 Stage 1"
    exit 0
}

# 檢查 --help
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🐳 Orbit Engine - Docker 容器執行${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 切換到專案目錄
cd "$(dirname "$0")"

# 容器和鏡像名稱
IMAGE_NAME="orbit-engine"
CONTAINER_NAME="orbit-engine-run"

# 處理 --build 參數
if [[ "$1" == "--build" ]]; then
    echo -e "${YELLOW}🔨 重新構建容器鏡像...${NC}"
    docker build -t $IMAGE_NAME .
    BUILD_EXIT=$?
    
    if [ $BUILD_EXIT -ne 0 ]; then
        echo -e "${YELLOW}⚠️  構建失敗（退出碼: $BUILD_EXIT）${NC}"
        exit $BUILD_EXIT
    fi
    
    echo -e "${GREEN}✅ 容器鏡像構建完成${NC}"
    echo ""
    
    # 移除 --build 參數，處理剩餘參數
    shift
fi

# 處理 --shell 參數（進入容器 shell）
if [[ "$1" == "--shell" ]]; then
    echo -e "${CYAN}🐚 進入容器 shell...${NC}"
    docker run -it --rm \
        -v $(pwd)/data:/orbit-engine/data \
        -v $(pwd)/config:/orbit-engine/config \
        $IMAGE_NAME /bin/bash
    exit $?
fi

# 檢查鏡像是否存在
if ! docker images | grep -q "^$IMAGE_NAME "; then
    echo -e "${YELLOW}⚠️  容器鏡像不存在，正在構建...${NC}"
    docker build -t $IMAGE_NAME .
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  構建失敗，請檢查 Dockerfile${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 容器鏡像構建完成${NC}"
    echo ""
fi

# 顯示執行模式
if [[ "$1" == "--stage" ]]; then
    echo -e "${CYAN}   執行模式: 容器 - 單一階段 (Stage $2)${NC}"
elif [[ "$1" == "--stages" ]]; then
    echo -e "${CYAN}   執行模式: 容器 - 階段範圍 ($2)${NC}"
else
    echo -e "${CYAN}   執行模式: 容器 - 全部六階段${NC}"
fi
echo ""

# 檢查 .env
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 已找到環境配置: .env（將複製到容器）${NC}"
    echo -e "${BLUE}   配置預覽:${NC}"
    grep -E "^[^#].*=" .env | head -3 | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  未找到 .env 文件，容器將使用內建配置${NC}"
fi

echo ""
echo -e "${BLUE}🚀 開始容器執行...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 構建容器執行命令
DOCKER_CMD="docker run --rm"

# 掛載數據目錄（持久化輸出）
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/data:/orbit-engine/data"

# 掛載配置目錄
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/config:/orbit-engine/config"

# 如果本地有 .env，覆蓋容器內的（確保使用最新配置）
if [ -f ".env" ]; then
    DOCKER_CMD="$DOCKER_CMD -v $(pwd)/.env:/orbit-engine/.env:ro"
fi

# 設置容器名稱
DOCKER_CMD="$DOCKER_CMD --name $CONTAINER_NAME"

# 添加鏡像名稱
DOCKER_CMD="$DOCKER_CMD $IMAGE_NAME"

# 如果有參數，添加執行命令
if [ $# -gt 0 ]; then
    DOCKER_CMD="$DOCKER_CMD python /orbit-engine/scripts/run_six_stages_with_validation.py $@"
fi

# 執行容器
echo -e "${CYAN}執行命令: ${DOCKER_CMD}${NC}"
echo ""

eval $DOCKER_CMD

# 保存退出碼
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 容器執行完成！${NC}"
    echo -e "${GREEN}   輸出位置: $(pwd)/data/outputs/${NC}"
else
    echo -e "${YELLOW}⚠️  容器執行結束（退出碼: $EXIT_CODE）${NC}"
fi

exit $EXIT_CODE
