#!/usr/bin/env python3
"""
Uptime Monitor Script for Render Services

This script keeps Render free-tier services awake by periodically pinging them.
Render free services sleep after 15 minutes of inactivity, so regular pings
prevent the cold start delay.

Usage:
    python uptime_monitor.py [--config CONFIG_PATH]

Configuration can be provided via:
1. Environment variables: BACKEND_URL, FRONTEND_URL, PING_INTERVAL
2. Config file (JSON or YAML)
3. Command-line arguments
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).parent.parent / "outputs" / "uptime_monitor.log",
            mode="a",
        ),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a single service to monitor."""

    name: str
    url: str
    timeout: float = 10.0
    expected_status: int = 200
    ping_path: str = "/health"


@dataclass
class MonitorConfig:
    """Main configuration for the uptime monitor."""

    services: List[ServiceConfig] = field(default_factory=list)
    interval_seconds: int = 600  # 10 minutes default
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout: float = 10.0
    log_responses: bool = False


def load_config_from_env() -> MonitorConfig:
    """Load configuration from environment variables."""
    services = []

    # Backend service
    backend_url = os.getenv("BACKEND_URL")
    if backend_url:
        services.append(
            ServiceConfig(
                name="backend",
                url=backend_url.rstrip("/"),
                ping_path="/api/health",
            )
        )

    # Frontend service
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        services.append(
            ServiceConfig(
                name="frontend",
                url=frontend_url.rstrip("/"),
                ping_path="/",
            )
        )

    interval = int(os.getenv("PING_INTERVAL", "600"))

    return MonitorConfig(
        services=services,
        interval_seconds=interval,
    )


def load_config_from_file(config_path: Path) -> MonitorConfig:
    """Load configuration from a JSON or YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        if config_path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    services = [
        ServiceConfig(
            name=s["name"],
            url=s["url"].rstrip("/"),
            timeout=s.get("timeout", 10.0),
            expected_status=s.get("expected_status", 200),
            ping_path=s.get("ping_path", "/health"),
        )
        for s in data.get("services", [])
    ]

    return MonitorConfig(
        services=services,
        interval_seconds=data.get("interval_seconds", 600),
        max_retries=data.get("max_retries", 3),
        retry_delay=data.get("retry_delay", 5.0),
        timeout=data.get("timeout", 10.0),
        log_responses=data.get("log_responses", False),
    )


def get_default_config() -> MonitorConfig:
    """Get default configuration for the preauth project."""
    return MonitorConfig(
        services=[
            ServiceConfig(
                name="backend",
                url="https://preauth-backend.onrender.com",
                ping_path="/api/health",
            ),
            ServiceConfig(
                name="frontend",
                url="https://preauth-frontend.onrender.com",
                ping_path="/",
            ),
        ],
        interval_seconds=600,  # Ping every 10 minutes
        max_retries=3,
        retry_delay=5.0,
    )


class UptimeMonitor:
    """Monitors and keeps services awake by periodic pinging."""

    def __init__(self, config: MonitorConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            follow_redirects=True,
        )
        self._running = False

    async def ping_service(self, service: ServiceConfig) -> Dict[str, Any]:
        """Ping a single service and return the result."""
        url = f"{service.url}{service.ping_path}"
        result = {
            "service": service.name,
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "error": None,
        }

        start_time = datetime.now()

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.get(url)
                result["status_code"] = response.status_code
                result["response_time_ms"] = (
                    datetime.now() - start_time
                ).total_seconds() * 1000

                if response.status_code == service.expected_status:
                    result["success"] = True
                    logger.info(
                        f"Ping successful: {service.name} "
                        f"({response.status_code}) - "
                        f"{result['response_time_ms']:.0f}ms"
                    )
                    break
                else:
                    result["error"] = f"Unexpected status: {response.status_code}"
                    logger.warning(
                        f"Ping returned unexpected status: {service.name} "
                        f"({response.status_code})"
                    )

            except httpx.TimeoutException:
                result["error"] = "Request timed out"
                logger.warning(
                    f"Ping timeout (attempt {attempt + 1}/{self.config.max_retries}): "
                    f"{service.name}"
                )

            except httpx.ConnectError as e:
                result["error"] = f"Connection error: {e}"
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{self.config.max_retries}): "
                    f"{service.name} - {e}"
                )

            except Exception as e:
                result["error"] = f"Unexpected error: {e}"
                logger.error(
                    f"Unexpected error pinging {service.name}: {e}"
                )

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay)

        return result

    async def ping_all_services(self) -> List[Dict[str, Any]]:
        """Ping all configured services concurrently."""
        tasks = [self.ping_service(service) for service in self.config.services]
        return await asyncio.gather(*tasks)

    async def run_once(self) -> List[Dict[str, Any]]:
        """Run a single ping cycle."""
        logger.info("Starting ping cycle...")
        results = await self.ping_all_services()

        success_count = sum(1 for r in results if r["success"])
        logger.info(
            f"Ping cycle complete: {success_count}/{len(results)} services responsive"
        )

        return results

    async def run_forever(self) -> None:
        """Run the monitor continuously."""
        self._running = True
        logger.info(
            f"Starting uptime monitor with {self.config.interval_seconds}s interval"
        )

        while self._running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Error during ping cycle: {e}")

            await asyncio.sleep(self.config.interval_seconds)

    def stop(self) -> None:
        """Stop the monitor."""
        self._running = False
        logger.info("Stopping uptime monitor...")

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.aclose()


async def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Uptime monitor for Render services"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (JSON or YAML)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ping cycle and exit",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Override ping interval in seconds",
    )
    args = parser.parse_args()

    # Load configuration
    if args.config:
        config = load_config_from_file(args.config)
    elif os.getenv("BACKEND_URL") or os.getenv("FRONTEND_URL"):
        config = load_config_from_env()
    else:
        config = get_default_config()

    if args.interval:
        config.interval_seconds = args.interval

    if not config.services:
        logger.error("No services configured for monitoring")
        return 1

    monitor = UptimeMonitor(config)

    try:
        if args.once:
            results = await monitor.run_once()
            return 0 if all(r["success"] for r in results) else 1
        else:
            await monitor.run_forever()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        monitor.stop()
    finally:
        await monitor.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)