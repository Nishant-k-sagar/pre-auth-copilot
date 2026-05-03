# Uptime Monitor Scripts

This directory contains scripts to keep Render services awake by periodically pinging them.

## Why is this needed?

Render's free tier puts services to sleep after 15 minutes of inactivity. This causes a "cold start" delay of 10-30 seconds on the first request after sleeping. Regular pings prevent this delay.

## Available Scripts

### 1. Python Uptime Monitor (`uptime_monitor.py`)

A full-featured async Python script with:
- Concurrent service pinging
- Configurable retry logic
- JSON/YAML config file support
- Environment variable configuration
- Logging to file and console

**Usage:**
```bash
# Run with default config (pings every 10 minutes)
python uptime_monitor.py

# Run once and exit
python uptime_monitor.py --once

# Use custom config file
python uptime_monitor.py --config /path/to/config.yaml

# Override interval (in seconds)
python uptime_monitor.py --interval 300  # 5 minutes
```

**Configuration:**
- Edit `uptime_config.yaml` to customize services and intervals
- Or set environment variables:
  - `BACKEND_URL` - Backend service URL
  - `FRONTEND_URL` - Frontend service URL
  - `PING_INTERVAL` - Ping interval in seconds

### 2. Shell Wrapper (`uptime_monitor.sh`)

A bash wrapper for the Python script.

**Usage:**
```bash
./uptime_monitor.sh           # Run continuously
./uptime_monitor.sh --once    # Run once
./uptime_monitor.sh --interval 300  # Custom interval
```

### 3. Simple Curl Script (`uptime_cron.sh`)

A lightweight bash script using curl, ideal for cron jobs.

**Usage:**
```bash
# Run directly
./uptime_cron.sh

# Add to crontab (every 10 minutes)
*/10 * * * * /path/to/uptime_cron.sh >> /var/log/uptime.log 2>&1
```

**Environment Variables:**
- `BACKEND_URL` - Backend URL (default: https://preauth-backend.onrender.com)
- `FRONTEND_URL` - Frontend URL (default: https://preauth-frontend.onrender.com)
- `LOG_FILE` - Log file path (default: /tmp/uptime.log)

### 4. GitHub Actions (`../.github/workflows/uptime-monitor.yml`)

Automated uptime monitoring using GitHub Actions.

**Features:**
- Runs every 10 minutes via cron
- Can be triggered manually
- No server required

## Recommended Setup

### Option 1: GitHub Actions (Easiest)

1. Commit the workflow file to your repository
2. GitHub Actions will automatically run every 10 minutes
3. No additional setup required

### Option 2: Cron Job

```bash
# Add to crontab
crontab -e

# Add this line to ping every 10 minutes
*/10 * * * * /path/to/backend/scripts/uptime_cron.sh >> /var/log/uptime.log 2>&1
```

### Option 3: Background Process

```bash
# Run in background with nohup
nohup python /path/to/backend/scripts/uptime_monitor.py > /var/log/uptime.log 2>&1 &
```

## Configuration File Format

```yaml
services:
  - name: backend
    url: https://preauth-backend.onrender.com
    ping_path: /api/health
    timeout: 10.0
    expected_status: 200

  - name: frontend
    url: https://preauth-frontend.onrender.com
    ping_path: /
    timeout: 10.0
    expected_status: 200

interval_seconds: 600  # 10 minutes
max_retries: 3
retry_delay: 5.0
timeout: 10.0
```

## Log Files

Logs are written to:
- Console (stdout)
- `backend/outputs/uptime_monitor.log` (Python script)