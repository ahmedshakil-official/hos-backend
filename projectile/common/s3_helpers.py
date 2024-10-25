import os
import boto3
import requests
from io import BytesIO
from zipfile import ZipFile

def download_and_zip_s3_files(s3_urls, zip_file_name):
    s3 = boto3.client('s3')

    # Create a BytesIO object to store the zip file in memory
    zip_buffer = BytesIO()

    # Create a ZipFile object
    with ZipFile(zip_buffer, 'w') as zip_file:
        for s3_url in s3_urls:
            # Extract the S3 bucket and key from the URL
            bucket, key = parse_s3_url(s3_url)

            # Download the file content from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            file_content = response['Body'].read()

            # Add the file to the zip archive
            zip_file.writestr(key, file_content)

    # Seek to the beginning of the buffer
    zip_buffer.seek(0)

    # Save the zip file to a local file or return it as needed
    with open(zip_file_name, 'wb') as f:
        f.write(zip_buffer.read())

def parse_s3_url(s3_url):
    # Example S3 URL: https://healthos-media.s3.amazonaws.com/banner/images/...
    parts = s3_url.split('/')
    key = '/'.join(parts[3:])
    return os.environ['AWS_MEDIA_BUCKET_NAME'], key
