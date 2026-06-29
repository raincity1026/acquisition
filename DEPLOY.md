# 部署手册（M4 上云）

一台轻量云服务器 + Docker Compose：**nginx（前端 + 反代）+ FastAPI（后端 + 盘后定时任务）+ PostgreSQL**。
镜像由 **GitHub Actions 构建并推到腾讯云 TCR**，服务器只 `pull` 启动（不在本机构建）。

---

## CI/CD：GitHub Actions + 腾讯云 TCR

push 到 `main` → GitHub runner 构建后端/前端镜像 → 推 TCR → SSH 到服务器 `docker compose pull && up -d`。

**一次性配置：**
1. 腾讯云开通 **容器镜像服务 TCR（个人版，免费）**，设访问凭证、建命名空间，建两个仓库 `acquisition-backend`、`acquisition-web`（首次推送一般自动创建）。
2. GitHub 仓库 Secrets：`TCR_REGISTRY`(=`ccr.ccs.tencentyun.com`)、`TCR_NAMESPACE`、`TCR_USERNAME`、`TCR_PASSWORD`，以及部署用的 `SSH_HOST`/`SSH_USER`/`SSH_KEY`。
3. 服务器 `.env.prod` 里加 `TCR_REGISTRY` 和 `TCR_NAMESPACE`（compose 拼镜像名用，见 `.env.prod.example`）。

之后合并到 `main` 即自动部署；也可在 Actions 页 `Run workflow` 手动触发。

**服务器手动部署（不走 CI 时）：**
```bash
cd ~/acquisition && git pull
echo "$TCR_PASSWORD" | docker login ccr.ccs.tencentyun.com -u "$TCR_USERNAME" --password-stdin
docker compose --env-file .env.prod -f docker-compose.prod.yml pull
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

---

## 已配好的（代码侧，无需你动）

- `backend/Dockerfile` + `docker-entrypoint.sh`：起容器时自动 `alembic upgrade head` 再跑 uvicorn；内置 APScheduler 盘后任务。
- `frontend/Dockerfile`：多阶段构建 Vue → nginx 托管静态文件 + 反代 `/api` 给后端（同域免跨域）。
- `frontend/nginx.conf`：SPA 路由回退、`/api` 反代、ACME 验证位、HTTPS 模板（注释，签证书后开）。
- `docker-compose.prod.yml`：三服务编排，PostgreSQL 数据持久化到卷 `pgdata`。
- `.env.prod.example`：所有敏感配置走环境变量（`.env.prod` 已 gitignore）。
- `scripts/backup.sh`：`pg_dump` 每日备份（配 crontab）。
- **盘后更新**：交易日 18:30（`Asia/Shanghai`）增量刷新所有已入库标的；非交易日跳过；单只失败隔离 + 重试 + AKShare 降级。可在 `.env.prod` 改 `UPDATE_HOUR/MINUTE`、`SCHEDULER_ENABLED`。

---

## 你要做的（运维侧）

### 1. 选节点 & 买服务器
- **香港节点**（推荐 MVP）：免备案、能抓 A 股数据源。2C2G 起步够用。
- **大陆节点**：访问/数据源最优，但要 **ICP 备案**（提前十几天办）+ 公安备案。
- ❌ 海外 / Vercel：抓不到 A 股数据源，不行。

### 2. 装 Docker
```bash
curl -fsSL https://get.docker.com | sh
```

### 3. 拉代码 + 配置
```bash
git clone <你的仓库> acquisition && cd acquisition
cp .env.prod.example .env.prod
# 编辑 .env.prod：改 POSTGRES_PASSWORD、DATABASE_URL 里的同一密码、
# JWT_SECRET（用 openssl rand -hex 32 生成）
```

### 4. 起服务
```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps        # 看是否 healthy
docker compose -f docker-compose.prod.yml logs -f backend
```
浏览器开 `http://服务器IP` 应能看到登录页。

### 4.5 ⚠️ 一次性导入全市场标的（搜索/自选的数据基础，**必做**）
全新部署 `instruments` 表是空的，不导入则**搜索无结果、加自选 404**（行情仍按需抓，但标的列表要预加载）：
```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml \
  exec backend uv run python -m app.seed_instruments
```
看到 `已导入标的 6xxx 条` 即成功。幂等，可重复跑。**这步同时就是下面第 5 步的连通性验证**——能拉到 6000+ 条即说明云机能访问 baostock。

### 5. ⚠️ 验证云端能抓数据源（spike 的云端版）
若上面 4.5 成功导入 6000+ 条，baostock 连通性已通过。再随便注册个号、搜一只票看图，确认能按需抓到行情即可。
若 4.5 报「所有数据源都拉取标的列表失败」，就是节点连不上数据源（网络/地域问题），换节点或排查。

### 6. 域名 + HTTPS
1. 买域名，DNS A 记录指向服务器 IP。
2. 大陆节点：域名先 **ICP 备案**（没备案大陆无法 80 端口开放）。香港节点跳过。
3. 签证书（webroot 方式，需先放开 `certbot/www`）：
   ```bash
   docker run --rm -v $PWD/certbot/conf:/etc/letsencrypt -v $PWD/certbot/www:/var/www/certbot \
     certbot/certbot certonly --webroot -w /var/www/certbot -d your-domain.com
   ```
4. 打开 `frontend/nginx.conf` 底部 443 注释块、填域名，重建 web：
   ```bash
   docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build web
   ```
5. 证书续期：`certbot renew` 加进 crontab（每月）。

### 7. 配每日备份
```bash
crontab -e
# 加一行：
0 3 * * * cd /path/to/acquisition && sh scripts/backup.sh >> backup/backup.log 2>&1
```

---

## 验收对照（M4 §5）
1. ✅ 定时任务交易日盘后跑 — 容器内 APScheduler（看 backend 日志「盘后更新完成」）
2. ✅ 非交易日不跑 — 交易日历判断
3. ✅ 单只失败不影响其他 — 隔离 + 重试 + 降级
4. 🔧 公网访问前端 + 调后端 — 你做（步骤 4、6）
5. 🔧 HTTPS 绿锁 — 你做（步骤 6）
6. ✅ 容器重启数据不丢 — 卷 `pgdata`
7. 🔧 云节点能抓数据源 — 你验证（步骤 5）
