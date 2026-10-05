from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditEvent


GENESIS_HASH = "0" * 64


def _canonical_event_payload(
    *,
    previous_hash: str,
    tenant_id: str,
    user_id: str | None,
    event_type: str,
    entity_type: str,
    entity_id: str,
    previous_state: str | None,
    new_state: str | None,
    model_version: str | None,
    policy_version: str | None,
    action_result: str,
    payload: dict,
    created_at: datetime,
) -> str:
    body = {
        "previous_hash": previous_hash,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "previous_state": previous_state,
        "new_state": new_state,
        "model_version": model_version,
        "policy_version": policy_version,
        "action_result": action_result,
        "payload": payload,
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_audit_event(
    db: Session,
    *,
    tenant_id: str,
    user_id: str | None,
    event_type: str,
    entity_type: str,
    entity_id: str,
    previous_state: str | None = None,
    new_state: str | None = None,
    model_version: str | None = None,
    policy_version: str | None = None,
    action_result: str = "SUCCESS",
    payload: dict | None = None,
) -> AuditEvent:
    previous = db.scalar(select(AuditEvent).order_by(AuditEvent.sequence.desc()).limit(1))
    previous_hash = previous.event_hash if previous else GENESIS_HASH
    created_at = datetime.now(timezone.utc)
    data = payload or {}
    canonical = _canonical_event_payload(
        previous_hash=previous_hash,
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
        model_version=model_version,
        policy_version=policy_version,
        action_result=action_result,
        payload=data,
        created_at=created_at,
    )
    event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    event = AuditEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
        model_version=model_version,
        policy_version=policy_version,
        action_result=action_result,
        payload_json=json.dumps(data, sort_keys=True),
        previous_hash=previous_hash,
        event_hash=event_hash,
        created_at=created_at,
    )
    db.add(event)
    db.flush()
    return event


def verify_audit_chain(db: Session) -> dict:
    events = list(db.scalars(select(AuditEvent).order_by(AuditEvent.sequence.asc())))
    expected_previous = GENESIS_HASH
    for event in events:
        payload = json.loads(event.payload_json or "{}")
        canonical = _canonical_event_payload(
            previous_hash=expected_previous,
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            previous_state=event.previous_state,
            new_state=event.new_state,
            model_version=event.model_version,
            policy_version=event.policy_version,
            action_result=event.action_result,
            payload=payload,
            created_at=event.created_at.replace(tzinfo=event.created_at.tzinfo or timezone.utc),
        )
        computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if event.previous_hash != expected_previous or event.event_hash != computed:
            return {
                "valid": False,
                "checked_events": len(events),
                "failed_sequence": event.sequence,
                "message": "Audit chain mismatch detected",
            }
        expected_previous = event.event_hash
    return {
        "valid": True,
        "checked_events": len(events),
        "latest_hash": expected_previous,
        "message": "Every audit event is linked and intact",
    }
