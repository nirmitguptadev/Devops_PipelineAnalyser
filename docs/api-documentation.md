# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
No authentication required for local development.

## Endpoints

### 1. Analyze Pipeline Log

**Endpoint:** `POST /api/analyze`

**Description:** Analyzes pipeline logs and categorizes failures with root cause analysis.

**Request Body:**
```json
{
  "pipeline_name": "my-ci-pipeline",
  "log_content": "BUILD FAILED: compilation error in Main.java",
  "ci_platform": "jenkins",
  "use_ai": true
}
```

**Response:**
```json
{
  "pipeline_name": "my-ci-pipeline",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "category": "build_failure",
  "root_cause": "Code compilation or build configuration issue",
  "error_lines": ["BUILD FAILED: compilation error in Main.java"],
  "recommendations": [
    "Check syntax errors in recent commits",
    "Verify build configuration files",
    "Ensure all dependencies are available"
  ],
  "severity": "high",
  "ai_insights": "The compilation error suggests missing imports or syntax issues",
  "troubleshooting": ["Check Java version", "Verify classpath"]
}
```

### 2. Get Recent Failures

**Endpoint:** `GET /api/failures?limit=10`

**Description:** Retrieves recent pipeline failures.

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 50)

**Response:**
```json
[
  {
    "id": 1,
    "pipeline_name": "my-ci-pipeline",
    "timestamp": "2025-01-15T10:30:00.000Z",
    "category": "build_failure",
    "severity": "high",
    "ci_platform": "jenkins",
    "created_at": "2025-01-15T10:30:00.000Z"
  }
]
```

### 3. Get Statistics

**Endpoint:** `GET /api/stats`

**Description:** Returns statistical analysis of pipeline failures.

**Response:**
```json
{
  "total_failures": 150,
  "by_category": {
    "build_failure": 45,
    "test_failure": 60,
    "deployment_failure": 30,
    "infrastructure_failure": 15
  },
  "by_severity": {
    "critical": 20,
    "high": 50,
    "medium": 60,
    "low": 20
  },
  "by_platform": {
    "jenkins": 100,
    "github_actions": 50
  }
}
```

### 4. Settings Management

**Get Settings:** `GET /api/settings`
**Jenkins Config:** `POST /api/settings/jenkins`
**GitHub Config:** `POST /api/settings/github`
**Test Connections:** `POST /api/settings/jenkins/test`

### 5. Webhook Endpoints

**Jenkins:** `POST /api/webhook/jenkins`
**GitHub:** `POST /api/webhook/github`

### 6. Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "jenkins_integration": true,
  "github_integration": false
}
```

## Error Responses

**Error Response Format:**
```json
{
  "error": "Error message description"
}
```

**HTTP Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input
- `500 Internal Server Error`: Server error
