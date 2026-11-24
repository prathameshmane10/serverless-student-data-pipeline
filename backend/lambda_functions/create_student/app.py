from datetime import datetime, timezone
import json
import os
import uuid
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
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        if "body" in event:
            raw_body = event["body"]

            if isinstance(raw_body, str):
                data = json.loads(raw_body)
            elif isinstance(raw_body, dict):
                data = raw_body
            else:
                return response(400, {"error": "Invalid request body format"})
        else:
            data = event

        if not isinstance(data, dict):
            return response(400, {"error": "Request payload must be a JSON object"})

        name = str(data.get("name") or "").strip()
        email = str(data.get("email") or "").strip().lower()
        course = str(data.get("course") or "").strip()

        # Validate required fields.
        if not all([name, email, course]):
            return response(400, {
                "message": "name, email and course are required",
            })

        # Basic email format validation.
        if "@" not in email or "." not in email.split("@")[-1]:
            return response(400, {
                "message": "Invalid email address",
            })

        student_id = f"STU-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        student = {
            "student_id": student_id,
            "name": name,
            "email": email,
            "course": course,
            "created_at": timestamp,
        }

        table.put_item(
            Item=student,
            ConditionExpression="attribute_not_exists(student_id)",
        )

        return response(201, {
            "message": "Student created successfully",
            "student": student,
        })

    except json.JSONDecodeError:
        return response(400, {
            "message": "Request body must contain valid JSON",
        })

    except ClientError as error:
        print("DynamoDB error:", error.response["Error"])
        return response(500, {
            "message": "Unable to create student",
        })

    except Exception as error:
        print("Unexpected error:", str(error))
        return response(500, {
            "message": "Internal server error",
        })