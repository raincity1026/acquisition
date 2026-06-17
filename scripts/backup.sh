#!/bin/sh
# PostgreSQL 定时备份。建议加进服务器 crontab（每天凌晨 3 点）：
#   0 3 * * * cd /path/to/acquisition && sh scripts/backup.sh >> backup/backup.log 2>&1
set -e
cd "$(dirname "$0")/.."
mkdir -p backup
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db \
  pg_dump -U "${POSTGRES_USER:-marsian}" "${POSTGRES_DB:-marsian}" \
  | gzip >"backup/marsian-$(date +%F).sql.gz"
echo "$(date '+%F %T') backup -> backup/marsian-$(date +%F).sql.gz"
# 只保留最近 14 天
find backup -name 'marsian-*.sql.gz' -mtime +14 -delete
