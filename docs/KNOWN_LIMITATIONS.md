# Known Limitations

## Model evidence

- Only RawNetLite model code and a checkpoint are included.
- AASIST is not integrated.
- Speaker verification is not integrated.
- RawNetLite output is uncalibrated.
- Training-data provenance and checkpoint rights need independent verification.
- No verified accuracy, EER, fairness, language, accent, codec, or unseen-generator report is bundled.

## Live media

- Judge scenarios are deterministic simulations.
- The optional loopback adapter is Windows-only and captures local system output.
- Twilio, SIP, contact-center, mobile-network, Zoom, and Teams media integrations are not configured.
- The local WebSocket hub is in-process and is not a multi-node event bus.

## Verification and prevention

- Trusted-device, OTP, callback, and supervisor channels are demo workflows without external credentials.
- Transaction prevention affects the included simulated transaction store, not a real bank.
- Automatic call termination is intentionally not implemented.

## Privacy and security

- Development JWT authentication is not enterprise single sign-on.
- SQLite is for local use, not high availability.
- Metadata retention is displayed as policy but automatic TTL deletion is not scheduled.
- Local SQLite storage does not provide managed encryption at rest.
- The simple rate limiter is process-local.
- Browser WebSockets use the development JWT in a query parameter. A production gateway should exchange it for a short-lived, single-use WebSocket ticket and prevent query logging.
- Audit hash chaining detects mutation but does not prevent an administrator from replacing the entire database and backups.

## Evaluation

- The evaluation tool expects labeled scores. It does not supply a dataset.
- EER is approximated with a threshold sweep.
- minDCF, actDCF, ROC-AUC, calibration curves, and performance confidence intervals require a fuller evaluation pipeline.
- Imported reports are user attestations and are not independently certified by the application.

## Deployment

- Docker configuration is included but was not executed in the artifact build environment because Docker was unavailable.
- High availability, disaster recovery, backup restore, centralized logging, secret rotation, and load testing remain pilot work.
- Browser visual QA was limited by the artifact environment. Automated component tests, TypeScript compilation, and the production build passed.

These limitations should be shown to judges. Clear boundaries increase credibility and create a concrete pilot roadmap.
