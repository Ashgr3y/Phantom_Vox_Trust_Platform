# API Guide

Interactive OpenAPI documentation is available at `/api/docs` while the backend is running.

## Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@phantomvox.local",
  "password": "PhantomVox@2026"
}
```

Pass the returned token as `Authorization: Bearer <token>`. WebSocket clients pass it in the `token` query parameter because browser WebSocket APIs cannot set an authorization header.

## Core endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service and privacy status |
| GET | `/api/v1/health/models` | Live RawNetLite adapter status |
| GET | `/api/v1/dashboard/summary` | Overview KPIs and recent records |
| POST | `/api/v1/sessions` | Create a tenant-scoped monitoring session |
| GET | `/api/v1/sessions` | Search and filter sessions |
| GET | `/api/v1/sessions/{id}` | Session, transaction, evidence, and decision timeline |
| POST | `/api/v1/sessions/{id}/audio` | Analyze a WAV, FLAC, or OGG upload with RawNetLite |
| POST | `/api/v1/sessions/{id}/stop` | Stop a session |
| WS | `/api/v1/ws/sessions/{id}` | Receive live session snapshots |
| POST | `/api/v1/demo/start` | Start one deterministic judge scenario |
| POST | `/api/v1/demo/{id}/advance` | Advance one scenario window for deterministic tests |
| GET | `/api/v1/incidents` | Filter incidents |
| GET | `/api/v1/incidents/{id}` | Review an incident and action trail |
| POST | `/api/v1/incidents/{id}/notes` | Add an analyst note |
| POST | `/api/v1/incidents/{id}/resolve` | Record genuine, fraud, or inconclusive disposition |
| GET | `/api/v1/policies` | List policy templates and thresholds |
| POST | `/api/v1/policies` | Create a policy draft |
| POST | `/api/v1/policies/{id}/publish` | Publish a policy version |
| POST | `/api/v1/policies/{id}/test` | Dry-run evidence through the policy |
| GET | `/api/v1/trusted-voices` | List consented voice profiles |
| POST | `/api/v1/trusted-voices/enroll` | Store consent and enrollment metadata |
| DELETE | `/api/v1/trusted-voices/{id}` | Revoke consent and remove embedding data |
| POST | `/api/v1/transactions/{id}/hold` | Place a sensitive action on hold |
| POST | `/api/v1/transactions/{id}/release` | Release a held action |
| POST | `/api/v1/transactions/{id}/block` | Block a sensitive action |
| POST | `/api/v1/verifications` | Initiate secondary verification |
| POST | `/api/v1/verifications/{id}/complete` | Complete verification |
| GET | `/api/v1/audit` | Read the audit chronology |
| POST | `/api/v1/audit/verify` | Recalculate and verify the hash chain |
| GET | `/api/v1/models` | Honest model inventory |
| GET | `/api/v1/evaluations` | Imported evaluation reports |
| POST | `/api/v1/evaluations/import` | Import a labeled evaluation report |
| GET | `/api/v1/integrations` | Integration inventory and modes |
| POST | `/api/v1/integrations/{id}/test` | Test or simulate a signed delivery |

## Start the mid-call demo

```http
POST /api/v1/demo/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "scenario": "mid_call_clone",
  "autoplay": true
}
```

The response contains a real stored session, transaction, evidence timeline, and current action state. As later windows arrive, the transaction moves to `ON_HOLD`, verification is created, and a critical incident is written.

## Audio upload behavior

- Maximum default upload: 20 MiB
- Allowed extensions: WAV, FLAC, OGG
- Temporary file is deleted after success or failure
- Raw audio is not retained
- RawNetLite optional dependencies must be installed
- Returned model score is marked `UNCALIBRATED_EVIDENCE`

## Signed integration test

The integration test endpoint returns an HMAC-SHA256 signature and the exact canonical JSON payload used to generate it. Demo adapters report `SIMULATED`, placeholders report `NOT_CONFIGURED`, and only configured local services report `DELIVERED`.
