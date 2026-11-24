# Student Management API Documentation

## 1. Project Overview

The Student Management API is a serverless REST API built using AWS API Gateway, AWS Lambda, and Amazon DynamoDB.

It provides CRUD (Create, Read, Update, Delete) operations for student records, along with email-based student search.

### Architecture

```text
Client / Postman / Frontend
          |
          v
    AWS API Gateway
          |
          v
     AWS Lambda
          |
          v
    Amazon DynamoDB
     StudentRecord
```

### AWS Configuration

| Configuration | Value |
|---|---|
| AWS Region | `ap-southeast-2` |
| API Name | `StudentManagementAPI` |
| API Type | REST API |
| API ID | `krmmk6s4hl` |
| Deployment Stage | `dev` |
| DynamoDB Table | `StudentRecord` |
| DynamoDB Partition Key | `student_id` |
| DynamoDB GSI | `EmailIndex` |
| Authentication | Not configured yet |
| CORS | Enabled |

## 2. API Base URL

**Base URL:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev
```

## 3. Available API Endpoints

| # | HTTP Method | Endpoint | Description |
|---|---|---|---|
| 1 | POST | `/students` | Create a new student |
| 2 | GET | `/students` | Retrieve all students |
| 3 | GET | `/students/{student_id}` | Retrieve a student by ID |
| 4 | PUT | `/students/{student_id}` | Update student information |
| 5 | DELETE | `/students/{student_id}` | Delete a student |
| 6 | GET | `/students/search?email={email}` | Search students by email |

## 4. API Endpoint Details

### 4.1 Create Student

**Method:** `POST`

**Endpoint:**

```http
POST /students
```

**Full URL:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev/students
```

**Headers:**

```http
Content-Type: application/json
```

**Request Body:**

```json
{
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "course": "AWS Cloud Computing"
}
```

**Lambda Function:** `student-create-function`

---

### 4.2 Get All Students

**Method:** `GET`

**Endpoint:**

```http
GET /students
```

**Full URL:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev/students
```

**Request Body:** Not required.

**Lambda Function:** `student-list-function`

---

### 4.3 Get Student by ID

**Method:** `GET`

**Endpoint:**

```http
GET /students/{student_id}
```

**Full URL Example:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev/students/STU-A1B2C3D4
```

**Path Parameter:**

| Parameter | Description | Required |
|---|---|---|
| student_id | Unique student identifier | Yes |

**Lambda Function:** `student-get-function`

---

### 4.4 Update Student

**Method:** `PUT`

**Endpoint:**

```http
PUT /students/{student_id}
```

**Full URL Example:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev/students/STU-A1B2C3D4
```

**Path Parameter:**

| Parameter | Description | Required |
|---|---|---|
| student_id | Unique student identifier | Yes |

**Headers:**

```http
Content-Type: application/json
```

**Request Body:**

Only provide the fields that need to be updated.

Example:

```json
{
    "course": "AWS Solutions Architect"
}
```

**Lambda Function:** `student-update-function`

---

### 4.5 Delete Student

**Method:** `DELETE`

**Endpoint:**

```http
DELETE /students/{student_id}
```

**Full URL Example:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev/students/STU-A1B2C3D4
```

**Path Parameter:**

| Parameter | Description | Required |
|---|---|---|
| student_id | Unique student identifier | Yes |

**Request Body:** Not required.

**Lambda Function:** `student-delete-function`

---

### 4.6 Search Student by Email

**Method:** `GET`

**Endpoint:**

```http
GET /students/search?email={email}
```

**Full URL Example:**

```text
https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev/students/search?email=rahul%40example.com
```

**Query Parameters:**

| Parameter | Description | Required |
|---|---|---|
| email | Student email address | Yes |

**Lambda Function:** `student-search-email-function`

**Important:** DynamoDB Global Secondary Index queries are eventually consistent. Search results may not reflect a recent write immediately.

## 5. CORS Configuration

Cross-Origin Resource Sharing (CORS) is enabled on the API Gateway resources to allow browser-based frontend applications to communicate with the backend API.

### Allowed Origins

```text
*
```

This wildcard is currently suitable only for development and testing.

For production, restrict the allowed origin to the actual frontend domain.

### Allowed HTTP Methods

```text
GET, POST, PUT, DELETE, OPTIONS
```

### Allowed Headers

```text
Content-Type
Authorization
X-Amz-Date
X-Api-Key
X-Amz-Security-Token
```

### CORS Resources

CORS is enabled for:

- `/students`
- `/students/{student_id}`
- `/students/search`

The API uses OPTIONS preflight requests to handle browser CORS checks.

**Security Note:** CORS is not an authentication or authorization mechanism. API authentication must be configured separately before production use.

