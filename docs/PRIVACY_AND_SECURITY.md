# Privacy and Security

## Default privacy posture

- Raw-audio retention is `false`.
- Judge scenarios do not contain or store real call audio.
- Audio uploads use a temporary file that is deleted in a `finally` block.
- The optional loopback adapter keeps chunks in memory unless a user explicitly enables saving.
- Stored records contain scores, versions, policies, decisions, and actions.

## Authentication and authorization

- Development authentication uses bcrypt password hashes and signed JWTs.
- API and WebSocket routes validate the token.
- Sensitive actions are restricted by Administrator, Operator, Analyst, or Auditor role.
- Queries scope records to the authenticated tenant.
- Production mode rejects the bundled development signing secret.

For a real deployment, replace development login with an enterprise identity provider, short-lived tokens, multifactor authentication, managed secret storage, and periodic access reviews.

## Application protections

- Configurable restricted CORS origins
- Input schemas and value ranges
- Audio extension and size validation
- Safe generated temporary names
- Simple per-client request limiting
- Safe production error messages
- Security response headers
- Audit events for login and sensitive state changes
- SHA-256 hash chain for tamper evidence

## Data retention

The local application displays a default 90-day metadata-retention policy but does not run an automatic deletion scheduler. A production deployment must implement and test TTL deletion, legal hold, export, subject-access, and erasure workflows.

## Encryption

The local SQLite demonstration is not a substitute for managed encryption. A pilot should use:

- TLS at every network boundary
- Encrypted database and backups
- KMS-managed keys
- Field protection for speaker embeddings and destinations
- Key rotation and access logging

## Audit semantics

Every audit hash covers the previous hash, tenant, actor, event, entity, state transition, model version, policy version, action result, payload, and timestamp. This supports tamper detection. It is not called blockchain and does not provide distributed consensus.

## Incident response

1. Disable affected integration credentials.
2. Preserve privacy-safe audit and incident metadata.
3. Verify the audit chain and model-policy versions.
4. Review false positive and false negative impact.
5. Revoke compromised trusted voice profiles.
6. Rotate keys and tokens where required.
7. Document corrective actions and validation evidence.
