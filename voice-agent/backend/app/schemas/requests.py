from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional

_ALLOWED_TTS_PROVIDERS = {"elevenlabs", "cartesia", "inworld", "deepgram"}


class TopicRequest(BaseModel):
    topic_title: Optional[str] = None
    topic: Optional[str] = None  # simple string fallback from frontend
    global_context: Optional[str] = ""
    why_this_matters: Optional[str] = ""
    key_questions: list[str] = Field(default_factory=list)
    user_name: Optional[str] = "Guest"
    userName: Optional[str] = None  # support camelCase from frontend
    tts_provider: str = "elevenlabs"

    @field_validator("tts_provider", mode="before")
    @classmethod
    def validate_tts_provider(cls, v: Any) -> str:
        if v not in _ALLOWED_TTS_PROVIDERS:
            raise ValueError(f"tts_provider must be one of {_ALLOWED_TTS_PROVIDERS}")
        return v

    @field_validator("global_context", mode="before")
    @classmethod
    def coerce_list_to_str(cls, v: Any) -> Any:
        if isinstance(v, list):
            return "\n\n".join(str(item) for item in v if item)
        return v

    @field_validator("key_questions", mode="before")
    @classmethod
    def coerce_key_questions(cls, v: Any) -> Any:
        if not isinstance(v, list):
            return []
        items: list[str] = []
        for item in v:
            if isinstance(item, str) and item.strip():
                items.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("question") or item.get("text") or item.get("content") or ""
                if isinstance(text, str) and text.strip():
                    items.append(text.strip())
        return items

    def get_topic_title(self) -> str:
        return self.topic_title or self.topic or "General Discussion"

    def get_user_name(self) -> str:
        return self.userName or self.user_name or "Guest"


class AgentDispatchRequest(BaseModel):
    interview_id: str


class ExtractRequest(BaseModel):
    interview_id: str
    transcript: str
    topic: Optional[str] = "General Discussion"


class LinkedInRequest(BaseModel):
    topic: str
    userName: Optional[str] = "Guest"
    transcript: str

class TwitterRequest(BaseModel):
    topic: str
    userName: Optional[str] = "Guest"
    transcript: str

# NewsletterRequest removed — newsletter generation feature retired.

class ResearchRequest(BaseModel):
    keyword: str
