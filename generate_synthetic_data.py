# Вспомогательный скрипт для искусственной генерации данных
import boto3
from botocore.client import Config
import os

ENDPOINT_URL = os.getenv("S3_ENDPOINT", "http://localhost:4566")
BUCKET = "retail-checks"
KEY = "processed/total_checks_sum.txt"

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id="fake",
        aws_secret_access_key="fake",
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def set_checks(count: int):
    s3 = get_s3()
    try:
        s3.head_bucket(Bucket=BUCKET)
    except:
        s3.create_bucket(Bucket=BUCKET)
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=str(count).encode())
    print(f"Записано чеков: {count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checks", type=int, required=True)
    args = parser.parse_args()
    set_checks(args.checks)
