import logging
import os
from io import BytesIO

import PIL
import boto3
from PIL import Image
from boto3 import Session
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

CONTENT_TYPE = "image/jpeg"
SUPPORTED_FORMAT = "JPEG"


def get_image_url(bucket, key, region) -> str:
    return "https://s3-{region}.amazonaws.com/{bucket}/{key}".format(
        bucket=bucket, key=key, region=region
    )


def get_image(boto_session: Session, bucket_name: str, key: str) -> object:
    s3_client = boto_session.client('s3')
    obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    obj_body = obj['Body'].read()
    return obj_body


def resize_image(image_body, new_size) -> BytesIO:
    logger.info('Resizing image with new size %s...', new_size)
    size_split = new_size.split('x')

    img = Image.open(BytesIO(image_body))

    # Checks if this is a jpeg file
    if img.format != SUPPORTED_FORMAT:
        logger.error("File format is %s", img.format)
        raise Exception(f"Unsupported image file format, expected ${SUPPORTED_FORMAT}, got {img.format}")

    new_img = img.resize(
        (int(size_split[0]), int(size_split[1])), PIL.Image.ANTIALIAS
    )
    buffer = BytesIO()
    new_img.save(buffer, SUPPORTED_FORMAT)
    buffer.seek(0)

    return buffer


def upload_image(boto_session: Session, body: BytesIO, bucket_name: str, new_key: str, description: str) -> object:
    s3_client = boto_session.client('s3')

    extra_args = {
        'Metadata': {'x-amz-meta-description': description},
        'ContentType': CONTENT_TYPE
    }

    try:
        logger.info('Uploading new image to bucket %s with key %s...', bucket_name, new_key)
        response = s3_client.upload_fileobj(Fileobj=body, Bucket=bucket_name, Key=new_key, ExtraArgs=extra_args)
    except ClientError as e:
        logger.error("Unable to upload image to bucket % with key %", bucket_name, new_key)
        raise e
    return response


def get_files_location(event):
    """
    Generator for the bucket and key names of each
    file contained in the event sent to this function from S3.
    (usually only one but this ensures we process them all).
    :param event: S3:ObjectCreated:Put notification event
    :return: yields bucket and key names
    """
    for event_record in event['Records']:
        bucket = event_record['s3']['bucket']['name']
        key = event_record['s3']['object']['key']
        yield bucket, key


def handler(event, context):
    logger.info("Starting picture resizer ...")
    logger.debug('## EVENT')
    logger.debug(event)

    aws_region = os.environ["AWS_REGION"]
    # example : "50x50"
    new_size = os.environ["NEW_SIZE"]
    new_image_description = os.environ["NEW_IMAGE_DESCRIPTION"]
    new_image_extension = os.environ["NEW_IMAGE_EXTENSION"]

    # Create a Boto3 session that can be used to construct clients
    session = boto3.session.Session()

    # Get the S3 bucket and key for each log file contained in the event
    for bucket, key in get_files_location(event):
        # Load the file
        logger.info('Loading file s3://%s/%s', bucket, key)
        original_image_body = get_image(session, bucket, key)

        logger.info('Loading file s3://%s/%s', bucket, key)
        new_image_body = resize_image(original_image_body, new_size)

        filename, file_extension = os.path.splitext(key)
        new_key = "{key}_{size}{ext}".format(key=filename, size=new_size, ext=new_image_extension)
        upload_image(session, new_image_body, bucket, new_key, new_image_description)

        new_image_url = get_image_url(bucket, new_key, aws_region)
        logger.info("New image URL is %s", new_image_url)
