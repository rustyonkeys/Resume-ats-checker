from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from resume import ResumeATSScorer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return{"message": "Api is working"}

@app.post("/api/analyse_resume")    # post request to the backend from the frontend to analyze the resume and job description
def analyse_resume(
    resume: UploadFile = File(...), 
    job_description: str = Form(None)):

    #saving the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete= False,suffix = ".pdf") as temp_file:
        temp_file.write(resume.file.read())
        temp_pdf_path= temp_file.name

    try:
        #initialize ATS Scorer
        scorer = ResumeATSScorer(temp_pdf_path)

        #run analysis pipeline
        scorer.extract_text()
        scorer.clean_text(scorer.resume_text)
        scorer.extract_features()
        scorer.calculate_content_score()
        format_issues, format_score = scorer.check_format_issues()

        keyword_score, matched_keywords = scorer.match_job_description(job_description)

        final_score= scorer.calculate_final_score()

        return {
            "total_score": final_score,
            "content_score" : scorer.content_score,
            "format_score": format_score,
            "keyword_score": keyword_score,
            "matched_keywords": matched_keywords,
            "format_issues": format_issues,
            "missing_features": scorer.get_missing_features()
        }
    finally:
        os.remove(temp_pdf_path)
    

#change your job description logic matching in resume.py