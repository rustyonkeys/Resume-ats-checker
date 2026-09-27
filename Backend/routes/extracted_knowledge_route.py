from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field

from LLM.extractknowledge import extract_resume_knowledge

#Creating a router instance
router = APIRouter()

#Creates a request model for one resume block.
# Creating a request model means: you define the exact shape of data your API expects from the frontend/client. In FastAPI, this is usually done using Pydantic’s BaseModel.
# Each block should match the output from your resumeparser.py

class ResumeBlock(BaseModel):
    index: int
    category: str | None = None          #  The | symbol means "or". This tells your code editor that this variable can either hold text data (str) or it can hold no value at all (None).
    text: str

class ExtractKnowledgeRequest(BaseModel):
    parsed_resume: list[ResumeBlock]     # Creates the full request body model for the API.
    jd : str = Field(..., min_length = 1)

@router.post(
    "/extractedresumeknowledge",
    status_code = status.HTTP_200_OK,
)

#“FastAPI, when someone calls this API, take the JSON body, convert it into an ExtractKnowledgeRequest object, and give it to me in the variable called request.”
async def extracted_resume_knowledge(request: ExtractKnowledgeRequest):   #we are passing an argument named request and it should have the type ExtractKnowledgeRequest
    try:
        parsed_blocks= [
            block.model_dump()
            for block in request.parsed_resume
        ]

        extract_knowledge = extract_resume_knowledge(parsed_blocks, request.jd)

        return {
            "message": "Extracted knowledge from resume successfully.",
            "extracted_knowledge": extract_knowledge
        }
    except ValueError as exc:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Knowledge extraction engine failed to process the request: {str(exc)}"
        ) from exc
