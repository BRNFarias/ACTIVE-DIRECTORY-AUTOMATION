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
    
    # ... (criação do new_job) ...
    new_job = Job(filename=os.path.basename(file_path), status="processado", created_at=datetime.utcnow())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    try:
        log_event("Job", f"Arquivo {new_job.filename} processado com sucesso")
    except Exception as e:
        print("Erro ao logar no Mongo:", e)

    # --- CORREÇÃO (Parte 2) ---
    try:
        conn = connect_ad()
        if conn:
            print("\n--- INICIANDO PROCESSAMENTO AD ---")
            
            usuarios_criados = 0
            usuarios_falhados = 0
            
            for index, row in df.iterrows():
                
                # Limpa o CPF
                username_limpo = "".join(str(row['CPF']).split())
                
                # Limpa o Nome
                nome_limpo_split = str(row['Nome Completo']).split()
                nome_completo_limpo = " ".join(nome_limpo_split)

                if not username_limpo or not nome_completo_limpo:
                    print(f"Ignorando linha {index+1} por dados ausentes (CPF ou Nome).")
                    usuarios_falhados += 1
                    continue 

                password = "SenhaTemporaria123!"
                
                # Verifica o retorno da função
                sucesso = create_user(conn, nome_completo_limpo, username_limpo, password)
                
                if sucesso:
                    usuarios_criados += 1
                else:
                    usuarios_falhados += 1

            print("--- PROCESSAMENTO AD CONCLUÍDO ---")
            # Loga o resultado real no Mongo
            log_event("AD", f"Processamento concluído. {usuarios_criados} usuários criados, {usuarios_falhados} falharam.")
        else:
            log_event("AD", "Falha ao conectar ao Active Directory")
    except Exception as e:
        log_event("Erro", f"Falha ao criar usuários no AD: {e}")
        print(f"Erro na integração AD: {e}") 
    # --- FIM DA CORREÇÃO ---

    # Retorno final
    return {
        "job_id": new_job.id,
        "rows": len(df),
        "status": "ok"
    }