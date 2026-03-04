import io
import uuid
import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_s3():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",
    )


def upload_file(file_bytes: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    s3 = _get_s3()
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=file_bytes, ContentType=content_type)
    return key


def download_file(key: str) -> bytes:
    s3 = _get_s3()
    resp = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return resp["Body"].read()


def get_file_stream(key: str):
    s3 = _get_s3()
    resp = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return resp["Body"], resp.get("ContentType", "application/octet-stream"), resp.get("ContentLength", 0)


def generate_asset_key(kind: str, ext: str) -> str:
    return f"{kind}/{uuid.uuid4().hex}.{ext}"
