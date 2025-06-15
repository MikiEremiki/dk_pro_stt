import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Union
from uuid import uuid4

import aiofiles
import boto3
from botocore.exceptions import ClientError

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


class S3ObjectStorage(ObjectStorage):
    """S3 implementation of object storage."""

    def __init__(self, bucket_name: str, aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, region_name: Optional[str] = None,
                 endpoint_url: Optional[str] = None):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url
        )
        logger.info(f"S3ObjectStorage initialized with bucket: {bucket_name}")

    async def upload_file(self, file_path: Union[str, Path], object_name: Optional[str] = None) -> str:
        """Upload a file to S3 and return its URL."""
        file_path = str(file_path)
        if not object_name:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            logger.debug(f"Uploaded file {file_path} to S3 bucket {self.bucket_name}/{object_name}")
            return self.get_url(object_name)
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise

    async def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        """Upload a file-like object to S3 and return its URL."""
        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
            logger.debug(f"Uploaded file object to S3 bucket {self.bucket_name}/{object_name}")
            return self.get_url(object_name)
        except ClientError as e:
            logger.error(f"Error uploading file object to S3: {e}")
            raise

    async def download_file(self, object_name: str, file_path: Union[str, Path]) -> None:
        """Download a file from S3."""
        file_path = str(file_path)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
            logger.debug(f"Downloaded file from S3 bucket {self.bucket_name}/{object_name} to {file_path}")
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            raise

    async def get_object(self, object_name: str) -> BinaryIO:
        """Get a file-like object from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
            return response['Body']
        except ClientError as e:
            logger.error(f"Error getting object from S3: {e}")
            raise

    async def delete_object(self, object_name: str) -> None:
        """Delete an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.debug(f"Deleted object from S3 bucket {self.bucket_name}/{object_name}")
        except ClientError as e:
            logger.error(f"Error deleting object from S3: {e}")
            raise

    def get_url(self, object_name: str) -> str:
        """Get the URL for an object in S3."""
        return f"https://{self.bucket_name}.s3.amazonaws.com/{object_name}"