"""
Carbon Room GitHub Integration
==============================
Backup manifest and certificates to GitHub for permanent storage.
Supports webhook-based CI/CD triggers.
"""

import base64
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"


class GitHubSyncError(Exception):
    """Base exception for GitHub sync operations."""
    pass


class GitHubRateLimitError(GitHubSyncError):
    """Rate limit exceeded."""
    pass


class GitHubAuthError(GitHubSyncError):
    """Authentication failed."""
    pass


class GitHubSync:
    """
    GitHub synchronization manager for Carbon Room.

    Handles:
    - Manifest backup to GitHub repo
    - Certificate storage
    - Webhook triggers for CI/CD
    - File versioning and history
    """

    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        backup_path: Optional[str] = None
    ):
        """
        Initialize GitHub sync.

        Args:
            token: GitHub personal access token (or use GITHUB_TOKEN env)
            repo: Repository in format "owner/repo" (or use GITHUB_REPO env)
            branch: Target branch (default: main)
            backup_path: Path in repo for backups (default: backups)
        """
        self.token = token or settings.GITHUB_TOKEN
        self.repo = repo or settings.GITHUB_REPO
        self.branch = branch or settings.GITHUB_BRANCH
        self.backup_path = backup_path or settings.GITHUB_BACKUP_PATH

        if not self.token:
            logger.warning("GitHub token not configured - sync disabled")

        if not self.repo:
            logger.warning("GitHub repo not configured - sync disabled")

    @property
    def is_configured(self) -> bool:
        """Check if GitHub sync is properly configured."""
        return bool(self.token and self.repo)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle GitHub API response and errors."""
        if response.status_code == 401:
            raise GitHubAuthError("GitHub authentication failed - check token")

        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise GitHubRateLimitError("GitHub API rate limit exceeded")
            raise GitHubSyncError(f"GitHub access forbidden: {response.text}")

        if response.status_code == 404:
            return {}  # Resource not found (may be expected)

        if response.status_code >= 400:
            raise GitHubSyncError(f"GitHub API error {response.status_code}: {response.text}")

        return response.json() if response.text else {}

    async def get_file(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get file content from GitHub.

        Args:
            path: File path in repository

        Returns:
            Dict with 'content', 'sha', and 'encoding' or None if not found
        """
        if not self.is_configured:
            return None

        url = f"{GITHUB_API_URL}/repos/{self.repo}/contents/{path}"
        params = {"ref": self.branch}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0
            )

        result = self._handle_response(response)
        if not result:
            return None

        # Decode content if base64 encoded
        if result.get("encoding") == "base64" and result.get("content"):
            content_bytes = base64.b64decode(result["content"])
            result["decoded_content"] = content_bytes.decode("utf-8")

        return result

    async def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        sha: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a file in GitHub.

        Args:
            path: File path in repository
            content: File content (will be base64 encoded)
            message: Commit message
            sha: SHA of existing file (required for updates)

        Returns:
            Dict with commit info
        """
        if not self.is_configured:
            raise GitHubSyncError("GitHub not configured")

        url = f"{GITHUB_API_URL}/repos/{self.repo}/contents/{path}"

        # Encode content to base64
        content_bytes = content.encode("utf-8")
        content_b64 = base64.b64encode(content_bytes).decode("ascii")

        payload = {
            "message": message,
            "content": content_b64,
            "branch": self.branch,
        }

        if sha:
            payload["sha"] = sha

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30.0
            )

        return self._handle_response(response)

    async def backup_manifest(
        self,
        manifest_data: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Backup manifest.json to GitHub.

        Creates versioned backups in the backup path.

        Args:
            manifest_data: Manifest dictionary to backup
            timestamp: Optional timestamp for filename

        Returns:
            Dict with backup info
        """
        if not self.is_configured:
            return {"status": "skipped", "reason": "GitHub not configured"}

        timestamp = timestamp or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        content = json.dumps(manifest_data, indent=2)

        # Current manifest path
        current_path = f"{self.backup_path}/manifest.json"

        # Versioned backup path
        backup_path = f"{self.backup_path}/archive/manifest_{timestamp}.json"

        results = {}

        try:
            # Get existing file SHA if it exists
            existing = await self.get_file(current_path)
            sha = existing.get("sha") if existing else None

            # Create versioned backup first
            results["archive"] = await self.create_or_update_file(
                path=backup_path,
                content=content,
                message=f"[Carbon Room] Manifest backup {timestamp}"
            )

            # Update current manifest
            results["current"] = await self.create_or_update_file(
                path=current_path,
                content=content,
                message=f"[Carbon Room] Update manifest {timestamp}",
                sha=sha
            )

            results["status"] = "success"
            logger.info(f"Manifest backed up to GitHub: {backup_path}")

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            logger.error(f"Manifest backup failed: {e}")

        return results

    async def backup_certificate(
        self,
        certificate_id: str,
        certificate_html: str,
        document_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Backup a certificate to GitHub.

        Args:
            certificate_id: Certificate ID (e.g., C6-30B3778C42BAC9E7)
            certificate_html: HTML content
            document_text: Optional plain text version

        Returns:
            Dict with backup info
        """
        if not self.is_configured:
            return {"status": "skipped", "reason": "GitHub not configured"}

        results = {}
        cert_folder = f"{self.backup_path}/certificates/{certificate_id}"

        try:
            # Backup HTML certificate
            results["html"] = await self.create_or_update_file(
                path=f"{cert_folder}/certificate.html",
                content=certificate_html,
                message=f"[Carbon Room] Certificate {certificate_id}"
            )

            # Backup plain text if provided
            if document_text:
                results["text"] = await self.create_or_update_file(
                    path=f"{cert_folder}/certificate.txt",
                    content=document_text,
                    message=f"[Carbon Room] Certificate text {certificate_id}"
                )

            results["status"] = "success"
            logger.info(f"Certificate backed up: {certificate_id}")

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            logger.error(f"Certificate backup failed: {e}")

        return results

    async def sync_all_certificates(
        self,
        certificates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync all certificates to GitHub.

        Args:
            certificates: List of certificate dicts with 'certificate_id',
                         'certificate_html', and optional 'document_text'

        Returns:
            Summary of sync operation
        """
        results = {
            "total": len(certificates),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        for cert in certificates:
            result = await self.backup_certificate(
                certificate_id=cert.get("certificate_id", "unknown"),
                certificate_html=cert.get("certificate_html", ""),
                document_text=cert.get("document_text")
            )

            if result.get("status") == "success":
                results["success"] += 1
            elif result.get("status") == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "certificate_id": cert.get("certificate_id"),
                "status": result.get("status"),
                "error": result.get("error")
            })

        return results

    async def get_manifest_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get manifest backup history from GitHub.

        Args:
            limit: Maximum number of commits to return

        Returns:
            List of commit info dicts
        """
        if not self.is_configured:
            return []

        url = f"{GITHUB_API_URL}/repos/{self.repo}/commits"
        params = {
            "path": f"{self.backup_path}/manifest.json",
            "sha": self.branch,
            "per_page": limit,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0
            )

        commits = self._handle_response(response)

        return [
            {
                "sha": commit.get("sha"),
                "message": commit.get("commit", {}).get("message"),
                "date": commit.get("commit", {}).get("committer", {}).get("date"),
                "author": commit.get("commit", {}).get("author", {}).get("name"),
            }
            for commit in commits
        ] if isinstance(commits, list) else []

    async def trigger_workflow(
        self,
        workflow_id: str,
        inputs: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a GitHub Actions workflow.

        Args:
            workflow_id: Workflow ID or filename (e.g., 'deploy.yml')
            inputs: Optional workflow inputs

        Returns:
            Workflow dispatch result
        """
        if not self.is_configured:
            return {"status": "skipped", "reason": "GitHub not configured"}

        url = f"{GITHUB_API_URL}/repos/{self.repo}/actions/workflows/{workflow_id}/dispatches"

        payload = {
            "ref": self.branch,
        }

        if inputs:
            payload["inputs"] = inputs

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30.0
            )

        if response.status_code == 204:
            return {"status": "success", "message": "Workflow triggered"}

        return self._handle_response(response)


# ============================================================================
# Synchronous wrapper for non-async contexts
# ============================================================================

class GitHubSyncSync:
    """
    Synchronous wrapper for GitHubSync.

    Use this when you need to call GitHub sync from non-async code.
    """

    def __init__(self, *args, **kwargs):
        self._async_sync = GitHubSync(*args, **kwargs)

    @property
    def is_configured(self) -> bool:
        return self._async_sync.is_configured

    def backup_manifest(
        self,
        manifest_data: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous backup_manifest."""
        import asyncio
        return asyncio.run(self._async_sync.backup_manifest(manifest_data, timestamp))

    def backup_certificate(
        self,
        certificate_id: str,
        certificate_html: str,
        document_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous backup_certificate."""
        import asyncio
        return asyncio.run(self._async_sync.backup_certificate(
            certificate_id, certificate_html, document_text
        ))

    def get_manifest_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Synchronous get_manifest_history."""
        import asyncio
        return asyncio.run(self._async_sync.get_manifest_history(limit))


# ============================================================================
# Webhook Handler for incoming GitHub webhooks
# ============================================================================

class GitHubWebhookHandler:
    """
    Handler for incoming GitHub webhooks.

    Validates signatures and routes events to appropriate handlers.
    """

    def __init__(self, secret: Optional[str] = None):
        """
        Initialize webhook handler.

        Args:
            secret: Webhook secret for signature validation
        """
        self.secret = secret or settings.SECRET_KEY

    def verify_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify GitHub webhook signature.

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        if not signature or not signature.startswith("sha256="):
            return False

        expected_signature = "sha256=" + hashlib.hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hashlib.compare_digest(expected_signature, signature)

    def handle_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle push event.

        Args:
            payload: Webhook payload

        Returns:
            Processing result
        """
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])

        logger.info(f"Push event received: {ref} with {len(commits)} commits")

        return {
            "event": "push",
            "ref": ref,
            "commits": len(commits),
            "processed": True
        }

    def handle_workflow_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle workflow_run event.

        Args:
            payload: Webhook payload

        Returns:
            Processing result
        """
        workflow = payload.get("workflow_run", {})
        name = workflow.get("name", "unknown")
        status = workflow.get("status", "unknown")
        conclusion = workflow.get("conclusion", "unknown")

        logger.info(f"Workflow run event: {name} - {status}/{conclusion}")

        return {
            "event": "workflow_run",
            "workflow": name,
            "status": status,
            "conclusion": conclusion,
            "processed": True
        }


# ============================================================================
# Factory function
# ============================================================================

def get_github_sync() -> GitHubSync:
    """Get configured GitHubSync instance."""
    return GitHubSync()


def get_github_sync_sync() -> GitHubSyncSync:
    """Get configured GitHubSyncSync instance (synchronous)."""
    return GitHubSyncSync()
