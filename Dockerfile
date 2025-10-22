# Usar uma imagem base oficial do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Atualizar o pip antes de tudo
RUN pip install --upgrade pip

# Copiar o arquivo de dependências
# (Corrija o nome abaixo se o seu for 'requeriments.txt')
COPY ./requirements.txt /app/requirements.txt

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da sua aplicação para dentro do container
COPY ./app /app/app
COPY ./create_tables.py /app/create_tables.py

# Comando para rodar a aplicação quando o container iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]