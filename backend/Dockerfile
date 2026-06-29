# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # 轻量服务器出网仅 ~900KB/s；uv 默认开十几条并发会把细管子挤爆、吞吐崩塌。
    # 降到 2 条，顺着下，基本吃满带宽。
    UV_CONCURRENT_DOWNLOADS=2 \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# debian 源换清华镜像加速 apt（适配 bookworm 的 deb822 格式）
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends tzdata ca-certificates; \
    rm -rf /var/lib/apt/lists/*

# 用 pip（腾讯内网源）装 uv，避开国内访问慢的 ghcr.io
RUN pip install --no-cache-dir uv

WORKDIR /app

# 1) 只拷依赖清单 → 先装依赖（不装本项目）。依赖不变时这层走缓存，
#    源码改动不会让它失效，避免每次部署全量重下 pandas/akshare 等。
#    --mount=type=cache 把 uv 下载缓存持久化到磁盘，即便层失效也从本地秒装、不重下。
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2) 再拷源码 → 只把本项目装进环境（很快，源码变动只动这层）。
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
