#!/bin/bash
set -e

printenv | grep -E '^(SMTP_|EMAIL_)' > /etc/environment 2>/dev/null || true

case "${1:-scheduler}" in
  scan)
    echo "Running one-time daily scan..."
    exec quant-daily
    ;;
  scheduler)
    echo "Starting cron scheduler (daily scan at 5 PM ${TZ})..."
    cron
    touch /app/logs/cron.log
    tail -F /app/logs/cron.log
    ;;
  *)
    exec "$@"
    ;;
esac
