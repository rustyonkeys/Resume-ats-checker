from dotenv import load_dotenv
load_dotenv(override=True)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from extensions.extensions import Base, engine
from models.resumes import Resume
from models.job_description import JobDescription
from routes.upload_resume_jd_route import router as upload_resume_router
from routes.extracted_knowledge_route import router as extracted_knowledge_router

# Base.metadata.create_all(bind=engine)

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
    tags = ["Premium Features"]
)

# app.include_router(
#     # extracted_knowledge_router,
#     prefix = "/api/v1/resume",  # so the full path will be /api/v1/resume/extractedresumeknowledge
#     tags = ["Resume Format Scoring"]
# )