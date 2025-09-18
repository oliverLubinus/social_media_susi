
import boto3
from botocore.exceptions import ClientError
import os
import logging
from susi.retry_utils import retry


from typing import Optional

@retry(Exception, tries=3, delay=2, backoff=2, logger=logging.getLogger(__name__))
def upload_file_to_s3(
    file_path: str,
    bucket_name: str,
    object_name: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region_name: Optional[str] = None
) -> Optional[str]:
    """
    Upload a file to an AWS S3 bucket and return its public URL.

    Args:
        file_path (str): Local path to the file to upload.
        bucket_name (str): Name of the S3 bucket.
        object_name (Optional[str]): S3 object name. Defaults to the file's basename if not provided.
        aws_access_key_id (Optional[str]): AWS access key ID. If None, uses default credentials/profile.
        aws_secret_access_key (Optional[str]): AWS secret access key. If None, uses default credentials/profile.
        region_name (Optional[str]): AWS region name. If None, uses default region.
        profile_name (Optional[str]): AWS CLI profile name. If provided, takes precedence over explicit keys.

    Returns:
        Optional[str]: Public URL of the uploaded file if successful, None otherwise.

    Raises:
        Exception: If upload fails after retries.

    Developer hint:
        - This function uses retry logic. If upload fails, it will retry up to 3 times with exponential backoff.
        - Make sure your AWS credentials and bucket permissions are correct.
        - The uploaded file is set to 'image/jpeg' content type by default.
    """
    # If no object name is provided, use the file's basename
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Always use environment variables or explicit keys for credentials.
    # For Docker/production, set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION as env vars.
    # If aws_access_key_id and aws_secret_access_key are None, boto3 will use environment variables or IAM roles.
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    try:
        # Upload the file to S3 with content type set to image/jpeg
        s3_client.upload_file(
            file_path, bucket_name, object_name,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
    except ClientError as e:
        # Error hint: Check your AWS credentials, bucket name, permissions, and network connection.
        logging.error(f"Error uploading to S3 (ClientError): {e}")
        return None
    except Exception as e:
        # Error hint: This may be a non-AWS error (e.g., file not found).
        logging.error(f"Unexpected error uploading to S3: {e}")
        return None

    # Construct the public URL for the uploaded file
    url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{object_name}"
    logging.info(f"File uploaded to S3: {url}")
    return url
