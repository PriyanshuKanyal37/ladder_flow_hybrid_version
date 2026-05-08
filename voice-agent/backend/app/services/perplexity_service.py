import json
import requests
from typing import Any, Dict
from app.core.config import settings

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar"


def _extract_first_json_object(content: str) -> str:
    """Extract the first complete JSON object from a string, ignoring surrounding text/fences."""
    start = content.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", content, 0)

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(content)):
        char = content[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start: index + 1]

    raise json.JSONDecodeError("Unterminated JSON object", content, start)


def _string_list(value: Any, dict_key: str | None = None) -> list[str]:
    """Normalize a list field — accepts plain strings or dicts with a known key."""
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
        elif dict_key and isinstance(item, dict):
            text = item.get(dict_key)
            if isinstance(text, str) and text.strip():
                items.append(text.strip())
    return items


def _text_value(value: Any) -> str:
    """Recursively flatten dict/list deep_context into plain text."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [_text_value(item) for item in value]
        return "\n\n".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = [_text_value(item) for item in value.values()]
        return "\n\n".join(part for part in parts if part)
    return ""


def _parse_research_content(content: str, keyword: str) -> Dict[str, Any]:
    """Parse Perplexity response content into a normalized ResearchResult shape."""
    try:
        result_json = json.loads(_extract_first_json_object(content.strip()))
    except json.JSONDecodeError as exc:
        print(f"Perplexity JSON Parse Error: {exc}", flush=True)
        return {
            "title": f"Research on {keyword}",
            "deep_context": content,
            "key_insights": [],
            "contrarian_angles": [],
            "discussion_points": [],
            "sources": [],
        }

    if not isinstance(result_json, dict):
        return {
            "title": f"Research on {keyword}",
            "deep_context": content,
            "key_insights": [],
            "contrarian_angles": [],
            "discussion_points": [],
            "sources": [],
        }

    title = result_json.get("title")
    key_insights = _string_list(result_json.get("key_insights"), "insight")
    deep_context = _text_value(result_json.get("deep_context"))
    if not deep_context:
        deep_context = "\n\n".join(key_insights) or content
    contrarian_angles = result_json.get("contrarian_angles")

    return {
        "title": title.strip() if isinstance(title, str) and title.strip() else f"Research on {keyword}",
        "deep_context": deep_context,
        "key_insights": key_insights,
        "contrarian_angles": contrarian_angles if isinstance(contrarian_angles, list) else [],
        "discussion_points": _string_list(result_json.get("discussion_points"), "question"),
        "sources": _string_list(result_json.get("sources"), "source"),
    }


def research_topic(keyword: str) -> Dict[str, Any]:
    """Research a topic using Perplexity API and return a normalized result."""
    api_key = settings.PERPLEXITY_API_KEY
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY is not set in environment variables")

    from app.prompts.perplexity_prompt import PERPLEXITY_SYSTEM_PROMPT

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": PERPLEXITY_SYSTEM_PROMPT},
            {"role": "user", "content": f"Research this topic comprehensively: '{keyword}'"},
        ],
        "temperature": 0.7,
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return _parse_research_content(content, keyword)
    except requests.exceptions.RequestException as e:
        print(f"Perplexity API Request Error: {e}")
        raise
    except Exception as e:
        print(f"Error in research_topic: {e}")
        raise
