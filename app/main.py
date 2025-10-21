from fastapi import FastAPI
from app.routes import job_routes
from dotenv import load_dotenv
import os

load_dotenv()

print("PostgreSQL URL:", os.getenv("DATABASE_URL"))
print("MongoDB URL:", os.getenv("MONGO_URL"))


app = FastAPI(
        title="Automacao Active Directory",
        description="API para automatizar criacao e remocao de usuario via upload de planilha",
        version="1.0.0"
)



#registra as rotas do modulo job_routes
app.include_router(job_routes.router)

@app.get("/")
def root():
        return{"message": "API funcionando com sucesso!"}

