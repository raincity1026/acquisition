#!/bin/sh
set -e
# 启动前先把数据库迁移到最新，再起服务（含 APScheduler 盘后任务）
uv run alembic upgrade head
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
