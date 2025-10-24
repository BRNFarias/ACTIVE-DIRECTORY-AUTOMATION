from fastapi import APIRouter, UploadFile, File, Depends
import shutil
import os
from app.database.postgres import get_db
from app.services.job_service import process_excel

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db=Depends(get_db)):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    try:
        result = process_excel(file_path, db)
    except Exception as e:
        os.remove(file_path)
        return{"error": str(e)}
    
    os.remove(file_path)
    return result

    

















#return {"filename": file.filename, "status": "upload recebido"}