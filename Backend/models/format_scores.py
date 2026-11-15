from uuid import uuid4
from sqlalchemy import Column, DateTime, Integer, String, CheckConstraint, Uuid, func, Text,text, ForeignKey, Enum as SAEnum
import enum
from sqlalchemy.dialects.postgresql import JSONB as Json
from extensions.extensions import Base

class scoring_status(enum.Enum):
    complete = "complete"
    partial = "partial"
    unscorable = "unscorable" 

class format_score(Base):
    __tablename__ = "format_scores"

    format_score_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    extraction_id = Column(Uuid(as_uuid=True), ForeignKey("resume_extraction.extraction_id"), nullable= False, index =True)
    scoring_status = Column(SAEnum(scoring_status, name = "SCORING_STATUS"), nullable = False, default = "unscorable", server_default = "unscorable")
    score = Column(Integer, nullable = False, default = 0, server_default = "0")
    max_score = Column(Integer, nullable =False, default= 0, server_default = "0")
    assessed_score = Column(Integer, nullable =False, default= 0, server_default = "0")
    assessed_max_score = Column(Integer, nullable =False, default= 0, server_default = "0")
    rule_version = Column(String(100), nullable = False)
    policy = Column(Json, nullable=False)
    breakdown = Column(Json, nullable=False)
    issues = Column(Json, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    suggestions = Column(Json, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    created_at = Column(DateTime(timezone = True), nullable =False, server_default = func.now())
    