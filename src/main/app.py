from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from analyzer import PipelineAnalyzer
from database import Database
from webhook_handler import WebhookHandler
from ingestion_scheduler import IngestionScheduler
from github_scheduler import GithubScheduler
from groq_analyzer import GroqAnalyzer
from settings_manager import SettingsManager

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
analyzer = PipelineAnalyzer()
groq_analyzer = GroqAnalyzer()
webhook_handler = WebhookHandler(os.getenv("WEBHOOK_SECRET"))
settings_manager = SettingsManager()

# Initialize Jenkins polling from settings or env
scheduler = None
jenkins_config = settings_manager.get_jenkins_config()
if jenkins_config and jenkins_config.get("enabled"):
    scheduler = IngestionScheduler(
        jenkins_url=jenkins_config["url"],
        username=jenkins_config["user"],
        api_token=jenkins_config["token"],
        poll_interval=jenkins_config.get("poll_interval") or 10,
        groq_analyzer=groq_analyzer,
    )
    scheduler.start()
    logger.info("Jenkins auto-ingestion enabled from settings")
else:
    logger.info("Jenkins integration not configured. Use Settings page to configure.")

# Initialize GitHub polling from settings
github_scheduler = None
github_config = settings_manager.get_github_config()
if github_config and github_config.get("enabled"):
    github_scheduler = GithubScheduler(
        token=github_config["token"],
        owner=github_config.get("owner"),
        repo=github_config.get("repo"),
        poll_interval=10,
        groq_analyzer=groq_analyzer,
    )
    github_scheduler.start()
    logger.info("GitHub auto-ingestion enabled from settings")
else:
    logger.info("GitHub integration not configured.")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(settings_manager.get_all_settings())


@app.route("/api/settings/jenkins", methods=["POST"])
def save_jenkins_settings():
    data = request.json
    try:
        settings_manager.set_jenkins_config(
            url=data["url"],
            user=data["user"],
            token=data["token"],
            poll_interval=data.get("poll_interval") or 300,
        )

        # Restart scheduler with new settings
        global scheduler
        if scheduler:
            scheduler.stop()

        scheduler = IngestionScheduler(
            jenkins_url=data["url"],
            username=data["user"],
            api_token=data["token"],
            poll_interval=data.get("poll_interval") or 10,
            groq_analyzer=groq_analyzer,
        )
        scheduler.start()

        return jsonify({"success": True, "message": "Jenkins integration enabled"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/settings/jenkins", methods=["DELETE"])
def disable_jenkins_settings():
    settings_manager.disable_jenkins()
    global scheduler
    if scheduler:
        scheduler.stop()
        scheduler = None
    return jsonify({"success": True})


@app.route("/api/settings/jenkins/test", methods=["POST"])
def test_jenkins_connection():
    data = request.json
    try:
        from jenkins_integration import JenkinsIntegration

        jenkins = JenkinsIntegration(data["url"], data["user"], data["token"])
        jobs = jenkins.get_all_jobs()

        if jobs:
            return jsonify({"success": True, "jobs_count": len(jobs)})
        else:
            return jsonify(
                {"success": False, "error": "Could not fetch jobs. Check credentials."}
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/settings/jenkins/status", methods=["GET"])
def jenkins_status():
    config = settings_manager.get_jenkins_config()
    if config and config.get("enabled"):
        return jsonify({"connected": True, "message": "Active"})
    return jsonify({"connected": False, "message": "Not configured"})


@app.route("/api/settings/github", methods=["POST"])
def save_github_settings():
    data = request.json
    try:
        settings_manager.set_github_config(
            token=data["token"], owner=data.get("owner"), repo=data.get("repo")
        )

        # Restart github scheduler with new settings
        global github_scheduler
        if github_scheduler:
            github_scheduler.stop()

        github_scheduler = GithubScheduler(
            token=data["token"],
            owner=data.get("owner"),
            repo=data.get("repo"),
            poll_interval=10,
            groq_analyzer=groq_analyzer,
        )
        github_scheduler.start()

        return jsonify({"success": True, "message": "GitHub integration enabled"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/settings/github", methods=["DELETE"])
def disable_github_settings():
    settings_manager.disable_github()
    global github_scheduler
    if github_scheduler:
        github_scheduler.stop()
        github_scheduler = None
    return jsonify({"success": True})


@app.route("/api/settings/github/test", methods=["POST"])
def test_github_connection():
    data = request.json
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {data['token']}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )
        response.raise_for_status()
        user_data = response.json()
        return jsonify({"success": True, "username": user_data["login"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/settings/github/status", methods=["GET"])
def github_status():
    config = settings_manager.get_github_config()
    if config and config.get("enabled"):
        return jsonify({"connected": True, "message": "Active"})
    return jsonify({"connected": False, "message": "Not configured"})


@app.route("/api/settings/groq/status", methods=["GET"])
def groq_status():
    # Always show as enabled since it's a built-in feature
    if groq_analyzer.enabled:
        return jsonify({"connected": True, "message": "Active"})
    return jsonify({"connected": False, "message": "Configured by admin"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze_pipeline():
    data = request.json
    log_content = data.get("log_content", "")
    pipeline_name = data.get("pipeline_name", "unknown")
    ci_platform = data.get("ci_platform", "jenkins")
    use_ai = data.get("use_ai", False)

    result = analyzer.analyze(log_content, pipeline_name)
    result["ci_platform"] = ci_platform

    # Add AI insights if enabled
    if use_ai and groq_analyzer.enabled:
        ai_insights = groq_analyzer.analyze_failure(
            log_content, result["category"], result["error_lines"]
        )
        if ai_insights:
            result["ai_insights"] = ai_insights.get("summary", "")
            result["troubleshooting"] = ai_insights.get("troubleshooting", [])

    db.save_analysis(result)

    return jsonify(result)


@app.route("/api/failures/latest-id", methods=["GET"])
def get_latest_failure_id():
    return jsonify({"latest_id": db.get_latest_failure_id()})


@app.route("/api/failures", methods=["GET"])
def get_failures():
    limit = request.args.get("limit", 50, type=int)
    after = request.args.get("after", 0, type=int)
    failures = db.get_recent_failures(limit, after_id=after)
    return jsonify(failures)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    stats = db.get_statistics()
    return jsonify(stats)


@app.route("/api/webhook/jenkins", methods=["POST"])
def jenkins_webhook():
    """Receive Jenkins webhook notifications"""
    data = request.json

    build_info = webhook_handler.parse_jenkins_webhook(data)
    if not build_info:
        return jsonify({"status": "ignored"}), 200

    # Fetch console log from Jenkins
    from jenkins_integration import JenkinsIntegration

    jenkins = JenkinsIntegration(
        os.getenv("JENKINS_URL"), os.getenv("JENKINS_USER"), os.getenv("JENKINS_TOKEN")
    )

    console_log = jenkins.get_build_console_log(
        build_info["pipeline_name"], build_info["build_number"]
    )

    if console_log:
        pipeline_name = f"{build_info['pipeline_name']}#{build_info['build_number']}"

        # Abort if scheduler already handled this build while jenkins triggered the webhook
        if db.is_build_analyzed(
            build_info["pipeline_name"], build_info["build_number"]
        ):
            return jsonify({"status": "ignored_already_analyzed"}), 200

        result = analyzer.analyze(console_log, pipeline_name)
        result["build_number"] = build_info["build_number"]
        result["jenkins_status"] = build_info["status"]
        result["ci_platform"] = "jenkins"

        # Add AI insights if enabled
        if groq_analyzer.enabled:
            ai_insights = groq_analyzer.analyze_failure(
                console_log, result["category"], result["error_lines"]
            )
            if ai_insights:
                result["ai_insights"] = ai_insights.get("summary", "")
                result["troubleshooting"] = ai_insights.get("troubleshooting", [])

        db.save_analysis(result)
        logger.info(f"Webhook processed: {pipeline_name}")
        return jsonify({"status": "analyzed", "category": result["category"]})

    return jsonify({"status": "error", "message": "Could not fetch console log"}), 500


@app.route("/api/webhook/github", methods=["POST"])
def github_webhook():
    """Receive GitHub Actions webhook notifications"""
    data = request.json

    build_info = webhook_handler.parse_github_actions_webhook(data)
    if not build_info:
        return jsonify({"status": "ignored"}), 200

    # For GitHub, we'd need to fetch logs via GitHub API
    # Simplified version - just log the event
    logger.info(f"GitHub webhook received: {build_info['pipeline_name']}")
    return jsonify({"status": "received"})


@app.route("/api/webhook/gitlab", methods=["POST"])
def gitlab_webhook():
    """Receive GitLab CI webhook notifications"""
    data = request.json

    build_info = webhook_handler.parse_gitlab_webhook(data)
    if not build_info:
        return jsonify({"status": "ignored"}), 200

    logger.info(f"GitLab webhook received: {build_info['pipeline_name']}")
    return jsonify({"status": "received"})


@app.route("/api/poll/trigger", methods=["POST"])
def trigger_poll():
    """Manually trigger Jenkins & GitHub polling"""
    triggered = False
    if scheduler:
        scheduler.poll_now()
        triggered = True
    if github_scheduler:
        github_scheduler.poll_now()
        triggered = True

    if not triggered:
        return jsonify({"error": "No integrations configured"}), 400

    return jsonify({"status": "polling triggered"})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "jenkins_integration": scheduler is not None,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
