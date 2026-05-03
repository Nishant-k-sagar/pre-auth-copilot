#!/bin/bash
#
# Uptime Monitor Wrapper Script for Render Services
#
# This script provides a simple way to run the uptime monitor.
# It can be used with cron or as a background process.
#
# Usage:
#   ./uptime_monitor.sh [--once] [--interval SECONDS]
#
# Options:
#   --once       Run a single ping cycle and exit
#   --interval   Override the ping interval (in seconds)
#   --help       Show this help message
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/uptime_config.yaml"

# Default values
RUN_ONCE=false
INTERVAL=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --once)
            RUN_ONCE=true
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --help)
            head -15 "$0" | tail -12
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build command
CMD="python ${SCRIPT_DIR}/uptime_monitor.py --config ${CONFIG_FILE}"

if [ "$RUN_ONCE" = true ]; then
    CMD="$CMD --once"
fi

if [ -n "$INTERVAL" ]; then
    CMD="$CMD --interval $INTERVAL"
fi

# Run the monitor
echo "Starting uptime monitor..."
echo "Command: $CMD"
exec $CMD