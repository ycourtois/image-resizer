# Image Resizer

It loads an image from an S3 bucket, resizes it and uploads it to the same bucket alongside the original file.

## Unit Testing

```
pip install -r requirements-dev.txt

python -m pytest tests/test_app.py::TestApp
```

## Execute your lambda function locally

Build the solution.

You will need to have python3.8 and docker installed.

```
sam build
```

Create a s3 bucket :

```
BUCKET_NAME=my-bucket
aws s3api create-bucket --bucket ${BUCKET_NAME} --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1
```

Upload an image with the following key : images/image1.jpg

```
aws s3api put-object --bucket ${BUCKET_NAME} --key images/image1.jpg --body tests/images/image1.jpg
```

You can now trigger your lambda function with sam local from a simulated s3 event

```
sam local generate-event s3 put --bucket ${BUCKET_NAME} --key images/image1.jpg | sam local invoke -e - ImageResizerFunction -n env.json
```
or
```
sam local invoke -e s3_event.json ImageResizerFunction -n env.json
```

Retrieve the new image.

```
aws s3api get-object --bucket ${BUCKET_NAME} --key images/image1_50x50.jpeg image_resized.jpg
```

## Deployment to AWS

### Prerequisites

Create an S3 bucket to store your artifacts (packaged template and lambda function code).

```
BUCKET_ARTIFACT=my-bucket-artifact
aws s3api create-bucket --bucket ${BUCKET_ARTIFACT} --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1
```

Update the s3_bucket variable in samconfig.toml file to point to the newly created bucket.

```
sam deploy
```

To avoid triggering indefinitely the S3 notification once the new file has been created, the application changes file extension from .jpg to .jpeg.
Since there is a suffix filter set to .jpg, newly created file will not trigger a new lambda function invocation.

### Testing lambda function


Upload an image.

```
aws s3api put-object --bucket yco-image-resizer --key images/image1.jpg --body tests/images/image1.jpg
```

Retrieve the new image.

```
aws s3api get-object --bucket yco-image-resizer --key images/image1_50x50.jpeg image_resized.jpg
```


## Delete resources

aws cloudformation delete-stack --stack-name yco-image-resizer

You will have to empty and delete your bucket manually since cloudformation will refuse to do it because it is not empty.


## Issues

Cloudformation does not seem able to update s3 event notification properly when modifying filters. \
Example : Inside template.yml, change ImagesExtension to jpeg instead if jpg.