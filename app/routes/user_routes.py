from fastapi import APIRouter, Depends, HTTPException, Body
from app.services.ad_service import connect_ad, list_users, delete_user, create_or_update_user
from typing import List
from pydantic import BaseModel
from datetime import datetime # <-- Importe o datetime

router = APIRouter(prefix="/users", tags=["Users"])

# Define um "modelo" de como o utilizador será enviado via API
class User(BaseModel):
    nome: str
    cpf: str
    status: str

# --- NOVO MODELO PARA CRIAÇÃO ---
class UserCreate(BaseModel):
    nome: str
    cpf: str
    inicio: str # Recebemos como texto, ex: "2025-10-31"
    fim: str    # Recebemos como texto, ex: "2026-10-31"
    senha: str

# ROTA 1: Listar todos os utilizadores (Já existe)
@router.get("/", response_model=List[User])
async def get_users_list(conn=Depends(connect_ad)):
    if not conn:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao AD")
    users = list_users(conn)
    return users

# --- NOVA ROTA 2: Criar um utilizador ---
@router.post("/")
async def create_single_user(user: UserCreate, conn=Depends(connect_ad)):
    if not conn:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao AD")

    try:
        # Converte as datas de string (do JSON) para objetos datetime
        # (O HTML envia no formato AAAA-MM-DD)
        inicio_date = datetime.strptime(user.inicio, "%Y-%m-%d")
        fim_date = datetime.strptime(user.fim, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD.")

    sucesso = create_or_update_user(conn, 
                                    user.nome, 
                                    user.cpf, 
                                    user.senha, 
                                    fim_date)
    
    if not sucesso:
        raise HTTPException(status_code=500, detail="Falha ao criar o usuário no AD (verifique os logs do Docker)")
    
    # Retorna o usuário criado no formato que a lista espera
    return {"nome": user.nome, "cpf": user.cpf, "status": "Inativo (Criado)"}


# ROTA 3: Excluir um utilizador (Já existe)
@router.delete("/{username}")
async def delete_user_by_username(username: str, conn=Depends(connect_ad)):
    if not conn:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao AD")
    
    sucesso = delete_user(conn, username)
    
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou falha ao deletar")
    return {"message": "Usuário deletado com sucesso"}