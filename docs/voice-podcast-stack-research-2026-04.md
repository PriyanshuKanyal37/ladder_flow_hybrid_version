# Human Podcast Voice Agent Stack Research

Research date: 2026-04-25

Goal: replace the current voice-interview pipeline with the best architecture for a 5 to 50 minute podcast that feels like a human host speaking with a human guest, asks live follow-up questions, and avoids a scripted AI-agent feel.

## Executive Recommendation

The best direction is not just "better TTS." The best direction is a podcast system where turn-taking, emotional delivery, and question selection are treated as core product logic.

Recommended default stack for LadderFlow:

```text
Browser client
-> LiveKit room
-> LiveKit Agents worker
-> Deepgram Flux or ElevenLabs Scribe v2 Realtime for speech-to-text and end-of-turn signals
-> Podcast Brain API using a strong reasoning LLM
-> dynamic question planner and conversation memory
-> ElevenLabs Eleven v3 Conversational through ElevenAgents if possible, or Cartesia Sonic 3 / ElevenLabs v3-style streaming TTS if staying fully custom
-> transcript persistence
-> memory extraction into Postgres and Neo4j
```

Best product choice:

Use a two-track proof of concept before deleting the current system:

1. ElevenAgents plus custom LLM endpoint for the best out-of-box human voice, emotional delivery, and turn-taking.
2. LiveKit custom pipeline with Deepgram Flux, a custom podcast brain, and high-end TTS for the best control and easiest integration with the existing LadderFlow app.

If I had to choose one stack for your current product, I would choose Track 2 first: LiveKit custom pipeline with Deepgram Flux, a strong LLM podcast brain, and expressive TTS. It gives you control over long-form interview logic, memory, transcripts, content extraction, and future testing. If ElevenAgents can integrate cleanly with your custom LLM and transcript/memory requirements, it may become the final best voice layer.

## Current Stack

The current backend is:

```text
LiveKit Agents
-> Deepgram nova-2 STT
-> OpenAI GPT-5 text LLM
-> ElevenLabs eleven_turbo_v2_5 TTS
-> Postgres + Neo4j after the session
```

This is technically valid, but it will often feel like "human to AI" because:

- `nova-2` is not the best current choice for voice-agent turn-taking.
- Plain TTS loses emotional and prosodic information from the guest's actual voice.
- The current voice prompt forces every response into 1 to 3 short sentences, which can feel support-agent-like instead of podcast-like.
- The agent asks from a prompt, but there is no explicit podcast director that chooses the next question based on emotional signal, story openings, contradictions, and conversation phase.
- Long sessions need rolling summaries and open-thread tracking, otherwise the agent repeats, pivots awkwardly, or forgets important points.

## What Actually Makes It Feel Human

The human feel comes from five things, in this order:

1. Turn timing: the host does not cut off the guest, but also does not leave dead air.
2. Interruptibility: the guest can interrupt naturally and the host stops gracefully.
3. Question quality: the host follows the most interesting live thread, not a fixed question list.
4. Emotional delivery: the voice sounds warm, curious, surprised, reflective, or serious at the right moment.
5. Long-form memory: the host remembers what was said 20 minutes ago and brings it back at the right time.

Voice quality alone is not enough. A beautiful voice with bad turn-taking still feels robotic.

## Stack Options

### Option A: ElevenAgents With Custom LLM

Pipeline:

```text
Browser
-> ElevenAgents conversation
-> ElevenLabs STT + turn-taking
-> custom LLM endpoint hosted by LadderFlow
-> Eleven v3 Conversational expressive voice
-> webhook/transcript/memory ingestion
```

Why it is strong:

- ElevenLabs Expressive Mode uses Eleven v3 Conversational and a new turn-taking system.
- The docs say Expressive Mode adapts tone, timing, and emotional delivery based on conversational context.
- The turn-taking system uses Scribe v2 Realtime signals, including emotional cues and speech patterns.
- It supports explicit expressive tags like `[laughs]`, `[whispers]`, `[sighs]`, `[slow]`, and `[excited]`.
- Custom LLM support means you can keep your own podcast brain instead of accepting generic agent logic.

Why it may be risky:

- It moves orchestration away from your current LiveKit worker.
- You need to verify exact webhook, transcript, session ownership, and memory extraction control.
- Eleven v3 Conversational does not currently preserve Professional Voice Clone characteristics well, according to ElevenLabs docs.
- If your whole product depends on custom long-session state, you need a careful integration test.

Best for:

Human voice quality, emotional delivery, and faster migration if ElevenAgents gives enough control.

Verdict:

This is the best "voice-first" option. I would test it seriously.

### Option B: LiveKit Custom Pipeline With Deepgram Flux And Expressive TTS

Pipeline:

```text
Browser
-> LiveKit room
-> LiveKit Agents worker
-> Deepgram Flux STT
-> LiveKit turn detector / adaptive interruption
-> Podcast Brain API
-> ElevenLabs or Cartesia streaming TTS
-> LadderFlow transcript and memory system
```

Why it is strong:

- Keeps your current frontend and backend shape.
- Deepgram Flux is specifically built for voice agents and end-of-turn detection.
- Flux supports `eot_threshold`, `eager_eot_threshold`, and `eot_timeout_ms`, which gives you real control over pacing.
- LiveKit has explicit turn handling, adaptive interruption handling, and turn detector plugins.
- You can implement a real podcast brain: topic phases, follow-up selection, rolling summary, open loops, and guest profile memory.
- You keep full ownership of transcripts, summaries, memory extraction, and content generation.

Why it may be risky:

- You still have a cascaded STT -> LLM -> TTS pipeline, so every hop adds latency.
- Emotional voice cues from the user's audio mostly become text unless you add emotion/prosody analysis.
- You must engineer cancellation, barge-in, and speculative generation carefully.

Best for:

Product control, custom long-form interview logic, and the least disruptive migration from the existing system.

Verdict:

This is the best engineering choice for LadderFlow if you want to own the podcast intelligence layer.

### Option C: OpenAI Realtime Speech-to-Speech

Pipeline:

```text
Browser or LiveKit
-> OpenAI Realtime API
-> gpt-realtime speech-to-speech
-> tool calls to LadderFlow backend
-> transcript and memory persistence
```

Why it is strong:

- OpenAI Realtime is native speech-to-speech, so it avoids separate STT and TTS hops.
- OpenAI docs say speech-to-speech gives the model more information about tone and inflection than text-only pipelines.
- It supports WebRTC, WebSocket, and SIP connection modes.
- It supports voice activity detection, semantic VAD, tools, and server-side controls.
- LiveKit officially supports OpenAI Realtime integrations.

Why it may be risky:

- You have less control over the voice identity compared with ElevenLabs or Cartesia.
- Some realtime model transcripts can arrive later than the response in realtime-model pipelines, which can complicate UI transcript synchronization.
- For a branded podcast product, voice quality and host identity may matter more than the lowest-latency path.

Best for:

Lowest architecture complexity for real-time speech reasoning and natural audio understanding.

Verdict:

Excellent technical option, but I would not choose it as the default if ElevenLabs-style host voice identity is central to the product.

### Option D: Hume EVI With Custom Language Model

Pipeline:

```text
Browser
-> Hume EVI
-> Hume prosody and turn detection
-> custom LadderFlow language model endpoint
-> Hume voice output
-> transcript, emotion data, and memory persistence
```

Why it is strong:

- Hume EVI is built around emotional intelligence and prosody.
- Hume docs describe measuring tone, rhythm, and timbre, then responding with empathic language and tone.
- EVI is always interruptible and uses vocal tone for end-of-turn detection.
- Custom language model support allows your own podcast brain to generate the text.

Why it may be risky:

- It is a larger platform change.
- Voice identity and output style may be less aligned with the ElevenLabs voices you already like.
- You need to verify long-session reliability, cost, and transcript/memory export in your exact use case.

Best for:

Emotion-sensitive interviews, coaching, therapy-like reflection, or products where emotional attunement is more important than brand voice.

Verdict:

Strong candidate for emotional intelligence. I would test it, but not make it the first production migration unless the demo clearly beats ElevenAgents.

### Option E: Vapi Or Retell As Orchestration Platform

Pipeline:

```text
Browser / phone
-> Vapi or Retell
-> provider-managed STT, LLM, TTS orchestration
-> custom LLM or tool endpoints
-> LadderFlow persistence
```

Why it is strong:

- Fastest to ship a working voice agent.
- Built-in orchestration, monitoring, fallbacks, and latency tools.
- Vapi explicitly presents the core voice pipeline as transcriber, model, and voice.
- Retell focuses on low-latency orchestration, reliability, fallbacks, and monitoring.

Why it may be risky:

- These platforms are more call-center and operations oriented than long-form creator podcast oriented.
- Deep product logic can become constrained by platform abstractions.
- You may still need to solve the hard part: dynamic podcast questioning and long-form memory.

Best for:

Phone call automation, sales calls, appointment agents, and production reliability with less custom infrastructure.

Verdict:

Useful benchmark, not my top recommendation for a creator podcast product.

## My Ranking

1. LiveKit custom pipeline with Deepgram Flux, Podcast Brain API, and expressive TTS.
2. ElevenAgents with custom LLM endpoint.
3. OpenAI Realtime speech-to-speech.
4. Hume EVI with custom language model.
5. Vapi or Retell orchestration.

Why I rank LiveKit custom first for LadderFlow:

- You already have LiveKit and session persistence.
- Your product value is not only voice. It is the interview, transcript, memory graph, and content generation.
- Long podcasts need custom state management more than generic agent flow.
- You can still use the best voice providers inside this architecture.

Why ElevenAgents might beat it after testing:

- If the user perception difference is huge, and ElevenAgents gives you enough custom LLM, transcript, and webhook control, the voice layer may be worth moving.

## Best Final Architecture

```text
Frontend
  - joins a LiveKit room or ElevenAgents session
  - shows live transcript, speaking/listening/thinking states
  - lets user pause, resume, end, and rate host quality

Voice Transport
  - LiveKit if keeping custom control
  - ElevenAgents session if prioritizing voice naturalness

Turn Layer
  - Deepgram Flux for end-of-turn if using LiveKit
  - ElevenLabs Scribe v2 Realtime turn-taking if using ElevenAgents
  - adaptive interruption handling
  - barge-in cancellation

Podcast Brain API
  - receives latest user turn, rolling summary, open threads, profile, and target duration
  - chooses the next conversational move
  - outputs a spoken host response plus metadata

Question Planner
  - decides whether to clarify, deepen, challenge, ask for a story, ask for proof, summarize, or pivot
  - never uses a static list as the main driver
  - uses pre-researched questions only as background, not script

Voice Output
  - Eleven v3 Conversational / Expressive Mode if using ElevenAgents
  - Cartesia Sonic 3 or ElevenLabs high-quality streaming TTS if staying custom

Session Memory
  - rolling summary every 3 to 5 minutes
  - open loops
  - contradiction list
  - strongest quotes
  - emotional moments
  - final transcript

Post Session
  - extract memories
  - update Postgres
  - update Neo4j graph
  - generate LinkedIn, Twitter, newsletter, podcast notes
```

## Podcast Brain Design

The brain should not simply answer the user. It should behave like a podcast producer and host combined.

Per turn, it should output:

```json
{
  "host_response": "Natural spoken response to say out loud.",
  "next_move": "deepen | clarify | challenge | story | proof | pivot | recap | close",
  "why_this_question": "Internal reason, not spoken.",
  "open_thread_updates": ["..."],
  "rolling_summary_update": "...",
  "risk_flags": ["repetition", "too_shallow", "user_fatigue"]
}
```

The spoken response should usually follow:

```text
micro-reaction -> specific reflection -> one strong question
```

Example:

```text
That's a sharp distinction. You're not saying AI should make people louder, you're saying it should make them clearer. What is one moment where you saw a founder use AI in a way that actually improved their thinking?
```

## Long Podcast Control

A 5 minute session and a 50 minute session need different pacing.

Recommended phases:

```text
0 to 5 min: warm-up and thesis discovery
5 to 15 min: stories, examples, and lived context
15 to 30 min: frameworks, contradictions, and specific proof
30 to 45 min: deeper beliefs, stakes, and implications
45 to 50 min: recap, strongest idea, final takeaway
```

The agent should not force all sessions to reach all phases. It should adapt based on target duration and user energy.

## Evaluation Plan

Do not choose based only on provider demos. Test your own use case.

Run the same 20-minute interview script across:

1. Current stack.
2. LiveKit + Deepgram Flux + upgraded podcast brain + current ElevenLabs.
3. LiveKit + Deepgram Flux + podcast brain + Cartesia Sonic 3.
4. ElevenAgents + custom LLM endpoint.
5. OpenAI Realtime.
6. Hume EVI.

Score each on:

- time from user speech end to first audio
- interruption behavior
- whether it waits during thoughtful pauses
- emotional warmth
- whether follow-up questions feel specific
- long-session coherence
- transcript quality
- total cost per 30 minute session
- integration control

Minimum acceptable target:

```text
P50 first audio after user turn: under 900 ms
P90 first audio after user turn: under 1800 ms
False interruption rate: under 5 percent
Question specificity score: 4 out of 5 or better
Repetition: no repeated question pattern within 15 minutes
```

## Migration Plan

Phase 1: Do not delete the current system yet.

- Add a new "podcast host mode" behind a feature flag.
- Keep current interview flow as fallback.
- Record timing metrics and user ratings.

Phase 2: Replace the weak points.

- Move from Deepgram `nova-2` to Flux or ElevenLabs Scribe v2 Realtime.
- Add explicit turn handling and interruption policy.
- Replace the current short support-agent voice prompt.
- Add dynamic question planner and rolling summary.

Phase 3: Test final voice layer.

- Test ElevenAgents with custom LLM.
- Test LiveKit with expressive TTS.
- Test OpenAI Realtime if lowest latency matters more than voice identity.

Phase 4: Make the production cut.

- Choose one primary stack.
- Keep one fallback voice provider.
- Keep detailed metrics from every session.

## Decision

My current best recommendation:

```text
Primary build:
LiveKit + Deepgram Flux + custom Podcast Brain API + ElevenLabs/Cartesia expressive TTS

Parallel test:
ElevenAgents + custom LLM endpoint

Fallback:
OpenAI Realtime for lowest-complexity native speech-to-speech
```

The real differentiator is the Podcast Brain API. Without that, any provider will still feel like an AI asking generic questions.

## Sources

- [ElevenLabs Expressive Mode](https://elevenlabs.io/docs/agents-platform/customization/voice/expressive-mode)
- [ElevenLabs Agents Platform overview](https://elevenlabs.io/docs/conversational-ai/docs/agent-setup)
- [ElevenLabs Conversation Flow](https://elevenlabs.io/docs/conversational-ai/customization/conversation-flow)
- [ElevenLabs Custom LLM](https://elevenlabs.io/docs/agents-platform/customization/llm/custom-llm)
- [LiveKit Turns overview](https://docs.livekit.io/agents/build/turns/)
- [LiveKit Realtime models overview](https://docs.livekit.io/agents/models/realtime/)
- [LiveKit Deepgram STT](https://docs.livekit.io/agents/models/stt/deepgram)
- [LiveKit ElevenLabs TTS](https://docs.livekit.io/agents/models/tts/elevenlabs)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime/voice-design)
- [OpenAI Realtime conversations](https://platform.openai.com/docs/guides/realtime-model-capabilities)
- [OpenAI Realtime transcription and VAD](https://platform.openai.com/docs/guides/realtime-transcription)
- [Deepgram Flux voice agent guide](https://developers.deepgram.com/docs/flux/agent)
- [Deepgram Flux end-of-turn configuration](https://developers.deepgram.com/docs/flux/configuration)
- [Deepgram eager end-of-turn](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot)
- [Cartesia Sonic 3](https://docs.cartesia.ai/build-with-cartesia/models/tts)
- [Cartesia WebSocket continuations](https://docs.cartesia.ai/build-with-cartesia/capability-guides/stream-inputs-using-continuations)
- [Hume EVI overview](https://dev.hume.ai/docs/empathic-voice-interface-evi/overview)
- [Hume EVI turn detection](https://dev.hume.ai/docs/speech-to-speech-evi/configuration/turn-detection)
- [Hume custom language model](https://dev.hume.ai/docs/empathic-voice-interface-evi/guides/custom-language-model)
- [Vapi core models](https://docs.vapi.ai/quickstart)
- [Vapi voice pipeline configuration](https://docs.vapi.ai/customization/voice-pipeline-configuration)
- [Retell orchestration overview](https://docs.retellai.com/general/orchestration_overview)
- [Retell reliability overview](https://docs.retellai.com/reliability/reliability-overview)
