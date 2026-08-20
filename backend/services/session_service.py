import logging
import uuid
from typing import Optional

import db
from core.session import Session

logger = logging.getLogger(__name__)


async def create_session(
    session_id: Optional[str] = None, tenant_id: Optional[str] = None
) -> Session:
    new_id = session_id or str(uuid.uuid4())
    existing = await db.get_session_record(new_id, tenant_id=None)
    if existing is not None:
        raise ValueError(f"Session with id {new_id} already exists")
    session = await db.create_session_record(new_id, tenant_id)
    logger.info(f"Created new session: {new_id} (tenant={tenant_id})")
    return session


async def get_session(
    session_id: str, tenant_id: Optional[str] = None
) -> Optional[Session]:
    return await db.get_session_record(session_id, tenant_id)


async def list_sessions(tenant_id: Optional[str] = None) -> list[Session]:
    return await db.list_session_records(tenant_id)


async def delete_session(
    session_id: str, tenant_id: Optional[str] = None
) -> bool:
    deleted = await db.delete_session_record(session_id, tenant_id)
    if deleted:
        logger.info(f"Deleted session: {session_id}")
    return deleted


async def get_or_create_session(
    session_id: Optional[str] = None, tenant_id: Optional[str] = None
) -> Session:
    """Retrieve an existing session or create a new one.

    If session_id is provided but not found, a conflict-safe insert converges
    concurrent first-use requests on one session. If the ID exists for a
    different tenant, a new session is created with a fresh UUID.
    """
    if session_id:
        session = await get_session(session_id, tenant_id)
        if session:
            return session

        created = await db.get_or_create_session_record(session_id, tenant_id)
        if created is not None:
            logger.info(
                "Retrieved or created session via get-or-create: %s (tenant=%s)",
                session_id,
                tenant_id,
            )
            return created

        return await create_session(None, tenant_id)

    return await create_session(None, tenant_id)


async def register_session_document(
    session_id: str,
    doc_id: str,
    tenant_id: Optional[str] = None,
) -> None:
    """Track a document as part of the session's active document set."""
    session = await get_session(session_id, tenant_id)
    if session is None:
        return
    await db.add_session_document(session_id, doc_id)
