
import os
import logging
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from skill_extractor import extract_skills_from_pdf

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Skill Extractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/extract-skills")
async def extract_skills_endpoint(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed. Please upload a PDF file.")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
            contents = await file.read()
            temp.write(contents)
            temp.flush()
            temp_path = temp.name
        
        skills = extract_skills_from_pdf(temp_path)
        os.unlink(temp_path)
        return {"success": True, "skills": skills}
    except Exception as e:
        logger.exception("Error processing file")
        raise HTTPException(status_code=500, detail=str(e))
