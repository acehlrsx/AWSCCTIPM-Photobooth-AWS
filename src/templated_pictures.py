"""
Triggered when an object is uploaded to awscc-photobooth/raw_photos

Payload:
- S3 Event Trigger
- 

Process
1. Access the template from S3 and read as a string
2. Access the folder of raw images from S3 (name of folder passed through payload)
3. Do the templating
4. Uplaod to S3
"""

import os
import json
import boto3
import requests
from PIL import Image
from io import BytesIO

s3 = boto3.client("s3")
s3_resource = boto3.resource("s3")
bucket = s3_resource.Bucket(os.environ["BUCKET"])
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])


def template_image(event):
    """
    - Get bucket and key
    - Create a template with Pillow Image
    - Process templating
    """
    # Get bucket, key
    FRAME_URL = "https://awscc-photobooth.s3.ap-southeast-1.amazonaws.com/assets/DBM-ICT-Week-Frame.png"
    BUCKET_URL = "https://awscc-photobooth.s3.ap-southeast-1.amazonaws.com"
    BUCKET = event["Records"][0]["s3"]["bucket"]["name"]
    full_key = event["Records"][0]["s3"]["object"]["key"]
    list_full_key = full_key.split("/")
    list_full_key.pop(0)
    REQUEST_ID = list_full_key[0]
    KEY = "/".join(list_full_key)
    OBJECT_URL = f"{BUCKET_URL}/{full_key}"
    print(OBJECT_URL, BUCKET, REQUEST_ID, KEY)

    # Create a template
    print("Starting")
    response = requests.get(FRAME_URL)
    print(response)
    template = Image.open(BytesIO(response.content))
    offset = (275, 175)
    image_resize = (4288, 2848)

    # Get object
    response = requests.get(OBJECT_URL)
    print(response)

    # Process templating
    buffer = BytesIO()
    image = Image.open(BytesIO(response.content))
    image = image.resize(image_resize)
    template.paste(image, offset)
    template.save(buffer, "PNG")
    buffer.seek(0)
    response = bucket.put_object(Key=f"templated_photos/{KEY}", Body=buffer)
    print(response)
    print("Finished!")
    return REQUEST_ID


def update_status(request_id):
    # Get number of objects in folder
    response = s3.list_objects_v2(Bucket=os.environ["BUCKET"], Prefix=f"templated_photos/{request_id}")
    key_count = response["KeyCount"]
    print(key_count, response)

    # Update status
    item = table.get_item(Key={"requestId": request_id})["Item"]
    if item["status"] == "sent":
        print("This item has already been sent.")
        return 4
    item["status"] = f"templated: {key_count}"
    item["imagePath"] = f"templated_photos/{request_id}"
    print(item)
    table.put_item(Item=item)
    return key_count


def handler(event, context):
    try:
        print(event)

        # Business Logic
        # Template the image
        request_id = template_image(event)

        # Update the status in DynamoDB
        key_count = update_status(request_id)

        # Invoke email_sender if key_count == 3
        if key_count == 3:
            print("It got here")
            payload = {"requestId": request_id}
            url = f"{os.environ['API_URL']}/send_email"
            response = requests.post(url=url, json=payload)
            print(response)

        status_code = 200
        message = "Successful."
    except Exception as e:
        status_code = 400
        message = "An error occured. " + str(e)

    body = {
        "message": message,
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