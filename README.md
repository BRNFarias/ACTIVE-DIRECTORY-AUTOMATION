# 🧠 Automação de Active Directory com API

Uma **API em FastAPI** projetada para automatizar a **criação de usuários no Active Directory (AD)** através do **upload de uma planilha Excel**.

Este projeto é **totalmente containerizado com Docker** e utiliza um **banco de dados PostgreSQL** para rastrear os *jobs* (planilhas) e um **MongoDB** para armazenar os logs de execução.

---

## ⚙️ Pré-requisitos

Antes de começar, você precisará ter:

- 🐳 **Docker Desktop** instalado e em execução  
- 🖥️ **Servidor Active Directory** (por exemplo, uma VM com Windows Server) acessível pela rede  
- 🔥 **Permissão de Firewall** no seu servidor AD para permitir conexões na porta **389 (LDAP)** (para autenticação *SIMPLE*)  

---

## 🚀 Guia de Instalação (Passo a Passo)

### **Passo 1: Obter o Projeto**

Clone o repositório para a sua máquina:

```bash
git clone https://github.com/BRNFarias/ACTIVE-DIRECTORY-AUTOMATION.git
cd ACTIVE-DIRECTORY-AUTOMATION
```

---

### **Passo 2: Configurar a Conexão com o Active Directory**

Esta é a etapa mais importante.  
O script precisa das credenciais para se conectar ao seu AD.

Abra o arquivo:  
`app/services/ad_service.py`

Edite as seguintes constantes no topo do arquivo com as suas próprias credenciais:

```python
# app/services/ad_service.py

# --- CONFIGURE ESTAS VARIÁVEIS ---
AD_SERVER = ""  # COLOQUE O IP DO SEU SERVIDOR AD
AD_PASSWORD = ""   # COLOQUE A SENHA DO SEU USUÁRIO AD
AD_USER = "DOMINIO\usuario"   # COLOQUE O SEU USUÁRIO AD (formato DOMINIO\usuario)
BASE_DN = "OU=Nome_Unidade_Organizacional,DC=seu_dominio,DC=local"  # CAMINHO ONDE OS USUÁRIOS SERÃO CRIADOS
# --- FIM DA CONFIGURAÇÃO ---
```

> 💡 **Importante sobre o BASE_DN:**  
> - Para criar usuários na pasta padrão **Users**, use:  
>   `CN=Users,DC=seu_dominio,DC=local`  
> - Para criar usuários em uma **Unidade Organizacional (OU)**, use:  
>   `OU=Usuarios Ativos,DC=seu_dominio,DC=local`

---

### **Passo 3: Executar o Ambiente Docker**

Estes comandos criarão a rede, iniciarão os bancos de dados e construirão a API.

#### 1️⃣ Crie a rede Docker
```bash
docker network create ad_net
```

#### 2️⃣ Inicie o Banco de Dados PostgreSQL
Armazena os *jobs* de upload.

```bash
docker run --name postgres-db --network ad_net -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=ad_jobs -p 5432:5432 -d postgres
```

#### 3️⃣ Inicie o Banco de Dados MongoDB
Armazena os logs de sucesso/erro.

```bash
docker run --name mongo-db --network ad_net -p 27017:27017 -d mongo
```

#### 4️⃣ Construa a Imagem da API
Instala as dependências do `requirements.txt` dentro da imagem.

```bash
docker build --no-cache -t active-automation-imagem .
```

#### 5️⃣ Inicie a API
Executa a API e injeta as URLs dos bancos de dados.

```bash
docker run --name active-automation --network ad_net -e DATABASE_URL="postgresql+psycopg2://admin:admin@postgres-db:5432/ad_jobs" -e MONGO_URL="mongodb://mongo-db:27017/" -p 8000:8000 -d active-automation-imagem
```

---

### **Passo 4: Criar as Tabelas no Banco**

Com o contêiner da API rodando, crie a tabela `jobs` no Postgres:

```bash
docker exec active-automation python create_tables.py
```

> Saída esperada:  
> `Tabelas criadas com sucesso`

---

## 🧩 Como Usar a Aplicação

Seu ambiente está **100% pronto**!

### 1️⃣ Acesse a Documentação da API
Abra no navegador:  
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

Você verá a documentação interativa (*Swagger UI*).

---

### 2️⃣ Teste o Upload

1. Clique em **POST /jobs/upload**  
2. Clique em **Try it out**  
3. Em “file”, selecione sua planilha Excel  
4. Clique em **Execute**

Se tudo der certo, a resposta será:

```json
{"status": "ok"}
```

---

### 3️⃣ Verifique o Resultado

- Vá até o **Active Directory** (na VM)  
- Abra a **OU configurada** (ex: *Usuarios Ativos*)  
- Pressione **F5** (Atualizar)  
- 🎉 O novo usuário deverá aparecer!

Você pode verificar:
- **Logs** no *MongoDB* (com MongoDB Compass)
- **Jobs** no *PostgreSQL* (com DBeaver)

---

## 📊 Formato da Planilha

A planilha Excel deve conter, no mínimo, as seguintes colunas:

| Nome Completo | CPF | Inicio | Fim |
|----------------|-----|--------|-----|
| João Silva     | 123.456.789-00 | 01/01/2025 | 31/12/2025 |

---

## 🧰 Tecnologias Utilizadas

- **FastAPI** – Framework backend  
- **Docker** – Containerização  
- **PostgreSQL** – Banco relacional para jobs  
- **MongoDB** – Banco NoSQL para logs  
- **LDAP (porta 389)** – Comunicação com Active Directory  

---

## 🧑‍💻 Autor

**Breno Rodrigues de Farias**  
[GitHub](https://github.com/BRNFarias)

---
