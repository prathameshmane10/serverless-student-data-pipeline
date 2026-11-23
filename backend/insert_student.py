from datetime import datetime, timezone
import uuid
import boto3
from botocore.exceptions import ClientError

# AWS CONFIGURATION
AWS_PROFILE = "student-pipeline-dev"
AWS_REGION = "ap-southeast-2"
TABLE_NAME = "StudentRecord"

# Create AWS Session and DynamoDB Resource
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
dynamodb = session.resource("dynamodb")

# Access DynamoDB Table
table = dynamodb.Table(TABLE_NAME)


def insert_student_record(name, email, course):
    # Validation
    if not all([name.strip(), email.strip(), course.strip()]):
        print("Error: All fields are required.")
        return None

    # Generate a unique student ID
    student_id = "STU-" + str(uuid.uuid4())[:8].upper()

    # Student record to insert
    student = {
        "student_id": student_id,
        "name": name.strip(),
        "email": email.strip(),
        "course": course.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = table.put_item(
            Item=student,
            ConditionExpression="attribute_not_exists(student_id)",
        )

        print("Student record inserted successfully")
        print("Student ID:", student_id)
        print("Response:", response["ResponseMetadata"]["HTTPStatusCode"])

        return student
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ConditionalCheckFailedException":
            print("Error: Student record with the same ID already exists.")
        else:
            print("Error inserting student record:", e.response["Error"]["Message"])

        return None


if __name__ == "__main__":
    students = [
        ("Amit Patil", "amit@example.com", "Python"),
        ("Priya Sharma", "priya@example.com", "DevOps"),
        ("Neha Joshi", "neha@example.com", "Docker"),
    ]

    for student in students:
        insert_student_record(*student)