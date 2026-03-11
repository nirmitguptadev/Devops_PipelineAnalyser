import json
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict:
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                return {}
        return {}

    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_jenkins_config(self) -> Optional[Dict]:
        """Get Jenkins configuration"""
        return self.settings.get("jenkins")

    def set_jenkins_config(
        self, url: str, user: str, token: str, poll_interval: int = 300
    ):
        """Save Jenkins configuration"""
        self.settings["jenkins"] = {
            "url": url,
            "user": user,
            "token": token,
            "poll_interval": poll_interval,
            "enabled": True,
        }
        self._save_settings()

    def disable_jenkins(self):
        """Disable Jenkins integration"""
        if "jenkins" in self.settings:
            self.settings["jenkins"]["enabled"] = False
            self._save_settings()

    def get_github_config(self) -> Optional[Dict]:
        """Get GitHub configuration"""
        return self.settings.get("github")

    def set_github_config(self, token: str, owner: str = None, repo: str = None):
        """Save GitHub configuration"""
        self.settings["github"] = {
            "token": token,
            "owner": owner,
            "repo": repo,
            "enabled": True,
        }
        self._save_settings()

    def disable_github(self):
        """Disable GitHub integration"""
        if "github" in self.settings:
            self.settings["github"]["enabled"] = False
            self._save_settings()

    def get_all_settings(self) -> Dict:
        """Get all settings (without sensitive data)"""
        safe_settings = {}

        if "jenkins" in self.settings:
            safe_settings["jenkins"] = {
                "url": self.settings["jenkins"].get("url"),
                "user": self.settings["jenkins"].get("user"),
                "poll_interval": self.settings["jenkins"].get("poll_interval"),
                "enabled": self.settings["jenkins"].get("enabled", False),
            }

        if "github" in self.settings:
            safe_settings["github"] = {
                "owner": self.settings["github"].get("owner"),
                "repo": self.settings["github"].get("repo"),
                "enabled": self.settings["github"].get("enabled", False),
            }

        return safe_settings
