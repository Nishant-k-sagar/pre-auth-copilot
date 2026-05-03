#!/bin/bash
#
# Simple Uptime Script using curl
#
# This is a lightweight alternative that uses curl instead of Python.
# Ideal for cron jobs or systems without Python dependencies.
#
# Usage:
#   ./uptime_cron.sh
#
# Add to crontab (runs every 10 minutes):
#   */10 * * * * /path/to/uptime_cron.sh >> /var/log/uptime.log 2>&1
#

set -e

# Configuration
BACKEND_URL="${BACKEND_URL:-https://preauth-backend.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://preauth-frontend.onrender.com}"
LOG_FILE="${LOG_FILE:-/tmp/uptime.log}"

# Timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Ping backend
log "Pinging backend: $BACKEND_URL/api/health"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${BACKEND_URL}/api/health" 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    log "Backend: OK (200)"
else
    log "Backend: FAILED (status: $BACKEND_STATUS)"
fi

# Ping frontend
log "Pinging frontend: $FRONTEND_URL"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    log "Frontend: OK (200)"
else
    log "Frontend: FAILED (status: $FRONTEND_STATUS)"
fi

log "Ping cycle complete"