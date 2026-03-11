# Jenkins Integration Setup Guide

## Overview

The Pipeline Failure Analyzer supports two methods of ingestion:

1. **Automatic Polling**: Periodically fetches failed builds from Jenkins
2. **Webhooks**: Real-time notifications when builds fail

## Method 1: Automatic Polling (Recommended)

### Step 1: Generate Jenkins API Token

1. Log into Jenkins
2. Click your username (top right) → Configure
3. Under "API Token", click "Add new Token"
4. Copy the generated token

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
JENKINS_URL=http://your-jenkins-server:8080
JENKINS_USER=your-username
JENKINS_TOKEN=your-api-token-here
POLL_INTERVAL=300  # Poll every 5 minutes
```

### Step 3: Start the Application

```bash
python src/main/app.py
```

The app will automatically:
- Poll Jenkins every 5 minutes (configurable)
- Fetch failed builds from all jobs
- Analyze console logs
- Store results in database
- Display on dashboard

### Step 4: Verify It's Working

Check the console logs:
```
INFO:__main__:Jenkins auto-ingestion enabled
INFO:ingestion_scheduler:Started Jenkins polling every 300 seconds
INFO:ingestion_scheduler:Starting Jenkins poll...
INFO:ingestion_scheduler:Found 3 failed builds in my-project
INFO:ingestion_scheduler:Analyzed and saved: my-project#123 - build_failure
```

## Method 2: Webhooks (Real-time)

### Step 1: Install Jenkins Notification Plugin

1. Go to Jenkins → Manage Jenkins → Manage Plugins
2. Install "Notification Plugin" or "Generic Webhook Trigger Plugin"

### Step 2: Configure Webhook in Jenkins Job

For each job you want to monitor:

1. Go to Job → Configure
2. Add Post-build Action → "Notification Endpoint"
3. Set URL: `http://your-app-server:5000/api/webhook/jenkins`
4. Format: JSON
5. Event: Job Completed

### Step 3: Test Webhook

Trigger a build that fails, then check your app logs:
```
INFO:__main__:Webhook processed: my-project#124
```

## Supported CI/CD Systems

### Jenkins
- Endpoint: `/api/webhook/jenkins`
- Fully supported with console log fetching

### GitHub Actions
- Endpoint: `/api/webhook/github`
- Configure in: Repository → Settings → Webhooks
- Events: Workflow runs

### GitLab CI
- Endpoint: `/api/webhook/gitlab`
- Configure in: Project → Settings → Webhooks
- Trigger: Pipeline events

## Manual Trigger

You can manually trigger a poll via API:

```bash
curl -X POST http://localhost:5000/api/poll/trigger
```

## Troubleshooting

### "Jenkins integration not configured"
- Check `.env` file exists
- Verify JENKINS_URL, JENKINS_USER, JENKINS_TOKEN are set
- Restart the application

### "Failed to fetch builds"
- Verify Jenkins URL is accessible
- Check API token is valid
- Ensure user has read permissions on jobs

### No builds appearing
- Check Jenkins jobs have failed builds
- Verify poll interval (default 5 minutes)
- Check application logs for errors

## Security Best Practices

1. **Use API Tokens**: Never use passwords
2. **Restrict Permissions**: Jenkins user only needs read access
3. **Secure Webhooks**: Set WEBHOOK_SECRET in .env
4. **HTTPS**: Use HTTPS in production
5. **Firewall**: Restrict webhook endpoint access

## Performance Tuning

```bash
# Poll more frequently (2 minutes)
POLL_INTERVAL=120

# Poll less frequently (10 minutes)
POLL_INTERVAL=600
```

Adjust based on:
- Number of Jenkins jobs
- Build frequency
- Server resources
