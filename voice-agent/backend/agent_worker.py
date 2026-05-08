"""
LadderFlow Voice Agent - LiveKit Worker

Run:
    python agent_worker.py dev
    python agent_worker.py start
"""

import asyncio
import json
import logging
import os
import uuid

import httpx
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession, room_io
from livekit.plugins import anthropic, cartesia, deepgram, elevenlabs, inworld, silero

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from app.core.config import settings  # noqa: E402

logger = logging.getLogger("ladderflow.agent")
logging.basicConfig(level=logging.INFO)


def prewarm(proc: JobProcess):
    """Load VAD once per worker process."""
    logger.info("Prewarming Silero VAD...")
    proc.userdata["vad"] = silero.VAD.load(
        min_silence_duration=1.0,
        min_speech_duration=0.2,
        activation_threshold=0.55,
        deactivation_threshold=0.35,
        prefix_padding_duration=0.3,
    )
    logger.info("Silero VAD ready.")


def _extract_metadata(ctx: JobContext) -> dict:
    """Pull context from dispatch → room → participant metadata."""
    if ctx.job.metadata:
        try:
            data = json.loads(ctx.job.metadata)
            if data:
                return data
        except json.JSONDecodeError:
            pass

    if ctx.room.metadata:
        try:
            data = json.loads(ctx.room.metadata)
            if data:
                return data
        except json.JSONDecodeError:
            pass

    for participant in ctx.room.remote_participants.values():
        if participant.metadata:
            try:
                data = json.loads(participant.metadata)
                if data:
                    return data
            except json.JSONDecodeError:
                continue

    return {}


def _build_instructions(system_prompt: str, topic_title: str, user_name: str) -> str:
    return system_prompt.strip() + f"""

[SESSION CONTEXT]
Guest name: {user_name}
Topic: {topic_title}

[VOICE DELIVERY RULES - CRITICAL]
- This is spoken audio via TTS. NEVER use markdown, bullets, dashes, or numbered lists.
- Keep every turn to 1-3 short sentences maximum. You are speaking, not writing.
- Use natural spoken language: contractions, casual phrasing.
- Vary sentence length. Keep it warm and curious.
"""


def _msg_text(msg: object) -> str:
    """Safely extract plain text from a ChatMessage.content field."""
    c = getattr(msg, "content", None)
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for item in c:
            if isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return " ".join(parts)
    return str(c)


async def _notify_interview_ended(interview_id: str) -> None:
    if not interview_id or not settings.INTERNAL_SECRET:
        return
    backend_base = os.getenv("BACKEND_INTERNAL_URL", "http://127.0.0.1:8000")
    url = f"{backend_base}/internal/interviews/{interview_id}/mark-ended"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                headers={"X-Internal-Secret": settings.INTERNAL_SECRET},
            )
        if resp.status_code != 200:
            logger.warning("mark-ended returned %s for interview %s", resp.status_code, interview_id)
    except Exception as exc:
        logger.warning("mark-ended call failed for interview %s: %s", interview_id, exc)


def _build_tts(provider: str):
    """
    Each provider tuned for maximum natural expressiveness for podcast-host
    persona. Voice IDs / models chosen for warm, empathetic baritone delivery.
    """
    if provider == "cartesia":
        # Sonic 3.5 — emotional expressiveness is BAKED into the model. The
        # explicit emotion/speed controls only worked on the older sonic-2
        # experimental API. For sonic-3+ we just pass voice + float speed.
        # 1.0 = normal pace; voice ID is the warm baritone host preset.
        return cartesia.TTS(
            model="sonic-3.5",
            voice="86e30c1d-714b-4074-a1f2-1cb6b552fb49",
            speed=1.0,
        )
    elif provider == "inworld":
        # Inworld TTS-2 — temperature is THE expressiveness knob.
        # 0.7 default → 1.1 pushes more emotional variation per sentence
        # without becoming chaotic. Voice "Evan" = warm host persona.
        return inworld.TTS(
            model="inworld-tts-2",
            voice="Evan",
            temperature=1.1,
            speaking_rate=1.0,
        )
    elif provider == "deepgram":
        # Aura-2 has no emotion knob — character is baked into the model.
        # Pluto voice is masculine, smooth, calm, empathetic baritone.
        return deepgram.TTS(model="aura-2-pluto-en")
    else:
        # ElevenLabs Flash v2.5 — stability lowered + style raised for
        # expressiveness. similarity_boost stays high so voice character
        # doesn't drift. speaker_boost on for clarity.
        return elevenlabs.TTS(
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
            api_key=settings.ELEVENLABS_API_KEY,
            enable_ssml_parsing=False,
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.30,          # was 0.45 — lower = more emotional variation
                similarity_boost=0.85,   # keep voice character locked
                style=0.65,              # was 0.40 — higher = more expressive style transfer
                use_speaker_boost=True,
            ),
        )


async def entrypoint(ctx: JobContext):
    logger.info("Agent joining room: %s", ctx.room.name)
    await ctx.connect()

    # Wait up to 60 s for the user to join before giving up on a stale dispatch.
    waited = 0
    while not ctx.room.remote_participants and waited < 60:
        await asyncio.sleep(1)
        waited += 1

    if not ctx.room.remote_participants:
        logger.warning("Room %s has no participants after 60 s. Exiting stale dispatch.", ctx.room.name)
        return

    metadata = _extract_metadata(ctx)
    system_prompt = metadata.get("system_prompt", "")
    topic_title = metadata.get("topic_title", "today's topic")
    user_name = metadata.get("user_name", "there")
    interview_id = metadata.get("interview_id", "")
    greeting = metadata.get("greeting") or (
        f"Hey {user_name}! Really glad you made it. "
        f"We are talking about {topic_title} today. "
        "Before we get into it, how are you doing?"
    )

    if not system_prompt:
        logger.warning("No system_prompt in metadata. Using fallback prompt.")
        system_prompt = (
            "You are a warm, incisive podcast host for LadderFlow. "
            "Ask one specific, thoughtful question at a time. "
            "Keep responses short because this is spoken audio."
        )

    instructions = _build_instructions(system_prompt, topic_title, user_name)
    vad = ctx.proc.userdata["vad"]

    stt_plugin = deepgram.STT(
        api_key=settings.DEEPGRAM_API_KEY or os.getenv("VITE_DEEPGRAM_API_KEY", ""),
        model="nova-2",
        language="en-US",
        smart_format=True,
        punctuate=True,
    )

    llm_plugin = anthropic.LLM(
        model="claude-sonnet-4-6",
        temperature=0.85,
        max_tokens=300,
        caching="ephemeral",
    )

    tts_provider_key = metadata.get("tts_provider", "elevenlabs")
    tts_plugin = _build_tts(tts_provider_key)

    # AgentSession owns the pipeline runtime; Agent owns instructions + settings.
    session = AgentSession(
        vad=vad,
        stt=stt_plugin,
        llm=llm_plugin,
        tts=tts_plugin,
        turn_handling={
            "endpointing": {"min_delay": 1.0},
            "interruption": {"enabled": True},
        },
    )

    agent = Agent(
        instructions=instructions,
        chat_ctx=llm.ChatContext(),
    )

    session_ended = asyncio.Event()

    async def _publish(payload: dict) -> None:
        try:
            if ctx.room.remote_participants:
                await ctx.room.local_participant.publish_data(
                    json.dumps(payload).encode(),
                    reliable=True,
                )
        except Exception as exc:
            logger.warning("publish_data failed: %s", exc)

    def _id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"

    @session.on("conversation_item_added")
    def on_conversation_item(ev) -> None:
        msg = ev.item
        text = _msg_text(msg)
        if not text:
            return
        if msg.role == "user":
            logger.info("[USER] %s", text)
            asyncio.create_task(_publish({"type": "transcript", "id": _id("u"), "role": "user", "text": text, "final": True}))
            asyncio.create_task(_publish({"type": "agent_state", "state": "thinking"}))
        elif msg.role == "assistant":
            logger.info("[AGENT] %s", text)
            asyncio.create_task(_publish({"type": "transcript", "id": _id("a"), "role": "assistant", "text": text, "final": True}))
            asyncio.create_task(_publish({"type": "agent_state", "state": "listening"}))

    @session.on("agent_state_changed")
    def on_agent_state(ev) -> None:
        _STATE_MAP = {"listening": "listening", "thinking": "thinking", "speaking": "speaking", "idle": "idle"}
        if mapped := _STATE_MAP.get(ev.new_state):
            asyncio.create_task(_publish({"type": "agent_state", "state": mapped}))

    @session.on("close")
    def on_session_close(ev) -> None:
        logger.info("Session closed: %s", ev.reason)
        session_ended.set()

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant) -> None:
        logger.info("Participant %s disconnected from room %s", participant.identity, ctx.room.name)
        session_ended.set()

    participant = list(ctx.room.remote_participants.values())[0]

    try:
        await session.start(
            agent,
            room=ctx.room,
            room_options=room_io.RoomOptions(participant_identity=participant.identity),
        )
        logger.info("AgentSession started OK")
    except Exception as exc:
        logger.error("session.start() failed: %s", exc, exc_info=True)
        return

    try:
        await _publish({"type": "agent_state", "state": "speaking"})
        logger.info("Sending greeting (%d chars)", len(greeting))
        session.say(greeting, allow_interruptions=True)
        await _publish({"type": "transcript", "id": _id("g"), "role": "assistant", "text": greeting, "final": True})
        await _publish({"type": "agent_state", "state": "listening"})
    except Exception as exc:
        logger.error("session.say() failed: %s", exc, exc_info=True)

    try:
        await session_ended.wait()
    except asyncio.CancelledError:
        pass

    logger.info("Room %s ended. interview_id=%s", ctx.room.name, interview_id or "unknown")

    if interview_id:
        await _notify_interview_ended(interview_id)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="ladderflow-host",
        )
    )
