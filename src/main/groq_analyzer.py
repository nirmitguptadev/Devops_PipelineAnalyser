import os
from groq import Groq
import logging

logger = logging.getLogger(__name__)


_UNSET = object()


class GroqAnalyzer:
    def __init__(self, api_key: str = _UNSET):
        if api_key is _UNSET:
            api_key = os.getenv("GROQ_API_KEY")

        self.enabled = bool(api_key)

        if self.enabled:
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.1-8b-instant"
            logger.info("Groq AI analyzer initialized")
        else:
            logger.warning("Groq API key not found. AI analysis disabled.")

    def analyze_failure(
        self, log_content: str, category: str, error_lines: list
    ) -> dict:
        """Generate AI summary with troubleshooting steps"""

        if not self.enabled:
            return None

        try:
            prompt = f"""Analyze this CI/CD pipeline failure:

Category: {category}
Context lines from the log:
{log_content[-2500:]}

Error Lines (Filtered Highlights):
{chr(10).join(error_lines[:20])}

Provide:
1. Summary (2-3 sentences explaining exactly what went wrong and where).
2. Troubleshooting Steps (3-4 specific actionable steps. DO NOT provide generic advice like "check dependencies" or "review logs". State the exact file name, variable, conflicting version, or specific command to run).

Format:
SUMMARY: [your summary]
TROUBLESHOOTING:
- [step 1]
- [step 2]
- [step 3]
- [step 4]"""

            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior DevOps engineer and strict code reviewer. You specialize in pinpointing exact code and resolving CI/CD pipeline failures with actionable commands.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=600,
            )

            content = response.choices[0].message.content.strip()

            # Parse response
            summary = ""
            troubleshooting = []

            if "SUMMARY:" in content:
                parts = content.split("TROUBLESHOOTING:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    steps = parts[1].strip().split("\n")
                    troubleshooting = [
                        s.strip().lstrip("-").strip() for s in steps if s.strip()
                    ]
            else:
                summary = content

            logger.info(f"AI analysis completed for {category}")
            return {"summary": summary, "troubleshooting": troubleshooting}

        except Exception as e:
            logger.error(f"Groq AI analysis failed: {e}")
            return None

    def suggest_fixes(self, category: str, root_cause: str) -> list:
        """Generate AI-powered fix suggestions"""

        if not self.enabled:
            return []

        try:
            prompt = f"""Given this pipeline failure:
Category: {category}
Root Cause: {root_cause}

Provide 3 specific, actionable fix recommendations. Format as a numbered list."""

            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a DevOps expert providing fix recommendations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=200,
            )

            suggestions = response.choices[0].message.content.strip()
            # Parse numbered list into array
            fixes = [
                line.strip()
                for line in suggestions.split("\n")
                if line.strip() and line[0].isdigit()
            ]
            return fixes[:3]

        except Exception as e:
            logger.error(f"AI fix suggestions failed: {e}")
            return []
