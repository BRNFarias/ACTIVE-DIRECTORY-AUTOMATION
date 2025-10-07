from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename, "status": "upload recebido"}
