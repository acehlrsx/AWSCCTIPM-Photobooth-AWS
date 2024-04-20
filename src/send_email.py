"""
Takes in requestId only as parameter. Gets the whole request data and sends an email to all clients.
"""

import os
import json
import boto3

s3 = boto3.client("s3")
ses = boto3.client("ses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])


def send_email(event_body):
    item = table.get_item(Key={"requestId": event_body["requestId"]})["Item"]
    print(item)
    image_path = item["imagePath"]  # templated_photos/{folder_name}
    s3_domain = f"https://awscc-photobooth.s3.ap-southeast-1.amazonaws.com"
    template_data = {}

    # Get all objects in folder
    response = s3.list_objects_v2(Bucket=os.environ["BUCKET"], Prefix=image_path)
    contents = response["Contents"]
    for i in range(3):
        template_data[f"image{i+1}"] = f"{s3_domain}/{contents[i]['Key']}"
    print(template_data)

    for email in item["emails"]:
        ses.send_templated_email(
            Source="awscloudclub.pupmnl@gmail.com",
            Destination={
                "ToAddresses": [email],
                "BccAddresses": ["markachilesflores2004@gmail.com", "awscloudclub.pupmnl@gmail.com"],
            },
            ReplyToAddresses=["markachilesflores2004@gmail.com", "awscloudclub.pupmnl@gmail.com"],
            Template="DBM-ICT-Week",
            TemplateData=json.dumps(template_data),
        )
    print("Finished sending email.")


def update_status(event_body):
    print("Updating status in DynamoDB")
    request_id = event_body["requestId"]
    item = table.get_item(Key={"requestId": request_id})["Item"]
    item["status"] = "sent"
    table.put_item(Item=item)
    print("Status updated")


def handler(event, context):
    try:
        event_body = json.loads(event.get("body"))
        print(event_body)

        # Send email
        send_email(event_body)

        # Update status in DynamoDB
        update_status(event_body)

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