# 🎓 Serverless Student Management System

A fully serverless student management platform built on **AWS API Gateway, AWS Lambda and Amazon DynamoDB**, with a responsive vanilla-JavaScript dashboard. It supports complete CRUD operations plus email search, with no servers to provision or maintain.

![AWS](https://img.shields.io/badge/AWS-Serverless-FF9900?logo=amazonaws&logoColor=white)
![Python](https://img.shields.io/badge/Python-Lambda-3776AB?logo=python&logoColor=white)
![DynamoDB](https://img.shields.io/badge/Amazon-DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)
![JavaScript](https://img.shields.io/badge/Frontend-Vanilla%20JS-F7DF1E?logo=javascript&logoColor=black)

<!-- Add a dashboard screenshot at docs/screenshots/dashboard.png -->
![Dashboard](docs/screenshots/dashboard.png)

## ✨ Features

- **Create, read, update and delete** student records through a REST API
- **Search by email** using a DynamoDB Global Secondary Index (`EmailIndex`)
- **Modern dashboard**: stat cards, sortable and filterable table, course distribution chart, modals, toast notifications and a dark/light theme
- **Input validation** and consistent JSON error responses in every Lambda function
- **Safe rendering**: API data is written to the DOM with `textContent`, which prevents HTML injection
- **CORS enabled** so the browser frontend can call the API directly

## 🏗️ Architecture

```text
Browser (HTML / CSS / JS)
        │  HTTPS
        ▼
Amazon API Gateway  (REST API, stage: dev)
        │
        ▼
AWS Lambda  (Python, one function per route)
        │
        ▼
Amazon DynamoDB  (table: StudentRecord, GSI: EmailIndex)
```

| Setting | Value |
|---|---|
| Region | `ap-southeast-2` (Sydney) |
| API type | REST API |
| Stage | `dev` |
| DynamoDB table | `StudentRecord` (partition key `student_id`) |
| GSI | `EmailIndex` (partition key `email`) |

More detail: [docs/deployment-architecture.md](docs/deployment-architecture.md)

## 🔌 API Endpoints

Base URL: `https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev`

| Method | Endpoint | Lambda | Description |
|---|---|---|---|
| `POST` | `/students` | `create_student` | Create a student |
| `GET` | `/students` | `list_students` | List all students |
| `GET` | `/students/{student_id}` | `get_student` | Get a student by ID |
| `PUT` | `/students/{student_id}` | `update_student` | Update name, email and/or course |
| `DELETE` | `/students/{student_id}` | `delete_student` | Delete a student |
| `GET` | `/students/search?email=` | `search_student_email` | Find students by email |

**Example**

```bash
curl -X POST "$API_URL/students" \
  -H "Content-Type: application/json" \
  -d '{"name":"Rahul Sharma","email":"rahul@example.com","course":"AWS Cloud Computing"}'
```

```json
{
  "message": "Student created successfully",
  "student": {
    "student_id": "STU-A1B2C3D4",
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "course": "AWS Cloud Computing",
    "created_at": "2026-11-24T10:15:30+00:00"
  }
}
```

Full reference: [docs/api-documentation.md](docs/api-documentation.md)

## 🗄️ Data Model

| Attribute | Type | Notes |
|---|---|---|
| `student_id` | String | Partition key, generated as `STU-XXXXXXXX` |
| `name` | String | Required |
| `email` | String | Required, stored lowercase, indexed by `EmailIndex` |
| `course` | String | Required |
| `created_at` | String | ISO-8601 UTC timestamp |
| `updated_at` | String | Set on update |

## 📁 Project Structure

```text
serverless-student-data-pipeline/
├── backend/
│   ├── lambda_functions/
│   │   ├── create_student/
│   │   ├── list_students/
│   │   ├── get_student/
│   │   ├── update_student/
│   │   ├── delete_student/
│   │   └── search_student_email/
│   ├── insert_student.py      # boto3 script: insert a student
│   ├── get_students.py        # boto3 script: list students
│   ├── search_student.py      # boto3 script: search by email
│   └── manage_student.py      # boto3 script: update / delete
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── docs/                      # API and deployment documentation
├── verify_aws.py              # checks AWS credentials / connectivity
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- An AWS account with the DynamoDB table, Lambda functions and API Gateway deployed as described above
- [AWS CLI](https://aws.amazon.com/cli/) configured with a profile (the helper scripts use `student-pipeline-dev`)

### Run the frontend

The API URL is set at the top of [frontend/js/app.js](frontend/js/app.js). Update `API_BASE_URL` if you deploy your own API.

```bash
cd frontend
python -m http.server 8000
# open http://localhost:8000
```

A static server such as VS Code Live Server works too.

### Run the backend helper scripts (optional)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

python verify_aws.py           # confirm AWS access
python backend/get_students.py
```

### Deploy the Lambda functions

Each folder in `backend/lambda_functions/` is one function (`app.py` with a `lambda_handler`). Create a Python Lambda per folder, give it DynamoDB permissions for `StudentRecord` (and `EmailIndex` for search), and attach it to its API Gateway route. Environment variables (all optional, with defaults):

| Variable | Default |
|---|---|
| `TABLE_NAME` | `StudentRecord` |
| `INDEX_NAME` | `EmailIndex` (search function) |
| `AWS_REGION` | `ap-southeast-2` |

> **Tip:** enable **Lambda Proxy integration** on each API Gateway method. The Lambda functions return `{statusCode, headers, body}`, and without proxy integration that envelope is passed back as the response body. The frontend handles both cases.

## 🔒 Security Notes

This project is a **development / learning build**:

- No authentication is configured yet (planned: Amazon Cognito or IAM authorizers)
- CORS allows `*`; restrict it to your frontend domain for production
- Search is an exact email match and uses an eventually consistent GSI, so a record just created may take a moment to appear

## 🛣️ Roadmap

- [ ] Authentication with Amazon Cognito
- [ ] Infrastructure as Code (AWS SAM / Terraform)
- [ ] Host the frontend on S3 + CloudFront
- [ ] Unit tests with `pytest` and `moto`
- [ ] CI/CD with GitHub Actions
- [ ] Pagination for the list endpoint

## 🧰 Tech Stack

AWS API Gateway · AWS Lambda (Python / boto3) · Amazon DynamoDB · HTML5 · CSS3 · JavaScript (ES6+)

## 👤 Author

**Prathamesh Mane** · [GitHub](https://github.com/prathameshmane10)

## 📄 License

Released under the MIT License. Add a `LICENSE` file before publishing.
