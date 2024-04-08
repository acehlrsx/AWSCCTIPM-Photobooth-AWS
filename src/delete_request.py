"""
Takes in the requestId and deletes the record from the database
"""

import os
import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])


def delete_request(requestId):
    item = table.get_item(Key={"requestId": requestId}).get("Item", None)
    if not item:
        return "Item doesn't exist."
    item["status"] = "cancelled"
    table.put_item(Item=item)
    return "Request deleted successfully!"


def handler(event, context):
    event_body = json.loads(event.get("body"))

    message = delete_request(event_body["requestId"])

    body = {
        "message": message,
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