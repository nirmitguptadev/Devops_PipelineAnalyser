from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from analyzer import PipelineAnalyzer
from database import Database
from webhook_handler import WebhookHandler
from ingestion_scheduler import IngestionScheduler

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
analyzer = PipelineAnalyzer()
webhook_handler = WebhookHandler(os.getenv('WEBHOOK_SECRET'))

# Initialize Jenkins polling if configured
scheduler = None
if os.getenv('JENKINS_URL') and os.getenv('JENKINS_USER') and os.getenv('JENKINS_TOKEN'):
    scheduler = IngestionScheduler(
        jenkins_url=os.getenv('JENKINS_URL'),
        username=os.getenv('JENKINS_USER'),
        api_token=os.getenv('JENKINS_TOKEN'),
        poll_interval=int(os.getenv('POLL_INTERVAL', 300))
    )
    scheduler.start()
    logger.info("Jenkins auto-ingestion enabled")
else:
    logger.warning("Jenkins integration not configured. Set JENKINS_URL, JENKINS_USER, JENKINS_TOKEN")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_pipeline():
    data = request.json
    log_content = data.get('log_content', '')
    pipeline_name = data.get('pipeline_name', 'unknown')
    
    result = analyzer.analyze(log_content, pipeline_name)
    db.save_analysis(result)
    
    return jsonify(result)

@app.route('/api/failures', methods=['GET'])
def get_failures():
    limit = request.args.get('limit', 50, type=int)
    failures = db.get_recent_failures(limit)
    return jsonify(failures)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = db.get_statistics()
    return jsonify(stats)

@app.route('/api/webhook/jenkins', methods=['POST'])
def jenkins_webhook():
    """Receive Jenkins webhook notifications"""
    data = request.json
    
    build_info = webhook_handler.parse_jenkins_webhook(data)
    if not build_info:
        return jsonify({'status': 'ignored'}), 200
    
    # Fetch console log from Jenkins
    from jenkins_integration import JenkinsIntegration
    jenkins = JenkinsIntegration(
        os.getenv('JENKINS_URL'),
        os.getenv('JENKINS_USER'),
        os.getenv('JENKINS_TOKEN')
    )
    
    console_log = jenkins.get_build_console_log(
        build_info['pipeline_name'],
        build_info['build_number']
    )
    
    if console_log:
        pipeline_name = f"{build_info['pipeline_name']}#{build_info['build_number']}"
        result = analyzer.analyze(console_log, pipeline_name)
        result['build_number'] = build_info['build_number']
        result['jenkins_status'] = build_info['status']
        db.save_analysis(result)
        logger.info(f"Webhook processed: {pipeline_name}")
        return jsonify({'status': 'analyzed', 'category': result['category']})
    
    return jsonify({'status': 'error', 'message': 'Could not fetch console log'}), 500

@app.route('/api/webhook/github', methods=['POST'])
def github_webhook():
    """Receive GitHub Actions webhook notifications"""
    data = request.json
    
    build_info = webhook_handler.parse_github_actions_webhook(data)
    if not build_info:
        return jsonify({'status': 'ignored'}), 200
    
    # For GitHub, we'd need to fetch logs via GitHub API
    # Simplified version - just log the event
    logger.info(f"GitHub webhook received: {build_info['pipeline_name']}")
    return jsonify({'status': 'received'})

@app.route('/api/webhook/gitlab', methods=['POST'])
def gitlab_webhook():
    """Receive GitLab CI webhook notifications"""
    data = request.json
    
    build_info = webhook_handler.parse_gitlab_webhook(data)
    if not build_info:
        return jsonify({'status': 'ignored'}), 200
    
    logger.info(f"GitLab webhook received: {build_info['pipeline_name']}")
    return jsonify({'status': 'received'})

@app.route('/api/poll/trigger', methods=['POST'])
def trigger_poll():
    """Manually trigger Jenkins polling"""
    if not scheduler:
        return jsonify({'error': 'Jenkins integration not configured'}), 400
    
    scheduler.poll_now()
    return jsonify({'status': 'polling triggered'})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'jenkins_integration': scheduler is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
