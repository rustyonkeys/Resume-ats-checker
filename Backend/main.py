# from fastapi import FastAPI, File, UploadFile, Form
# from fastapi.middleware.cors import CORSMiddleware
# import tempfile
# import os
# try:
#     from services.resume_ats_scorer_service import ResumeATSScorer
# except ImportError:
#     from Backend.services.resume_ats_scorer_service import ResumeATSScorer

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],
#     allow_credentials = True,
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

# @app.get("/")
# def root():
#     return{"message": "Api is working"}

# @app.post("/api/analyse_resume")    # post request to the backend from the frontend to analyze the resume and job description
# def analyse_resume(
#     resume: UploadFile = File(...), 
#     job_description: str = Form(None)):

#     #saving the uploaded file temporarily
#     with tempfile.NamedTemporaryFile(delete= False,suffix = ".pdf") as temp_file:
#         temp_file.write(resume.file.read())
#         temp_pdf_path= temp_file.name

#     try:
#         #initialize ATS Scorer
#         scorer = ResumeATSScorer(temp_pdf_path)

#         #run analysis pipeline
#         scorer.extract_text()
#         scorer.clean_text(scorer.resume_text)
#         scorer.extract_features()
#         scorer.calculate_content_score()
#         format_issues, format_score = scorer.check_format_issues()

#         keyword_score, matched_keywords = scorer.match_job_description(job_description)

#         final_score= scorer.calculate_final_score()

#         return {
#             "total_score": final_score,
#             "content_score" : scorer.content_score,
#             "format_score": format_score,
#             "keyword_score": keyword_score,
#             "matched_keywords": matched_keywords,
#             "format_issues": format_issues,
#             "missing_features": scorer.get_missing_features()
#         }
#     finally:
#         os.remove(temp_pdf_path)


from dotenv import load_dotenv
load_dotenv(override=True)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.upload_resume_jd_route import router as upload_resume_router
from routes.extracted_knowledge_route import router as extracted_knowledge_router



app = FastAPI(
    title = "ATS Engine Base",
    version= "1.0.0"
)

allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def api_health():
    return {
        "message": "API health is good", 
        "service": "ATS Engine Base"
        }

app.include_router(
    upload_resume_router, 
    prefix = "/api/v1/resume", 
    tags= ["Resume Tracking"]
    )


app.include_router(
    extracted_knowledge_router,
    prefix = "/api/v1/resume",  # so the full path will be /api/v1/resume/extractedresumeknowledge
    tags = ["Resume Extracted Knowledge"]
)