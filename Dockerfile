# Usar uma imagem base oficial do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# --- ETAPA DE CONFIANÇA DO CERTIFICADO ---
# 1. Instala as ferramentas de certificados do Debian
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# 2. Copia o seu certificado (do Passo 1) para o local correto
#    (Mude o .cer para .crt para que o update-ca-certificates o reconheça)
COPY ./ca_cert.cer /usr/local/share/ca-certificates/skynex_ca.crt

# 3. Atualiza o "trust store" (lista de CAs confiáveis) do sistema operativo
RUN update-ca-certificates
# --- FIM DA ETAPA DE CONFIANÇA ---

# Atualizar o pip antes de tudo
RUN pip install --upgrade pip

# Copiar o arquivo de dependências
COPY ./requirements.txt /app/requirements.txt

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da sua aplicação para dentro do container
COPY ./app /app/app
COPY ./create_tables.py /app/create_tables.py

# Comando para rodar a aplicação quando o container iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]