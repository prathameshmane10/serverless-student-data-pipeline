import boto3

session = boto3.Session(
    profile_name = "student-pipeline-dev"
)

sts = session.client('sts')

identity = sts.get_caller_identity()

print("Aws Connection Successful")
print("Account: " + identity['Account'])
print("Arn: " + identity['Arn'])

print("configured region: " + session.region_name)