FROM python:3.12-slim

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_DEFAULT_INDEX=https://mirrors.tencentyun.com/pypi/simple \
    PIP_INDEX_URL=https://mirrors.tencentyun.com/pypi/simple

# debian 源换清华镜像加速 apt（适配 bookworm 的 deb822 格式）
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends tzdata ca-certificates; \
    rm -rf /var/lib/apt/lists/*

# 用 pip（清华源）装 uv，避开国内访问慢的 ghcr.io
RUN pip install --no-cache-dir uv

WORKDIR /app

# 先装依赖（利用缓存），再拷源码
COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
