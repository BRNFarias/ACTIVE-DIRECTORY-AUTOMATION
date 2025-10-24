from app.database.postgres import Base, engine
from app.models.job import Job

print("Criando tabelas do banco de dados...")
Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso")