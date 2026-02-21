from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)


# ==============================
# RULEBOOK LOADING
# ==============================

@lru_cache(maxsize=1)
def load_rulebook() -> dict:
    rulebook_path = Path(__file__).resolve().parent / "rulebook.yml"
    if not rulebook_path.exists():
        raise FileNotFoundError(f"rulebook.yml not found at: {rulebook_path}")

    with rulebook_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ==============================
# RULE-BASED LOGIC
# ==============================

def _contains_p1_override(text: str, rulebook: dict) -> bool:
    t = text.lower()
    phrases = rulebook.get("overrides", {}).get("p1_phrases", []) or []
    return any(str(phrase).lower() in t for phrase in phrases)


def _route_team_rule_based(title: str, description: str, rulebook: dict) -> str:
    text = f"{title}\n{description}".lower()

    routing = rulebook.get("routing", {})
    rules: Dict[str, List[str]] = routing.get("rules", {}) or {}
    team_order = routing.get("teams", []) or list(rules.keys())

    for team in team_order:
        keywords = rules.get(team, []) or []
        if any(str(k).lower() in text for k in keywords):
            return str(team)

    return "Application Support"


def _severity_rule_based(title: str, description: str, rulebook: dict) -> Tuple[str, float, str]:
    text = f"{title}\n{description}".lower()

    if _contains_p1_override(text, rulebook):
        return "P1", 0.99, "Critical override phrase detected."

    signals = rulebook.get("severity", {}).get("signals", {}) or {}

    for sev in ["P1", "P2", "P3", "P4"]:
        keywords = signals.get(sev, []) or []
        if any(str(k).lower() in text for k in keywords):
            return sev, 0.75, f"Detected {sev} severity keywords."

    return "P3", 0.55, "Defaulted to P3 due to weak signals."


def _fix_suggestions_rule_based(team: str, severity: str, rulebook: dict) -> List[str]:
    fixes = rulebook.get("fixes", {}) or {}
    base = fixes.get("base", []) or []
    by_team = fixes.get("by_team", {}) or {}
    p1_addendum = fixes.get("p1_addendum", []) or []

    steps = base + by_team.get(team, [])
    if severity == "P1":
        steps += p1_addendum

    return [str(s) for s in steps][:5]


# ==============================
# SAFE JSON EXTRACTION
# ==============================

def _extract_json_object(text: str) -> dict:
    text = text.strip()

    # Remove markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"```[a-zA-Z]*", "", text)
        text = text.replace("```", "").strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output:\n{text}")

    return json.loads(match.group(0))


def _normalize_fixes(fixes: List[str]) -> List[str]:
    out: List[str] = []
    for f in fixes:
        if f is None:
            continue
        s = str(f).strip()
        # remove leading numbering like "1)" or "1." or "-"
        s = re.sub(r"^\s*(?:[-*]|\d+\)|\d+\.)\s+", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            continue
        if s not in out:
            out.append(s)
    return out


def _refine_fixes(ai_fixes: List[str], team: str, severity: str, rulebook: dict) -> List[str]:
    """Refine AI fixes using the rulebook as guardrails.

    - Normalize formatting and dedupe
    - Ensure 3-5 steps
    - Fill gaps with rulebook base/team defaults
    - Append P1 addendum when severity is P1
    """
    fixes_cfg = rulebook.get("fixes", {}) or {}
    base = [str(s) for s in (fixes_cfg.get("base", []) or [])]
    by_team: Dict[str, List[str]] = fixes_cfg.get("by_team", {}) or {}
    team_defaults = [str(s) for s in (by_team.get(team, []) or [])]
    p1_addendum = [str(s) for s in (fixes_cfg.get("p1_addendum", []) or [])]

    refined = _normalize_fixes(ai_fixes)

    # Ensure minimum quality/quantity
    if len(refined) < 3:
        refined = _normalize_fixes(refined + base + team_defaults)

    if severity == "P1":
        refined = _normalize_fixes(refined + p1_addendum)

    refined = refined[:5]
    if len(refined) < 3:
        refined = _normalize_fixes(base + team_defaults + refined)[:5]

    return refined


# ==============================
# MAIN TRIAGE FUNCTION
# ==============================

def triage_ticket(title: str, description: str) -> dict:
    rulebook = load_rulebook()
    text = f"{title}\n{description}"

    # --- Hard override ---
    if _contains_p1_override(text, rulebook):
        team = _route_team_rule_based(title, description, rulebook)
        return {
            "severity": "P1",
            "confidence": 0.99,
            "reasoning": "Rule-based critical override triggered.",
            "triage_source": "rulebook_override",
            "assigned_team": team,
            "suggested_fixes": _fix_suggestions_rule_based(team, "P1", rulebook),
        }

    # --- If no API key, fallback immediately ---
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        team = _route_team_rule_based(title, description, rulebook)
        severity, confidence, reasoning = _severity_rule_based(title, description, rulebook)
        return {
            "severity": severity,
            "confidence": confidence,
            "reasoning": reasoning,
            "triage_source": "rulebook_no_api_key",
            "assigned_team": team,
            "suggested_fixes": _fix_suggestions_rule_based(team, severity, rulebook),
        }

    # --- AI TRIAGE ---
    try:
        from google import genai  # type: ignore

        team = _route_team_rule_based(title, description, rulebook)
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an enterprise IT incident triage agent.

Return STRICT JSON ONLY (no markdown, no extra keys) in this schema:
{{
  "severity": "P1|P2|P3|P4",
  "confidence": 0.0,
  "reasoning": "short explanation",
  "suggested_fixes": ["step 1", "step 2", "step 3"]
}}

Constraints:
- If the text indicates production down/system outage/data breach/security incident => severity must be P1.
- confidence must be a float between 0 and 1.
- reasoning must be <= 25 words.
- suggested_fixes must contain 3 to 5 short actionable steps.
- suggested_fixes must be relevant to the assigned team: {team}

Ticket:
Title: {title}
Description: {description}
""".strip()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw = (response.text or "").strip()
        parsed = _extract_json_object(raw)

        severity = str(parsed.get("severity", "P3"))
        confidence = float(parsed.get("confidence", 0.6))
        reasoning = str(parsed.get("reasoning", "AI triage result."))
        ai_fixes = parsed.get("suggested_fixes", []) or []
        if not isinstance(ai_fixes, list):
            ai_fixes = []

        if severity not in {"P1", "P2", "P3", "P4"}:
            severity = "P3"
        confidence = max(0.0, min(1.0, confidence))

        # Rulebook refinement layer
        suggested_fixes = _refine_fixes([str(x) for x in ai_fixes], team, severity, rulebook)

        return {
            "severity": severity,
            "confidence": confidence,
            "reasoning": reasoning,
            "triage_source": "gemini",
            "assigned_team": team,
            "suggested_fixes": suggested_fixes,
        }

    except Exception as e:
        # Optional: log error here
        print("AI TRIAGE ERROR:", str(e))

        team = _route_team_rule_based(title, description, rulebook)
        severity, confidence, reasoning = _severity_rule_based(title, description, rulebook)

        return {
            "severity": severity,
            "confidence": confidence,
            "reasoning": reasoning,
            "assigned_team": team,
            "suggested_fixes": _fix_suggestions_rule_based(team, severity, rulebook),
        }