import logging

import boto3
import io
import os
import string
import random

from PIL.Image import Image
from botocore.exceptions import ClientError

# Enable logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageS3Storage:

    def __init__(self):
        self.minio_access_key = os.environ['MINIO_ROOT_USER']
        self.minio_secret_key = os.environ['MINIO_ROOT_PASSWORD']
        self.s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id=self.minio_access_key,
            aws_secret_access_key=self.minio_secret_key)

        logger.info(
            "Connected to MINIO at http://localhost:9000 with access_key %s and secret_key %s",
            masked_print(self.minio_access_key),
            masked_print(self.minio_secret_key))

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
                raise FileNotFoundError(f"File '{file_path}' does not exist in bucket '{self.bucket_name}'.")
            else:
                raise Exception(f"Failed to download file '{file_path}' from the bucket '{self.bucket_name}: {e}")

    def __create_bucket(self, bucket_name: str) -> None:
        try:
            self.s3.create_bucket(Bucket=bucket_name)
            logger.info("Successfully created bucket %s for storing stickers", masked_print(bucket_name))
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyOwnedByYou':
                logger.info(f"Bucket '{bucket_name}' already exists. Ignoring creation of it")
            else:
                raise Exception(f"Failed to create bucket: {e}")

    def __generate_file_name(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def masked_print(value: str) -> str:
    symbols_to_mask = int(0.8 * len(value))
    return value[:-symbols_to_mask] + 'X' * symbols_to_mask
