.PHONY: dev-backend dev-frontend dev init-data

# 导入药品说明书数据到 RAG 向量库（首次运行或数据更新时执行）
init-data:
	cd backend && python -m rag.pipeline --input_dir data/package_inserts

# 开发模式启动后端
dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

# 开发模式启动前端
dev-frontend:
	cd frontend && npm run dev

# 一键启动说明
dev:
	@echo "请在两个终端分别运行："
	@echo "  make dev-backend"
	@echo "  make dev-frontend"
