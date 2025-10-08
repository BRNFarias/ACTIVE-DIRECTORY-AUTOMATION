from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database.postgres import Base

class Job(Base):
    __tablename__="jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, default="pendente")
    created_at = Column(DateTime, default=datetime.utcnow)