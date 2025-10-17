import pandas as pd
import os
from datetime import datetime
from app.models.job import Job
from app.database.mongodb import log_event
from app.services.ad_service import connect_ad, create_user

def process_excel(file_path: str, db):
    required_cols = ["Nome Completo", "CPF", "Inicio", "Fim"]

    # Leitura da planilha
    df = pd.read_excel(file_path)

    if not all(col in df.columns for col in required_cols):
        log_event("Erro", f"Arquivo invalido: colunas obrigatorias ausentes ({file_path})")
        raise ValueError("Planilha invalida. Colunas obrigatorias ausente")
    
    # Cria registro no banco
    new_job = Job(filename=os.path.basename(file_path), status="processado", created_at=datetime.utcnow())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)  # atualiza o objeto com o ID gerado pelo banco

    # Log no Mongo
    try:
        log_event("Job", f"Arquivo {new_job.filename} processado com sucesso")
    except Exception as e:
        print("Erro ao logar no Mongo:", e)

    # Integração AD
    try:
        conn = connect_ad()
        if conn:
            for index, row in df.iterrows():
                username = row['CPF']  # Usar CPF como login
                password = "SenhaTemporaria123!"  # Pode gerar automaticamente
                create_user(conn, row['Nome Completo'], username, password)

            log_event("AD", f"Usuarios do arquivo {new_job.filename} criados com sucesso!")
        else:
            log_event("AD", "Falha ao conectar ao Active Directory")
    except Exception as e:
        log_event("Erro", f"Falha ao criar usuários no AD: {e}")
        print(f"Erro na integração AD: {e}")

    # Retorno final
    return {
        "job_id": new_job.id,
        "rows": len(df),
        "status": "ok"
    }