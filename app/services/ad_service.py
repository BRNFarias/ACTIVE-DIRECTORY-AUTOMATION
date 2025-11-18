from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE, SUBTREE
from ldap3.core.exceptions import LDAPException
from datetime import datetime
import ldap3
import ssl

# --- Correção do MD4 ---
ldap3.HASH_MD4_NOT_SUPPORTED = True

# --- CONFIGURAÇÃO (Restaurada para a máquina atual) ---
AD_SERVER = "172.16.58.43"
AD_PASSWORD = "Senai@134"
AD_USER = "SKYNEX\\breno"
BASE_DN = "OU=Usuarios Ativos,DC=skynex,DC=local"
DOMAIN_BASE_DN = BASE_DN.split(',', 1)[-1] 

def connect_ad():
    """ Conecta-se ao AD com LDAPS (preferencial) ou SIMPLE. """
    try:
        # Tenta LDAPS (Porta 636)
        ad_server = Server(AD_SERVER, get_info=ALL, use_ssl=True, port=636)
        conn = Connection(ad_server, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
        print("Conexão AD (LDAPS) bem-sucedida.")
        return conn
    except LDAPException:
        try:
            # Fallback para SIMPLE (Porta 389)
            print("LDAPS falhou, tentando conexão não segura (389)...")
            ad_server_simple = Server(AD_SERVER, get_info=ALL, port=389)
            conn_simple = Connection(ad_server_simple, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
            print("Conexão AD (SIMPLE) bem-sucedida.")
            return conn_simple
        except LDAPException as e:
            print(f"Erro fatal na conexão AD: {e}")
            return None

def _datetime_to_ldap_timestamp(dt: datetime) -> str:
    epoch_as_filetime = 116444736000000000
    filetime = int(dt.timestamp() * 10000000) + epoch_as_filetime
    return str(filetime)

# --- FUNÇÃO 1: LOGIN ---
def check_user_credentials(user_email, user_password):
    if not user_password:
        return None

    user_upn = user_email
    if "@" not in user_email:
        domain_suffix = DOMAIN_BASE_DN.replace('DC=', '').replace(',', '.')
        user_upn = f"{user_email}@{domain_suffix}"
    
    try:
        print(f"Tentando login SIMPLE para {user_upn}...")
        conn = Connection(
            Server(AD_SERVER, get_info=ALL, use_ssl=True, port=636),
            user=user_upn, 
            password=user_password, 
            authentication="SIMPLE", 
            auto_bind=True
        )
        print("Login SIMPLE (LDAPS) bem-sucedido.")
    except LDAPException:
        try:
            domain = AD_USER.split('\\')[0] 
            username_part = user_email.split('@')[0]
            if "@" not in user_email:
                username_part = user_email
            ntlm_user = f"{domain}\\{username_part}"
            
            print(f"Tentando NTLM para {ntlm_user}...")
            conn = Connection(
                Server(AD_SERVER, get_info=ALL, port=389), 
                user=ntlm_user,  
                password=user_password, 
                authentication=NTLM, 
                auto_bind=True
            )
            print("Login NTLM (Porta 389) bem-sucedido.")
        except LDAPException as e_ntlm:
            print(f"Falha login: {e_ntlm}")
            return None

    try:
        search_filter = f'(&(objectClass=user)(userPrincipalName={user_upn}))'
        conn.search(search_base=DOMAIN_BASE_DN, search_filter=search_filter, search_scope=SUBTREE, attributes=['displayName', 'sAMAccountName', 'userPrincipalName'])
        
        if not conn.entries:
             conn.search(search_base=DOMAIN_BASE_DN, search_filter=f'(&(objectClass=user)(sAMAccountName={user_email.split("@")[0]}))', search_scope=SUBTREE, attributes=['displayName', 'userPrincipalName', 'sAMAccountName'])
             if not conn.entries:
                return {"nome": user_email, "email": user_upn, "cpf": user_email.split('@')[0]}
        
        user_entry = conn.entries[0]
        return {
            "nome": str(user_entry.displayName),
            "email": str(user_entry.userPrincipalName) if 'userPrincipalName' in user_entry else user_upn,
            "cpf": str(user_entry.sAMAccountName)
        }
    except Exception:
        return {"nome": user_email, "email": user_upn, "cpf": user_email.split('@')[0]}


# --- FUNÇÃO 2: LISTAR UTILIZADORES ---
def list_users(conn):
    try:
        conn.search(search_base=BASE_DN,
                    search_filter='(objectClass=user)',
                    search_scope=SUBTREE,
                    attributes=['sAMAccountName', 'displayName', 'userAccountControl'])
        users = []
        for entry in conn.entries:
            uac = int(entry.userAccountControl.value)
            status = "Inativo" if (uac & 2) else "Ativo"
            users.append({
                "nome": str(entry.displayName),
                "cpf": str(entry.sAMAccountName),
                "status": status
            })
        return users
    except LDAPException as e:
        print(f"Erro ao listar usuários: {e}")
        return []

# --- FUNÇÃO 3: CRIAR OU REATIVAR ---
def create_or_reactivate_user(conn, nome, username, password, fim_date: datetime):
    """
    Se o usuário não existe -> Cria.
    Se o usuário existe -> Atualiza a data de fim e Reativa (Unlock/Enable).
    """
    expiration_timestamp = _datetime_to_ldap_timestamp(fim_date)
    nome_parts = nome.split()
    givenName = nome_parts[0]
    sn = " ".join(nome_parts[1:]) if len(nome_parts) > 1 else nome_parts[0]

    # 1. Verifica se o usuário já existe
    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE) 

    # === CENÁRIO 1: USUÁRIO EXISTE (RENOVAÇÃO/REATIVAÇÃO) ===
    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn 
        print(f"--- REATIVANDO USUÁRIO: {username} ---")
        
        changes = {
            # Atualiza validade
            'accountExpires': [(MODIFY_REPLACE, [expiration_timestamp])],
            # Garante nome atualizado
            'displayName': [(MODIFY_REPLACE, [nome])], 
            'givenName': [(MODIFY_REPLACE, [givenName])], 
            'sn': [(MODIFY_REPLACE, [sn])],
            # ATIVA A CONTA (512)
            'userAccountControl': [(MODIFY_REPLACE, ['512'])]
        }
        
        try:
            conn.modify(user_dn, changes)
            if conn.result['description'] == 'success':
                print(f"Sucesso: Usuário {username} reativado até {fim_date}.")
                return True
            else:
                print(f"Erro AD ao reativar: {conn.result}")
                return False
        except LDAPException as e:
            print(f"Exceção ao reativar usuário: {e}")
            return False

    # === CENÁRIO 2: NOVO USUÁRIO (CRIAÇÃO) ===
    else:
        print(f"--- CRIANDO NOVO USUÁRIO: {username} ---")
        dn = f"CN={nome},{BASE_DN}" 
        upn = f"{username}@{DOMAIN_BASE_DN.replace('DC=', '').replace(',', '.')}"
        
        attributes = {
            "givenName": givenName,
            "sn": sn,
            "userPrincipalName": upn,
            "sAMAccountName": username,
            "displayName": nome,
            "accountExpires": expiration_timestamp, 
            "userAccountControl": 514 # Cria desabilitado inicialmente
        }

        try:
            # Etapa 1: Criar
            conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
            
            # Etapa 2: Senha
            conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [f'"{password}"'.encode('utf-16-le')])]})
            
            # Etapa 3: Ativar
            conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, ['512'])]})
            
            print(f"Sucesso: Usuário {username} criado.")
            return True
            
        except LDAPException as e:
            print(f"Erro na criação: {e}")
            return False