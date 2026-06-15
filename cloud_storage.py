#!/usr/bin/env python3
"""
Cloud Storage Manager for CogniVault
Handles pushing local vector db and files to AWS S3 / Cloudflare R2
"""

import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from pathlib import Path
import tempfile

class CloudStorageManager:
    def __init__(self, endpoint_url=None, access_key=None, secret_key=None, region_name="auto", bucket_name=None):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.bucket_name = bucket_name
        self.s3_client = None

        if self.access_key and self.secret_key:
            self._init_client()

    def _init_client(self):
        """Initialize the S3/R2 client"""
        try:
            config = Config(
                retries = {
                    'max_attempts': 3,
                    'mode': 'standard'
                }
            )

            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url if self.endpoint_url else None,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region_name,
                config=config
            )
        except Exception as e:
            print(f"Error initializing S3 client: {e}")
            self.s3_client = None

    def is_configured(self):
        """Check if cloud storage has been configured correctly"""
        return self.s3_client is not None and self.bucket_name is not None and len(self.bucket_name.strip()) > 0

    def test_connection(self):
        """Test the connection to the bucket"""
        if not self.is_configured():
            return False, "Not configured"

        try:
            # Check if bucket exists, if not try to create it
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    # Bucket doesn't exist, try to create it
                    if self.region_name and self.region_name != 'us-east-1' and self.region_name != 'auto':
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region_name}
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    return False, f"Bucket access error: {str(e)}"

            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def sync_directory_to_cloud(self, local_dir_path: Path, prefix="cognivault_backup"):
        """
        Recursively upload an entire directory to S3/R2.
        local_dir_path: Path object to the local directory (e.g. ~/cognivault_data)
        prefix: Prefix in the S3 bucket to place the files
        """
        if not self.is_configured():
            return False, "Cloud storage not configured", 0, 0

        if not local_dir_path.exists() or not local_dir_path.is_dir():
            return False, f"Directory does not exist: {local_dir_path}", 0, 0

        files_uploaded = 0
        files_failed = 0
        failed_files_list = []

        try:
            for root, dirs, files in os.walk(local_dir_path):
                for file in files:
                    local_path = os.path.join(root, file)

                    # Calculate relative path to construct S3 key
                    rel_path = os.path.relpath(local_path, local_dir_path)
                    s3_key = f"{prefix}/{rel_path}".replace("\\", "/") # Ensure forward slashes for S3

                    try:
                        self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
                        files_uploaded += 1
                    except Exception as e:
                        print(f"Failed to upload {local_path}: {e}")
                        files_failed += 1
                        failed_files_list.append(local_path)

            if files_failed > 0:
                return True, f"Synced with errors. Uploaded: {files_uploaded}, Failed: {files_failed}", files_uploaded, files_failed
            else:
                return True, f"Successfully synced {files_uploaded} files to cloud.", files_uploaded, files_failed

        except Exception as e:
            return False, f"Sync failed: {str(e)}", files_uploaded, files_failed
