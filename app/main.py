from fastapi import FastAPI
from app.routes import job_routes
from app.routes import user_routes # (Assumindo que este ficheiro existe)
from app.routes import auth_routes # (Assumindo que este ficheiro existe)
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware # <-- 1. IMPORTE O CORS

load_dotenv()

print("PostgreSQL URL:", os.getenv("DATABASE_URL"))
print("MongoDB URL:", os.getenv("MONGO_URL"))


app = FastAPI(
        title="Automacao Active Directory",
        description="API para automatizar criacao e remocao de usuario via upload de planilha",
        version="1.0.0"
)

# --- INÍCIO DA CORREÇÃO ---
# 2. DEFINA AS "ORIGENS" (O SEU FRONT-END)
origins = [
    "http://localhost",
    "http://localhost:3000", # Porta padrão do React
    "http://localhost:8080", # Porta padrão do Vue
    "http://localhost:5173", # Porta padrão do Vite
    "http://localhost:4200", # Porta padrão do Angular
    "null", # Permite testes locais com 'file://'
    "*" # Permite tudo (bom para testes)
]

# 3. ADICIONE O MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Permite estas origens
    allow_credentials=True,
    allow_methods=["*"],         # Permite todos os métodos (GET, POST, DELETE, etc.)
    allow_headers=["*"],         # Permite todos os cabeçalhos
)
# --- FIM DA CORREÇÃO ---


#registra as rotas do modulo job_routes
app.include_router(job_routes.router)
app.include_router(user_routes.router) # (Assumindo que este ficheiro existe)
app.include_router(auth_routes.router) # (Assumindo que este ficheiro existe)

@app.get("/")
def root():
        return{"message": "API funcionando com sucesso!"}