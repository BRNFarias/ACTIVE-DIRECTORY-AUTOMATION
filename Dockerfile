# Usar uma imagem base oficial do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Atualizar o pip antes de tudo
RUN pip install --upgrade pip

# Copiar o arquivo de dependências
COPY ./requirements.txt /app/requirements.txt

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia a nossa nova pasta ssl para dentro da imagem
COPY ./ssl /app/ssl

# Copiar o código da sua aplicação para dentro do container
COPY ./app /app/app
COPY ./create_tables.py /app/create_tables.py

# --- INÍCIO DA CORREÇÃO (SSL - Linha Única) ---
# O comando CMD deve estar todo numa única linha.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile=/app/ssl/localhost.key", "--ssl-certfile=/app/ssl/localhost.crt"]
# --- FIM DA CORREÇÃO ---