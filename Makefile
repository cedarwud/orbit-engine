# 軌道引擎系統 Makefile
# 簡化開發和部署流程

.PHONY: help build build-n up down dev-up dev-down logs status clean clean-i test health tle-setup tle-status tle-download tle-cleanup
.PHONY: test-runner test-sgp4 test-fast test-coverage check lint performance install-deps setup dev-check release-check view-coverage test-status
.PHONY: test-container-stage1 test-container-stage2 test-container-baseprocessor test-container-all validate-container-stage1 validate-container-stage2 validate-container-all

# 默認目標
help:
	@echo "🚀 軌道引擎系統 Docker 管理"
	@echo ""
	@echo "📦 基本命令:"
	@echo "  build       - 構建 Docker 映像檔"
	@echo "  build-n     - 構建 Docker 映像檔 (無快取)"
	@echo "  up          - 啟動生產環境服務"
	@echo "  down        - 停止生產環境服務"
	@echo "  logs        - 查看服務日誌"
	@echo "  status      - 檢查服務狀態"
	@echo ""
	@echo "🛠️ 開發命令:"
	@echo "  dev-up      - 啟動開發環境 (支援熱重載)"
	@echo "  dev-down    - 停止開發環境"
	@echo "  dev-logs    - 查看開發環境日誌"
	@echo "  dev-exec    - 進入開發容器"
	@echo ""
	@echo "📡 TLE 數據管理:"
	@echo "  tle-setup   - 安裝 TLE 自動下載排程"
	@echo "  tle-status  - 檢查 TLE 下載狀態"
	@echo "  tle-download- 手動下載 TLE 數據"
	@echo "  tle-cleanup - 清理過期 TLE 數據"
	@echo ""
	@echo "🧪 處理命令:"
	@echo "  run-stages  - 執行完整多階段處理"
	@echo "  run-stage1  - 只執行階段1"
	@echo "  run-fast    - 使用 FAST 驗證模式執行"
	@echo "  health      - 健康檢查"
	@echo ""
	@echo "🛠️ 維護命令:"
	@echo "  clean       - 清理未使用的 Docker 資源"
	@echo "  clean-i     - 強制清理專案所有 Docker 資源 (危險!)"
	@echo "  clean-data  - 清理輸出數據 (謹慎使用!)"
	@echo "  test        - 執行測試套件"
	@echo ""
	@echo "🎓 學術合規性:"
	@echo "  compliance         - 檢查學術合規性（手動執行）"
	@echo "  compliance-help    - 顯示檢查指南"

# 📦 基本 Docker 命令
build:
	@echo "🔨 構建六階段處理系統映像檔..."
	docker compose build

build-n:
	@echo "🔨 構建六階段處理系統映像檔 (無快取)..."
	docker compose build --no-cache

up:
	@echo "🚀 啟動六階段處理系統 (生產模式)..."
	docker compose up -d
	@echo "✅ 服務已啟動，使用 'make status' 檢查狀態"

down:
	@echo "🛑 停止六階段處理系統..."
	docker compose down

logs:
	@echo "📋 查看服務日誌..."
	docker compose logs -f --tail=100

status:
	@echo "📊 服務狀態:"
	docker compose ps
	@echo ""
	@echo "🔍 健康狀態:"
	@docker exec satellite-processor python /orbit-engine/scripts/health_check.py 2>/dev/null || echo "❌ 容器未運行或健康檢查失敗"

# 📡 TLE 數據管理命令
tle-setup:
	@echo "📡 安裝 TLE 自動下載排程..."
	@docker exec satellite-processor /orbit-engine/scripts/tle_management/tle_cron_scheduler.sh install || \
	 docker exec orbit-engine-dev /orbit-engine/scripts/tle_management/tle_cron_scheduler.sh install

tle-status:
	@echo "📊 TLE 下載狀態檢查..."
	@docker exec satellite-processor /orbit-engine/scripts/tle_management/tle_cron_scheduler.sh status || \
	 docker exec orbit-engine-dev /orbit-engine/scripts/tle_management/tle_cron_scheduler.sh status

tle-download:
	@echo "🌐 手動下載 TLE 數據..."
	@docker exec satellite-processor /orbit-engine/scripts/tle_management/daily_tle_download_enhanced.sh || \
	 docker exec orbit-engine-dev /orbit-engine/scripts/tle_management/daily_tle_download_enhanced.sh

tle-download-force:
	@echo "⚡ 強制重新下載 TLE 數據..."
	@docker exec satellite-processor /orbit-engine/scripts/tle_management/daily_tle_download_enhanced.sh --force || \
	 docker exec orbit-engine-dev /orbit-engine/scripts/tle_management/daily_tle_download_enhanced.sh --force

tle-cleanup:
	@echo "🧹 清理過期 TLE 數據..."
	@docker exec satellite-processor /orbit-engine/scripts/tle_management/intelligent_data_cleanup.sh || \
	 docker exec orbit-engine-dev /orbit-engine/scripts/tle_management/intelligent_data_cleanup.sh

tle-logs:
	@echo "📋 查看 TLE 下載日誌..."
	@docker exec satellite-processor /orbit-engine/scripts/tle_management/tle_cron_scheduler.sh logs 50 || \
	 docker exec orbit-engine-dev /orbit-engine/scripts/tle_management/tle_cron_scheduler.sh logs 50

# 🛠️ 開發環境命令
dev-up:
	@echo "🛠️ 啟動開發環境..."
	docker compose up -d
	@echo "✅ 開發環境已啟動"
	@echo "💡 進入容器: make dev-exec"
	@echo "🚀 執行處理: make dev-run-stages"

dev-down:
	@echo "🛑 停止開發環境..."
	docker compose down

dev-logs:
	@echo "📋 開發環境日誌..."
	docker compose logs -f --tail=50

dev-exec:
	@echo "🖥️ 進入開發容器..."
	docker exec -it orbit-engine-dev bash

dev-status:
	@echo "📊 開發環境狀態:"
	docker compose ps

# 🧪 六階段處理命令
run-stages:
	@echo "🚀 執行完整六階段處理..."
	docker exec satellite-processor python /orbit-engine/scripts/run_six_stages_with_validation.py --validation-level=STANDARD

run-fast:
	@echo "⚡ 執行六階段處理 (FAST 模式)..."
	docker exec satellite-processor python /orbit-engine/scripts/run_six_stages_with_validation.py --validation-level=FAST

run-comprehensive:
	@echo "🔍 執行六階段處理 (COMPREHENSIVE 模式)..."
	docker exec satellite-processor python /orbit-engine/scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE

run-stage1:
	@echo "📡 執行階段1 (TLE軌道計算)..."
	docker exec satellite-processor python /orbit-engine/scripts/run_six_stages_with_validation.py --stage=1

run-stage6:
	@echo "🌐 執行階段6 (動態池規劃)..."
	docker exec satellite-processor python /orbit-engine/scripts/run_six_stages_with_validation.py --stage=6

# 開發環境處理命令
dev-run-stages:
	@echo "🛠️ 開發環境：執行完整六階段處理..."
	docker exec orbit-engine-dev python /orbit-engine/scripts/run_six_stages_with_validation.py --validation-level=FAST

dev-run-stage:
	@echo "🛠️ 開發環境：執行階段 $(STAGE)..."
	docker exec orbit-engine-dev python /orbit-engine/scripts/run_six_stages_with_validation.py --stage=$(STAGE) --validation-level=FAST

# 🔍 健康和監控
health:
	@echo "🔍 執行健康檢查..."
	@docker exec satellite-processor python /orbit-engine/scripts/health_check.py || \
	 docker exec orbit-engine-dev python /orbit-engine/scripts/health_check.py 2>/dev/null || \
	 echo "❌ 無法執行健康檢查 - 請確認容器運行狀態"

show-outputs:
	@echo "📂 查看輸出目錄:"
	@docker exec satellite-processor ls -la /orbit-engine/data/outputs/ 2>/dev/null || \
	 docker exec orbit-engine-dev ls -la /orbit-engine/data/outputs/ 2>/dev/null || \
	 echo "❌ 無法訪問輸出目錄"

show-validation:
	@echo "📋 查看驗證快照:"
	@docker exec satellite-processor ls -la /orbit-engine/data/validation_snapshots/ 2>/dev/null || \
	 docker exec orbit-engine-dev ls -la /orbit-engine/data/validation_snapshots/ 2>/dev/null || \
	 echo "❌ 無法訪問驗證目錄"

# 🧪 測試命令
test:
	@echo "🧪 執行測試套件..."
	@docker exec satellite-processor python -m pytest /orbit-engine/tests/ -v 2>/dev/null || \
	 docker exec orbit-engine-dev python -m pytest /orbit-engine/tests/ -v 2>/dev/null || \
	 echo "❌ 無法執行測試 - 請確認容器運行狀態"

# 🛠️ 維護命令
clean:
	@echo "🧹 清理未使用的 Docker 資源..."
	docker system prune -f
	docker volume prune -f

clean-i:
	@echo "⚠️ 強制清理軌道引擎專案所有 Docker 資源..."
	@read -p "確定要清理所有容器、映像檔、網路和卷宗嗎? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "🛑 停止所有相關容器..."; \
		docker compose down --volumes --remove-orphans 2>/dev/null || true; \
		docker compose down --volumes --remove-orphans 2>/dev/null || true; \
		echo "🗑️ 刪除相關容器..."; \
		docker rm -f orbit-engine-dev orbit-postgres-dev orbit-dev-monitor 2>/dev/null || true; \
		echo "🗑️ 刪除相關映像檔..."; \
		docker rmi -f orbit-engine-dev orbit-engine-orbit-engine-dev postgres:15 alpine:latest 2>/dev/null || true; \
		echo "🗑️ 刪除相關網路..."; \
		docker network rm orbit-engine-dev-network 2>/dev/null || true; \
		echo "🗑️ 清理未使用資源..."; \
		docker system prune -f --volumes; \
		echo "✅ 軌道引擎專案 Docker 資源已完全清理"; \
	else \
		echo "❌ 取消清理"; \
	fi

clean-data:
	@echo "⚠️ 清理輸出數據目錄..."
	@read -p "確定要清理所有輸出數據嗎? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker exec satellite-processor rm -rf /orbit-engine/data/outputs/* 2>/dev/null || true; \
		docker exec satellite-processor rm -rf /orbit-engine/data/validation_snapshots/* 2>/dev/null || true; \
		docker exec orbit-engine-dev rm -rf /orbit-engine/data/outputs/* 2>/dev/null || true; \
		docker exec orbit-engine-dev rm -rf /orbit-engine/data/validation_snapshots/* 2>/dev/null || true; \
		echo "✅ 數據已清理"; \
	else \
		echo "❌ 取消清理"; \
	fi

restart:
	@echo "🔄 重啟服務..."
	make down
	make up

dev-restart:
	@echo "🔄 重啟開發環境..."
	make dev-down
	make dev-up

# 📊 信息命令
info:
	@echo "ℹ️ 六階段處理系統信息:"
	@echo "  🏗️ 項目名稱: Six Stages Orbit Engine System"
	@echo "  📦 Docker 映像: orbit-engine-system"
	@echo "  🌐 網路: satellite-network (172.30.0.0/16)"
	@echo "  📂 數據目錄: ./data/"
	@echo "  🔧 配置文件: ./config/"
	@echo "  📝 源碼目錄: ./src/"
	@echo ""
	@echo "📋 快速啟動:"
	@echo "  1. make build        # 首次構建"
	@echo "  2. make up          # 啟動服務"  
	@echo "  3. make run-stages  # 執行處理"
	@echo ""
	@echo "🛠️ 開發模式:"
	@echo "  1. make dev-up       # 啟動開發環境"
	@echo "  2. make dev-exec     # 進入容器"
	@echo "  3. make dev-run-stages  # 執行處理"

# =============================================================================
# 🧪 測試和CI/CD命令 (TDD重構)
# =============================================================================

# 顏色定義
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m

# 測試相關命令
test-runner: ## 執行完整測試套件 (推薦)
	@echo "$(BLUE)🚀 執行完整測試套件$(NC)"
	@./scripts/test-runner.sh

test-sgp4: ## 僅執行SGP4軌道引擎測試
	@echo "$(BLUE)🛰️ 執行SGP4測試$(NC)"
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py -v

test-fast: ## 快速測試 (僅關鍵測試)
	@echo "$(BLUE)⚡ 快速測試$(NC)"
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_tle_epoch_time_usage_mandatory -v

test-coverage: ## 生成測試覆蓋率報告
	@echo "$(BLUE)📊 生成覆蓋率報告$(NC)"
	python -m pytest tests/unit/ --cov=src --cov-report=html:tests/reports/coverage_html --cov-report=term-missing
	@echo "$(GREEN)📈 覆蓋率報告: tests/reports/coverage_html/index.html$(NC)"

# 代碼品質檢查
check: ## 執行預提交檢查
	@echo "$(BLUE)🛡️ 執行預提交檢查$(NC)"
	@./scripts/pre-commit-check.sh

lint: ## 檢查代碼語法 (輕量級)
	@echo "$(BLUE)🐍 檢查Python語法$(NC)"
	python -m py_compile src/shared/engines/sgp4_orbital_engine.py
	@echo "$(GREEN)✅ 語法檢查通過$(NC)"

# 性能測試
performance: ## 執行性能基準測試
	@echo "$(BLUE)⚡ 性能基準測試$(NC)"
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_sgp4_calculation_performance -v
	python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_batch_calculation_performance -v

# 開發流程快捷命令
dev-check: check test-sgp4 ## 開發檢查 (預提交 + 核心測試)
	@echo "$(GREEN)🎉 開發檢查完成！$(NC)"

release-check: test-runner test-coverage ## 發布檢查 (完整測試 + 覆蓋率)
	@echo "$(GREEN)🚀 發布檢查完成！$(NC)"

# 測試環境設置
install-deps: ## 安裝測試依賴
	@echo "$(BLUE)📦 安裝測試依賴$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ 依賴安裝完成$(NC)"

# 🐳 容器測試和驗證命令
test-container-stage1: ## 容器內執行Stage 1 TDD測試
	@echo "$(BLUE)🐳 容器內Stage 1測試$(NC)"
	@./scripts/test-in-container.sh stage1

test-container-stage2: ## 容器內執行Stage 2 TDD測試
	@echo "$(BLUE)🐳 容器內Stage 2測試$(NC)"
	@./scripts/test-in-container.sh stage2

test-container-baseprocessor: ## 容器內執行BaseProcessor接口測試
	@echo "$(BLUE)🐳 容器內BaseProcessor測試$(NC)"
	@./scripts/test-in-container.sh baseprocessor

test-container-all: ## 容器內執行所有TDD測試
	@echo "$(BLUE)🐳 容器內所有測試$(NC)"
	@./scripts/test-in-container.sh all

# 容器內驗證命令
validate-container-stage1: ## 容器內驗證Stage 1輸出
	@echo "$(BLUE)🔍 容器內Stage 1驗證$(NC)"
	@docker exec orbit-engine-dev bash -c "cd /orbit-engine && PYTHONPATH=src python scripts/run_six_stages_with_validation.py --stage 1 --validation-level=FAST"

validate-container-stage2: ## 容器內驗證Stage 2輸出
	@echo "$(BLUE)🔍 容器內Stage 2驗證$(NC)"
	@docker exec orbit-engine-dev bash -c "cd /orbit-engine && PYTHONPATH=src python scripts/run_six_stages_with_validation.py --stage 2 --validation-level=FAST"

validate-container-all: ## 容器內執行完整驗證
	@echo "$(BLUE)🔍 容器內完整驗證$(NC)"
	@docker exec orbit-engine-dev bash -c "cd /orbit-engine && PYTHONPATH=src python scripts/run_six_stages_with_validation.py --validation-level=FAST"

test-setup: install-deps ## 初始化測試環境
	@echo "$(BLUE)🔧 初始化測試環境$(NC)"
	mkdir -p tests/reports
	@echo "$(GREEN)✅ 測試環境設置完成$(NC)"

# 狀態檢查
test-status: ## 顯示測試環境狀態
	@echo "$(BLUE)📊 測試環境狀態$(NC)"
	@echo "================================================================"
	@echo "Python版本: $$(python --version)"
	@echo "pytest版本: $$(python -m pytest --version)"
	@echo "TLE數據文件: $$(ls data/tle_data/starlink/tle/*.tle 2>/dev/null | wc -l) 個"
	@echo "最近測試: $$(ls -t tests/reports/*.html 2>/dev/null | head -1 | xargs ls -l 2>/dev/null || echo '無')"
	@echo "================================================================"

# ═══════════════════════════════════════════════════════════════════════
# 🎓 學術合規性檢查 (Academic Compliance)
# ═══════════════════════════════════════════════════════════════════════

.PHONY: compliance compliance-help

compliance: ## 🔍 檢查學術合規性（手動執行）
	@echo "🔍 運行學術合規性檢查..."
	@echo ""
	@python tools/academic_compliance_checker.py src/

compliance-help: ## 📚 顯示學術合規性幫助
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "🎓 學術合規性檢查系統（手動工具）"
	@echo "═══════════════════════════════════════════════════════════════"
	@echo ""
	@echo "📚 完整標準指南："
	@echo ""
	@echo "  📖 docs/ACADEMIC_STANDARDS.md - 全局學術合規性標準"
	@echo "     適用所有六個階段的開發規範"
	@echo ""
	@echo "───────────────────────────────────────────────────────────────"
	@echo ""
	@echo "🔍 檢查命令："
	@echo ""
	@echo "  # 檢查整個專案"
	@echo "  make compliance"
	@echo ""
	@echo "  # 檢查特定階段"
	@echo "  python tools/academic_compliance_checker.py src/stages/stage1_orbital_calculation/"
	@echo "  python tools/academic_compliance_checker.py src/stages/stage2_orbital_computing/"
	@echo "  python tools/academic_compliance_checker.py src/stages/stage3_coordinate_transformation/"
	@echo "  python tools/academic_compliance_checker.py src/stages/stage4_link_feasibility/"
	@echo "  python tools/academic_compliance_checker.py src/stages/stage5_signal_analysis/"
	@echo "  python tools/academic_compliance_checker.py src/stages/stage6_research_optimization/"
	@echo ""
	@echo "  # 快速關鍵字掃描"
	@echo "  grep -r \"估計\\|假設\\|約\\|大概\\|模擬\" src/ --include=\"*.py\""
	@echo ""
	@echo "───────────────────────────────────────────────────────────────"
	@echo ""
	@echo "✅ 核心原則："
	@echo ""
	@echo "  ❌ 禁止: 估計值、假設參數、模擬數據、簡化算法"
	@echo "  ✅ 要求: 實測數據、學術引用、官方來源、完整實現"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"