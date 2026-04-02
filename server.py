import os
import uuid
import shutil
import zipfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import validator_openai as vo
import normalizer as norm

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

SESSION_CACHE = {}

@app.get("/")
async def root():
    return {"status": "alive", "message": "HR Data Validation API is running"}

@app.post("/api/validate")
async def validate_files(
    legacyFile: UploadFile = File(...), 
    adpFile: UploadFile = File(...),
    fieldGroup: str = "personal"
):
    # Only Personal, Job, Tax, Compliance supported
    if fieldGroup.lower() == "personal":
        required_fields = vo.PERSONAL_FIELDS
    elif fieldGroup.lower() == "tax":
        required_fields = vo.TAX_FIELDS
    elif fieldGroup.lower() == "compliance":
        required_fields = vo.COMPLIANCE_FIELDS
    else:
        required_fields = vo.JOB_FIELDS # Default to Job

    req_id = str(uuid.uuid4())
    leg_path = os.path.join(UPLOAD_DIR, f"{req_id}_legacy_{legacyFile.filename}")
    adp_path = os.path.join(UPLOAD_DIR, f"{req_id}_adp_{adpFile.filename}")

    # File loading and processing logic
    legacy_raw = vo.load_excel(leg_path)
    adp_raw = vo.load_excel(adp_path)
    
    # Store result in cache
    SESSION_CACHE[req_id] = {"req_id": req_id, "group": fieldGroup} # Placeholder
    return {"sessionId": req_id, "summary": {}, "validationSheet": []}

@app.get("/api/export/{session_id}")
async def export_excel(session_id: str):
    if session_id not in SESSION_CACHE:
        raise HTTPException(status_code=404, detail="Session not found")
    # Generate and return Excel
    return FileResponse("path/to/existing/file.xlsx") # Placeholder

@app.get("/api/export-zip")
async def export_zip(
    personal_id: str, 
    job_id: str, 
    tax_id: str = None,
    compliance_id: str = None
):
    # Zip generation logic - Only 4 files Max
    zip_path = os.path.join(OUTPUT_DIR, f"Validation_Export_{personal_id[:8]}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add files
        pass
    return FileResponse(zip_path)
