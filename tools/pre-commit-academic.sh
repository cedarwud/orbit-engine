#!/bin/bash
#
# Git Pre-commit Hook - 學術合規性自動檢查
#
# 安裝方式:
#   cp tools/pre-commit-academic.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# 功能:
#   - 在 git commit 前自動運行學術合規性檢查
#   - 如果發現 CRITICAL 違規，阻止提交
#   - 提供修正建議

echo "🔍 執行學術合規性檢查..."
echo ""

# 只檢查即將提交的 Python 文件
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep ".py$")

if [ -z "$STAGED_FILES" ]; then
    echo "✅ 沒有 Python 文件變更，跳過檢查"
    exit 0
fi

echo "📄 檢查文件:"
echo "$STAGED_FILES" | sed 's/^/   - /'
echo ""

# 創建臨時目錄存放暫存的文件
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# 複製暫存的文件到臨時目錄
for FILE in $STAGED_FILES; do
    mkdir -p "$TEMP_DIR/$(dirname $FILE)"
    git show ":$FILE" > "$TEMP_DIR/$FILE"
done

# 運行合規性檢查（只檢查暫存的文件）
CHECK_RESULT=0
for FILE in $STAGED_FILES; do
    python tools/academic_compliance_checker.py "$TEMP_DIR/$FILE" >> /tmp/compliance_check.log 2>&1
    if [ $? -ne 0 ]; then
        CHECK_RESULT=1
    fi
done

# 顯示檢查結果
cat /tmp/compliance_check.log

if [ $CHECK_RESULT -ne 0 ]; then
    echo ""
    echo "❌ 學術合規性檢查失敗"
    echo ""
    echo "🔧 修正建議:"
    echo "   1. 查看上方違規詳情"
    echo "   2. 參考 docs/ACADEMIC_COMPLIANCE_GUIDE.md"
    echo "   3. 修正後重新提交"
    echo ""
    echo "⚠️ 如需強制提交 (不建議):"
    echo "   git commit --no-verify"
    echo ""
    exit 1
fi

echo ""
echo "✅ 學術合規性檢查通過，允許提交"
exit 0
