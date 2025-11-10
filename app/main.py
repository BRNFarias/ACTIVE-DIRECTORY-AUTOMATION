from fastapi import FastAPI
from app.routes import job_routes
from app.routes import user_routes 
from app.routes import auth_routes 
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware # <-- IMPORTANTE
from prometheus_client import make_asgi_app

load_dotenv()

print("PostgreSQL URL:", os.getenv("DATABASE_URL"))
print("MongoDB URL:", os.getenv("MONGO_URL"))

app = FastAPI(
        title="Automacao Active Directory",
        description="API para automatizar criacao e remocao de usuario via upload de planilha",
        version="1.0.0"
)

# --- CONFIGURAÇÃO DO CORS ---
origins = [
    "http://localhost",      # Para o seu site no IIS
    "https://localhost",     # Para o seu site no IIS (HTTPS)
    "null",                  # Para testes locais com file://
    "*"                      # Permite tudo (bom para testes)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],         # Permite todos os métodos (GET, POST, DELETE, etc.)
    allow_headers=["*"],
)
# --- FIM DO CORS ---


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ... resto das rotas ...
# Registra as rotas
app.include_router(job_routes.router)
app.include_router(user_routes.router) 
app.include_router(auth_routes.router) 

@app.get("/")
def root():
        return{"message": "API funcionando com sucesso!"}