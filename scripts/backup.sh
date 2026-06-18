#!/bin/sh
# PostgreSQL 定时备份。建议加进服务器 crontab（每天凌晨 3 点）：
#   0 3 * * * cd /path/to/acquisition && sh scripts/backup.sh >> backup/backup.log 2>&1
set -e
cd "$(dirname "$0")/.."

# 从 .env.prod 读取用户名/库名，保证与实际部署一致（别用硬编码默认值）
if [ -f .env.prod ]; then
  set -a
  . ./.env.prod
  set +a
fi
PG_USER="${POSTGRES_USER:?请在 .env.prod 设置 POSTGRES_USER}"
PG_DB="${POSTGRES_DB:?请在 .env.prod 设置 POSTGRES_DB}"

mkdir -p backup
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$PG_USER" "$PG_DB" \
  | gzip >"backup/acquisition-$(date +%F).sql.gz"
echo "$(date '+%F %T') backup -> backup/acquisition-$(date +%F).sql.gz"
# 只保留最近 14 天
find backup -name 'acquisition-*.sql.gz' -mtime +14 -delete
