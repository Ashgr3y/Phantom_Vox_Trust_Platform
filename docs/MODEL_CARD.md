# RawNetLite Model Card

## Model identity

- Display name: RawNetLite
- Purpose: lightweight synthetic-speech evidence
- Architecture file: `models/rawnetlite/RawNetLite.py`
- Checkpoint: `models/rawnetlite/augmented_triple_cross_domain_focal_rawnet_lite.pt`
- Input: mono 16 kHz waveform in 3-second windows
- Output: sigmoid score used as uncalibrated synthetic-speech evidence

## Supplied artifact hashes

```text
checkpoint SHA-256: 44f5483b514902fb7698654d03c55c98aef128075c2310ba8b94f1f770449028
architecture SHA-256: eb42fde4384a704ca15a733b6fba3c4b5fd8d1e114f5cb143765fed2f3cb2161
```

## Architecture

The included implementation contains:

- One-dimensional convolution and batch normalization
- Three one-dimensional residual blocks
- Adaptive temporal pooling
- Bidirectional GRU
- Two fully connected layers and a sigmoid output

It does **not** contain the spectro-temporal graph-attention architecture required to call it AASIST.

## Intended use

- Local research and hackathon demonstrations
- One evidence input to a wider risk and verification policy
- Offline upload inference after optional ML dependencies are installed

## Prohibited interpretation

- Do not call the score an impersonation probability.
- Do not claim 99 percent accuracy.
- Do not claim Indian-language, codec, replay, or unseen-generator robustness without a labeled evaluation.
- Do not use it as the only authentication factor.
- Do not directly terminate a call or transfer solely from one window score.

## Known limitations

- Training data and checkpoint provenance require independent verification.
- No bundled calibration set or operating threshold evidence is provided.
- No bundled evaluation proves generalization to current voice generators.
- Short, noisy, compressed, replayed, or overlapping audio may be unreliable.
- Demographic, language, accent, gender, and device fairness are not established.
- The optional runtime is computationally heavier than the base judge demo.

## Required evaluation before pilot

- Genuine speech, TTS, voice conversion, replay, and adversarial samples
- Seen and unseen generators
- Hindi, Marathi, Tamil, Telugu, Bengali, Kannada, Malayalam, Gujarati, Punjabi, and Indian English
- 8 kHz and 16 kHz telephony paths
- Speakerphone, noise, packet loss, and compression
- Known speaker, unknown speaker, and cloned known speaker
- Precision, recall, F1, EER, false acceptance, false rejection, calibration error, latency, CPU, and RAM

## Other model labels

- AASIST is an unimplemented adapter position.
- Speaker verification is an unimplemented adapter position.
- Prosody, context, quality, and OOD evidence in judge scenarios are explicitly demo or rule-based.
