from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE, SUBTREE
from ldap3.core.exceptions import LDAPException
from datetime import datetime, timedelta
import ldap3
import ssl
import os
from dotenv import load_dotenv

# --- Correção do MD4 ---
ldap3.HASH_MD4_NOT_SUPPORTED = True

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO (Via Variáveis de Ambiente) ---
AD_SERVER = os.getenv("AD_SERVER")
AD_PASSWORD = os.getenv("AD_PASSWORD")
AD_USER = os.getenv("AD_USER")
BASE_DN = os.getenv("BASE_DN")

if not all([AD_SERVER, AD_PASSWORD, AD_USER, BASE_DN]):
    raise ValueError("Faltam variáveis de ambiente do AD (AD_SERVER, AD_PASSWORD, etc). Verifique o arquivo .env.")

DOMAIN_BASE_DN = BASE_DN.split(',', 1)[-1] 

# --- FUNÇÕES AUXILIARES DE DATA ---
def _datetime_to_ldap_timestamp(dt: datetime) -> str:
    """Converte datetime Python para FileTime do AD (Integer)"""
    epoch_as_filetime = 116444736000000000
    filetime = int(dt.timestamp() * 10000000) + epoch_as_filetime
    return str(filetime)

def _ad_filetime_to_datetime(filetime_val):
    """Converte FileTime do AD (Integer ou Datetime) para datetime Python"""
    if isinstance(filetime_val, datetime):
        return filetime_val.replace(tzinfo=None) 
    try:
        val = int(filetime_val)
        if val == 0 or val == 9223372036854775807:
            return None 
        return datetime.utcfromtimestamp((val - 116444736000000000) / 10000000)
    except Exception:
        return None

def connect_ad():
    """ Conecta-se ao AD com LDAPS (preferencial) ou SIMPLE. """
    try:
        ad_server = Server(AD_SERVER, get_info=ALL, use_ssl=True, port=636)
        conn = Connection(ad_server, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
        print("Conexão AD (LDAPS) bem-sucedida.")
        return conn
    except LDAPException:
        try:
            print("LDAPS falhou, tentando conexão não segura (389)...")
            ad_server_simple = Server(AD_SERVER, get_info=ALL, port=389)
            conn_simple = Connection(ad_server_simple, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
            print("Conexão AD (SIMPLE) bem-sucedida.")
            return conn_simple
        except LDAPException as e:
            print(f"Erro fatal na conexão AD: {e}")
            return None

# --- FUNÇÃO 1: LOGIN ---
def check_user_credentials(user_email, user_password):
    if not user_password:
        return None

    user_upn = user_email
    if "@" not in user_email:
        domain_suffix = DOMAIN_BASE_DN.replace('DC=', '').replace(',', '.')
        user_upn = f"{user_email}@{domain_suffix}"
    
    try:
        conn = Connection(
            Server(AD_SERVER, get_info=ALL, use_ssl=True, port=636),
            user=user_upn, password=user_password, authentication="SIMPLE", auto_bind=True
        )
    except LDAPException:
        try:
            domain = AD_USER.split('\\')[0] 
            username_part = user_email.split('@')[0] if "@" in user_email else user_email
            ntlm_user = f"{domain}\\{username_part}"
            conn = Connection(Server(AD_SERVER, get_info=ALL, port=389), user=ntlm_user, password=user_password, authentication=NTLM, auto_bind=True)
        except LDAPException:
            return None

    try:
        search_filter = f'(&(objectClass=user)(userPrincipalName={user_upn}))'
        conn.search(search_base=DOMAIN_BASE_DN, search_filter=search_filter, search_scope=SUBTREE, attributes=['displayName', 'sAMAccountName', 'userPrincipalName'])
        
        if not conn.entries:
             conn.search(search_base=DOMAIN_BASE_DN, search_filter=f'(&(objectClass=user)(sAMAccountName={user_email.split("@")[0]}))', search_scope=SUBTREE, attributes=['displayName', 'userPrincipalName', 'sAMAccountName'])
        
        if conn.entries:
            user_entry = conn.entries[0]
            return {
                "nome": str(user_entry.displayName),
                "email": str(user_entry.userPrincipalName) if 'userPrincipalName' in user_entry else user_upn,
                "cpf": str(user_entry.sAMAccountName)
            }
    except Exception:
        pass
    return {"nome": user_email, "email": user_upn, "cpf": user_email.split('@')[0]}

# --- FUNÇÃO 2: LISTAR UTILIZADORES ---
def list_users(conn):
    try:
        conn.search(search_base=BASE_DN,
                    search_filter='(objectClass=user)',
                    search_scope=SUBTREE,
                    attributes=['sAMAccountName', 'displayName', 'userAccountControl', 'accountExpires'])
        users = []
        now = datetime.utcnow()
        
        for entry in conn.entries:
            uac = int(entry.userAccountControl.value)
            expire_val = entry.accountExpires.value if 'accountExpires' in entry else 0
            
            if uac & 2:
                status = "Inativo"
            else:
                expire_dt = _ad_filetime_to_datetime(expire_val)
                if expire_dt and expire_dt < now:
                    status = "Expirado" 
                else:
                    status = "Ativo"
            
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
    expiration_timestamp = _datetime_to_ldap_timestamp(fim_date)
    nome_parts = nome.split()
    givenName = nome_parts[0]
    sn = " ".join(nome_parts[1:]) if len(nome_parts) > 1 else nome_parts[0]

    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE) 

    if len(conn.entries) > 0:
        # CORREÇÃO AQUI: Usar entry_dn em vez de dn
        user_dn = conn.entries[0].entry_dn 
        print(f"--- REATIVANDO/ATUALIZANDO USUÁRIO: {username} ---")
        
        changes = {
            'accountExpires': [(MODIFY_REPLACE, [expiration_timestamp])],
            'displayName': [(MODIFY_REPLACE, [nome])], 
            'givenName': [(MODIFY_REPLACE, [givenName])], 
            'sn': [(MODIFY_REPLACE, [sn])],
            'userAccountControl': [(MODIFY_REPLACE, ['512'])] 
        }
        
        try:
            conn.modify(user_dn, changes)
            return True
        except LDAPException as e:
            print(f"Exceção ao reativar usuário: {e}")
            return False

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
            "userAccountControl": 514
        }

        try:
            conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
            conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [f'"{password}"'.encode('utf-16-le')])]})
            conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, ['512'])]}) 
            return True
        except LDAPException as e:
            print(f"Erro na criação: {e}")
            return False

# --- FUNÇÃO 4: ROTINA DE LIMPEZA ---
def disable_expired_users_routine():
    conn = connect_ad()
    if not conn:
        return "Erro de conexão com o AD"

    print("\n--- INICIANDO ROTINA DE LIMPEZA ---")
    search_filter = '(&(objectClass=user)(accountExpires=*)(!(accountExpires=0))(!(accountExpires=9223372036854775807)))'
    
    try:
        conn.search(search_base=BASE_DN,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['sAMAccountName', 'accountExpires', 'userAccountControl'])
        
        count_disable = 0
        now = datetime.utcnow()
        users_disabled = []
        
        for entry in conn.entries:
            username = str(entry.sAMAccountName)
            expire_dt = _ad_filetime_to_datetime(entry.accountExpires.value)
            
            if not expire_dt:
                continue

            if expire_dt < now:
                current_uac = int(entry.userAccountControl.value)
                if not (current_uac & 2):
                    print(f"-> DESABILITANDO {username}...")
                    new_uac = current_uac | 2 
                    
                    try:
                        # CORREÇÃO AQUI: Usar entry_dn em vez de dn
                        conn.modify(entry.entry_dn, {'userAccountControl': [(MODIFY_REPLACE, [str(new_uac)])]})
                        if conn.result['description'] == 'success':
                            count_disable += 1
                            users_disabled.append(username)
                        else:
                            print(f"Erro AD: {conn.result}")
                    except Exception as e:
                        print(f"Erro ao desabilitar: {e}")

        conn.unbind()
        
        if count_disable > 0:
            return f"Sucesso. Usuários desabilitados: {', '.join(users_disabled)}"
        else:
            return "Nenhum usuário precisou ser desabilitado."

    except Exception as e:
        print(f"Erro na rotina: {e}")
        return f"Erro: {e}"