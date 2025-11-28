# Automação Active Directory – (API + Observabilidade)

Sistema completo para automatizar a criação e gerenciamento de usuários no **Active Directory**, com API em FastAPI, monitoramento via Grafana/Loki, bancos PostgreSQL e MongoDB, além de um front-end simples para interação.

Tudo containerizado com Docker e pronto para rodar.

---

## Tecnologias Utilizadas

### **Back-End**
- FastAPI
- LDAP3 (integração AD)
- PostgreSQL
- MongoDB
- Docker & Docker Compose
- Grafana + Loki + Promtail (observabilidade)

# Configuração

## Criar o arquivo `.env`
Crie um arquivo `.env` na raiz do projeto:

```toml
AD_SERVER="IP_DO_SERVIDOR"
AD_USER="DOMINIO\\usuario"
AD_PASSWORD="SuaSenha"
BASE_DN=OU="Usuarios Ativos",DC="empresa",DC="local"
```

Certifique-se de ter o arquivo **ca_cert.cer** na raiz, caso sua infraestrutura de AD exija certificado.

---

# Como subir o ambiente

## Subir containers
```bash
docker-compose up --build -d
```

---

## 🗃️ Criar tabelas no PostgreSQL
```bash
docker exec active-automation python create_tables.py
```

---

# Endpoints importantes

- **Swagger:** http://localhost:8000/docs  
- **Grafana:** http://localhost:3000

---

# Acesso aos bancos (debug)

## PostgreSQL
```bash
docker exec -it postgres-db psql -U admin -d ad_jobs
```

## MongoDB
```bash
docker exec -it mongo-db mongosh -u admin -p admin
```

---

# Formato da planilha para upload

| Nome            | CPF              | Inicio      | Fim         |
|----------------|------------------|-------------|-------------|
| Fulano da Silva | 123.456.789-00   | 2025-01-01 | 2025-12-31 |

A planilha deve estar no formato **XLSX**.

---

# Comandos úteis

```bash
docker-compose ps
docker-compose logs -f api
docker-compose down
docker-compose up -d
```

---

# Estrutura do Projeto

```
ACTIVE-DIRECTORY-AUTOMATION/
├── create_tables.py
├── docker-compose.yaml
├── Dockerfile
├── loki-config.yaml
├── mongo-init.js
├── promtail-config.yaml
├── requirements.txt
│
├── app/
│   ├── main.py
│   ├── database/
│   ├── models/
│   ├── routes/
│   └── services/
│
└── Front-End-Active-Automation/
    ├── index.html
    ├── cadastro.html
    ├── novo-usuario.html
    ├── arquivo.html
    ├── css/
    ├── js/
    └── assets/
```

---

# Licença
Desenvolvido para automação de processos internos via Active Directory.

---

#  Autor
**Breno Rodrigues de Farias**

