#!/bin/sh
set -e
# 直接用构建时装好的 .venv（uv sync --no-dev 装的），运行时绝不再 sync——
# 否则 `uv run` 会在容器启动时重装环境、还会拉 dev 依赖(ruff/mypy)，又慢又会卡住 uvicorn。
# 启动前先把数据库迁移到最新，再起服务（含 APScheduler 盘后任务）。
.venv/bin/alembic upgrade head
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
