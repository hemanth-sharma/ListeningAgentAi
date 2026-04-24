from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Mission(Base):
    __tablename__ = "missions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=False)