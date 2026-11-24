import boto3
from botocore.exceptions import ClientError

# AWS CONFIGURATION
AWS_PROFILE = "student-pipeline-dev"    
AWS_REGION = "ap-southeast-2"
TABLE_NAME = "StudentRecord"

# Create AWS Session and DynamoDB Resource
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

#connect to DynamoDB
dynamodb = session.resource("dynamodb")

# Access DynamoDB Table
table = dynamodb.Table(TABLE_NAME)

def get_all_students():
    students = []
    try:
        #first Scan
        response = table.scan()
        students.extend(response.get("Items", []))

        #handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            students.extend(response.get("Items", []))

        return students

    except ClientError as e:
        print("Error retrieving student records:", e.response["Error"]["Message"])
        return None


def display_students():
    students = get_all_students()
    if students is None:
        print("Failed to retrieve student records.")
        return

    if not students:
        print("No student records found.")
        return

    print("\n========== STUDENT RECORDS ==========\n")

    for index, student in enumerate(students, start=1):
        print(f"Student {index}:")
        print(f"  Student ID: {student.get('student_id', 'N/A')}")
        print(f"  Name: {student.get('name', 'N/A')}")
        print(f"  Email: {student.get('email', 'N/A')}")
        print(f"  Course: {student.get('course', 'N/A')}")
        print(f"  Created At: {student.get('created_at', 'N/A')}")
        print("-----------------------------------")

        print()


    print("========== END OF RECORDS ==========\n")
    print("Total Students:", len(students))


if __name__ == "__main__":
    display_students()
