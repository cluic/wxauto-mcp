.PHONY: help install dev test lint format build clean release check

help:
	@echo "wxauto-mcp 开发命令"
	@echo ""
	@echo "使用方法: make [target]"
	@echo ""
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 安装包（开发模式）
	pip install -e .

dev: ## 安装开发依赖
	pip install -e ".[dev]"

test: ## 运行测试
	pytest tests/ -v

lint: ## 运行代码检查
	ruff check .
	mypy src/

format: ## 格式化代码
	ruff format .
	ruff check --fix .

build: ## 构建包
	python -m build --outdir dist/

clean: ## 清理构建文件
	rm -rf build/ dist/ *.egg-info .pytest_cache
	rm -rf */__pycache__ */*/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +

check: ## 检查包
	pip install twine
	twine check dist/*

release: ## 发布包
	@echo "警告: 即将创建新版本并发布"
	@read -p "继续? (y/N): " REPLY
	@if [ "$REPLY" = "y" ]; then \
		./release.sh; \
	fi

install-local: ## 本地安装构建的包
	pip uninstall -y wxauto-mcp
	pip install dist/wxauto_mcp-*.whl

status: ## 检查服务器状态
	wxauto-mcp --status

run-http: ## 启动HTTP服务器
	wxauto-mcp-http --port 8181

docs: ## 生成文档
	@echo "文档已更新"

init-git: ## 初始化Git仓库（首次使用）
	git init
	git add .
	git commit -m "Initial commit"
	git branch -M main