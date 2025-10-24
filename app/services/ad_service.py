from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException

# configuração do AD
AD_SERVER = "172.16.58.43" # IP DO WINDOWS Server
AD_PASSWORD = "Senai@134"
AD_USER = "SKYNEX\\breno" # Usuario com permissao
BASE_DN = "OU=Usuarios Ativos,DC=skynex,DC=local" # Apontando para sua OU

def connect_ad():
    try:
        ad_server = Server(AD_SERVER, get_info=ALL)
        conn = Connection(ad_server, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
        return conn
    except LDAPException as e:
        print(f"Erro detalhado ao conectar ao AD (SIMPLE): {e}")
        return None

 # Criar Usuario no AD   

def create_user(conn, nome, username, password):
    
    dn = f"CN={nome},{BASE_DN}" 
    
    nome_parts = nome.split()
    givenName = nome_parts[0]
    sn = " ".join(nome_parts[1:]) if len(nome_parts) > 1 else nome_parts[0]
    
    attributes = {
        "givenName": givenName,
        "sn": sn,
        "userPrincipalName": f"{username}@dominio.com.br",
        "sAMAccountName": username,
        "displayName": nome,
        "accountExpires": 0,
        # --- INÍCIO DA CORREÇÃO ---
        # 1. Criar a conta como HABILITADA (512) + DESABILITADA (2) = 514
        "userAccountControl": 514 
        # --- FIM DA CORREÇÃO ---
    }

    try:
        print("\n--- INICIANDO CREATE_USER ---")
        print(f"  DN (Caminho): '{dn}'")
        print(f"  Atributos (Criando Desabilitado): {attributes}")
        
        # ETAPA 1: Adiciona o usuário (desabilitado)
        conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
        
        # ETAPA 2: Define Senha
        print("  ... Definindo senha...")
        conn.extend.microsoft.modify_password(dn, password)
        
        # --- INÍCIO DA CORREÇÃO ---
        # ETAPA 3: Habilita a conta (define para 512)
        print("  ... Habilitando conta...")
        conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [512])]})
        # --- FIM DA CORREÇÃO ---
        
        print(f"Usuario {nome} criado com sucesso!")
        return True
    except LDAPException as e:
        print(f"Erro ao criar usuario: {e}")
        return False

# Deletar usuario no AD
def delete_user(conn, username):
    dn = f"CN={username},{BASE_DN}"
    try:
        conn.delete(dn)
        print(f"Usuario {username} deletado com sucesso!")
    except LDAPException as e:
        print(f"Erro ao deletar usuario: {e}")
