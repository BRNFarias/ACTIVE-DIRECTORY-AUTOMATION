import pandas as pd
import os
from datetime import datetime
from app.models.job import Job
from app.database.mongodb import log_event
# Importamos a nossa nova função
from app.services.ad_service import connect_ad, create_or_update_user 

def process_excel(file_path: str, db):
    required_cols = ["Nome Completo", "CPF", "Inicio", "Fim"]

    # Leitura da planilha
    df = pd.read_excel(file_path, dtype=str) # Lê tudo como string primeiro

    if not all(col in df.columns for col in required_cols):
        log_event("Erro", f"Arquivo invalido: colunas obrigatorias ausentes ({file_path})")
        raise ValueError("Planilha invalida. Colunas obrigatorias ausente")
    
    # Cria registro no banco
    new_job = Job(filename=os.path.basename(file_path), status="processado", created_at=datetime.utcnow())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Log no Mongo
    try:
        log_event("Job", f"Arquivo {new_job.filename} processado com sucesso")
    except Exception as e:
        print("Erro ao logar no Mongo:", e)

    # Integração AD
    try:
        conn = connect_ad()
        if conn:
            print("\n--- INICIANDO PROCESSAMENTO AD ---")
            
            usuarios_sucesso = 0
            usuarios_falhados = 0
            
            for index, row in df.iterrows():
                
                # 1. Limpa o CPF (remove TODOS os espaços, tabs, etc.)
                username_limpo = "".join(str(row['CPF']).split())
                
                # 2. Limpa o Nome (remove espaços extras)
                nome_completo_limpo = " ".join(str(row['Nome Completo']).split())

                # 3. LÊ A DATA DE FIM
                try:
                    # Converte a data da planilha (ex: 10/10/2025) para datetime
                    fim_date = pd.to_datetime(row['Fim'], format='%d/%m/%Y')
                except ValueError:
                    print(f"Ignorando linha {index+1}: Data de Fim '{row['Fim']}' em formato inválido (esperado DD/MM/AAAA).")
                    usuarios_falhados += 1
                    continue

                # Ignora linhas onde o CPF ou Nome estão vazios
                if not username_limpo or not nome_completo_limpo:
                    print(f"Ignorando linha {index+1} por dados ausentes (CPF ou Nome).")
                    usuarios_falhados += 1
                    continue 

                password = "SenhaTemporaria123!"
                
                # 4. CHAMA A NOVA FUNÇÃO
                sucesso = create_or_update_user(conn, 
                                                nome_completo_limpo, 
                                                username_limpo, 
                                                password, 
                                                fim_date) # Passa a data de expiração
                
                if sucesso:
                    usuarios_sucesso += 1
                else:
                    usuarios_falhados += 1

            print("--- PROCESSAMENTO AD CONCLUÍDO ---")
            log_event("AD", f"Processamento concluído. {usuarios_sucesso} usuários criados/atualizados, {usuarios_falhados} falharam.")
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