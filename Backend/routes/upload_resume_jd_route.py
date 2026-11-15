import os
import hashlib
import logging
import tempfile
from pathlib import Path 
from fastapi import (
    APIRouter, 
    File, 
    UploadFile, 
    Form, 
    Depends,
    HTTPException,
    status)

from sqlalchemy.orm import Session
from uuid import UUID,uuid4
from sqlalchemy.exc import SQLAlchemyError

from services.file_validation import file_validation
from services.resumeparser import parse_resume
from services.scoring.resume_format_scoring import score_resume_format
from services.scoring.response_formatter import (
    format_scoring_response,
    format_validation_response,
)
from services.scoring.document_features import extract_features
from extensions.extensions import get_db
from models.job_description import JobDescription
from models.resumes import Resume
from models.resume_extraction import ResumeExtraction


#creating a router instance
logger = logging.getLogger(__name__)
router = APIRouter()

allowed_file_extensions = ['.pdf', '.docx']
max_file_size_mb = 5  #endforcing a strict 5 MB threshold
max_size_bytes = max_file_size_mb * 1024 * 1024

@router.post(
        "/uploadresume",
        status_code = status.HTTP_200_OK,)

async def upload_resume(
    file: UploadFile = File(...),
    jd: str = Form(..., min_length=1),
    user_id: UUID = Form(...),
    db: Session = Depends(get_db)
):
    
    # Upload and validate a resume together with a job description.
    
    temp_file_path: str | None = None               # a temporary file path can contain a string or None and initially it is set to None.
    try:
        #validating the original uploaded file name and extension
        original_filename = file.filename
        extension = Path(original_filename).suffix.lower()
        if not original_filename or not original_filename.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A resume filename is required.",
            )

        jd = jd.strip()
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description cannot be empty.",
            )

        if extension not in allowed_file_extensions:
            raise HTTPException(
                status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail = (
                    f"Unsupported file extension."
                    f"Allowed extensions are:" f"{', '.join(sorted(allowed_file_extensions))}"
                ),
            )
        #Create a temporary file using the original file extension
        with tempfile.NamedTemporaryFile(
            delete = False,
            suffix = extension
        ) as temp_file:
            temp_file_path = temp_file.name
            uploaded_size = 0
            file_hash = hashlib.sha256()


            #save the uploaded file in chunks
            while True:
                chunk = await file.read(1024*1024)

                if not chunk:
                    break
                uploaded_size += len(chunk)

                if uploaded_size > max_size_bytes:
                    raise HTTPException(
                        status_code = status.HTTP_413_CONTENT_TOO_LARGE,
                        detail = (
                            f"File size exceeds the maximum allowed size of {max_file_size_mb} MB."
                        ),
                    )

                file_hash.update(chunk)
                temp_file.write(chunk)

        if uploaded_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty.",
        )

        resume_id = uuid4() #Generates a unique identifier for the resume
        content = Path(temp_file_path).read_bytes() #Reads the content of the temporary file as bytes
        
        resume_record = Resume(
            resume_id=resume_id,
            user_id=user_id,
            original_filename=original_filename,
            storage_key=f"metadata-test/{resume_id}{extension}",
            file_type=extension.lstrip("."),
            size_bytes=len(content),
            file_sha256=hashlib.sha256(content).hexdigest(),
            validation_status="pending",
        )
        
        jobdescription_id = uuid4()
        jd_record = JobDescription(
            job_description_id = jobdescription_id,
            resume_id = resume_id,
            jd_text = jd,
            role_title = None,
            company_name = None,
            source_url = None
        )
        
        extraction_id = uuid4()
        resume_extraction_record = ResumeExtraction(
            extraction_id = extraction_id,
            resume_id = resume_id,
            extracted_text = None,
            sections = None,
            contact_info = None,
            page_count = None,
            extraction_method= None,
            # analysis_key
            parser_version = "resume-pipeline-v1",
            extraction_settings = {},
            processing_status = "pending",
            error_code = None
        )

        db.add(resume_record)
        #The JD is being inserted before its parent resume exists in PostgreSQL. db.add() only queues a record; it does not immediately insert it.
        db.flush()  # Insert the resume before inserting its JD.
        db.add(jd_record)
        db.add(resume_extraction_record)
        db.commit()

        resume_extraction_record.processing_status = "processing"
        db.commit()

        validation_result = None
        failure_code = "EXTRACTION_VALIDATION_FAILED"
        
        try:
                #Connect uploadresume.py to file_validation.py
            validation_result = file_validation(
                file_path=temp_file_path,
                allowed_file_extensions=allowed_file_extensions,
                max_mb = max_file_size_mb
            )
            resume_text = validation_result["full_resume_text"]

            failure_code = "RESUME_PARSING_FAILED"
            parsed_resume = parse_resume(resume_text)

            failure_code = "SECTION_EXTRACTION_FAILED"
            pdf_analysis = validation_result.get("pdf_analysis") or {}
            embedded_links = [
                link["uri"]
                for page in pdf_analysis.get("pages", [])
                for link in (page.get("links") or [])
            ]

            features = extract_features(
                resume_text,
                parsed_resume,
                embedded_links,
            )

        except Exception as exc:
            logger.exception(
                "Resume extraction failed: extraction_id=%s, code=%s",
                extraction_id,
                failure_code,
            )
            db.rollback()

            # The initial commit preserves this record after rollback.
            try:
                failed_record = db.get(ResumeExtraction, extraction_id)
                failed_record.processing_status = "failed"
                failed_record.error_code = failure_code

                parent_record = db.get(Resume, resume_id)
                if validation_result is not None:
                    parent_record.validation_status = "valid"
                    parent_record.validation_error = None
                elif isinstance(exc, ValueError):
                    parent_record.validation_status = "invalid"
                    parent_record.validation_error = failure_code

                db.commit()
            except SQLAlchemyError:
                db.rollback()
                logger.exception(
                    "Could not save failed status: extraction_id=%s",
                    extraction_id,
                )

            raise
        # Fill the same record after extraction succeeds.
        resume_extraction_record.extracted_text = resume_text
        resume_extraction_record.sections = features["sections"]
        resume_extraction_record.contact_info = features["contact_info"]
        resume_extraction_record.page_count = validation_result["page_count"]
        resume_extraction_record.extraction_method = validation_result[
            "text_extraction_method"
        ]
        resume_extraction_record.processing_status = "completed"
        resume_extraction_record.error_code = None

        resume_record.validation_status = "valid"
        resume_record.validation_error = None
        db.commit()


        #  A scoring failure must not mark successful extraction as failed.
        resume_format_score = score_resume_format(
            parsed_resume=parsed_resume,
            validation_result=validation_result,
            file_path=temp_file_path,
            language="en",
        )

        public_validation = format_validation_response(validation_result)
        public_format_score = format_scoring_response(resume_format_score)

        return{
            "message": "Resume uploaded and validated successfully",
            "filename": original_filename,
            "job_description_received": True,
            "job_description_id": str(jobdescription_id),
            "extraction_id": str(extraction_id),
            "validation": public_validation,
            "resume_format_score": public_format_score,
            "detailed_breakdown_format_score": resume_format_score,
            }
            
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database operation failed during resume upload.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save resume data to the database.",
        ) from exc

    except ValueError as exc:
        db.rollback()
        raise  HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = str(exc)
        ) from exc
    
    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error during resume upload.")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Resume upload failed due to an unexpected error {exc}"
        ) from exc
    
    finally:
        try:
            await file.close()

        finally:
            #Always remove the temporary file if it was created, regardless of whether the operation succeeded or failed.
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    logger.warning(
                        "Could not remove the temporary resume file.",
                        exc_info=True,
                    )

