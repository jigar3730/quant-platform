#!/bin/bash
set -e

# 1. Ensure the logs directory and log file exist so cron doesn't throw errors
mkdir -p /app/logs
touch /app/logs/cron.log /app/logs/dashboard.log

# 2. Preserve environment variables so the cron daemon can read them.
# Filters for SMTP, EMAIL, your TimeZone, and crucial system paths.
printenv | grep -E '^(SMTP_|EMAIL_|TZ=|PATH=|PYTHONPATH=)' > /etc/environment 2>/dev/null || true

case "${1:-scheduler}" in
  scan)
    echo "Running one-time daily scan..."
    exec quant-daily
    ;;
    
  scheduler)
    echo "Starting Streamlit Dashboard (quant-view) in the background..."
    # Launches the dashboard on port 5000 and directs logs cleanly to dashboard.log
    quant-view --server.port 5000 --server.address 0.0.0.0 > /app/logs/dashboard.log 2>&1 &

    echo "Starting cron scheduler (breakout 5:17 PM, swing 5:27 PM, lynch Fri 6:17 PM ${TZ})..."
    
    # Exec into cron in the foreground. This becomes Process 1 (PID 1), 
    # keeping the container running permanently and executing your schedules.
    exec cron -f
    ;;
    
  *)
    exec "$@"
    ;;
esac