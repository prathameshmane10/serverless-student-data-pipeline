import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

AWS_PROFILE = "student-pipeline-dev"  # Change to match `aws configure list-profiles`
AWS_REGION = "ap-southeast-2"
TABLE_NAME = "StudentRecord"
INDEX_NAME = "EmailIndex"

session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def get_student_by_id(student_id):
    try:
        response = table.get_item(
            Key={"student_id": student_id},
            ConsistentRead=True,
        )
        student = response.get("Item")

        if student:
            print("\nStudent Found!")
            print("---------------------------")
            for key, value in student.items():
                print(f"{key}: {value}")
            return student

        print("Student not found.")
        return None

    except ClientError as error:
        print("DynamoDB Error:", error.response["Error"]["Message"])
        return None


def search_student_by_email(email):
    try:
        response = table.query(
            IndexName=INDEX_NAME,
            KeyConditionExpression=Key("email").eq(email.strip().lower()),
        )
        students = response.get("Items", [])

        if students:
            print("\nStudents Found!")
            print("---------------------------")
            for student in students:
                for key, value in student.items():
                    print(f"{key}: {value}")
                print("---------------------------")
            return students

        print("No student found with this email.")
        return []

    except ClientError as error:
        print("DynamoDB Error:", error.response["Error"]["Message"])
        return None


if __name__ == "__main__":
    print("\n===== SEARCH BY STUDENT ID =====")
    get_student_by_id("STU-9DCE9EEB")

    print("\n===== SEARCH BY EMAIL =====")
    search_student_by_email("rahul@example.com")