# Five-Minute Judge Demo Script

## Before entering the room

- Start the application locally.
- Verify the login works.
- Run the mid-call scenario once and reset it.
- Keep your own consented genuine and cloned samples offline if you plan to demonstrate upload inference.
- Keep a screen recording and this script offline.
- Do not claim any unverified percentage.

## 0:00 to 0:25 - Problem

Say:

> A cloned executive voice can sound convincing enough to trigger a payment, password reset, or policy exception. Detection alone is not prevention. Phantom Vox continuously evaluates voice, identity, context, and channel quality, then holds the sensitive action until the person proves control of a trusted channel.

Show the Overview page and the privacy card.

## 0:25 to 0:55 - Architecture

Say:

> Audio is processed in short ephemeral windows. Each evidence module reports a score, quality, availability, explanation, and version. TrustFusion weights recent windows, requires consecutive high-risk evidence, and can abstain when quality is poor.

Open Live Guard.

## 0:55 to 2:20 - Mid-call clone

1. Choose **Mid-call clone**.
2. Select **Start monitoring**.
3. Point out the first low-risk windows.
4. As the Risk Index rises, point to synthetic evidence, speaker mismatch, and high-value context.
5. Show that a single window does not immediately cause a critical state.
6. Show the transaction state change to **ON HOLD**.

Say:

> This is a backend state transition, not a red label on the screen. The payment record moved from pending to on hold.

## 2:20 to 2:55 - Verification and escalation

Open the trusted-device dialog. Explain the masked destination and expiry. Simulate failure if the automated demo has not already done so.

Say:

> Voice never acts as the only authenticator. A separate trusted channel decides whether the held action may continue.

## 2:55 to 3:35 - Investigation

Open Investigations and select the new critical incident.

Show:

- peak Risk Index
- decision timeline
- transaction hold
- verification result
- supervisor escalation
- model and policy versions
- privacy-safe export

## 3:35 to 4:05 - Privacy and audit

Open Privacy & Audit and select **Verify audit integrity**.

Say:

> Raw audio is off by default. The audit chain links the actor, state transition, model, policy, action result, and previous hash. We call this a hash chain, not blockchain.

## 4:05 to 4:35 - Scientific honesty

Open Model Trust.

Say:

> The included executable detector is RawNetLite. AASIST and speaker verification are adapter positions, not false claims. This page refuses to show benchmark metrics until a real labeled evaluation is imported.

## 4:35 to 5:00 - Market and close

Say:

> We begin in shadow mode, then agent assist, then trusted verification, and only then controlled prevention. The defensible advantage is not one classifier. It is privacy-first, explainable, action-level prevention designed for Indian languages and telecom conditions, with those claims gated by evidence.

Close with:

> Phantom Vox hears the risk, proves the decision, and stops the sensitive action before fraud becomes a loss.

## Backup sequence

If audio hardware is unavailable, use seeded judge scenarios. If the browser loses the WebSocket, refresh the saved session. If an external integration is unavailable, use the signed demo webhook and clearly state that it is simulated.
