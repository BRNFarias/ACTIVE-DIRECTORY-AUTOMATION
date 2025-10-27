from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
from ldap3.constants import SEARCH_SCOPE_WHOLE_SUBTREE # <-- ESTA É A CORREÇÃO
from ldap3.core.exceptions import LDAPException
from datetime import datetime

# --- CONFIGURAÇÃO (igual a antes) ---
AD_SERVER = "172.16.58.43" # IP DO WINDOWS Server
AD_PASSWORD = "Senai@134"
AD_USER = "SKYNEX\\breno" # Usuario com permissao
BASE_DN = "OU=Usuarios Ativos,DC=skynex,DC=local" # Onde os utilizadores serão criados

def connect_ad():
    try:
        ad_server = Server(AD_SERVER, get_info=ALL)
        conn = Connection(ad_server, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
        return conn
    except LDAPException as e:
        print(f"Erro detalhado ao conectar ao AD (SIMPLE): {e}")
        return None

# --- FUNÇÃO AUXILIAR PARA A DATA DE EXPIRAÇÃO ---
def _datetime_to_ldap_timestamp(dt: datetime) -> str:
    epoch_as_filetime = 116444736000000000
    filetime = int(dt.timestamp() * 10000000) + epoch_as_filetime
    return str(filetime)

# --- FUNÇÃO PRINCIPAL ATUALIZADA ---
def create_or_update_user(conn, nome, username, password, fim_date: datetime):
    
    expiration_timestamp = _datetime_to_ldap_timestamp(fim_date)

    nome_parts = nome.split()
    givenName = nome_parts[0]
    sn = " ".join(nome_parts[1:]) if len(nome_parts) > 1 else nome_parts[0]

    # 1. Verifica se o usuário (pelo CPF/username) já existe
    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SEARCH_SCOPE_WHOLE_SUBTREE,
                attributes=['dn'])

    # 2. SE O USUÁRIO JÁ EXISTE (LÓGICA DE REATIVAÇÃO)
    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn
        print(f"\n--- USUÁRIO EXISTENTE ENCONTRADO (Reativando) ---")
        
        changes = {
            'accountExpires': [(MODIFY_REPLACE, [expiration_timestamp])], 
            'userAccountControl': [(MODIFY_REPLACE, [512])], 
            'displayName': [(MODIFY_REPLACE, [nome])], 
            'givenName': [(MODIFY_REPLACE, [givenName])], 
            'sn': [(MODIFY_REPLACE, [sn])]
        }

        try:
            conn.modify(user_dn, changes)
            
            print("  ... Redefinindo senha (forçando troca no login)...")
            conn.extend.microsoft.modify_password(user_dn, password, must_change_password=True)
            
            print(f"Usuario {nome} reativado e atualizado com sucesso!")
            return True
        except LDAPException as e:
             try:
                 print("  ... Falha na modificação, tentando renomear CN...")
                 conn.modify_dn(user_dn, f'CN={nome}')
                 conn.modify(f"CN={nome},{BASE_DN}", changes)
                 conn.extend.microsoft.modify_password(f"CN={nome},{BASE_DN}", password, must_change_password=True)
                 print(f"Usuario {nome} reativado e RENOMEADO com sucesso!")
                 return True
             except Exception as ex:
                 print(f"Erro ao reativar/atualizar usuario {nome}: {ex}")
                 return False

    # 3. SE O USUÁRIO NÃO EXISTE (LÓGICA DE CRIAÇÃO)
    else:
        dn = f"CN={nome},{BASE_DN}" 
                
        attributes = {
            "givenName": givenName,
            "sn": sn,
            "userPrincipalName": f"{username}@dominio.com.br",
            "sAMAccountName": username,
            "displayName": nome,
            "accountExpires": expiration_timestamp, 
            "userAccountControl": 514 # Cria como Desabilitado (512 + 2)
        }

        try:
            print("\n--- INICIANDO CREATE_USER (Novo) ---")
            
            # Etapa 1: Adiciona o usuário (desabilitado)
            conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
            
            # Etapa 2: Define Senha
            print("  ... Definindo senha (forçando troca no login)...")
            conn.extend.microsoft.modify_password(dn, password, must_change_password=True)
            
            # Etapa 3: Habilita a conta
            print("  ... Habilitando conta...")
            conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [512])]})
            
            print(f"Usuario {nome} criado com sucesso!")
            return True
        except LDAPException as e:
            print(f"Erro ao criar usuario: {e}")
            return False

# Deletar usuario no AD
def delete_user(conn, username):
    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SEARCH_SCOPE_WHOLE_SUBTREE,
                attributes=['dn'])
    
    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn
        try:
            conn.delete(user_dn)
            print(f"Usuario {username} deletado com sucesso!")
        except LDAPException as e:
            print(f"Erro ao deletar usuario: {e}")
    else:
        print(f"Erro: Usuário {username} não encontrado para deleção.")