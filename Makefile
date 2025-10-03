# Orbit Engine 快捷命令
# 使用方式: make <命令>

.PHONY: help run run-stage docker docker-stage docker-build docker-shell test clean

# 預設顯示幫助
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🛰️  Orbit Engine - 快捷命令"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📦 本地執行 (虛擬環境):"
	@echo "  make run              - 執行全部六階段"
	@echo "  make run-stage STAGE=1 - 執行指定階段"
	@echo "  make run-stages STAGES=1-3 - 執行階段範圍"
	@echo ""
	@echo "🐳 容器執行:"
	@echo "  make docker           - 容器執行全部六階段"
	@echo "  make docker-stage STAGE=5 - 容器執行指定階段"
	@echo "  make docker-build     - 重新構建容器"
	@echo "  make docker-shell     - 進入容器 shell"
	@echo ""
	@echo "🧪 測試與清理:"
	@echo "  make test             - 執行測試套件"
	@echo "  make clean            - 清理輸出文件"
	@echo ""
	@echo "📚 範例:"
	@echo "  make run-stage STAGE=5         # 本地執行 Stage 5"
	@echo "  make docker-stage STAGE=5      # 容器執行 Stage 5"
	@echo "  make docker-build docker       # 重建後執行"
	@echo ""

# 本地執行 (全部階段)
run:
	@./run.sh

# 本地執行 (指定階段)
run-stage:
	@if [ -z "$(STAGE)" ]; then \
		echo "❌ 請指定階段: make run-stage STAGE=1"; \
		exit 1; \
	fi
	@./run.sh --stage $(STAGE)

# 本地執行 (階段範圍)
run-stages:
	@if [ -z "$(STAGES)" ]; then \
		echo "❌ 請指定範圍: make run-stages STAGES=1-3"; \
		exit 1; \
	fi
	@./run.sh --stages $(STAGES)

# 容器執行 (全部階段)
docker:
	@./run-docker.sh

# 容器執行 (指定階段)
docker-stage:
	@if [ -z "$(STAGE)" ]; then \
		echo "❌ 請指定階段: make docker-stage STAGE=1"; \
		exit 1; \
	fi
	@./run-docker.sh --stage $(STAGE)

# 容器執行 (階段範圍)
docker-stages:
	@if [ -z "$(STAGES)" ]; then \
		echo "❌ 請指定範圍: make docker-stages STAGES=1-3"; \
		exit 1; \
	fi
	@./run-docker.sh --stages $(STAGES)

# 重新構建容器
docker-build:
	@./run-docker.sh --build

# 進入容器 shell
docker-shell:
	@./run-docker.sh --shell

# 執行測試
test:
	@echo "🧪 執行測試套件..."
	@source venv/bin/activate && python -m pytest tests/ -v

# 執行 ITU-Rpy 驗證測試
test-itur:
	@echo "🧪 執行 ITU-Rpy 驗證測試..."
	@source venv/bin/activate && python -m pytest tests/test_itur_official_validation.py -v

# 清理輸出文件
clean:
	@echo "🧹 清理輸出文件..."
	@rm -rf data/outputs/stage*/*.json
	@rm -rf data/validation_snapshots/*.json
	@echo "✅ 清理完成"

# 顯示環境狀態
status:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 Orbit Engine 環境狀態"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "虛擬環境:"
	@if [ -d "venv" ]; then \
		echo "  ✅ 已建立 (venv/)"; \
	else \
		echo "  ❌ 未建立"; \
	fi
	@echo ""
	@echo "環境配置:"
	@if [ -f ".env" ]; then \
		echo "  ✅ .env 已配置"; \
		grep -E "^[^#].*=" .env | sed 's/^/     /'; \
	else \
		echo "  ❌ .env 未配置"; \
	fi
	@echo ""
	@echo "容器鏡像:"
	@if docker images | grep -q "orbit-engine"; then \
		echo "  ✅ orbit-engine 已構建"; \
	else \
		echo "  ❌ orbit-engine 未構建"; \
	fi
	@echo ""
