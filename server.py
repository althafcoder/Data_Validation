import os
import uuid
import zipfile
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import validator_openai as vo
import normalizer as norm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cache for results (in-memory, for local use)
SESSION_CACHE = {}

@app.post("/api/validate")
async def validate_files(
    legacyFile: UploadFile = File(...),
    adpFile: UploadFile = File(...),
    fieldGroup: str = "personal"
):
    # Support for all field groups
    fg = fieldGroup.lower()
    if fg == "personal":
        required_fields = vo.PERSONAL_FIELDS
    elif fg == "tax":
        required_fields = vo.TAX_FIELDS
    elif fg == "compliance":
        required_fields = vo.COMPLIANCE_FIELDS
    elif fg == "direct_deposit":
        required_fields = vo.DIRECT_DEPOSIT_FIELDS
    elif fg == "deduction":
        required_fields = vo.DEDUCTION_FIELDS
    else:
        required_fields = vo.JOB_FIELDS # Default to Job

    req_id = str(uuid.uuid4())
    leg_path = os.path.join(UPLOAD_DIR, f"{req_id}_legacy_{legacyFile.filename}")
    adp_path = os.path.join(UPLOAD_DIR, f"{req_id}_adp_{adpFile.filename}")

    with open(leg_path, "wb") as f:
        f.write(await legacyFile.read())
    with open(adp_path, "wb") as f:
        f.write(await adpFile.read())

    # File loading and processing logic
    print(f"\n[INFO] Starting validation for group: {fieldGroup}")
    print(f"[INFO] Files saved to {leg_path} and {adp_path}")
    
    # Map internal group names to pretty filenames
    pretty_names = {
        "personal": "Personal Info Validation",
        "job": "Job Information Validation",
        "tax": "Tax Information Validation",
        "compliance": "Compliance Information Validation",
        "direct_deposit": "Direct Deposit Info Validation",
        "deduction": "Deduction Info Validation"
    }
    display_name = pretty_names.get(fg, fg.capitalize())
    output_filename = f"{display_name}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    primary_key = "Account Number" if fg == "direct_deposit" else "SSN"
    sheet_idx = 1 if fg == "direct_deposit" else 0

    try:
        if fg == "deduction":
            res = vo.run_deduction_validation(
                legacy_path=leg_path,
                adp_path=adp_path,
                company="G&W Products",
                output_path=output_path
            )
        else:
            res = vo.run_validation(
                legacy_path=leg_path,
                adp_path=adp_path,
                company="G&W Products",
                output_path=output_path,
                required_fields=required_fields,
                primary_key=primary_key,
                sheet_idx=sheet_idx
            )
        print(f"[SUCCESS] Validation complete. Output: {output_path}")
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[ERROR] Validation failed: {str(e)}")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
    
    summary = res.get("summary", {})
    
    # Store result in cache
    SESSION_CACHE[req_id] = {
        "req_id": req_id, 
        "group": fieldGroup, 
        "output_path": output_path,
        "summary": summary
    }
    
    return {
        "sessionId": req_id, 
        "summary": summary, 
        "outputFile": output_filename,
        "validationSheet": res.get("validationSheet", []),
        "discrepancies": res.get("discrepancies", []),
        "missingInADP": res.get("missingInADP", []),
        "missingInLegacy": res.get("missingInLegacy", [])
    }

@app.get("/api/export/{session_id}")
async def export_excel(session_id: str):
    if session_id not in SESSION_CACHE:
        raise HTTPException(status_code=404, detail="Session not found")
    
    file_path = SESSION_CACHE[session_id]["output_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result file missing")
        
    return FileResponse(
        file_path, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=os.path.basename(file_path)
    )

@app.get("/api/export-zip")
async def export_zip(
    personal_id: str,
    job_id: str = None,
    tax_id: str = None,
    compliance_id: str = None,
    dd_id: str = None,
    ded_id: str = None
):
    # Zip generation logic
    zip_filename = "Payroll_Validation_Full_Report.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_filename)
    
    session_ids = [personal_id, job_id, tax_id, compliance_id, dd_id, ded_id]
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for sid in session_ids:
            if sid and sid in SESSION_CACHE:
                file_path = SESSION_CACHE[sid]["output_path"]
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=zip_filename
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
