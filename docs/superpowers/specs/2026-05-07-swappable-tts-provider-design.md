# Swappable TTS Provider + Claude LLM — Design Spec

**Date:** 2026-05-07
**Scope:** Per-interview TTS provider selection + swap LLM from GPT-4o to Claude Sonnet 4.6
**Status:** Approved for implementation

---

## Problem

LadderFlow's voice pipeline hardcodes ElevenLabs as TTS and GPT-4o as LLM in `agent_worker.py`. Users cannot choose their TTS provider. GPT-4o should be replaced with Claude Sonnet 4.6 across the board.

---

## Goals

1. Add TTS provider dropdown to interview setup page (4 options, per-interview, default ElevenLabs)
2. Switch LLM from `openai.LLM(model="gpt-4o")` → `anthropic.LLM(model="claude-sonnet-4-6")`

---

## Supported TTS Providers

All 4 providers support real-time streaming natively via their livekit plugins.

| Key | Dropdown Label | Plugin | Model ID | TTFB | Cost/1K chars | Quality ELO |
|---|---|---|---|---|---|---|
| `elevenlabs` | ElevenLabs Flash v2.5 | `livekit.plugins.elevenlabs` | `eleven_turbo_v2_5` | ~75ms | $0.050 | 1,179 (2nd) |
| `cartesia` | Cartesia Sonic 3.5 | `livekit.plugins.cartesia` | `sonic-3.5` | ~90ms | ~$0.038 | 1,054 |
| `inworld` | Inworld TTS-2 | `livekit.plugins.inworld` | `inworld-tts-2` | <200ms | $0.025 | 1,236 (#1) |
| `deepgram` | Deepgram Aura-2 | `livekit.plugins.deepgram` | `aura-2-asteria-en` | ~90ms | $0.030 | Mid |

Default: `elevenlabs`

---

## LLM Change

Replace `openai.LLM(model="gpt-4o")` with `anthropic.LLM(model="claude-sonnet-4-6")`.

- Plugin: `livekit-agents[anthropic]` → `livekit.plugins.anthropic.LLM`
- `ANTHROPIC_API_KEY` already set in `.env`
- `max_completion_tokens=200` and `temperature=0.85` carry over as equivalent params

---

## Architecture

### Data Flow (TTS selection)

```
[Setup Page /interview/new]
  └─ dropdown: tts_provider = "cartesia"
       │
       ▼
[POST /agent-config]  (TopicRequest body)
  └─ tts_provider stored in dispatch_metadata JSON blob
       │
       ▼
[POST /agent-dispatch]
  └─ dispatch_metadata sent as LiveKit job metadata (unchanged)
       │
       ▼
[agent_worker.py — entrypoint()]
  └─ metadata["tts_provider"] → _build_tts() → correct streaming plugin
```

No new tables. No new endpoints. `dispatch_metadata` is already a freeform JSON blob.

---

## File Changes

### 1. `voice-agent/backend/app/schemas/requests.py`

Add to `TopicRequest`:

```python
tts_provider: str = "elevenlabs"
```

Validate against allowed set: `{"elevenlabs", "cartesia", "inworld", "deepgram"}`. Reject unknown values with HTTP 400.

### 2. `voice-agent/backend/app/api/routes_audio.py`

In `/agent-config`, add to `dispatch_metadata`:

```python
"tts_provider": req.tts_provider,
```

In `/agent-config/resume`, preserve from prior metadata:

```python
tts_provider = prior_metadata.get("tts_provider", "elevenlabs")
# include in new dispatch_metadata
```

### 3. `voice-agent/backend/agent_worker.py`

**LLM change** — replace:
```python
# before
from livekit.plugins import openai
llm_plugin = openai.LLM(model="gpt-4o", temperature=0.85, max_completion_tokens=200)

# after
from livekit.plugins import anthropic
llm_plugin = anthropic.LLM(model="claude-sonnet-4-6", temperature=0.85, max_tokens=200)
```

**TTS factory** — replace hardcoded ElevenLabs block with:

```python
def _build_tts(provider: str):
    if provider == "cartesia":
        from livekit.plugins import cartesia
        return cartesia.TTS(model="sonic-3.5")
    elif provider == "inworld":
        from livekit.plugins import inworld
        return inworld.TTS(model="inworld-tts-2")
    elif provider == "deepgram":
        from livekit.plugins import deepgram
        return deepgram.TTS(model="aura-2-asteria-en")
    else:  # elevenlabs default
        from livekit.plugins import elevenlabs
        return elevenlabs.TTS(
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
            api_key=settings.ELEVENLABS_API_KEY,
            enable_ssml_parsing=False,
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.45,
                similarity_boost=0.85,
                style=0.40,
                use_speaker_boost=True,
            ),
        )
```

Call site:
```python
tts_provider_key = metadata.get("tts_provider", "elevenlabs")
tts_plugin = _build_tts(tts_provider_key)
```

### 4. `voice-agent/backend/requirements.txt`

Add:
```
livekit-agents[cartesia]~=1.5
livekit-agents[inworld]~=1.5
livekit-agents[anthropic]~=1.5
```

Deepgram and ElevenLabs already installed.

### 5. `voice-agent/backend/.env`

Add when ready:
```
CARTESIA_API_KEY=<key>
INWORLD_API_KEY=<key>
```

`ANTHROPIC_API_KEY` already present.

### 6. `frontend/app/(dashboard)/interview/new/page.tsx`

Add `ttsProvider` state (`useState<string>("elevenlabs")`). Add dropdown below guest name field. Pass `tts_provider` in the `generateAgentConfig` call body.

Dropdown order:
```
ElevenLabs Flash v2.5   → "elevenlabs"
Cartesia Sonic 3.5      → "cartesia"
Inworld TTS-2           → "inworld"
Deepgram Aura-2         → "deepgram"
```

### 7. `frontend/lib/api/agent.ts`

Add `tts_provider: string` to `generateAgentConfig` request body.

---

## Error Handling

- Unknown `tts_provider` → HTTP 400
- Missing API key for selected provider → agent worker catches `Exception`, logs warning, falls back to ElevenLabs
- Package not installed → `ImportError` caught, falls back to ElevenLabs

---

## Resume Sessions

`/agent-config/resume` reads `tts_provider` from original `dispatch_metadata`. Missing = defaults to `"elevenlabs"`. No breakage for legacy records.

---

## Out of Scope

- STT provider swapping
- Mid-session provider switching
- Voice ID selection per provider
- User-level TTS preference persistence

---

## Success Criteria

1. Dropdown on setup page, 4 options, defaults to ElevenLabs
2. Selected provider flows end-to-end to agent worker without errors
3. All 4 providers produce real-time streaming audio in the interview room
4. Claude Sonnet 4.6 replaces GPT-4o as LLM with no behavior regression
5. Transcript capture, autosave, memory extraction unaffected
6. Resume sessions don't break on missing `tts_provider` in old records
