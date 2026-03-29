"""S3/MinIO storage helpers for uploading rendered files and generating download URLs."""

from __future__ import annotations

from botocore.exceptions import ClientError


def get_s3_client(
    endpoint_url: str,
    access_key: str,
    secret_key: str,
):
    """Create a boto3 S3 client configured for MinIO or AWS S3."""
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=boto3.session.Config(signature_version="s3v4"),
    )


def ensure_bucket(client, bucket_name: str) -> None:
    """Create the S3 bucket if it doesn't already exist."""
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError:
        client.create_bucket(Bucket=bucket_name)


def upload_file(
    client,
    bucket: str,
    key: str,
    data: bytes,
    content_type: str,
) -> str:
    """Upload a file to S3 and return the object key."""
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def get_download_url(
    client,
    bucket: str,
    key: str,
    expires_in: int = 3600,
) -> str:
    """Generate a presigned download URL for an S3 object."""
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def delete_file(client, bucket: str, key: str) -> None:
    """Delete a file from S3."""
    client.delete_object(Bucket=bucket, Key=key)
