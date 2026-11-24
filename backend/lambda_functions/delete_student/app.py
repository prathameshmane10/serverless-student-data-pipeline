import json
import os

import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "StudentRecord")

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
        if event.get("pathParameters"):
            data = event["pathParameters"]
        elif "body" in event and event["body"] is not None:
            body = event["body"]

            if isinstance(body, str):
                data = json.loads(body)
            elif isinstance(body, dict):
                data = body
            else:
                return response(400, {"message": "Invalid request body"})
        else:
            data = event

        if not isinstance(data, dict):
            return response(400, {"message": "Invalid request payload"})

        student_id = data.get("studentId") or data.get("student_id") or ""

        if not isinstance(student_id, str) or not student_id.strip():
            return response(400, {"message": "studentId is required"})

        result = table.delete_item(
            Key={"student_id": student_id.strip()},
            ConditionExpression="attribute_exists(student_id)",
            ReturnValues="ALL_OLD"
        )

        deleted_student = result.get("Attributes")

        return response(200, {
            "message": "Student deleted successfully",
            "deleted_student": deleted_student
        })

    except json.JSONDecodeError:
        return response(400, {"message": "Invalid JSON request body"})

    except ClientError as error:
        error_code = error.response["Error"]["Code"]

        if error_code == "ConditionalCheckFailedException":
            return response(404, {"message": "Student not found"})

        print("DynamoDB error:", error.response["Error"])
        return response(500, {"message": "Unable to delete student"})

    except Exception as error:
        print("Unexpected error:", str(error))
        return response(500, {"message": "Internal server error"})