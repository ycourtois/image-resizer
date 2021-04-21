import logging
import os
from unittest import mock

import boto3
import botocore
import pytest
from moto import mock_s3

from src.app import handler


@mock_s3
class TestApp:
    def setup_method(self, method):
        self._logger = logging.getLogger(__name__)
        self.region = "eu-west-1"
        self.s3_bucket = "images_bucket"
        self.images_path_directory = "images"
        self.access_key = "fake_access_key"
        self.secret_key = "fake_access_key"
        self.images = ["image1.jpg", "image2.jpg"]
        self.new_size = "50x50"
        self.description = "awesome image"
        self.new_extension = ".jpeg"

        self.s3_resource = boto3.resource(
            "s3",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self.s3_client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self._populate_s3_bucket()

    def teardown_method(self, method):
        self._empty_s3_bucket()

    def _empty_s3_bucket(self) -> None:
        bucket = self.s3_resource.Bucket(self.s3_bucket)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()

    def _populate_s3_bucket(self) -> None:

        try:
            self.s3_resource.meta.client.head_bucket(Bucket=self.s3_bucket)
        except botocore.exceptions.ClientError:
            pass
        else:
            err = "{bucket} should not exist.".format(bucket=self.s3_bucket)
            raise EnvironmentError(err)
        self.s3_client.create_bucket(Bucket=self.s3_bucket,
                                     CreateBucketConfiguration={'LocationConstraint': self.region})
        current_dir = os.path.dirname(__file__)
        images_dir = os.path.join(current_dir, self.images_path_directory)
        self._upload_images(images_dir)

    def _upload_images(self, images_dir: str) -> None:
        client = boto3.client("s3")
        fixtures_paths = [
            os.path.join(path, filename)
            for path, _, files in os.walk(images_dir)
            for filename in files
        ]
        for path in fixtures_paths:
            key = os.path.relpath(path, images_dir)
            client.upload_file(Filename=path, Bucket=self.s3_bucket, Key=key)

    def _get_s3_event(self):
        return {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": self.region,
                    "eventTime": "2019-11-03T19:37:27.192Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "AWS:AIDAINPONIXQXGT5NGHY6"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "192.168.0.1"
                    },
                    "responseElements": {
                        "x-amz-request-id": "D82B88E5F771F645",
                        "x-amz-id-2": "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "828aa6fc-f7b5-4305-8584-487c791949c1",
                        "bucket": {
                            "name": self.s3_bucket,
                            "ownerIdentity": {
                                "principalId": "A3I5XTEXAMAI3E"
                            },
                            "arn": f"arn:aws:s3:::{self.s3_bucket}"
                        },
                        "object": {
                            "key": self.images[0],
                            "size": 1024,
                            "eTag": "b21b84d653bb07b05b1e6b33684dc11b",
                            "sequencer": "0C0F6F405D6ED209E1"
                        }
                    }
                },
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": self.region,
                    "eventTime": "2019-11-03T19:37:27.192Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "AWS:AIDAINPONIXQXGT5NGHY6"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "192.168.0.1"
                    },
                    "responseElements": {
                        "x-amz-request-id": "D82B88E5F771F645",
                        "x-amz-id-2": "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "828aa6fc-f7b5-4305-8584-487c791949c1",
                        "bucket": {
                            "name": self.s3_bucket,
                            "ownerIdentity": {
                                "principalId": "A3I5XTEXAMAI3E"
                            },
                            "arn": f"arn:aws:s3:::{self.s3_bucket}"
                        },
                        "object": {
                            "key": self.images[1],
                            "size": 1024,
                            "eTag": "b21b84d653bb07b05b1e6b33684dc11b",
                            "sequencer": "0C0F6F405D6ED209E1"
                        }
                    }
                }
            ]
        }

    @pytest.fixture(autouse=True)
    def mock_settings_env_vars(self):
        with mock.patch.dict(os.environ, {"AWS_REGION": self.region,
                                          "NEW_SIZE": self.new_size,
                                          "NEW_IMAGE_DESCRIPTION": self.description,
                                          "NEW_IMAGE_EXTENSION": self.new_extension}):
            yield

    def test_app(self):
        # given
        event = self._get_s3_event()

        # when
        handler(event, None)

        # then
        self._logger.info("Checking if new images has been well created and uploaded to s3 bucket %s...",
                          self.s3_bucket)
        for image in self.images:
            filename, file_extension = os.path.splitext(image)

            new_image = "{key}_{size}{ext}".format(key=filename, size=self.new_size, ext=self.new_extension)
            head_object = self.s3_client.head_object(Bucket=self.s3_bucket, Key=new_image)
            assert head_object is not None
            assert head_object['Metadata']['x-amz-meta-description'] == self.description