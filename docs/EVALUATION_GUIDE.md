# Evaluation Guide

Phantom Vox intentionally ships without a fabricated benchmark. Use this guide to create evidence judges can reproduce.

## 1. Build a labeled protocol

Copy `evaluation/protocols/manifest_template.csv` and provide one row per evaluated sample.

Required columns:

- `sample_id`
- `label`: `genuine` or `spoof`
- `score`: detector or fusion score from 0 to 1

Coverage columns:

- attack type
- generator
- language
- accent
- gender
- codec
- noise condition
- duration

Keep train, validation, calibration, and final test speakers and generators separated. Freeze the final test manifest before threshold tuning.

## 2. Required test matrix

| Dimension | Minimum coverage |
|---|---|
| Attack | TTS, voice conversion, replay, adversarial or post-processed audio |
| Generator | Seen and unseen tools |
| Language | Hindi, Marathi, Tamil, Telugu, Bengali, Kannada, Malayalam, Gujarati, Punjabi, Indian English |
| Channel | Clean 16 kHz, Opus, 8 kHz telephony, speakerphone, compression |
| Environment | Quiet, traffic, office, fan, packet loss |
| Identity | Known speaker, unknown speaker, cloned known speaker |
| Duration | Short, medium, and long utterances |
| Speech condition | Silence, music, overlapping speech, clipped speech |

## 3. Generate metrics

```bash
cd evaluation
python evaluate.py protocols/my_labeled_scores.csv \
  --threshold 0.50 \
  --output reports/my-evaluation.json
```

The script calculates:

- confusion matrix
- accuracy
- precision
- recall
- F1
- false acceptance rate
- false rejection rate
- approximate EER and threshold
- subgroup metrics for each coverage dimension

The generated report starts with `verified: false`. Set it to true only after reviewing label provenance, protocol separation, sample counts, and repeatability.

## 4. Add operational measurements

Record separately:

- first sufficient-speech score latency
- high-risk action latency
- CPU and RAM at one, ten, and target concurrent streams
- upload and streaming failure rates
- database and WebSocket recovery behavior

## 5. Calibration

Do not tune the operating threshold on the final test set. Use a held-out calibration set, produce a calibration curve, and report expected calibration error. Preserve the threshold, calibration version, and policy version used for each evaluation.

## 6. Import into Model Trust

Use the **Import evaluation report** action in Model Trust. The page displays values only from the supplied file. The application does not invent missing values or independently certify an uploaded claim.

## 7. Judge-facing evidence package

- Immutable test manifest
- Dataset and consent provenance
- Model and checkpoint hashes
- Configuration and threshold file
- Evaluation command
- JSON report
- Confusion matrix and subgroup tables
- Latency and resource log
- Failure examples
- Known limitations and remediation plan
