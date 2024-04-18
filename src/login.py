import os
import json
import hashlib
import boto3
import datetime
import jwt

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])
secret_token = os.environ["SECRET_TOKEN"]


def check_credentials(event_body):
    try:
        # Get the payload
        username = event_body["username"]
        password = event_body["password"]

        # Get the data from database
        response = table.get_item(Key={"requestId": "credentials"}, ProjectionExpression="user_list")
        item = response.get("Item")
        print(response, item)

        # Encrypt password using hmac and hashlib
        encrypted_password = hashlib.sha256((password + secret_token).encode()).hexdigest()
        print(encrypted_password)

        # Compare password given in payload and password stored in database
        for entry in item["user_list"]:
            if entry["username"] == username:
                if entry["password"] == encrypted_password:
                    entry["last_logged_in"] = str(datetime.datetime.utcnow())
                    table.put_item(Item={"requestId": "credentials", "user_list": item["user_list"]})
                    return generate_jwt(username)
                else:
                    raise Exception("Password is incorrect.")
        else:
            raise Exception("User is not found.")

    except Exception as e:
        raise e


def generate_jwt(username):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12),
    }
    jwt_token = jwt.encode(payload, secret_token, "HS256")
    return jwt_token


def handler(event, context):
    try:
        event_body = json.loads(event.get("body"))

        # Business
        jwt_token = check_credentials(event_body)
        print(jwt_token)

        status_code = 200
        message = "Successful."
    except Exception as e:
        status_code = 400
        message = "An error occured. " + str(e)
        jwt_token = ""

    body = {"message": message, "token": jwt_token, "event": event}
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # This allows CORS from any origin
        },
        "body": json.dumps(body),
    }
    return response