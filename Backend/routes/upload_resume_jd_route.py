import os
import hashlib
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

from services.file_validation import file_validation
from services.resumeparser import parse_resume
from services.scoring.resume_format_scoring import score_resume_format
from services.scoring.response_formatter import (
    format_scoring_response,
    format_validation_response,
)

from extensions.extensions import get_db
from models.job_description import JobDescription
from models.resumes import Resume
# from LLM.extractknowledge import extract_resume_knowledge

#creating a router instance
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
                
                temp_file.write(chunk)

                #Connect uploadresume.py to file_validation.py
        validation_result = file_validation(
                file_path=temp_file_path,
                allowed_file_extensions=allowed_file_extensions,
                max_mb = max_file_size_mb
        )

        resume_text = validation_result["full_resume_text"]

        #calling resumeparser.py file
        parsed_resume = parse_resume(resume_text)
        resume_format_score = score_resume_format(parsed_resume=parsed_resume, validation_result=validation_result, file_path=temp_file_path, language="en")
        public_validation = format_validation_response(validation_result)
        public_format_score = format_scoring_response(resume_format_score)

        # extract_knowledge = extract_resume_knowledge(parsed_resume)


                # The resume parser will eventually be called here:
                    # resume_text = extract_resume_text(temp_file_path)
                    # parsed_resume = parse_resume(resume_text)
                    # jd_analysis = analyse_job_description(jd)

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
            validation_status="valid",
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


        try:
            db.add(resume_record)
            #The JD is being inserted before its parent resume exists in PostgreSQL. db.add() only queues a record; it does not immediately insert it.
            db.flush()  # Insert the resume before inserting its JD.
            db.add(jd_record)
            db.commit()
        except Exception:
            db.rollback()
            raise

        return{
            "message": "Resume uploaded and validated successfully",
            "filename": original_filename,
            "job_description_received": True,
            "validation": public_validation,
            "resume_format_score": public_format_score
            # "text": parsed_resume,
            # "extracted_knowledge": extract_knowledge
            }
            
    except HTTPException:
        raise
    
    except ValueError as exc:
        raise  HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = str(exc)
        ) from exc
    
    except Exception as exc:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Resume upload failed due to an unexpected error {exc}"
        ) from exc
    
    finally:
        await file.close()

        #Always remove the temporary file if it was created, regardless of whether the operation succeeded or failed.
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

