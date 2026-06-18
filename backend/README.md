# acquisition — backend

盘后 A 股复盘工具的后端。M0 打通最小数据链：Baostock → 标准化 → PostgreSQL → `GET /api/kline`。

## 本地开发

```bash
cp .env.example .env
docker compose up -d            # 起本地 PostgreSQL (端口 5433)
uv sync                         # 安装依赖
uv run alembic upgrade head     # 建表
uv run uvicorn app.main:app --reload
```

## 质量门禁

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy app
uv run pytest                   # 加 -m "not integration" 跳过触网测试
```

技术栈：FastAPI + SQLAlchemy 2.0(async) + asyncpg + Alembic；uv / ruff / mypy(strict) / pytest。
设计规格见 `../docs/M0_核心模块设计规格.md`。
