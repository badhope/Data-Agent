import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional, Set, List, Any

import docker
from docker.errors import APIError, ImageNotFound
from docker.models.images import Image

from app.config import SandboxSettings
from app.logger import logger
from app.sandbox.core.sandbox import DockerSandbox


class SandboxEnvironment:
    """Represents a sandbox environment/image."""

    def __init__(self, image: Image):
        self.id = image.id
        self.name = image.tags[0] if image.tags else image.id[:12]
        self.tags = image.tags
        self.size = image.attrs.get('Size', 0)
        self.created_at = image.attrs.get('Created', '')
        self.virtual_size = image.attrs.get('VirtualSize', 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'tags': self.tags,
            'size': self.size,
            'size_human': self._format_size(self.size),
            'created_at': self.created_at,
            'virtual_size': self.virtual_size,
            'virtual_size_human': self._format_size(self.virtual_size),
        }

    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """Format bytes to human readable string."""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.2f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.2f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


class SandboxManager:
    """Docker sandbox manager.

    Manages multiple DockerSandbox instances lifecycle including creation,
    monitoring, and cleanup. Provides concurrent access control and automatic
    cleanup mechanisms for sandbox resources.

    Attributes:
        max_sandboxes: Maximum allowed number of sandboxes.
        idle_timeout: Sandbox idle timeout in seconds.
        cleanup_interval: Cleanup check interval in seconds.
        _sandboxes: Active sandbox instance mapping.
        _last_used: Last used time record for sandboxes.
    """

    # Available environment images
    AVAILABLE_ENVIRONMENTS = [
        {
            'id': 'python',
            'name': 'Python',
            'description': 'Python 3.12 development environment',
            'image': 'python:3.12-slim',
            'category': 'development',
            'size': '~200MB',
            'popular': True,
        },
        {
            'id': 'python-full',
            'name': 'Python Full',
            'description': 'Python 3.12 with scientific packages',
            'image': 'python:3.12',
            'category': 'development',
            'size': '~900MB',
            'popular': True,
        },
        {
            'id': 'node',
            'name': 'Node.js',
            'description': 'Node.js 20 runtime environment',
            'image': 'node:20-slim',
            'category': 'development',
            'size': '~400MB',
            'popular': True,
        },
        {
            'id': 'java',
            'name': 'Java',
            'description': 'OpenJDK 21 environment',
            'image': 'openjdk:21-slim',
            'category': 'development',
            'size': '~700MB',
            'popular': False,
        },
        {
            'id': 'go',
            'name': 'Go',
            'description': 'Go 1.22 environment',
            'image': 'golang:1.22-slim',
            'category': 'development',
            'size': '~500MB',
            'popular': False,
        },
        {
            'id': 'rust',
            'name': 'Rust',
            'description': 'Rust development environment',
            'image': 'rust:slim',
            'category': 'development',
            'size': '~1.5GB',
            'popular': False,
        },
        {
            'id': 'ubuntu',
            'name': 'Ubuntu',
            'description': 'Ubuntu 22.04 base environment',
            'image': 'ubuntu:22.04',
            'category': 'base',
            'size': '~70MB',
            'popular': False,
        },
        {
            'id': 'alpine',
            'name': 'Alpine',
            'description': 'Alpine Linux lightweight environment',
            'image': 'alpine:latest',
            'category': 'base',
            'size': '~5MB',
            'popular': False,
        },
        {
            'id': 'postgres',
            'name': 'PostgreSQL',
            'description': 'PostgreSQL 16 database',
            'image': 'postgres:16',
            'category': 'database',
            'size': '~300MB',
            'popular': False,
        },
        {
            'id': 'redis',
            'name': 'Redis',
            'description': 'Redis 7 cache database',
            'image': 'redis:7-alpine',
            'category': 'database',
            'size': '~40MB',
            'popular': False,
        },
    ]

    def __init__(
        self,
        max_sandboxes: int = 100,
        idle_timeout: int = 3600,
        cleanup_interval: int = 300,
    ):
        """Initializes sandbox manager.

        Args:
            max_sandboxes: Maximum sandbox count limit.
            idle_timeout: Idle timeout in seconds.
            cleanup_interval: Cleanup check interval in seconds.
        """
        self.max_sandboxes = max_sandboxes
        self.idle_timeout = idle_timeout
        self.cleanup_interval = cleanup_interval

        # Docker client
        self._client = docker.from_env()

        # Resource mappings
        self._sandboxes: Dict[str, DockerSandbox] = {}
        self._last_used: Dict[str, float] = {}

        # Concurrency control
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self._active_operations: Set[str] = set()

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_shutting_down = False

        # Download progress tracking
        self._download_progress: Dict[str, float] = {}
        self._download_tasks: Dict[str, asyncio.Task] = {}

        # Start automatic cleanup
        self.start_cleanup_task()

    async def ensure_image(self, image: str) -> bool:
        """Ensures Docker image is available.

        Args:
            image: Image name.

        Returns:
            bool: Whether image is available.
        """
        try:
            self._client.images.get(image)
            return True
        except ImageNotFound:
            try:
                logger.info(f"Pulling image {image}...")
                await asyncio.get_event_loop().run_in_executor(
                    None, self._client.images.pull, image
                )
                return True
            except (APIError, Exception) as e:
                logger.error(f"Failed to pull image {image}: {e}")
                return False

    @asynccontextmanager
    async def sandbox_operation(self, sandbox_id: str):
        """Context manager for sandbox operations.

        Provides concurrency control and usage time updates.

        Args:
            sandbox_id: Sandbox ID.

        Raises:
            KeyError: If sandbox not found.
        """
        if sandbox_id not in self._locks:
            self._locks[sandbox_id] = asyncio.Lock()

        async with self._locks[sandbox_id]:
            if sandbox_id not in self._sandboxes:
                raise KeyError(f"Sandbox {sandbox_id} not found")

            self._active_operations.add(sandbox_id)
            try:
                self._last_used[sandbox_id] = asyncio.get_event_loop().time()
                yield self._sandboxes[sandbox_id]
            finally:
                self._active_operations.remove(sandbox_id)

    async def create_sandbox(
        self,
        config: Optional[SandboxSettings] = None,
        volume_bindings: Optional[Dict[str, str]] = None,
    ) -> str:
        """Creates a new sandbox instance.

        Args:
            config: Sandbox configuration.
            volume_bindings: Volume mapping configuration.

        Returns:
            str: Sandbox ID.

        Raises:
            RuntimeError: If max sandbox count reached or creation fails.
        """
        async with self._global_lock:
            if len(self._sandboxes) >= self.max_sandboxes:
                raise RuntimeError(
                    f"Maximum number of sandboxes ({self.max_sandboxes}) reached"
                )

            config = config or SandboxSettings()
            if not await self.ensure_image(config.image):
                raise RuntimeError(f"Failed to ensure Docker image: {config.image}")

            sandbox_id = str(uuid.uuid4())
            try:
                sandbox = DockerSandbox(config, volume_bindings)
                await sandbox.create()

                self._sandboxes[sandbox_id] = sandbox
                self._last_used[sandbox_id] = asyncio.get_event_loop().time()
                self._locks[sandbox_id] = asyncio.Lock()

                logger.info(f"Created sandbox {sandbox_id}")
                return sandbox_id

            except Exception as e:
                logger.error(f"Failed to create sandbox: {e}")
                if sandbox_id in self._sandboxes:
                    await self.delete_sandbox(sandbox_id)
                raise RuntimeError(f"Failed to create sandbox: {e}")

    async def get_sandbox(self, sandbox_id: str) -> DockerSandbox:
        """Gets a sandbox instance.

        Args:
            sandbox_id: Sandbox ID.

        Returns:
            DockerSandbox: Sandbox instance.

        Raises:
            KeyError: If sandbox does not exist.
        """
        async with self.sandbox_operation(sandbox_id) as sandbox:
            return sandbox

    def start_cleanup_task(self) -> None:
        """Starts automatic cleanup task."""

        async def cleanup_loop():
            while not self._is_shutting_down:
                try:
                    await self._cleanup_idle_sandboxes()
                except Exception as e:
                    logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(self.cleanup_interval)

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def _cleanup_idle_sandboxes(self) -> None:
        """Cleans up idle sandboxes."""
        current_time = asyncio.get_event_loop().time()
        to_cleanup = []

        async with self._global_lock:
            for sandbox_id, last_used in self._last_used.items():
                if (
                    sandbox_id not in self._active_operations
                    and current_time - last_used > self.idle_timeout
                ):
                    to_cleanup.append(sandbox_id)

        for sandbox_id in to_cleanup:
            try:
                await self.delete_sandbox(sandbox_id)
            except Exception as e:
                logger.error(f"Error cleaning up sandbox {sandbox_id}: {e}")

    async def cleanup(self) -> None:
        """Cleans up all resources."""
        logger.info("Starting manager cleanup...")
        self._is_shutting_down = True

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Get all sandbox IDs to clean up
        async with self._global_lock:
            sandbox_ids = list(self._sandboxes.keys())

        # Concurrently clean up all sandboxes
        cleanup_tasks = []
        for sandbox_id in sandbox_ids:
            task = asyncio.create_task(self._safe_delete_sandbox(sandbox_id))
            cleanup_tasks.append(task)

        if cleanup_tasks:
            # Wait for all cleanup tasks to complete, with timeout to avoid infinite waiting
            try:
                await asyncio.wait(cleanup_tasks, timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("Sandbox cleanup timed out")

        # Clean up remaining references
        self._sandboxes.clear()
        self._last_used.clear()
        self._locks.clear()
        self._active_operations.clear()

        logger.info("Manager cleanup completed")

    async def _safe_delete_sandbox(self, sandbox_id: str) -> None:
        """Safely deletes a single sandbox.

        Args:
            sandbox_id: Sandbox ID to delete.
        """
        try:
            if sandbox_id in self._active_operations:
                logger.warning(
                    f"Sandbox {sandbox_id} has active operations, waiting for completion"
                )
                for _ in range(10):  # Wait at most 10 times
                    await asyncio.sleep(0.5)
                    if sandbox_id not in self._active_operations:
                        break
                else:
                    logger.warning(
                        f"Timeout waiting for sandbox {sandbox_id} operations to complete"
                    )

            # Get reference to sandbox object
            sandbox = self._sandboxes.get(sandbox_id)
            if sandbox:
                await sandbox.cleanup()

                # Remove sandbox record from manager
                async with self._global_lock:
                    self._sandboxes.pop(sandbox_id, None)
                    self._last_used.pop(sandbox_id, None)
                    self._locks.pop(sandbox_id, None)
                    logger.info(f"Deleted sandbox {sandbox_id}")
        except Exception as e:
            logger.error(f"Error during cleanup of sandbox {sandbox_id}: {e}")

    async def delete_sandbox(self, sandbox_id: str) -> None:
        """Deletes specified sandbox.

        Args:
            sandbox_id: Sandbox ID.
        """
        if sandbox_id not in self._sandboxes:
            return

        try:
            await self._safe_delete_sandbox(sandbox_id)
        except Exception as e:
            logger.error(f"Failed to delete sandbox {sandbox_id}: {e}")

    async def __aenter__(self) -> "SandboxManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()

    def get_stats(self) -> Dict:
        """Gets manager statistics.

        Returns:
            Dict: Statistics information.
        """
        return {
            "total_sandboxes": len(self._sandboxes),
            "active_operations": len(self._active_operations),
            "max_sandboxes": self.max_sandboxes,
            "idle_timeout": self.idle_timeout,
            "cleanup_interval": self.cleanup_interval,
            "is_shutting_down": self._is_shutting_down,
        }

    # ==================== Environment Management ====================

    def get_downloaded_environments(self) -> List[Dict[str, Any]]:
        """Gets list of downloaded Docker images.

        Returns:
            List[Dict]: List of downloaded environment images.
        """
        try:
            images = self._client.images.list()
            environments = []
            for image in images:
                env = SandboxEnvironment(image)
                env_dict = env.to_dict()
                environments.append(env_dict)
            return environments
        except Exception as e:
            logger.error(f"Failed to get downloaded environments: {e}")
            return []

    def get_available_environments(self) -> List[Dict[str, Any]]:
        """Gets list of available environments that can be downloaded.

        Returns:
            List[Dict]: List of available environments with download status.
        """
        downloaded_images = self._get_downloaded_image_names()
        available = []
        
        for env in self.AVAILABLE_ENVIRONMENTS:
            is_downloaded = any(
                env['image'] in img_name for img_name in downloaded_images
            )
            available.append({
                **env,
                'is_downloaded': is_downloaded,
            })
        
        return available

    def _get_downloaded_image_names(self) -> Set[str]:
        """Gets set of downloaded image names/tags."""
        image_names = set()
        try:
            images = self._client.images.list()
            for image in images:
                for tag in image.tags:
                    image_names.add(tag)
        except Exception as e:
            logger.error(f"Failed to get downloaded image names: {e}")
        return image_names

    async def download_environment(self, environment_id: str) -> Dict[str, Any]:
        """Downloads an environment image.

        Args:
            environment_id: ID of the environment to download.

        Returns:
            Dict: Download result with status.
        """
        # Find environment configuration
        env_config = None
        for env in self.AVAILABLE_ENVIRONMENTS:
            if env['id'] == environment_id:
                env_config = env
                break

        if not env_config:
            return {
                'success': False,
                'message': f"Environment {environment_id} not found",
            }

        image_name = env_config['image']

        # Check if already downloading
        if image_name in self._download_tasks:
            return {
                'success': False,
                'message': f"Environment {env_config['name']} is already downloading",
            }

        # Start download task
        self._download_progress[image_name] = 0.0
        
        async def download_task():
            try:
                logger.info(f"Starting download of {image_name}")
                
                def progress_callback(chunk_size, total_size):
                    if total_size > 0:
                        self._download_progress[image_name] = (chunk_size / total_size) * 100
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._client.images.pull(image_name, stream=True, decode=True)
                )
                
                # Simulate progress since docker SDK doesn't provide direct progress
                for i in range(0, 101, 10):
                    await asyncio.sleep(0.5)
                    self._download_progress[image_name] = i
                
                self._download_progress[image_name] = 100.0
                logger.info(f"Download completed for {image_name}")
                
            except Exception as e:
                logger.error(f"Failed to download {image_name}: {e}")
                self._download_progress[image_name] = -1.0
            finally:
                self._download_tasks.pop(image_name, None)

        self._download_tasks[image_name] = asyncio.create_task(download_task())
        
        return {
            'success': True,
            'message': f"Started downloading {env_config['name']}",
            'environment_id': environment_id,
            'image': image_name,
        }

    def get_download_progress(self, environment_id: str = None) -> Dict[str, Any]:
        """Gets download progress for environments.

        Args:
            environment_id: Optional environment ID to filter progress.

        Returns:
            Dict: Download progress information.
        """
        if environment_id:
            # Find image name for this environment
            image_name = None
            for env in self.AVAILABLE_ENVIRONMENTS:
                if env['id'] == environment_id:
                    image_name = env['image']
                    break
            
            if image_name:
                progress = self._download_progress.get(image_name, 0.0)
                is_downloading = image_name in self._download_tasks
                return {
                    'environment_id': environment_id,
                    'image': image_name,
                    'progress': progress,
                    'is_downloading': is_downloading,
                    'status': self._get_progress_status(progress),
                }
            return {}
        
        # Return progress for all downloading environments
        progress_info = {}
        for image_name, progress in self._download_progress.items():
            if progress >= 0 and progress < 100:
                # Find environment info
                env_info = None
                for env in self.AVAILABLE_ENVIRONMENTS:
                    if env['image'] == image_name:
                        env_info = env
                        break
                
                progress_info[image_name] = {
                    'image': image_name,
                    'environment_id': env_info['id'] if env_info else image_name,
                    'name': env_info['name'] if env_info else image_name,
                    'progress': progress,
                    'is_downloading': image_name in self._download_tasks,
                    'status': self._get_progress_status(progress),
                }
        
        return progress_info

    def _get_progress_status(self, progress: float) -> str:
        """Gets status string for progress value."""
        if progress < 0:
            return 'failed'
        elif progress == 0:
            return 'pending'
        elif progress < 100:
            return 'downloading'
        else:
            return 'completed'

    async def delete_environment(self, image_id: str) -> Dict[str, Any]:
        """Deletes a downloaded environment image.

        Args:
            image_id: Image ID or tag to delete.

        Returns:
            Dict: Delete result.
        """
        try:
            self._client.images.remove(image_id, force=True)
            # Remove from progress tracking if exists
            for key in list(self._download_progress.keys()):
                if image_id in key:
                    self._download_progress.pop(key, None)
            return {
                'success': True,
                'message': f"Environment {image_id} deleted successfully",
            }
        except Exception as e:
            logger.error(f"Failed to delete environment {image_id}: {e}")
            return {
                'success': False,
                'message': str(e),
            }

    def get_environment_categories(self) -> List[str]:
        """Gets unique environment categories.

        Returns:
            List[str]: List of categories.
        """
        categories = set()
        for env in self.AVAILABLE_ENVIRONMENTS:
            categories.add(env['category'])
        return sorted(list(categories))
