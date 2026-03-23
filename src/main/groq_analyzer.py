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
            prompt = f"""A CI/CD pipeline build failed. Identify the exact mistake in the build commands or scripts.

Failure category: {category}

Key error lines (most important — read these first):
{chr(10).join(error_lines[:20])}

Full log (last 2500 chars):
{log_content[-2500:]}

Rules:
- If you see a typo, extra space, wrong path, or bad syntax in a command or script name, say that directly.
- Do NOT say "check the path" or "verify the directory" — say exactly what is wrong and what to change it to.
- CORE PROBLEM must be one sentence naming the specific command, file, or line that is broken and why.
- HOW TO FIX steps must be direct edits or commands, not general advice.

Format:
CORE PROBLEM: [one sentence — name the exact broken thing]
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
                temperature=0.1,
                max_tokens=400,
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
