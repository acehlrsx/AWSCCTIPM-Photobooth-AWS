"""
R-20200000
Returns all the requests, except for the counters
"""

import os
import json
import boto3
from datetime import datetime
import pytz

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])


def get_requests(query_string_parameters):
    if not query_string_parameters:
        now = datetime.now(tz=pytz.timezone("Asia/Manila")).strftime("%Y%m%d")
    else:
        now = query_string_parameters.get("date")
    items = table.scan().get("Items")
    requests = [item for item in items if item["requestId"][2:10] == now]

    if not requests:
        return "No requests found.", requests

    return "All requests successfully retrieved!", requests


def handler(event, context):
    print(event)
    path_parameters = event.get("queryStringParameters")

    message, requests = get_requests(path_parameters)

    body = {
        "message": message,
        "requests": requests,
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