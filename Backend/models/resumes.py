from uuid import uuid4

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, String, Text, Uuid, func

from extensions.extensions import Base


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_resumes_positive_size"),
        CheckConstraint("file_type IN ('pdf', 'docx')", name="ck_resumes_file_type"),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid')",
            name="ck_resumes_validation_status",
        ),
        CheckConstraint("length(file_sha256) = 64", name="ck_resumes_sha256_length"),
        CheckConstraint("length(trim(original_filename)) > 0", name="ck_resumes_filename"),
        CheckConstraint("length(trim(storage_key)) > 0", name="ck_resumes_storage_key"),
    )

    resume_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    # Add the users.user_id foreign key when the users model is registered.
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    original_filename = Column(Text, nullable=False)
    storage_key = Column(Text, nullable=False, unique=True)
    file_type = Column(String(4), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    validation_status = Column(
        String(7), nullable=False, default="pending", server_default="pending"
    )
    validation_error = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
