import os
import json
import boto3
import hashlib

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])
secret_token = os.environ["SECRET_TOKEN"]


def upload_credentials(event_body):
    try:
        # Get payload
        username = event_body["username"]
        password = event_body["password"]
        print(username, password)

        # Check if payload is empty string?
        if not (username and password):
            raise Exception("Username and Password must not be empty strings.")

        # Check if user already exists
        response = table.get_item(Key={"requestId": "credentials"}, ProjectionExpression="user_list")
        item = response.get("Item")
        creds_list = item["user_list"]
        print(response, item)

        for entry in creds_list:
            if entry["username"] == username:
                raise Exception("Username already exists. Please contact developers if you think this is a mistake.")

        # Upload user to DynamoDB
        encrypted_password = hashlib.sha256((password + secret_token).encode()).hexdigest()
        user_credentials = {"last_logged_in": "", "username": username, "password": encrypted_password}
        print(user_credentials)

        creds_list.append(user_credentials)
        response = table.put_item(Item={"requestId": "credentials", "user_list": creds_list})

    except Exception as e:
        raise e


def handler(event, context):
    """
    Register new admins to the database.

    Resources:
    - DynamoDB

    Payload:
    - username: str
    - password: str, SHA256 encoded

    Database schema
    - username: str
    - password: str, SHA256 encoded
    - last_logged_in: datetime
    """

    try:
        event_body = json.loads(event.get("body"))

        # Upload credentials
        upload_credentials(event_body)

        status_code = 200
        message = f"Successfully created {event_body['username']}."
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