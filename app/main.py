from fastapi import FastAPI
from app.routes import job_routes

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
