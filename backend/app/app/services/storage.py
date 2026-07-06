"""File storage abstraction."""

import io
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import boto3
from botocore.client import Config

from app.config import get_settings

settings = get_settings()


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, content: bytes, filename: str, content_type: str) -> str:
        pass

    @abstractmethod
    async def read(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        pass

    @abstractmethod
    def get_url(self, file_path: str) -> str:
        pass


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, filename: str, content_type: str) -> str:
        ext = Path(filename).suffix or ".jpg"
        relative = f"{uuid.uuid4().hex}{ext}"
        full_path = self.base_path / relative
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return relative

    async def read(self, file_path: str) -> bytes:
        full_path = self.base_path / file_path
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, file_path: str) -> None:
        full_path = self.base_path / file_path
        if full_path.exists():
            os.remove(full_path)

    def get_url(self, file_path: str) -> str:
        return f"/api/v1/photos/files/{file_path}"


class S3Storage(StorageBackend):
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.s3_bucket_name

    async def save(self, content: bytes, filename: str, content_type: str) -> str:
        ext = Path(filename).suffix or ".jpg"
        key = f"photos/{uuid.uuid4().hex}{ext}"
        self.client.upload_fileobj(
            io.BytesIO(content),
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    async def read(self, file_path: str) -> bytes:
        buffer = io.BytesIO()
        self.client.download_fileobj(self.bucket, file_path, buffer)
        return buffer.getvalue()

    async def delete(self, file_path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=file_path)

    def get_url(self, file_path: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": file_path},
            ExpiresIn=3600,
        )


def get_storage() -> StorageBackend:
    if settings.storage_type == "s3":
        return S3Storage()
    return LocalStorage(settings.local_storage_path)
