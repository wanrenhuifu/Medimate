.PHONY: dev-backend dev-frontend dev

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
