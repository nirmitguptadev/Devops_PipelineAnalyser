# User Guide

## Getting Started

### Quick Start (Manual Mode)

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python src/main/app.py`
4. Access dashboard at http://localhost:5000
5. Manually paste logs in the web interface

### Production Setup (Auto-Ingestion)

1. Create `.env` file from `.env.example`
2. Configure Jenkins credentials:
   ```bash
   JENKINS_URL=http://your-jenkins:8080
   JENKINS_USER=your-username
   JENKINS_TOKEN=your-api-token
   ```
3. Run: `python src/main/app.py`
4. App automatically polls Jenkins every 5 minutes

See [Jenkins Integration Guide](docs/jenkins-integration.md) for detailed setup.

### Using Docker

```bash
cd infrastructure/docker
docker-compose up --build
```

## Features

### Analyze Pipeline Logs

1. Enter pipeline name
2. Paste log content
3. Click "Analyze"
4. View categorized results with recommendations

### View Statistics

The dashboard displays:
- Failure distribution by category
- Severity levels
- Historical trends

### Recent Failures Table

Shows the last 10 pipeline failures with:
- Pipeline name
- Category
- Severity
- Timestamp

## API Usage

### Analyze Logs Programmatically

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "my-pipeline",
    "log_content": "BUILD FAILED: compilation error"
  }'
```

### Get Failure Statistics

```bash
curl http://localhost:5000/api/stats
```

## Troubleshooting

### Application won't start
- Check Python version (3.9+)
- Verify all dependencies installed
- Check port 5000 is available

### Database errors
- Delete `pipeline_analyzer.db` and restart
- Check file permissions

### Docker issues
- Ensure Docker is running
- Check port conflicts
- Rebuild image: `docker-compose build --no-cache`
