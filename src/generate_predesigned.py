"""
Generate multiple pre-signed urls for files to be uploaded from frontend.

Payload:
- objects: list[str]
- folderName: str

Response:
- presignedPosts: dict{obj: {url, fields}}

Can be revised to onle need the folderName since there are always 3 pictures to be uploaded. Will always return 3 presigned_post urls
"""

import os
import json
import boto3

s3 = boto3.client("s3")
bucket_name = os.environ["BUCKET"]


def generate_endpoints(event_body):
    # Get payload
    objects = event_body["objects"]
    folder_name = event_body["folderName"]
    print(objects, folder_name)

    # Check if payload is empty
    if not (objects and folder_name):
        raise Exception("objects and folderName")

    # Loop through each object and generate a presigned_post
    # Add presigned_post to a dictionary `presigned_posts`
    presigned_posts = {}
    for obj in objects:
        print(obj)
        response = s3.generate_presigned_post(Bucket=bucket_name, Key=f"raw_photos/{folder_name}/{obj}", ExpiresIn=600)
        print(response)
        presigned_posts[obj] = {"url": response["url"], "fields": response["fields"]}

    print(presigned_posts)
    return presigned_posts


def handler(event, context):
    try:
        event_body = json.loads(event.get("body"))

        # Business logic
        presigned_posts = generate_endpoints(event_body)

        status_code = 200
        message = "Successful."
    except Exception as e:
        status_code = 400
        message = "An error occured. " + str(e)
        presigned_posts = {}

    body = {
        "message": message,
        "presignedPosts": presigned_posts,
        "event": event,
    }
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # This allows CORS from any origin
        },
        "body": json.dumps(body),
    }
    return response