from fastapi import APIRouter, UploadFile, File, Depends
import shutil
import os
import logging # <--- 1. Adicione esta importação
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
        # Opcional: Você pode logar o erro aqui também se quiser
        logging.error(f"Erro ao processar planilha '{file.filename}': {e}")
        return{"error": str(e)}
    
    os.remove(file_path)

    # <--- 2. Adicione o log de sucesso AQUI
    logging.info(f"Upload da planilha '{file.filename}' concluído com sucesso.")
    
    return result