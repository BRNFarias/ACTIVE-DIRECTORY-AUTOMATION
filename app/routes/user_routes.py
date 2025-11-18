from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
# Importa a nova função de reativação
from app.services.ad_service import connect_ad, list_users, create_or_reactivate_user
from app.database.postgres import get_db
from sqlalchemy.orm import Session
from datetime import datetime, date

router = APIRouter(prefix="/users", tags=["Users"])

class UserCreate(BaseModel):
    nome: str
    username: str
    password: str
    fim_data: date 

@router.get("/")
def get_users_list():
    conn = connect_ad()
    if not conn:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao Active Directory")
    
    users = list_users(conn)
    conn.unbind()
    return {"users": users}

@router.post("/create")
def create_new_user(user_data: UserCreate, db: Session = Depends(get_db)):
    conn = connect_ad()
    if not conn:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao Active Directory")
    
    # Converte date para datetime
    fim_datetime = datetime.combine(user_data.fim_data, datetime.min.time())

    # Usa a função que cria ou reativa
    success = create_or_reactivate_user(conn, user_data.nome, user_data.username, user_data.password, fim_datetime)
    conn.unbind()

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao criar/reativar usuário {user_data.username}.")
    
    return {"message": f"Usuário {user_data.username} processado com sucesso."}