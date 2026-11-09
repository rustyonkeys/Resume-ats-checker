from uuid import uuid4
from sqlalchemy import Column, DateTime, Integer, String, CheckConstraint, Uuid, func, Text, ForeignKey, Enum as SAEnum
import enum
from sqlalchemy.dialects.postgresql import JSONB as Json
from extensions.extensions import Base


class extraction_method(enum.Enum):
    native = "native"
    ocr_assisted = "ocr_assisted"

class processing_status(enum.Enum):
    pending="pending"
    processing="processing"
    completed="completed"
    failed="failed"

class ResumeExtraction(Base):
    __tablename__ = "resume_extraction"
    __table_args__ = (
    CheckConstraint(
        "page_count IS NULL OR page_count > 0",
        name="ck_resume_extraction_page_count",
    ),
)

    extraction_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    resume_id = Column(Uuid(as_uuid = True),ForeignKey("resumes.resume_id"),nullable=False, index=True)
    parser_version = Column(String(100), nullable=True)
    extraction_settings = Column(Json, nullable=False, default= dict, server_default= "{}")
    extracted_text = Column(Text, nullable=True)
    sections = Column(Json)
    contact_info = Column(Json)
    page_count = Column(Integer, nullable=True)
    extraction_method = Column(SAEnum(extraction_method, name= "resume_extraction_method"), nullable=True)
    # analysis_key = Column(String(255), nullable=True) this 
    processing_status = Column(SAEnum(processing_status, name= "resume_extraction_status"), nullable=False, default= "pending", server_default="pending")
    error_code = Column(String(220), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default= func.now())
