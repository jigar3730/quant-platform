#!/bin/bash
set -e

# Preserve your environment variables for the cron daemon
printenv | grep -E '^(SMTP_|EMAIL_)' > /etc/environment 2>/dev/null || true

case "${1:-scheduler}" in
  scan)
    echo "Running one-time daily scan..."
    exec quant-daily
    ;;
  scheduler)
    echo "Starting Streamlit Dashboard (quant-view) in the background..."
    # Launches the dashboard on port 5000 and directs logs to dashboard.log
    quant-view --server.port 5000 --server.address 0.0.0.0 > /app/logs/dashboard.log 2>&1 &

    echo "Starting cron scheduler (daily scan at 5 PM ${TZ})..."
    cron
    touch /app/logs/cron.log
    
    # Keeps the container alive and streams the execution logs
    exec tail -F /app/logs/cron.log
    ;;
  *)
    exec "$@"
    ;;
esac