import json


def handler(event, context):
    print("Hello start")
    try:
        print("Trying the body")
        body = {
            "message": "Hello!",
            "event": event,
        }
    except Exception as e:
        print("Something happened.", e)
        body = {"message": "Something happened. " + str(e), "event": event}

    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # This allows CORS from any origin
        },
        "body": json.dumps(body),
    }
    print("Hello finish")
    return response