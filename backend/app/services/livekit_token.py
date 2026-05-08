"""
LiveKit room token generator.

Generates a signed JWT that the frontend uses to join a LiveKit room.
The system_prompt is stored in the room's metadata so the agent worker can
read it when it enters the room — no extra API calls needed.
"""
import json
import uuid
from livekit import api
from app.core.config import settings


def create_room_token(
    room_name: str,
    participant_identity: str,
    participant_name: str,
    system_prompt: str,
    topic_title: str,
    user_name: str,
    interview_id: str,
) -> str:
    """
    Create a signed JWT for a participant to join a LiveKit room.

    Room metadata carries the system_prompt + context so the agent worker
    picks it up automatically without any HTTP calls.
    """
    # Embed all agent context in the room metadata (agent reads this on join)
    room_metadata = json.dumps({
        "system_prompt": system_prompt,
        "topic_title": topic_title,
        "user_name": user_name,
        "interview_id": interview_id,
    })

    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(participant_identity)
        .with_name(participant_name)
        .with_metadata(room_metadata)          # participant metadata
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )
    return token


def generate_room_name(user_id: str, topic_title: str) -> str:
    """Generate a unique, human-readable room name for the session."""
    slug = topic_title.lower().replace(" ", "-")[:30]
    short_id = str(uuid.uuid4())[:8]
    return f"ladder-{slug}-{short_id}"
