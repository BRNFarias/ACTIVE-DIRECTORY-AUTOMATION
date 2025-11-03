from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.ad_service import check_user_credentials

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str # O front-end envia 'email'
    senha: str

@router.post("/login")
async def login(request: LoginRequest):
    # Chama a nova função de verificação no AD
    user_details = check_user_credentials(request.email, request.senha)
    
    if not user_details:
        raise HTTPException(
            status_code=401, 
            detail="Credenciais inválidas. Verifique e tente novamente."
        )
    # Se for bem-sucedido, retorna os detalhes do utilizador
    return user_details