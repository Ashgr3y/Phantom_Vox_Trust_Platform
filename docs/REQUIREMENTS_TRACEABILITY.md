# Requirements Traceability

| Requirement | Implementation | Evidence | Status |
|---|---|---|---|
| Real-time monitoring | Per-session WebSocket and deterministic sequential windows | Live Guard timeline and `/ws/sessions/{id}` | Implemented for demo sessions |
| Voice-clone evidence | Preserved RawNetLite adapter and checkpoint | Model Trust inventory and audio upload API | Implemented with optional ML install |
| Mid-call attack handling | Recency-weighted decisions, consecutive windows, hysteresis | Mid-call clone scenario and backend tests | Implemented |
| Contextual risk | Transaction value and context evidence module | High-context uncertain scenario | Demo policy evidence |
| Speaker consistency | Evidence adapter interface and trusted voice registry | Trusted Voices and evidence card | Demo adapter only |
| Prosody | Versioned evidence interface | Live Guard evidence card | Rule/demo evidence only |
| Poor-quality handling | Quality gate and abstention | Poor-quality scenario | Implemented |
| Uncertainty | Missing-evidence coverage check | `UNCERTAIN` decision | Implemented |
| Prevention | Stored transaction `PENDING` to `ON_HOLD` transition | Live Guard action panel and API test | Implemented |
| Secondary verification | Trusted-device, OTP, callback, supervisor schema and UI | Verification dialog and stored state | Demo channel |
| Incident management | Search, detail, timeline, actions, disposition, export | Investigations tab | Implemented |
| Consent-based voice enrollment | Consent record, expiry, revocation, deletion | Trusted Voices tab | Metadata flow implemented; model absent |
| Policy configuration | Stored thresholds, templates, dry run, publish, versions | Policies tab and API tests | Implemented baseline |
| Telephone integration | Adapter cards and optional Windows loopback | Integrations tab and `adapters/` | Loopback local; Twilio and SIP not configured |
| Signed external events | HMAC-signed integration test payload | Integrations test endpoint | Implemented demo delivery |
| Model transparency | Correct installed-model inventory and limitations | Model Trust tab | Implemented |
| No fabricated accuracy | Empty benchmark state until import | Model Trust tab | Implemented |
| Evaluation pipeline | Labeled CSV metric script | `evaluation/evaluate.py` | Implemented; dataset not bundled |
| Indian-language validation | Protocol fields and UI labels | Evaluation guide | Not yet evidenced |
| Privacy by default | Raw audio off, temporary deletion, metadata-only audit | Privacy tab and automated test | Implemented locally |
| Authentication | Bcrypt development login and signed JWT | Login and protected endpoint tests | Implemented for development |
| Tenant isolation | Tenant IDs and scoped queries | Backend model and routes | Implemented; needs expanded adversarial tests |
| Tamper evidence | SHA-256 audit hash chain | Verify Audit Integrity action | Implemented |
| Responsive interface | Desktop, tablet, and mobile CSS breakpoints | React UI | Implemented; browser visual QA environment dependent |
| Deployment | Docker Compose and local scripts | Dockerfile and scripts | Configured; Docker not executed in build environment |
| Automated verification | Backend, frontend, and production build tests | Test suites | 12 tests passed |

## SIH judge interpretation

The complete, defensible implemented path is:

> A deterministic live-risk scenario raises recent evidence, stores a transaction hold, initiates verification, records an incident, and produces a verifiable privacy-safe audit trail.

The package must not be presented as a proven multilingual telecom detector until the validation and external integration rows above are completed.
