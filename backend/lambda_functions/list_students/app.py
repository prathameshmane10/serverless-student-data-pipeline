
import json
import os
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "StudentRecord")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)


# Convert DynamoDB Decimal values into JSON-compatible numbers.
def decimal_converter(value):
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    raise TypeError(f"Unsupported type: {type(value)}")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, default=decimal_converter)
    }


def lambda_handler(event, context):

    try:
        students = []
        scan_kwargs = {}

        # Continue scanning until DynamoDB has no remaining pages.
        while True:
            result = table.scan(**scan_kwargs)

            students.extend(result.get("Items", []))

            last_key = result.get("LastEvaluatedKey")

            if not last_key:
                break

            scan_kwargs["ExclusiveStartKey"] = last_key

        return response(200, {
            "message": "Students retrieved successfully",
            "total_students": len(students),
            "students": students
        })

    except ClientError as error:
        print("DynamoDB error:", error.response["Error"])

        return response(500, {
            "message": "Unable to retrieve students"
        })

    except Exception as error:
        print("Unexpected error:", str(error))

        return response(500, {
            "message": "Internal server error"
        })
