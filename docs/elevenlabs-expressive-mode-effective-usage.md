# ElevenLabs Expressive Mode: Effective Usage (Low Cost)

Date: 2026-04-27

## 1) Direct answer

- Can you use ElevenLabs Expressive Mode? Yes.
- Can you use full Expressive Mode inside your current custom LiveKit pipeline as-is? No.
- Why: full Expressive Mode is part of ElevenLabs Agents runtime (ElevenAgents + Eleven v3 Conversational + their turn system).

## 2) Best architecture for your requirement

Use dual-mode routing:

1. Standard mode (default, low cost):
   - LiveKit + Deepgram + LadderFlow brain + ElevenLabs Turbo/Flash TTS
2. Expressive mode (premium, highest human feel):
   - ElevenAgents + Expressive Mode + your custom LLM endpoint

This gives high quality when needed, but keeps average cost low.

## 3) When to route to Expressive mode

Route only these sessions:

1. Paid/premium users
2. Demos and high-value calls
3. Emotional or storytelling sessions
4. Sessions where user explicitly selects "Expressive"

Keep all other sessions in Standard mode.

## 4) Cost guardrails (critical)

Apply all guardrails:

1. Hard max duration (example: 20-25 min for Expressive)
2. Auto-end after inactivity/silence window
3. Disable burst unless you truly need it
4. Use cheaper LLM tier in ElevenAgents when acceptable
5. Cap concurrent Expressive sessions
6. Add monthly Expressive minute quota per user/team

## 5) Product behavior improvements (required in both modes)

Voice quality alone is not enough. To avoid robotic feel:

1. Remove strict short-response policy for podcast turns
2. Increase tiny output cap so host can acknowledge + bridge + ask follow-up
3. Add dynamic follow-up planner (no static list progression)
4. Add rolling memory/open-thread tracking every few minutes

## 6) Minimal implementation plan

### Phase A: Add mode switch

1. Add `voiceMode` in request:
   - `standard`
   - `expressive`
2. Save selected mode in interview metadata.

### Phase B: Backend routing

1. If `voiceMode=standard`:
   - Use existing `/agent-config` + `/agent-dispatch` (LiveKit path)
2. If `voiceMode=expressive`:
   - New route: `/agent-config/elevenlabs`
   - Return ElevenAgents session config to frontend

### Phase C: Frontend connect logic

1. If Standard: use current LiveKit hook
2. If Expressive: start ElevenAgents session client
3. Keep transcript/autosave/finalize flow same for both paths

## 7) Pricing expectation (practical)

- Expressive mode is premium quality, premium cost.
- Standard mode is your cost-efficient default.
- Goal is not "make expressive cheap"; goal is "use expressive only where ROI is high."

## 8) Decision rule

Use this:

1. If highest realism is required and user/value justifies cost -> Expressive
2. Otherwise -> Standard

Default should remain Standard.

## 9) Success metrics

Track weekly:

1. Cost per 30-min session by mode
2. P50/P90 first audio latency
3. User rating ("felt human")
4. Repeat-question rate in 15 min
5. Expressive usage rate vs conversion/retention

If Expressive quality lift is real and business ROI is positive, increase routing share gradually.

