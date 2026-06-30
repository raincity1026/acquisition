# syntax=docker/dockerfile:1
FROM python:3.12-slim

# 在服务器(国内)上构建：用阿里源(域内)+ 单线程下载。
# 关键：UV_CONCURRENT_DOWNLOADS=1 —— 这台轻量服务器多并发会把出网挤崩，
# 单流才能吃满 ~900KB/s(已由 pip 单连接验证)。
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CONCURRENT_DOWNLOADS=1 \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# debian 源换清华镜像加速 apt
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends tzdata ca-certificates; \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# 1) 只拷依赖清单 → 先装依赖(不装本项目)。依赖不变走缓存，源码改动不失效。
#    --mount=type=cache 把 uv 下载缓存留在服务器磁盘，重建也从本地秒装。
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2) 再拷源码 → 只把本项目装进环境(很快)。
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
