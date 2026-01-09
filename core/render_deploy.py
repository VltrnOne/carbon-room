"""
Carbon Room Render Integration
==============================
Deploy and manage Carbon Room on Render.com.
Includes health checks, auto-scaling config, and deployment triggers.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

import httpx

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Render API base URL
RENDER_API_URL = "https://api.render.com/v1"


class RenderDeployError(Exception):
    """Base exception for Render deployment operations."""
    pass


class ServiceType(str, Enum):
    """Render service types."""
    WEB_SERVICE = "web_service"
    PRIVATE_SERVICE = "private_service"
    BACKGROUND_WORKER = "background_worker"
    STATIC_SITE = "static_site"
    CRON_JOB = "cron_job"


class ServiceStatus(str, Enum):
    """Render service status."""
    CREATED = "created"
    BUILDING = "building"
    BUILD_FAILED = "build_failed"
    DEPLOYING = "deploying"
    LIVE = "live"
    DEPROVISIONED = "deprovisioned"
    SUSPENDED = "suspended"


class RenderDeploy:
    """
    Render.com deployment manager for Carbon Room.

    Handles:
    - Service deployment and management
    - Health check monitoring
    - Auto-scaling configuration
    - Deploy hooks and triggers
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        service_id: Optional[str] = None,
        deploy_hook: Optional[str] = None
    ):
        """
        Initialize Render deployment manager.

        Args:
            api_key: Render API key (or use RENDER_API_KEY env)
            service_id: Service ID to manage (or use RENDER_SERVICE_ID env)
            deploy_hook: Deploy hook URL (or use RENDER_DEPLOY_HOOK env)
        """
        self.api_key = api_key or settings.RENDER_API_KEY
        self.service_id = service_id or settings.RENDER_SERVICE_ID
        self.deploy_hook = deploy_hook or settings.RENDER_DEPLOY_HOOK

        if not self.api_key:
            logger.warning("Render API key not configured")

    @property
    def is_configured(self) -> bool:
        """Check if Render deployment is properly configured."""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Render API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle Render API response and errors."""
        if response.status_code == 401:
            raise RenderDeployError("Render authentication failed - check API key")

        if response.status_code == 403:
            raise RenderDeployError(f"Render access forbidden: {response.text}")

        if response.status_code == 404:
            raise RenderDeployError(f"Render resource not found: {response.text}")

        if response.status_code == 429:
            raise RenderDeployError("Render API rate limit exceeded")

        if response.status_code >= 400:
            raise RenderDeployError(
                f"Render API error {response.status_code}: {response.text}"
            )

        return response.json() if response.text else {}

    # ========================================================================
    # Service Management
    # ========================================================================

    async def get_service(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get service details.

        Args:
            service_id: Service ID (uses default if not provided)

        Returns:
            Service details dict
        """
        if not self.is_configured:
            return {"error": "Render not configured"}

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                timeout=30.0
            )

        return self._handle_response(response)

    async def list_services(self) -> List[Dict[str, Any]]:
        """
        List all services.

        Returns:
            List of service dicts
        """
        if not self.is_configured:
            return []

        url = f"{RENDER_API_URL}/services"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                timeout=30.0
            )

        result = self._handle_response(response)
        return result.get("services", []) if isinstance(result, dict) else result

    async def get_service_status(
        self,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get service status and health.

        Args:
            service_id: Service ID (uses default if not provided)

        Returns:
            Status dict with 'status', 'health', 'url'
        """
        service = await self.get_service(service_id)

        return {
            "service_id": service.get("id"),
            "name": service.get("name"),
            "status": service.get("status"),
            "type": service.get("type"),
            "url": service.get("serviceDetails", {}).get("url"),
            "region": service.get("serviceDetails", {}).get("region"),
            "created_at": service.get("createdAt"),
            "updated_at": service.get("updatedAt"),
        }

    # ========================================================================
    # Deployment Operations
    # ========================================================================

    async def trigger_deploy(
        self,
        service_id: Optional[str] = None,
        clear_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger a new deployment.

        Args:
            service_id: Service ID (uses default if not provided)
            clear_cache: Whether to clear build cache

        Returns:
            Deploy info dict
        """
        if not self.is_configured:
            return {"error": "Render not configured"}

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}/deploys"

        payload = {}
        if clear_cache:
            payload["clearCache"] = "clear"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=60.0
            )

        result = self._handle_response(response)
        logger.info(f"Deployment triggered for service {service_id}")
        return result

    async def trigger_deploy_hook(self) -> Dict[str, Any]:
        """
        Trigger deployment using deploy hook URL.

        This is the simplest way to trigger a deploy without API authentication.

        Returns:
            Deploy result
        """
        if not self.deploy_hook:
            return {"error": "Deploy hook not configured"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.deploy_hook,
                timeout=60.0
            )

        if response.status_code == 200:
            logger.info("Deploy hook triggered successfully")
            return {"status": "triggered", "message": "Deployment started"}
        else:
            raise RenderDeployError(
                f"Deploy hook failed: {response.status_code} {response.text}"
            )

    async def get_deploys(
        self,
        service_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get deployment history.

        Args:
            service_id: Service ID (uses default if not provided)
            limit: Maximum number of deploys to return

        Returns:
            List of deploy info dicts
        """
        if not self.is_configured:
            return []

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}/deploys"
        params = {"limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0
            )

        result = self._handle_response(response)
        return result.get("deploys", []) if isinstance(result, dict) else result

    async def get_latest_deploy(
        self,
        service_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest deployment.

        Args:
            service_id: Service ID (uses default if not provided)

        Returns:
            Latest deploy info or None
        """
        deploys = await self.get_deploys(service_id, limit=1)
        return deploys[0] if deploys else None

    async def cancel_deploy(
        self,
        deploy_id: str,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a running deployment.

        Args:
            deploy_id: Deploy ID to cancel
            service_id: Service ID (uses default if not provided)

        Returns:
            Cancellation result
        """
        if not self.is_configured:
            return {"error": "Render not configured"}

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}/deploys/{deploy_id}/cancel"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                timeout=30.0
            )

        result = self._handle_response(response)
        logger.info(f"Deploy {deploy_id} cancelled")
        return result

    # ========================================================================
    # Environment Variables
    # ========================================================================

    async def get_env_vars(
        self,
        service_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get environment variables for a service.

        Args:
            service_id: Service ID (uses default if not provided)

        Returns:
            List of env var dicts
        """
        if not self.is_configured:
            return []

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}/env-vars"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                timeout=30.0
            )

        result = self._handle_response(response)
        return result.get("envVars", []) if isinstance(result, dict) else result

    async def set_env_var(
        self,
        key: str,
        value: str,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set an environment variable.

        Args:
            key: Variable name
            value: Variable value
            service_id: Service ID (uses default if not provided)

        Returns:
            Result dict
        """
        if not self.is_configured:
            return {"error": "Render not configured"}

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}/env-vars"

        payload = [{"key": key, "value": value}]

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30.0
            )

        result = self._handle_response(response)
        logger.info(f"Environment variable {key} updated")
        return result

    # ========================================================================
    # Health Checks
    # ========================================================================

    async def check_health(
        self,
        health_url: Optional[str] = None,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check service health endpoint.

        Args:
            health_url: Health check URL (derived from service if not provided)
            service_id: Service ID for URL lookup

        Returns:
            Health check result
        """
        if not health_url:
            status = await self.get_service_status(service_id)
            base_url = status.get("url")
            if not base_url:
                return {"healthy": False, "error": "No service URL available"}
            health_url = f"{base_url}/health"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    health_url,
                    timeout=10.0
                )

            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "url": health_url,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except httpx.TimeoutException:
            return {
                "healthy": False,
                "error": "Health check timed out",
                "url": health_url,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "url": health_url,
                "timestamp": datetime.utcnow().isoformat(),
            }

    # ========================================================================
    # Logs
    # ========================================================================

    async def get_logs(
        self,
        service_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get service logs.

        Args:
            service_id: Service ID (uses default if not provided)
            limit: Maximum number of log entries

        Returns:
            List of log entry dicts
        """
        if not self.is_configured:
            return []

        service_id = service_id or self.service_id
        if not service_id:
            raise RenderDeployError("No service ID provided")

        url = f"{RENDER_API_URL}/services/{service_id}/logs"
        params = {"limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0
            )

        result = self._handle_response(response)
        return result.get("logs", []) if isinstance(result, dict) else result


# ============================================================================
# Render Configuration Generator
# ============================================================================

def generate_render_yaml(
    name: str = "carbon-room",
    repo: str = "",
    branch: str = "main",
    build_command: str = "pip install -r requirements.txt",
    start_command: str = "uvicorn api.server:app --host 0.0.0.0 --port $PORT",
    env_vars: Optional[Dict[str, str]] = None,
    health_check_path: str = "/health",
    auto_deploy: bool = True,
    plan: str = "free",
    region: str = "oregon"
) -> str:
    """
    Generate render.yaml configuration file.

    Args:
        name: Service name
        repo: GitHub repository URL
        branch: Git branch to deploy
        build_command: Build command
        start_command: Start command
        env_vars: Environment variables
        health_check_path: Health check endpoint path
        auto_deploy: Enable auto-deploy on push
        plan: Render plan (free, starter, standard, etc.)
        region: Deployment region

    Returns:
        render.yaml content as string
    """
    env_vars = env_vars or {}

    config = {
        "services": [
            {
                "type": "web",
                "name": name,
                "runtime": "python",
                "repo": repo,
                "branch": branch,
                "plan": plan,
                "region": region,
                "buildCommand": build_command,
                "startCommand": start_command,
                "healthCheckPath": health_check_path,
                "autoDeploy": auto_deploy,
                "envVars": [
                    {"key": k, "value": v}
                    for k, v in env_vars.items()
                ]
            }
        ],
        "databases": [
            {
                "name": f"{name}-db",
                "plan": "free",
                "databaseName": "carbon_room",
                "user": "carbon_room_user",
                "region": region,
            }
        ] if plan != "free" else []
    }

    # Convert to YAML format
    import yaml
    return yaml.dump(config, default_flow_style=False, sort_keys=False)


def generate_dockerfile() -> str:
    """
    Generate Dockerfile for Carbon Room.

    Returns:
        Dockerfile content
    """
    return '''# Carbon Room Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \\
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')"

# Start command
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8003"]
'''


# ============================================================================
# Synchronous wrapper for non-async contexts
# ============================================================================

class RenderDeploySync:
    """
    Synchronous wrapper for RenderDeploy.

    Use this when you need to call Render API from non-async code.
    """

    def __init__(self, *args, **kwargs):
        self._async_deploy = RenderDeploy(*args, **kwargs)

    @property
    def is_configured(self) -> bool:
        return self._async_deploy.is_configured

    def trigger_deploy(
        self,
        service_id: Optional[str] = None,
        clear_cache: bool = False
    ) -> Dict[str, Any]:
        """Synchronous trigger_deploy."""
        import asyncio
        return asyncio.run(self._async_deploy.trigger_deploy(service_id, clear_cache))

    def trigger_deploy_hook(self) -> Dict[str, Any]:
        """Synchronous trigger_deploy_hook."""
        import asyncio
        return asyncio.run(self._async_deploy.trigger_deploy_hook())

    def get_service_status(
        self,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous get_service_status."""
        import asyncio
        return asyncio.run(self._async_deploy.get_service_status(service_id))

    def check_health(
        self,
        health_url: Optional[str] = None,
        service_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous check_health."""
        import asyncio
        return asyncio.run(self._async_deploy.check_health(health_url, service_id))


# ============================================================================
# Factory functions
# ============================================================================

def get_render_deploy() -> RenderDeploy:
    """Get configured RenderDeploy instance."""
    return RenderDeploy()


def get_render_deploy_sync() -> RenderDeploySync:
    """Get configured RenderDeploySync instance (synchronous)."""
    return RenderDeploySync()
