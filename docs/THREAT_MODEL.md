# Threat Model

## Protected assets

- Sensitive transaction state
- Trusted identity and consent records
- Speaker embeddings when a real adapter is added
- Model scores and decision explanations
- Policy versions and thresholds
- Incident and audit integrity
- Integration secrets and destinations

## Threats and controls

| Threat | Current control | Remaining production work |
|---|---|---|
| Voice cloning and TTS | Synthetic evidence plus sequential policy | Calibrated ensemble and unseen-generator validation |
| Voice conversion | Model adapter and evaluation protocol | Dedicated labeled evaluation |
| Replay attack | OOD and policy slots | Replay detector and channel challenge |
| Known-speaker clone | Speaker mismatch plus synthetic evidence design | Real consented speaker model |
| Mid-call injection | Recent-window weighting and consecutive decisions | Continuous production stream adapter |
| Noisy-channel evasion | Quality gate and abstention | Codec-specific calibration |
| False positive on genuine caller | Step-up verification before irreversible action | Pilot threshold tuning and appeals workflow |
| Stolen API token | Signed token and role checks | Enterprise IdP, rotation, MFA, revocation |
| Cross-tenant access | Tenant-scoped queries | Automated exhaustive authorization testing |
| Malicious audio upload | Extension and size checks, temporary deletion | MIME sniffing, sandboxing, antivirus |
| Audit tampering | SHA-256 hash chain | External anchoring and protected log export |
| Policy manipulation | Role gate, version and audit record | Four-eyes approval and signed policy release |
| Model poisoning | Versioned inventory | Signed model registry and supply-chain scanning |
| Prompt or UI deception | Plain capability labels | Operator training and controlled integrations |
| Denial of service | Request limit and upload cap | Distributed limits, queues, autoscaling |

## Abuse cases judges may ask about

### Attacker plays a clone after a genuine introduction

The system weights recent windows and requires consecutive high-risk evidence. It does not average the whole call in a way that hides the new attack.

### Audio quality is too poor

The system emits `INSUFFICIENT_AUDIO` and requests a secure callback. It does not automatically approve.

### Detector is uncertain but payment value is high

Context can raise the decision to step-up verification. Missing evidence cannot be counted as zero risk.

### An operator disagrees with the model

The operator can resolve the incident as genuine, fraud, or inconclusive. Every action is attributed and audited.

### Audit records are edited directly in the database

Recalculating the chain identifies the first mismatched sequence. Database administrators still require appropriate access controls and external protected backups.
