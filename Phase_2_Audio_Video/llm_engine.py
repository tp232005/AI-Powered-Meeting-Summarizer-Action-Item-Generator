"""
Ollama LLM Engine for enhanced meeting analysis.
Communicates with local Ollama instance via REST API.
Gracefully falls back to None if Ollama is unavailable.
"""
import json
import requests
import config


class OllamaEngine:
    """Interface to Ollama LLM for enhanced meeting analysis."""

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL
        self.generate_url = f"{self.base_url}/api/generate"

    # ── Connection Check ──

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m.get("name", "") for m in r.json().get("models", [])]
                return any(self.model in m for m in models)
            return False
        except Exception:
            return False

    def list_models(self) -> list:
        """List available Ollama models."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    # ── Core Generation ──

    def _generate(self, prompt: str, system: str = "", temperature: float = 0.3) -> str | None:
        """Send prompt to Ollama and return response text."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 2048},
            }
            r = requests.post(self.generate_url, json=payload, timeout=config.OLLAMA_TIMEOUT)
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception:
            pass
        return None

    # ── Enhanced Summary ──

    def generate_summary(self, transcript: str, style: str = "concise") -> str | None:
        """Generate an LLM-enhanced summary of the meeting transcript."""
        style_instructions = {
            "concise": "Write a concise 2-3 sentence summary of this meeting.",
            "detailed": "Write a detailed summary of this meeting covering all key points in 5-7 sentences.",
            "executive": "Write an executive-style summary suitable for sending to leadership. Focus on decisions, outcomes, and next steps.",
        }
        system = (
            "You are MeetMind, an expert meeting analyst. "
            "Produce clear, professional meeting summaries. "
            "Focus on decisions, action items, and key outcomes."
        )
        prompt = f"{style_instructions.get(style, style_instructions['concise'])}\n\nMeeting Transcript:\n{transcript}"
        return self._generate(prompt, system)

    def translate_text(self, text: str, output_language: str) -> str | None:
        """Translate generated output while retaining the original transcript."""
        if not text or output_language == "English":
            return text
        prompt = (
            f"Translate the following meeting output into {output_language}. "
            "Preserve names, dates, task meaning, and bullet structure. Return only the translation.\n\n"
            f"{text}"
        )
        return self._generate(prompt, "You are a precise professional meeting translator.", temperature=0.1)

    # ── Enhanced Decision Extraction ──

    def extract_decisions(self, transcript: str) -> list | None:
        """Use LLM to extract decisions from the meeting."""
        system = "You are an expert meeting analyst. Extract only firm decisions from meetings."
        prompt = (
            "Extract all firm decisions made in this meeting. "
            "Return each decision as a separate line starting with '- '. "
            "Only include actual decisions, not discussions or suggestions.\n\n"
            f"Meeting Transcript:\n{transcript}"
        )
        result = self._generate(prompt, system)
        if result:
            decisions = [line.strip().lstrip("- ").strip() for line in result.split("\n") if line.strip().startswith("-")]
            return [d for d in decisions if len(d) > 10]
        return None

    # ── Enhanced Task Extraction ──

    def extract_tasks(self, transcript: str) -> list | None:
        """Use LLM to extract tasks with structured information."""
        system = "You are an expert meeting analyst. Extract action items from meetings."
        prompt = (
            "Extract all action items/tasks from this meeting. "
            "For each task, provide a JSON object with these fields:\n"
            '- "task": the task description\n'
            '- "assignee": who is responsible (use "Team" if unclear)\n'
            '- "deadline": when it\'s due (use "Not specified" if unclear)\n'
            '- "priority": "high", "medium", or "low"\n\n'
            "Return ONLY a JSON array of objects, no other text.\n\n"
            f"Meeting Transcript:\n{transcript}"
        )
        result = self._generate(prompt, system, temperature=0.1)
        if result:
            try:
                # Try to parse JSON from the response
                json_match = result
                if "```" in result:
                    json_match = result.split("```")[1]
                    if json_match.startswith("json"):
                        json_match = json_match[4:]
                tasks = json.loads(json_match.strip())
                if isinstance(tasks, list):
                    return [
                        {
                            "task": t.get("task", ""),
                            "assignee": t.get("assignee", "Team"),
                            "deadline": t.get("deadline", "Not specified"),
                            "priority": t.get("priority", "low"),
                            "status": "pending",
                        }
                        for t in tasks
                        if t.get("task")
                    ]
            except (json.JSONDecodeError, IndexError):
                pass
        return None

    # ── Risk Analysis ──

    def analyze_risks(self, transcript: str) -> list | None:
        """Use LLM to identify risks from the meeting discussion."""
        system = "You are a risk analyst reviewing meeting transcripts."
        prompt = (
            "Identify all risks, concerns, and potential issues raised in this meeting. "
            "For each risk, provide a JSON object with these fields:\n"
            '- "description": the risk description\n'
            '- "severity": "high", "medium", or "low"\n'
            '- "mitigation": any suggested mitigation discussed\n\n'
            "Return ONLY a JSON array of objects, no other text.\n\n"
            f"Meeting Transcript:\n{transcript}"
        )
        result = self._generate(prompt, system, temperature=0.2)
        if result:
            try:
                json_match = result
                if "```" in result:
                    json_match = result.split("```")[1]
                    if json_match.startswith("json"):
                        json_match = json_match[4:]
                risks = json.loads(json_match.strip())
                if isinstance(risks, list):
                    return [
                        {
                            "description": r.get("description", ""),
                            "severity": r.get("severity", "low"),
                            "mitigation": r.get("mitigation", "Not discussed"),
                            "keywords": [],
                        }
                        for r in risks
                        if r.get("description")
                    ]
            except (json.JSONDecodeError, IndexError):
                pass
        return None

    # ── Generate Report Email ──

    def generate_email_report(self, analysis: dict, title: str) -> str | None:
        """Generate a professional email report from the analysis."""
        summary = analysis.get("short_summary", "")
        decisions = analysis.get("decisions", [])
        tasks = analysis.get("tasks", [])

        system = "You are a professional executive assistant drafting meeting follow-up emails."
        prompt = (
            f"Write a professional follow-up email for the meeting '{title}'.\n\n"
            f"Summary: {summary}\n\n"
            f"Decisions made:\n" + "\n".join(f"- {d}" for d in decisions[:10]) + "\n\n"
            f"Action items:\n" + "\n".join(
                f"- {t['task']} (Assignee: {t['assignee']}, Deadline: {t['deadline']})"
                for t in tasks[:10]
            ) + "\n\n"
            "Write a concise, professional email that includes:\n"
            "1. Brief greeting\n"
            "2. Meeting summary paragraph\n"
            "3. Key decisions list\n"
            "4. Action items with owners and deadlines\n"
            "5. Closing line\n"
            "Use a professional but friendly tone."
        )
        return self._generate(prompt, system, temperature=0.4)
