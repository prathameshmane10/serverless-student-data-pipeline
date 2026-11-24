from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

AWS_PROFILE = "student-pipeline-dev"
AWS_REGION = "ap-southeast-2"
TABLE_NAME = "StudentRecord"

session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def update_student(student_id, name, email, course):
    if not all([student_id.strip(), name.strip(), email.strip(), course.strip()]):
        print("Error: All fields are required.")
        return None

    try:
        response = table.update_item(
            Key={"student_id": student_id.strip()},
            UpdateExpression=(
                "SET #student_name = :name, "
                "email = :email, "
                "course = :course, "
                "updated_at = :updated_at"
            ),
            ConditionExpression="attribute_exists(student_id)",
            ExpressionAttributeNames={
                "#student_name": "name",
            },
            ExpressionAttributeValues={
                ":name": name.strip(),
                ":email": email.strip().lower(),
                ":course": course.strip(),
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )

        print("Student record updated successfully")
        print("Updated Student Record:")

        for key, value in response["Attributes"].items():
            print(f"{key}: {value}")

        return response["Attributes"]

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ConditionalCheckFailedException":
            print("Error: Student record does not exist.")
        else:
            print("Error updating student record:", e.response["Error"]["Message"])

        return None


def delete_student(student_id):
    if not student_id.strip():
        print("Error: Student ID is required.")
        return False

    try:
        response = table.delete_item(
            Key={"student_id": student_id.strip()},
            ConditionExpression="attribute_exists(student_id)",
            ReturnValues="ALL_OLD",
        )

        print("\nStudent deleted successfully!")
        print("Deleted Record:", response.get("Attributes"))

        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ConditionalCheckFailedException":
            print("Error: Student record does not exist.")
        else:
            print("Error deleting student record:", e.response["Error"]["Message"])

        return False


def verify_student(student_id):
    response = table.get_item(
        Key={"student_id": student_id.strip()},
        ConsistentRead=True,
    )
    return response.get("Item")


if __name__ == "__main__":
    target_student_id = "STU-9DCE9EEB"
    # print("\n===== UPDATE STUDENT RECORD =====")

    # update_student(
    #     student_id=target_student_id,
    #     name="Rahul Sharma Updated",
    #     email="rahul.updated@example.com",
    #     course="AWS Cloud Computing Updated",
    # )

    

    print("\n===== VERIFY UPDATE =====")
    verified_student = verify_student(target_student_id)
    print(verified_student)

    # Uncomment only when you want to delete this student.
    #
    print("\n===== DELETE STUDENT =====")
    delete_student(target_student_id)
    
    print("\n===== VERIFY DELETION =====")
    print(verify_student(target_student_id))