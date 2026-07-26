import os
import tempfile
from pathlib import Path 
from fastapi import (
    APIRouter, 
    File, 
    UploadFile, 
    Form, 
    HTTPException,
    status)

from services.file_validation.file_validation import file_validation
from services.resume_parser.resumeparser import parse_resume


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
    jd: str = Form(..., min_length=1)
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

                resume_text = validation_result['full_resume_text']

                parsed_resume = parse_resume(resume_text)
                
                # The resume parser will eventually be called here:
                    # resume_text = extract_resume_text(temp_file_path)
                    # parsed_resume = parse_resume(resume_text)
                    # jd_analysis = analyse_job_description(jd)
                return{
                    "message": "Resume uploaded and validated successfully",
                    "filename": original_filename,
                    "job_desciption_received": True,
                    "validation": validation_result,
                    "text": parsed_resume
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

