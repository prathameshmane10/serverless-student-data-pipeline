from datetime import datetime, timezone
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
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        if event.get("pathParameters"):
            data = dict(event["pathParameters"])
            raw_body = event.get("body")

            if isinstance(raw_body, str) and raw_body.strip():
                body_data = json.loads(raw_body)
                if not isinstance(body_data, dict):
                    return response(400, {"message": "Request body must be a JSON object"})
                data.update(body_data)
            elif isinstance(raw_body, dict):
                data.update(raw_body)
            elif raw_body is not None:
                return response(400, {"message": "Invalid request body"})

        elif "body" in event:
            body = event["body"]

            if isinstance(body, str):
                data = json.loads(body)
                if not isinstance(data, dict):
                    return response(400, {"message": "Request body must be a JSON object"})
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

        # Only update fields supplied by the caller.
        allowed_fields = ("name", "email", "course")
        updates = {}

        for field in allowed_fields:
            if field in data:
                value = data[field]

                if not isinstance(value, str) or not value.strip():
                    return response(400, {
                        "message": f"{field} must be a non-empty string",
                    })

                updates[field] = value.strip()

        if not updates:
            return response(400, {
                "message": "At least one field (name, email, course) is required",
            })

        if "email" in updates:
            updates["email"] = updates["email"].lower()

            if (
                "@" not in updates["email"]
                or "." not in updates["email"].split("@")[-1]
            ):
                return response(400, {
                    "message": "Invalid email address",
                })

        # Build an UpdateExpression from the validated fields.
        expression_names = {}
        expression_values = {}
        set_expressions = []

        for index, (field, value) in enumerate(updates.items()):
            name_key = f"#field{index}"
            value_key = f":value{index}"

            expression_names[name_key] = field
            expression_values[value_key] = value

            set_expressions.append(f"{name_key} = {value_key}")

        expression_names["#updated_at"] = "updated_at"
        expression_values[":updated_at"] = datetime.now(timezone.utc).isoformat()
        set_expressions.append("#updated_at = :updated_at")

        result = table.update_item(
            Key={"student_id": student_id.strip()},
            UpdateExpression="SET " + ", ".join(set_expressions),
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ConditionExpression="attribute_exists(student_id)",
            ReturnValues="ALL_NEW",
        )

        return response(200, {
            "message": "Student updated successfully",
            "student": result["Attributes"],
        })

    except json.JSONDecodeError:
        return response(400, {"message": "Invalid JSON request body"})

    except ClientError as error:
        error_code = error.response["Error"]["Code"]

        if error_code == "ConditionalCheckFailedException":
            return response(404, {"message": "Student not found"})

        print("DynamoDB error:", error.response["Error"])
        return response(500, {"message": "Unable to update student"})

    except Exception as error:
        print("Unexpected error:", str(error))
        return response(500, {"message": "Internal server error"})