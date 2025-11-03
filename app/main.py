from fastapi import FastAPI
from app.routes import job_routes
from app.routes import user_routes # <-- 1. ADICIONE ESTA LINHA
from app.routes import auth_routes
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware 

load_dotenv()

print("PostgreSQL URL:", os.getenv("DATABASE_URL"))
print("MongoDB URL:", os.getenv("MONGO_URL"))

app = FastAPI(
        title="Automacao Active Directory",
        description="API para automatizar criacao e remocao de usuario via upload de planilha",
        version="1.0.0"
)

# --- Configuração do CORS (Mantenha como está) ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://localhost:4200",
    "null",
    "*" 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Fim do CORS ---

#registra as rotas
app.include_router(job_routes.router)
app.include_router(user_routes.router)
app.include_router(auth_routes.router) # <-- 2. ADICIONE ESTA LINHA

@app.get("/")
def root():
        return{"message": "API funcionando com sucesso!"}