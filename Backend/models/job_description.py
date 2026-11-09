from sqlalchemy import Column, String, Text, Uuid, DateTime, ForeignKey, func, CheckConstraint
from uuid import uuid4
from extensions.extensions import Base

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (
    CheckConstraint(
        "length(trim(jd_text)) > 0",
        name="ck_job_descriptions_nonempty_text",
    ),)

# jd_id               UUID PK
# user_id             UUID FK → users.user_id
# jd_text             TEXT
# role_title          TEXT ?
# company_name        TEXT ?
# source_url          TEXT ?
    job_description_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    # user_id = Column(Uuid(as_uuid=True), nullable=True)
    resume_id = Column(Uuid(as_uuid=True),(ForeignKey("resumes.resume_id")), nullable=True, index=True)
    jd_text= Column(Text, nullable=False)
    role_title= Column(String(225), nullable=True)
    company_name= Column(String(225), nullable=True)
    source_url= Column(String(225), nullable=True)
    created_at= Column(DateTime(timezone=True), nullable=False, server_default= func.now())
