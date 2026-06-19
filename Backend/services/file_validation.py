import pdfplumber 
import fitz  # PyMuPDF
import os

# //File extension and size validation
pdf_path = ""

def file_validation(pdf_path, allowed_file_extensions, mx_mb):
    file_size_bytes = os.path.getsize(pdf_path)
    max_size_bytes = mx_mb * 1024 * 1024

    # validate extention
    _, ext = os.path.splitext(pdf_path)
    if ext.lower() not in allowed_file_extensions:
        raise ValueError(f"Unsupported file extension")

    # validate empty file
    if file_size_bytes == 0:
        raise ValueError(f"File is empty")

    # validate_size
    if file_size_bytes>max_size_bytes:
        raise ValueError(f"File size exceeds the maximum allowed size of {mx_mb} MB")

    # Deep Pdf Content validation
    if ext.lower() == '.pdf':
        try:
            with fitz.open(pdf_path) as doc:
                if len(doc) == 0:
                    raise ValueError(f"PDF is corrupted or contains no pages")
                
                #check if the pdf is readable
                first_page_text = doc.load_page(0).get_text().strip()

                if not first_page_text:
                    has_text = any(
                        page.get_text().strip() for page in doc
                    )
                    if not has_text:
                        raise ValueError(f"PDF is unreadable and contains no text")
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise ValueError(f"PDF file is corrupted or unreadable: {str(e)}")



    return True




allowed_file_extensions = ['.pdf', '.docx']
mx_mb = 5  #endforcing a strict 5 MB threshold

#testing the file validation service
try:
    file_validation(pdf_path, allowed_file_extensions, mx_mb)
    print("File successfully validated!")
except ValueError as e:
    print(f"File validation failed: {e}")
    exit(1)