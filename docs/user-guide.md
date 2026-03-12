# User Guide

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/nirmitguptadev/Devops_PipelineAnalyser.git
cd Devops_PipelineAnalyser

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main/app.py
```

### 2. Access the Application

Open your browser and go to: **http://localhost:5000**

## Features

### Manual Log Analysis

1. **Navigate to the main dashboard**
2. **Paste your pipeline logs** in the text area
3. **Enter pipeline name** (optional)
4. **Select CI platform** (Jenkins/GitHub Actions)
5. **Enable AI analysis** for enhanced insights
6. **Click "Analyze"** to get results

**Results include:**
- Failure category (Build, Test, Deployment, Infrastructure)
- Root cause analysis
- Specific error lines
- Actionable recommendations
- AI-powered troubleshooting tips (if enabled)

### Auto-Ingestion Setup

#### Jenkins Integration
1. Go to **Settings** page
2. Enter Jenkins details:
   - Jenkins URL (e.g., http://localhost:8080)
   - Username
   - API Token
   - Poll interval (minutes)
3. Click **Test Connection**
4. Click **Save** to enable auto-polling

#### GitHub Integration
1. Go to **Settings** page
2. Enter GitHub details:
   - Personal Access Token
   - Owner/Organization (optional)
   - Repository (optional)
3. Click **Test Connection**
4. Click **Save** to enable auto-polling

### Dashboard Features

- **Recent Failures Table**: Last 10 pipeline failures
- **Statistics Charts**: Failure distribution by category and severity
- **Integration Status**: Shows Jenkins/GitHub connection status
- **Manual Polling**: Trigger immediate polling of configured systems

## Docker Deployment

### Using Docker Compose

```bash
cd infrastructure/docker
docker-compose up --build
```

**Access:**
- Application: http://localhost:5000
- All data persists in Docker volumes

## API Usage

### Analyze Logs Programmatically

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "my-pipeline",
    "log_content": "BUILD FAILED: compilation error",
    "ci_platform": "jenkins",
    "use_ai": true
  }'
```

### Get Statistics

```bash
curl http://localhost:5000/api/stats
```

### Get Recent Failures

```bash
curl http://localhost:5000/api/failures?limit=5
```

## Configuration

### Environment Variables (.env file)

```bash
# Jenkins Integration (Optional)
JENKINS_URL=http://your-jenkins:8080
JENKINS_USER=your-username
JENKINS_TOKEN=your-api-token

# GitHub Integration (Optional)
GITHUB_TOKEN=your-github-personal-access-token

# Groq AI Analysis (Optional)
GROQ_API_KEY=your-groq-api-key

# Application Settings
SECRET_KEY=your-secret-key
WEBHOOK_SECRET=your-webhook-secret
```

### Webhook Setup

#### Jenkins Webhook
1. Install "Generic Webhook Trigger" plugin
2. Configure webhook URL: `http://your-app:5000/api/webhook/jenkins`
3. Set trigger on build completion

#### GitHub Webhook
1. Go to repository Settings → Webhooks
2. Add webhook URL: `http://your-app:5000/api/webhook/github`
3. Select "Workflow runs" events

## Troubleshooting

### Application Issues

**Port 5000 already in use:**
```bash
# Kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Dependencies not found:**
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

**Database errors:**
```bash
# Reset database
rm pipeline_analyzer.db
python src/main/app.py
```

### Integration Issues

**Jenkins connection failed:**
- Verify Jenkins URL is accessible
- Check username/API token
- Ensure Jenkins API is enabled

**GitHub connection failed:**
- Verify Personal Access Token has correct permissions
- Check token expiration
- Ensure repository access

### Docker Issues

**Container won't start:**
```bash
# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

**Port conflicts:**
```bash
# Change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs in the console
3. Check Docker logs: `docker-compose logs`
