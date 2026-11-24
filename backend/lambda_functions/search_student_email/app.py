import json
import os

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "StudentRecord")
INDEX_NAME = os.environ.get("INDEX_NAME", "EmailIndex")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):

    try:
        # Support query string parameters, proxy body events, and direct Lambda test events.
        if event.get("queryStringParameters"):
            data = event["queryStringParameters"] or {}
        elif "body" in event and event["body"] is not None:
            body = event["body"]

            if isinstance(body, str):
                data = json.loads(body)
                if not isinstance(data, dict):
                    return response(400, {
                        "message": "Request body must be a JSON object"
                    })
            elif isinstance(body, dict):
                data = body
            else:
                return response(400, {
                    "message": "Invalid request body"
                })
        else:
            data = event

        if not isinstance(data, dict):
            return response(400, {
                "message": "Invalid request payload"
            })

        email = data.get("email") or ""

        if not isinstance(email, str) or not email.strip():
            return response(400, {
                "message": "Email is required"
            })

        email = email.strip().lower()

        if "@" not in email or "." not in email.split("@")[-1]:
            return response(400, {
                "message": "Invalid email address"
            })

        # Query the Global Secondary Index.
        result = table.query(
            IndexName=INDEX_NAME,
            KeyConditionExpression=Key("email").eq(email)
        )

        students = result.get("Items", [])

        # Handle pagination for large result sets.
        while "LastEvaluatedKey" in result:
            result = table.query(
                IndexName=INDEX_NAME,
                KeyConditionExpression=Key("email").eq(email),
                ExclusiveStartKey=result["LastEvaluatedKey"]
            )

            students.extend(result.get("Items", []))

        if not students:
            return response(404, {
                "message": "No students found for this email",
                "email": email
            })

        return response(200, {
            "message": "Student search completed successfully",
            "total_students": len(students),
            "students": students
        })

    except json.JSONDecodeError:
        return response(400, {
            "message": "Request body must contain valid JSON"
        })

    except ClientError as error:
        print("DynamoDB error:", error.response["Error"])

        return response(500, {
            "message": "Unable to search students"
        })

    except Exception as error:
        print("Unexpected error:", str(error))

        return response(500, {
            "message": "Internal server error"
        })