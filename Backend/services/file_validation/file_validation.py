from pathlib import Path
from docx import Document
import fitz


def validate_text_quality(
        text: str, 
        min_words: int=40 , 
        min_chars: int=100) -> bool:
    """To check if the extracted text meets the minimum content thresholds. """
    clean_text = text.strip()

    #Splits by whitespace to find geniune words
    words = clean_text.split()

    if len(words)<(min_words):
        raise ValueError(
            f"Resume contains insufficient text ({len(words)} words found). "
            f"Minimum required is {min_words} words."
        )
    
    if len(clean_text)<min_chars:
        raise ValueError(
            f"Resume contains insufficient text ({len(clean_text)} characters found). "
            f"Minimum required is {min_chars} characters."
        )
    return True


# File extension and size validation

def file_validation(
        file_path: str, 
        allowed_file_extensions: set[str], 
        max_mb: int,
        min_words: int=40 , 
        min_chars: int=100)-> dict:

    #Validate an uploaded resume file.

    # Raises:
    #     ValueError: When the file fails validation.

    # Returns:
    #     dict: Basic validation information.
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise ValueError(f"Uploaded file cannot be found")
    
    file_size_bytes = path.stat().st_size
    max_size_bytes = max_mb * 1024 * 1024
    extension = path.suffix.lower()

    # validate extension
    if extension not in allowed_file_extensions:
        raise ValueError(
            f"Unsupported file extension"
            f"Allowed extensions are: {', '.join(sorted(allowed_file_extensions))}")

    # validate empty file
    if file_size_bytes == 0:
        raise ValueError(f"File is empty")
    
    # validate file size
    if file_size_bytes > max_size_bytes:
        raise ValueError(f"File size exceeds the maximum allowed size of {max_mb} MB")
    
    page_count = None
    contains_text = None

    # Deep pdf content validation
    if extension == '.pdf':
        try:
            with fitz.open(file_path) as document:
                if document.page_count == 0:
                    raise ValueError(f"PDF is corrupted or contains no pages")
                
                if document.needs_pass:
                    raise ValueError(f"Password-protected pdfs are not supported")
                
                page_count = document.page_count

                contains_text = any(
                    page.get_text().strip() 
                    for page in document
                )
                if not contains_text:
                    raise ValueError(
                        f"PDF contains no extractable text"
                        f"It may be a scanned or image only PDF, which is not supported.")


                full_pdf_text = ""
                for page in document:
                        full_pdf_text += page.get_text() + "\n"
                
                validate_text_quality(
                    full_pdf_text,
                    min_words = min_words,
                    min_chars = min_chars,
                )
                
# ValueError created by you
# return the same error
        except ValueError:
            raise
# Unexpected library/system error
# convert it into a clearer ValueError

        except Exception as exc:
            raise ValueError(f"Pdf file is corrupted or unreadable: {str(exc)}") from exc
        
    elif extension == ".docx":
        try:
            document = Document(file_path)
            extracted_text = "\n".join(
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

            contains_text = bool(extracted_text)

            if not contains_text:
                raise ValueError(
                    "DOCX contains no extractable text")

        except ValueError:
            raise

        except Exception as exc:
            raise ValueError(
            f"DOCX file is corrupted or unreadable: {exc}"
        ) from exc
        
    return {
        "valid": True,
        "extension": extension,
        "size_bytes": file_size_bytes,
        "page_count": page_count,
        "contains_extractable_text": contains_text,
        "full_resume_text": full_pdf_text
    }




