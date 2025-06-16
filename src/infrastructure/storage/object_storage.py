import logging
import os
import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Union, Dict, Any
from uuid import uuid4

import aiofiles
import nats
from nats.js.api import ObjectStoreConfig
from nats.js.object_store import ObjectStore

from src.config import settings

logger = logging.getLogger(__name__)


class ObjectStorage(ABC):
    """Interface for object storage."""

    @abstractmethod
    async def upload_file(self, file_path: Union[str, Path], object_name: Optional[str] = None) -> str:
        """Upload a file to the storage and return its URL."""
        pass

    @abstractmethod
    async def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        """Upload a file-like object to the storage and return its URL."""
        pass

    @abstractmethod
    async def download_file(self, object_name: str, file_path: Union[str, Path]) -> None:
        """Download a file from the storage."""
        pass

    @abstractmethod
    async def get_object(self, object_name: str) -> BinaryIO:
        """Get a file-like object from the storage."""
        pass

    @abstractmethod
    async def delete_object(self, object_name: str) -> None:
        """Delete an object from the storage."""
        pass

    @abstractmethod
    def get_url(self, object_name: str) -> str:
        """Get the URL for an object."""
        pass


class LocalObjectStorage(ObjectStorage):
    """Local file system implementation of object storage."""

    def __init__(self, base_dir: Union[str, Path], base_url: str = "http://localhost:8000/files"):
        self.base_dir = Path(base_dir)
        self.base_url = base_url
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"LocalObjectStorage initialized with base_dir: {self.base_dir}")

    async def upload_file(self, file_path: Union[str, Path], object_name: Optional[str] = None) -> str:
        """Upload a file to the local storage and return its URL."""
        file_path = Path(file_path)
        if not object_name:
            object_name = f"{uuid4()}{file_path.suffix}"

        dest_path = self.base_dir / object_name
        os.makedirs(dest_path.parent, exist_ok=True)

        async with aiofiles.open(file_path, "rb") as src_file:
            content = await src_file.read()
            async with aiofiles.open(dest_path, "wb") as dest_file:
                await dest_file.write(content)

        logger.debug(f"Uploaded file {file_path} to {dest_path}")
        return self.get_url(object_name)

    async def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        """Upload a file-like object to the local storage and return its URL."""
        dest_path = self.base_dir / object_name
        os.makedirs(dest_path.parent, exist_ok=True)

        content = file_obj.read()
        async with aiofiles.open(dest_path, "wb") as dest_file:
            await dest_file.write(content)

        logger.debug(f"Uploaded file object to {dest_path}")
        return self.get_url(object_name)

    async def download_file(self, object_name: str, file_path: Union[str, Path]) -> None:
        """Download a file from the local storage."""
        src_path = self.base_dir / object_name
        file_path = Path(file_path)
        os.makedirs(file_path.parent, exist_ok=True)

        async with aiofiles.open(src_path, "rb") as src_file:
            content = await src_file.read()
            async with aiofiles.open(file_path, "wb") as dest_file:
                await dest_file.write(content)

        logger.debug(f"Downloaded file {src_path} to {file_path}")

    async def get_object(self, object_name: str) -> BinaryIO:
        """Get a file-like object from the local storage."""
        src_path = self.base_dir / object_name
        return open(src_path, "rb")

    async def delete_object(self, object_name: str) -> None:
        """Delete an object from the local storage."""
        file_path = self.base_dir / object_name
        if file_path.exists():
            os.remove(file_path)
            logger.debug(f"Deleted file {file_path}")

    def get_url(self, object_name: str) -> str:
        """Get the URL for an object."""
        return f"{self.base_url}/{object_name}"


class NatsObjectStorage(ObjectStorage):
    """NATS JetStream implementation of object storage."""

    def __init__(self, bucket_name: str = "transcription", nats_url: Optional[str] = None):
        self.bucket_name = bucket_name
        self.nats_url = nats_url or settings.NATS_URL
        self._nc = None
        self._js = None
        self._object_store = None
        logger.info(f"NatsObjectStorage initialized with bucket: {bucket_name}")

    async def _ensure_connected(self) -> None:
        """Ensure connection to NATS and initialize object store."""
        if self._nc is None or not self._nc.is_connected:
            self._nc = await nats.connect(self.nats_url)
            self._js = self._nc.jetstream()
            await self._get_or_create_object_store()

    async def _get_or_create_object_store(self) -> None:
        """Get or create the object store."""
        try:
            # Try to get existing object store
            self._object_store = await self._js.object_store(self.bucket_name)
        except Exception as e:
            logger.debug(f"Object store {self.bucket_name} not found, creating: {e}")
            # Create new object store if it doesn't exist
            config = ObjectStoreConfig(
                name=self.bucket_name,
                storage="file",
                max_bytes=getattr(settings, "OBJECT_STORE_MAX_BYTES", 1024 * 1024 * 1024)  # Default 1GB
            )
            self._object_store = await self._js.create_object_store(config)
            logger.info(f"Created object store: {self.bucket_name}")

    async def upload_file(self, file_path: Union[str, Path], object_name: Optional[str] = None) -> str:
        """Upload a file to NATS object store and return its URL."""
        await self._ensure_connected()

        file_path = Path(file_path)
        if not object_name:
            object_name = f"{uuid4()}{file_path.suffix}"

        try:
            async with aiofiles.open(file_path, "rb") as file:
                content = await file.read()
                await self._object_store.put(object_name, content)

            logger.debug(f"Uploaded file {file_path} to NATS object store {self.bucket_name}/{object_name}")
            return self.get_url(object_name)
        except Exception as e:
            logger.error(f"Error uploading file to NATS object store: {e}")
            raise

    async def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        """Upload a file-like object to NATS object store and return its URL."""
        await self._ensure_connected()

        try:
            content = file_obj.read()
            await self._object_store.put(object_name, content)

            logger.debug(f"Uploaded file object to NATS object store {self.bucket_name}/{object_name}")
            return self.get_url(object_name)
        except Exception as e:
            logger.error(f"Error uploading file object to NATS object store: {e}")
            raise

    async def download_file(self, object_name: str, file_path: Union[str, Path]) -> None:
        """Download a file from NATS object store."""
        await self._ensure_connected()

        file_path = Path(file_path)
        os.makedirs(file_path.parent, exist_ok=True)

        try:
            obj_info = await self._object_store.get(object_name)

            async with aiofiles.open(file_path, "wb") as file:
                await file.write(obj_info.data)

            logger.debug(f"Downloaded file from NATS object store {self.bucket_name}/{object_name} to {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file from NATS object store: {e}")
            raise

    async def get_object(self, object_name: str) -> BinaryIO:
        """Get a file-like object from NATS object store."""
        await self._ensure_connected()

        try:
            obj_info = await self._object_store.get(object_name)
            return io.BytesIO(obj_info.data)
        except Exception as e:
            logger.error(f"Error getting object from NATS object store: {e}")
            raise

    async def delete_object(self, object_name: str) -> None:
        """Delete an object from NATS object store."""
        await self._ensure_connected()

        try:
            await self._object_store.delete(object_name)
            logger.debug(f"Deleted object from NATS object store {self.bucket_name}/{object_name}")
        except Exception as e:
            logger.error(f"Error deleting object from NATS object store: {e}")
            raise

    def get_url(self, object_name: str) -> str:
        """Get the URL for an object in NATS object store."""
        # In a real implementation, this might generate a signed URL or use a gateway
        # For simplicity, we'll just return a path that can be used with an API endpoint
        api_base_url = getattr(settings, "API_BASE_URL", "http://localhost:8000")
        return f"{api_base_url}/api/v1/files/{self.bucket_name}/{object_name}"
