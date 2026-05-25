from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
import uuid


class BaseModel:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
