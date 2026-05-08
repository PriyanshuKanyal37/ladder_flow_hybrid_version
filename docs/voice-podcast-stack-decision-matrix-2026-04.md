# Voice Podcast Stack Decision Matrix

Research date: 2026-04-25

## Recommended Shortlist

| Rank | Stack | Best For | Main Risk | Decision |
|---:|---|---|---|---|
| 1 | LiveKit + Deepgram Flux + Podcast Brain + expressive TTS | Best product control and long-form podcast logic | More engineering work | Build first |
| 2 | ElevenAgents + custom LLM endpoint | Best human voice and emotional delivery | Platform control must be verified | Run parallel POC |
| 3 | OpenAI Realtime | Native speech-to-speech and low pipeline complexity | Less branded voice control | Keep as fallback / benchmark |
| 4 | Hume EVI + custom language model | Emotional intelligence and prosody | Larger platform shift | Test if emotional coaching matters |
| 5 | Vapi / Retell | Production call-agent orchestration | Less ideal for creator podcast UX | Not first choice |

## Final Choice For LadderFlow

Use this as the main rebuild path:

```text
LiveKit
-> Deepgram Flux
-> LiveKit turn handling
-> Podcast Brain API
-> ElevenLabs or Cartesia expressive TTS
-> Postgres transcript
-> Neo4j memory graph
```

Run this as the competing POC:

```text
ElevenAgents
-> Eleven v3 Conversational / Expressive Mode
-> custom LadderFlow LLM endpoint
-> transcript and webhook ingestion
-> Postgres + Neo4j memory graph
```

## Why This Is Better Than Current Stack

Current stack:

```text
Deepgram nova-2
-> GPT-5
-> ElevenLabs eleven_turbo_v2_5
```

Better stack:

```text
turn-aware STT
-> dynamic podcast brain
-> expressive voice
-> rolling long-form memory
```

The current system is a voice interview agent. The target system should be a real-time podcast host.

## What To Optimize First

1. Turn-taking: replace `nova-2` with Flux or use ElevenAgents turn-taking.
2. Question planning: add a planner that chooses the next question from the live answer.
3. Prompt style: remove the hard `1-3 short sentences maximum` rule for podcast mode.
4. Memory: maintain rolling summaries and open threads every 3 to 5 minutes.
5. Voice: use Eleven v3 Conversational / Expressive Mode or another TTS with real emotional controls.

## Provider Notes

ElevenLabs:

- Best candidate for emotional host voice.
- Expressive Mode is strongest when using ElevenAgents with Eleven v3 Conversational.
- Custom LLM support is the key requirement for LadderFlow.

Deepgram Flux:

- Best STT upgrade for a custom LiveKit pipeline.
- Built for voice agents and end-of-turn detection.
- Supports eager end-of-turn for lower latency.

LiveKit:

- Best transport/orchestration base for keeping your current product architecture.
- Supports turn handling, realtime models, and provider plugins.

OpenAI Realtime:

- Best native speech-to-speech option.
- Useful benchmark for latency and audio understanding.
- Less ideal if your host voice needs to be ElevenLabs-quality or branded.

Cartesia Sonic 3:

- Strong TTS candidate for a custom pipeline.
- WebSocket continuations help preserve prosody when streaming text from an LLM.
- Good if you want TTS control without moving orchestration to ElevenAgents.

Hume EVI:

- Strongest emotional/prosody concept.
- Worth testing for interviews where emotional sensitivity is central.

Vapi / Retell:

- Good for production phone agents.
- Not the best first choice for a custom long-form podcast product.

## Required Podcast Brain Behavior

The podcast host should never just ask the next item from a list.

Every turn should decide:

- Did the guest say something vague that needs clarification?
- Did they mention a story opening?
- Did they make a strong claim that needs proof?
- Did they reveal a contradiction?
- Did their tone suggest excitement, discomfort, uncertainty, or conviction?
- Is the session early, middle, or closing?
- What is the one question a human host would ask next?

## Production Acceptance Criteria

Use these before choosing the final stack:

| Metric | Target |
|---|---:|
| P50 first audio after user turn | under 900 ms |
| P90 first audio after user turn | under 1800 ms |
| False interruption rate | under 5 percent |
| Repeated question pattern | none within 15 minutes |
| Transcript quality | usable without heavy cleanup |
| Long-session coherence | remembers earlier themes after 30 minutes |
| User perception | "felt like a human host" from test users |

## Best Next Step

Build two thin POCs against the same 20-minute test interview:

1. LiveKit + Deepgram Flux + Podcast Brain + expressive TTS.
2. ElevenAgents + custom LLM endpoint.

Do not choose based on provider demos. Choose based on recorded LadderFlow conversations, because your actual win condition is dynamic questioning plus human-feeling delivery.
