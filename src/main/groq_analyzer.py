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
Log (last 2500 chars):
{log_content[-2500:]}

Key Error Lines:
{chr(10).join(error_lines[:20])}

Explain this to a developer in plain, simple language:
1. CORE PROBLEM: One sentence — what exactly broke and why (e.g. "A required package is missing" or "A test is comparing the wrong value"). No jargon.
2. HOW TO FIX: 2-3 simple steps to resolve it. Each step should be a direct action (e.g. "Run pip install X", "Change line Y in file Z"). Avoid vague advice.

Format:
CORE PROBLEM: [one sentence]
HOW TO FIX:
- [step 1]
- [step 2]
- [step 3]"""

            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that explains CI/CD pipeline failures in simple, plain language that any developer can understand. Avoid technical jargon. Focus on what broke and the simplest way to fix it.",
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

            if "CORE PROBLEM:" in content:
                parts = content.split("HOW TO FIX:")
                summary = parts[0].replace("CORE PROBLEM:", "").strip()
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
