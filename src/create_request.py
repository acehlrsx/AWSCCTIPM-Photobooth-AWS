"""
Create the request in DynamoDB

payload = {
    pointPerson
    emails
}

schema:
- requestId: R-20231121-000
- pointPerson
- emails
- imagePath
- status: pending|uploaded|templated|sent

admin schema:
- requestId = "1111"
- count

Process:
1. Clean up `pointPerson` and `emails`: trim whitespace, remove empty strings.
2. Update count per day: check if it exists, increment by 1, put_item.
3. Create requestId and upload request to table.
4. Send response.
"""

import os
import json
import boto3
import pytz
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])


def clean_data(event_body):
    event_body["pointPerson"] = event_body["pointPerson"].strip()
    # Svelte gives a list of dictionaries
    event_body["emails"] = [email["value"] for email in event_body["emails"]]
    event_body["emails"] = [email.strip() for email in event_body["emails"]]
    return event_body


def update_count():
    now = datetime.now(tz=pytz.timezone("Asia/Manila")).strftime("%Y%m%d")
    item = table.get_item(Key={"requestId": now}).get("Item", None)
    if not item:
        item = {"requestId": now, "count": 1}
    else:
        item["count"] += 1
    table.put_item(Item=item)
    return item


def create_request(counter, event_body):
    event_body["requestId"] = f"R-{counter['requestId']}-{counter['count']:03}"
    event_body["status"] = "pending"
    table.put_item(Item=event_body)
    return event_body


def handler(event, context):
    event_body = json.loads(event.get("body"))
    print(event_body)
    # Clean up data
    event_body = clean_data(event_body)

    # Update count per day
    counter = update_count()

    # Create request
    event_body = create_request(counter, event_body)

    # Send response
    body = {
        "message": "Request created successfully!",
        "event": event_body,
    }
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # This allows CORS from any origin
        },
        "body": json.dumps(body),
    }
    return response