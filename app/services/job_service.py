import pandas as pd
import os
from datetime import datetime
from app.models.job import Job
from app.database.mongodb import log_event

def process_excel(file_path: str, db):
    required_cols = ["Nome Completo", "CPF", "Inicio", "Fim"]

    df = pd.read_excel(file_path)

    if not all(col in df.columns for col in required_cols):
        log_event("Erro",f"Arquivo invalido: colunas obrigatorias ausentes ({file_path})")
        raise ValueError("Planilha invalida. Colunas obrigatorias ausente")
    
    # cria registro no banco
    new_job = Job(filename=os.path.basename(file_path), status="processado", created_at=datetime.utcnow())

    # log no Mongo
    log_event("Job",f"Arquivo {new_job.filename} processado com sucesso")

    return {"job_id": new_job.id, "rows": len(df), "status": "ok"}
