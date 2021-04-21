import logging
import os
from unittest import mock

import pytest

from src.app import handler


class TestApp:
    def setup_method(self, method):
        self._logger = logging.getLogger(__name__)
        self.region = "eu-west-1"
        self.s3_bucket = "yco-image-resizer"
        self.s3_key = "images/image1.jpg"
        self.new_size = "50x50"
        self.description = "awesome image"
        self.new_extension = ".jpeg"

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
                            "key": self.s3_key,
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

    def test_handler(self):
        # given
        event = self._get_s3_event()

        # when
        handler(event, None)
