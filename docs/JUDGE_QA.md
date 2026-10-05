# Judge Questions and Answers

## Is this actually AASIST?

No. The included executable model is RawNetLite, a convolutional residual and bidirectional-GRU architecture. AASIST is shown only as an uninstalled future adapter.

## What exactly is prevented?

In the complete demo, a stored sensitive transaction changes from `PENDING` to `ON_HOLD`. Verification and incident records are created and audit events are chained. The platform does not falsely claim it terminated a real bank transfer.

## Why not block every suspicious call?

Voice detectors can make mistakes, especially with noise, codecs, new generators, and accents. Phantom Vox uses a safer rollout: monitor, warn, hold, verify, and escalate before controlled blocking.

## Can one genuine beginning hide a later cloned segment?

No. The decision engine gives more weight to recent windows and requires consecutive suspicious windows. It does not use one whole-call average.

## What happens when audio quality is bad?

The system abstains with `INSUFFICIENT_AUDIO` and recommends a secure callback. It does not automatically approve.

## Is the Risk Index an impersonation probability?

No. It is a policy score. The RawNetLite sigmoid output is also labelled uncalibrated evidence until a real calibration report exists.

## What is your novelty?

The novelty is the full trust-to-prevention workflow: quality-aware multi-evidence fusion, recent-window decisions, active trusted-channel verification, action-level holds, privacy-first operation, and tamper-evident evidence. A standard classifier alone is not presented as novel.

## Does it support Indian languages?

The interface and evaluation protocol support per-language evidence, but the package does not claim measured multilingual robustness. The next evidence milestone is a labeled Indian-language and telecom-codec benchmark.

## Is speaker verification real?

Not in this package. Consent, enrollment metadata, expiry, revocation, and the adapter contract are implemented. ECAPA-TDNN or another validated speaker model must be integrated before speaker scores are called real.

## Is your OTP real?

No. The judge verification channel is an explicitly labelled demo. The stored verification transition is real within the application. SMS, trusted-device push, or callback providers require configured credentials and pilot controls.

## Why use a hash chain instead of blockchain?

A standard cryptographic hash chain is sufficient to detect changes in this local audit sequence. Blockchain would add complexity without solving access control, privacy, or model reliability.

## How is privacy protected?

Raw audio retention is off. Uploads are temporary and deleted after inference. The audit stores scores, versions, decisions, and actions. A production pilot still needs managed encryption, automatic retention jobs, and legal review.

## Can this scale to many calls?

The modular interfaces are ready for a shared session broker and PostgreSQL. The local release uses one process and is not presented as a high-availability telecom platform.

## What is the market entry strategy?

Start with payment approvals, account recovery, contact centers, and executive approvals. Deploy in shadow mode first, measure false positives, add agent assist, then enable step-up verification for high-value actions.

## What would you build next?

1. A real SIP or Twilio streaming adapter.
2. A calibrated anti-spoofing ensemble.
3. Consent-based speaker verification.
4. Indian-language and codec evaluation.
5. Enterprise identity, KMS, PostgreSQL, Redis, observability, and high availability.
