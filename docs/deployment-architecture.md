# Frontend Deployment Architecture

## Hosting Services

- Amazon S3: Stores static frontend files.
- Amazon CloudFront: Distributes frontend content.
- Origin Access Control (OAC): Restricts S3 access to CloudFront.

## S3 Configuration

- AWS Region: ap-southeast-2
- Bucket: student-pipeline-frontend
- Public Access: Blocked
- Object Ownership: Bucket owner enforced
- Versioning: Enabled
- Encryption: SSE-S3
- Static Website Hosting: Disabled

## Security Design

The S3 bucket remains private. CloudFront accesses S3
using Origin Access Control (OAC). Users access the
frontend through CloudFront over HTTPS.


## CloudFront Configuration

- Distribution: Created
- Origin: Private S3 bucket REST endpoint
- Origin Access Control: student-pipeline-frontend-oac
- Signing Protocol: SigV4
- Viewer Protocol: Redirect HTTP to HTTPS
- Default Root Object: index.html
- Cache Policy: CachingOptimized
- Allowed Methods: GET, HEAD

## Security

- S3 public access remains blocked.
- CloudFront accesses S3 using OAC.
- S3 bucket policy restricts access to the CloudFront distribution.