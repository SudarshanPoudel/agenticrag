import os
import shutil
import uuid
from typing import Optional
from starlette.concurrency import run_in_threadpool


class StorageManager:
    def __init__(self, local_dir: str, s3_client: Optional[object] = None, s3_bucket: Optional[str] = None):
        self.local_dir = local_dir
        os.makedirs(self.local_dir, exist_ok=True)

        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        if self.s3_client and not self.s3_bucket:
            raise ValueError("s3_bucket must be provided if s3_client is used.")

    def save(self, key: str, data: bytes, use_local: Optional[bool] = None):
        """Save to remote if S3 configured, else local. Override with use_local=True/False"""
        if (use_local is True) or (use_local is None and not self.s3_client):
            path = os.path.join(self.local_dir, key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
        else:
            self.s3_client.put_object(Bucket=self.s3_bucket, Key=key, Body=data)

    def load(self, key: str, use_local: Optional[bool] = None) -> bytes:
        if (use_local is True) or (use_local is None and not self.s3_client):
            path = os.path.join(self.local_dir, key)
            with open(path, "rb") as f:
                return f.read()
        else:
            resp = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
            return resp["Body"].read()

    def delete(self, key: str, use_local: Optional[bool] = None):
        if (use_local is True) or (use_local is None and not self.s3_client):
            path = os.path.join(self.local_dir, key)
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        else:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=key)

    def get_url(self, key: str, use_local: Optional[bool] = None) -> str:
        if (use_local is True) or (use_local is None and not self.s3_client):
            return os.path.join(self.local_dir, key)
        else:
            return self.s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": self.s3_bucket, "Key": key}, ExpiresIn=3600
            )

    def copy(self, src_path: str, dest_folder: str, remove_original: bool = False, use_local: Optional[bool] = None):
        """Copy file or folder to destination (local or remote)"""
        if os.path.isdir(src_path):
            for root, _, files in os.walk(src_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, src_path)
                    key = os.path.join(dest_folder, rel_path).replace("\\", "/")
                    with open(full_path, "rb") as file_obj:
                        self.save(key, file_obj.read(), use_local=use_local)
            if remove_original:
                shutil.rmtree(src_path)
        else:
            filename = os.path.basename(src_path)
            key = os.path.join(dest_folder, filename).replace("\\", "/")
            with open(src_path, "rb") as file_obj:
                self.save(key, file_obj.read(), use_local=use_local)
            if remove_original:
                os.remove(src_path)

    def move_local_to_remote(self, src: str, dest_key: Optional[str] = None, remove_local: bool = True):
        """Move local file or folder to remote (S3)"""
        if not self.s3_client:
            raise RuntimeError("S3 client not configured.")

        path = os.path.join(self.local_dir, src)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")

        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, self.local_dir)
                    key = os.path.join(dest_key or "", rel_path).replace("\\", "/")
                    with open(full_path, "rb") as file_obj:
                        self.save(key, file_obj.read(), use_local=False)
            if remove_local:
                shutil.rmtree(path)
        else:
            key = os.path.join(dest_key or "", os.path.basename(path)).replace("\\", "/")
            with open(path, "rb") as file_obj:
                self.save(key, file_obj.read(), use_local=False)
            if remove_local:
                os.remove(path)

    def move_remote_to_local(self, key: str, dest_folder: Optional[str] = None, remove_remote: bool = False):
        if not self.s3_client:
            raise RuntimeError("S3 client not configured.")

        data = self.load(key, use_local=False)
        local_path = os.path.join(dest_folder or self.local_dir, key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data)
        if remove_remote:
            self.delete(key, use_local=False)

    async def asave(self, key: str, data: bytes, use_local: Optional[bool] = None):
        await run_in_threadpool(self.save, key, data, use_local)

    async def aload(self, key: str, use_local: Optional[bool] = None) -> bytes:
        return await run_in_threadpool(self.load, key, use_local)

    async def adelete(self, key: str, use_local: Optional[bool] = None):
        await run_in_threadpool(self.delete, key, use_local)

    async def aget_url(self, key: str, use_local: Optional[bool] = None) -> str:
        return await run_in_threadpool(self.get_url, key, use_local)

    async def acopy(self, src_path: str, dest_folder: str, remove_original: bool = False, use_local: Optional[bool] = None):
        await run_in_threadpool(self.copy, src_path, dest_folder, remove_original, use_local)

    async def amove_local_to_remote(self, src: str, dest_key: Optional[str] = None, remove_local: bool = True):
        await run_in_threadpool(self.move_local_to_remote, src, dest_key, remove_local)

    async def amove_remote_to_local(self, key: str, dest_folder: Optional[str] = None, remove_remote: bool = False):
        await run_in_threadpool(self.move_remote_to_local, key, dest_folder, remove_remote)

    def _generate_unique_key(self, folder_name: str = "") -> str:
        unique_id = str(uuid.uuid4())
        return f"{folder_name}/{unique_id}" if folder_name else unique_id
