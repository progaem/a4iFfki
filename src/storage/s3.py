"""
This module handles all interractions with S3(Minio) database
"""
import io
import os
import string
import random

from PIL.Image import Image

import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

from common.exceptions import ImageS3StorageError


class ImageS3Storage:

    def __init__(self):
        self.minio_access_key = os.environ['MINIO_ROOT_USER']
        self.minio_secret_key = os.environ['MINIO_ROOT_PASSWORD']
        self.s3 = boto3.client(
            's3',
            endpoint_url='http://s3:9000',
            aws_access_key_id=self.minio_access_key,
            aws_secret_access_key=self.minio_secret_key,
            config=Config(signature_version='s3v4'))

        self.bucket_name = "stickers"
        self.stickers_prefix = "sticker_files"

        self.__create_bucket(self.bucket_name)

    def save_and_convert_to_bytes(self, image: Image, file_path: str = "") -> tuple[str, bytes]:
        """Saves file to file_path (or randomly generated path if not specified). Returns file path and bytes"""
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        byte_image = buf.getvalue()

        if not file_path:
            file_path = f"{self.stickers_prefix}/{self.__generate_file_name()}.png"

        self.s3.put_object(Bucket=self.bucket_name, Key=file_path, Body=byte_image)
        return file_path, byte_image

    def get_bytes_from_path(self, file_path: str) -> bytes:
        """Returns bytes from file path, if file doesn't exist throws an Exception"""
        try:
            with io.BytesIO() as buffer:
                self.s3.download_fileobj(self.bucket_name, file_path, buffer)
                buffer.seek(0)
                return buffer.read()
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise FileNotFoundError(
                    f"File '{file_path}' does not exist in bucket '{self.bucket_name}'."
                ) from e
            raise ImageS3StorageError(
                f"Failed to download file '{file_path}' from the bucket '{self.bucket_name}",
                "download-file",
                str(e)
            ) from e
    
    def remove_all(self, file_paths_to_remove: list[str]) -> None:
        """Removes all files located at the file paths"""
        try:
            fomatted_file_entries = [
                {'Key': file_path } for file_path in file_paths_to_remove
            ]
            self.s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={
                    'Objects': fomatted_file_entries,
                },
            )
        except Exception as e:
            raise ImageS3StorageError(
                f"Failed to delete files",
                "delete-objects",
                str(e)
            ) from e

    def __create_bucket(self, bucket_name: str) -> None:
        try:
            self.s3.create_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code != 'BucketAlreadyOwnedByYou':
                raise ImageS3StorageError(
                    f"Failed to create bucket:",
                    "create-bucket",
                    str(e)
                ) from e

    def __generate_file_name(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
