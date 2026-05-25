import logging
from datetime import datetime, timezone

from ms3.database.mongo_connection import get_mongo_db

logger = logging.getLogger(__name__)


async def emit_alert(
    alert_type: str,
    message: str,
    tenant_id: str = "",
    session_id: str = "",
    severity: str = "warning",
) -> str:
    try:
        db = get_mongo_db()
        collection = db["alerts"]

        alert_doc = {
            "alert_type": alert_type,
            "message": message,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "severity": severity,
            "created_at": datetime.now(timezone.utc),
        }

        result = await collection.insert_one(alert_doc)
        return str(result.inserted_id)

    except Exception as e:
        logger.error("Failed to emit alert [%s] %s: %s", severity, alert_type, e)
        return ""
