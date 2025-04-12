from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
from typing import Dict, List
from io import BytesIO
from PyPDF2 import PdfReader

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google AI
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Root endpoint
@app.get("/")
@app.head("/")
async def read_root():
    return {"message": "API is working!"}

# PDF text extractor
def extract_text_from_pdf(pdf_file: BytesIO) -> str:
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# New endpoint to compare two resumes
@app.post("/api/compare_resumes")
async def compare_resumes(files: List[UploadFile] = File(...)) -> Dict[str, str]:
    if len(files) != 2:
        raise HTTPException(status_code=400, detail="Please upload exactly two PDF files.")

    try:
        # Extract text from both PDFs
        texts = []
        for file in files:
            content = await file.read()
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Both files must be PDFs.")
            text = extract_text_from_pdf(BytesIO(content))
            texts.append(text)

        # Construct comparison prompt
        prompt = f"""
Compare the following two resumes. Analysis strengths, weaknesses, and unique qualities of each candidate. Provide which name of candidate is perfect for software engineering position and Give a 50 words vaild reason for selection.

Resume 1:
{texts[0]}

Resume 2:
{texts[1]}
"""

        # Generate comparison
        response = model.generate_content(prompt)
        return {"comparison": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing resumes: {str(e)}")
