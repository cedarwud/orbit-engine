#!/bin/bash

# 容器內測試執行腳本 - 統一測試環境
# 用途: 確保所有測試都在容器環境內執行，避免環境不一致問題

set -e

CONTAINER_NAME="orbit-engine-dev"
WORK_DIR="/orbit-engine"

echo "🐳 容器內測試執行器 - Orbit Engine"
echo "=================================="

# 檢查容器是否運行
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ 錯誤: 容器 $CONTAINER_NAME 未運行"
    echo "請先啟動容器: docker run --name $CONTAINER_NAME ..."
    exit 1
fi

echo "✅ 容器 $CONTAINER_NAME 運行中"

# 解析參數
TEST_TARGET="${1:-all}"

case $TEST_TARGET in
    "stage1")
        echo "🧪 執行 Stage 1 TDD 測試..."
        docker exec $CONTAINER_NAME bash -c "cd $WORK_DIR && PYTHONPATH=src python -m pytest tests/unit/stages/ -k stage1 -v"
        ;;
    "stage2")
        echo "🧪 執行 Stage 2 TDD 測試..."
        docker exec $CONTAINER_NAME bash -c "cd $WORK_DIR && PYTHONPATH=src python -m pytest tests/unit/stages/ -k stage2 -v"
        ;;
    "baseprocessor"|"interface")
        echo "🧪 執行 BaseProcessor 接口測試..."
        docker exec $CONTAINER_NAME bash -c "cd $WORK_DIR && PYTHONPATH=src python -m pytest tests/unit/shared/test_base_processor_interface.py -v"
        ;;
    "all")
        echo "🧪 執行所有 TDD 測試..."
        docker exec $CONTAINER_NAME bash -c "cd $WORK_DIR && PYTHONPATH=src python -m pytest tests/unit/shared/test_base_processor_interface.py -v"
        ;;
    *)
        echo "使用方式: $0 [stage1|stage2|baseprocessor|all]"
        echo "範例:"
        echo "  $0 stage1        - 測試 Stage 1"
        echo "  $0 stage2        - 測試 Stage 2"
        echo "  $0 baseprocessor - 測試 BaseProcessor 接口"
        echo "  $0 all           - 執行所有測試 (預設)"
        exit 1
        ;;
esac

echo "✅ 容器內測試執行完成"