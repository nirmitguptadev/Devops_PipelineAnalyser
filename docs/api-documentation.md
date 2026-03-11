# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Analyze Pipeline Log

**Endpoint:** `POST /api/analyze`

**Description:** Analyzes pipeline logs and categorizes failures with root cause analysis.

**Request Body:**
```json
{
  "pipeline_name": "my-ci-pipeline",
  "log_content": "BUILD FAILED: compilation error in Main.java"
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
  "severity": "high"
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
  }
}
```

### 4. Health Check

**Endpoint:** `GET /api/health`

**Description:** Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "error": "Error message description"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Future versions will include:
- 100 requests per minute per IP
- 1000 requests per hour per IP
