from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException
from datetime import datetime
import ldap3
import ssl # Precisamos disto para as constantes de protocolo, mas não para o validate=NONE

# --- Correção do MD4 (para o Login NTLM funcionar) ---
ldap3.HASH_MD4_NOT_SUPPORTED = True

# --- CONFIGURAÇÃO ---
AD_SERVER = "172.16.58.43" # IP DO WINDOWS Server
AD_PASSWORD = "Senai@134"
AD_USER = "SKYNEX\\breno" # Usuario com permissao
BASE_DN = "OU=Usuarios Ativos,DC=skynex,DC=local" # Onde os utilizadores serão criados
# Pega a raiz do domínio (ex: DC=skynex,DC=local) para pesquisas globais
DOMAIN_BASE_DN = BASE_DN.split(',', 1)[-1] 

def connect_ad():
    """ 
    Conecta-se ao AD com LDAPS (Porta 636), validando o certificado 
    contra o trust store do sistema (que agora inclui o nosso CA).
    """
    try:
        # --- VERSÃO DE PRODUÇÃO ---
        # Já não precisamos do Tls(validate=ssl.CERT_NONE).
        # O ldap3 irá validar o certificado (comportamento padrão),
        # e encontrará o nosso 'ca_cert.cer' que instalámos no Dockerfile.
        ad_server = Server(
            AD_SERVER, 
            get_info=ALL, 
            use_ssl=True, 
            port=636
            # O parâmetro 'tls=' foi removido
        )
        
        conn = Connection(ad_server, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
        print("Conexão AD (LDAPS - Porta 636) bem-sucedida. (Certificado validado!)")
        return conn
        
    except LDAPException as e:
        print(f"Erro detalhado ao conectar ao AD (LDAPS - Porta 636): {e}")
        # Fallback para porta 389 (LDAP simples) se o LDAPS falhar
        print("Tentando conexão alternativa (SIMPLE - Porta 389)...")
        try:
            ad_server_simple = Server(AD_SERVER, get_info=ALL, port=389)
            conn_simple = Connection(ad_server_simple, user=AD_USER, password=AD_PASSWORD, authentication="SIMPLE", auto_bind=True)
            print("Conexão AD (SIMPLE) bem-sucedida. Aviso: Ativação de usuário pode falhar se o AD exigir SSL.")
            return conn_simple
        except LDAPException as e_simple:
            print(f"Erro detalhado ao conectar ao AD (SIMPLE): {e_simple}")
            return None

# --- FUNÇÃO AUXILIAR PARA A DATA DE EXPIRAÇÃO ---
def _datetime_to_ldap_timestamp(dt: datetime) -> str:
    """ Converte um objeto datetime do Python para o formato FILETIME do AD. """
    epoch_as_filetime = 116444736000000000
    filetime = int(dt.timestamp() * 10000000) + epoch_as_filetime
    return str(filetime)

# --- FUNÇÃO 1: LOGIN (Para o Front-end) ---
def check_user_credentials(user_email, user_password):
    """ Tenta autenticar um usuário no AD (SIMPLE ou NTLM). """
    if not user_password:
        return None

    conn = None
    auth_method = None
    
    user_upn = user_email
    
    if "@" not in user_email:
        domain_suffix = DOMAIN_BASE_DN.replace('DC=', '').replace(',', '.')
        user_upn = f"{user_email}@{domain_suffix}"
    
    try:
        # Tenta LDAPS primeiro (Produção)
        print(f"Tentando login SIMPLE para {user_upn}...")
        conn = Connection(
            Server(AD_SERVER, get_info=ALL, use_ssl=True, port=636), # Sem 'tls=' 
            user=user_upn, 
            password=user_password, 
            authentication="SIMPLE", 
            auto_bind=True
        )
        auth_method = "SIMPLE (LDAPS)"
        print("Login SIMPLE (LDAPS) bem-sucedido. (Certificado validado!)")
        
    except LDAPException as e_simple_ssl:
        print(f"LDAPS falhou ({e_simple_ssl}), tentando NTLM (Porta 389)...")
        try:
            # Fallback para NTLM
            conn_ntlm = Connection(
                Server(AD_SERVER, get_info=ALL, port=389), 
                user=user_upn, 
                password=user_password, 
                authentication=NTLM, 
                auto_bind=True
            )
            auth_method = "NTLM (Porta 389)"
            print("Login NTLM (Porta 389) bem-sucedido.")
            conn = conn_ntlm # Define o 'conn' para ser usado na busca de detalhes
        except LDAPException as e_ntlm:
            print(f"Falha na tentativa de login (LDAPS e NTLM) para {user_email}: {e_ntlm}")
            return None

    # Se o login funcionou (por LDAPS ou NTLM), busca os detalhes
    try:
        search_filter = f'(&(objectClass=user)(userPrincipalName={user_upn}))'
        
        conn.search(search_base=DOMAIN_BASE_DN, 
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['displayName', 'sAMAccountName', 'userPrincipalName'])
        
        if not conn.entries:
             conn.search(search_base=DOMAIN_BASE_DN, 
                    search_filter=f'(&(objectClass=user)(sAMAccountName={user_email.split("@")[0]}))',
                    search_scope=SUBTREE,
                    attributes=['displayName', 'userPrincipalName', 'sAMAccountName'])
             if not conn.entries:
                print(f"Login bem-sucedido ({auth_method}) para {user_email}, mas não foi possível encontrar os detalhes da conta.")
                return {"nome": user_email, "email": user_upn, "cpf": user_email.split('@')[0]}
        
        user_entry = conn.entries[0]
        
        return {
            "nome": str(user_entry.displayName),
            "email": str(user_entry.userPrincipalName) if 'userPrincipalName' in user_entry else user_upn,
            "cpf": str(user_entry.sAMAccountName)
        }
    except Exception as e_search:
        print(f"Erro ao buscar detalhes do usuário após login: {e_search}")
        return {"nome": user_email, "email": user_upn, "cpf": user_email.split('@')[0]}


# --- FUNÇÃO 2: LISTAR UTILIZADORES (Para o Front-end) ---
def list_users(conn):
    """ Lista os usuários da OU base, retornando nome, cpf e status. """
    try:
        conn.search(search_base=BASE_DN,
                    search_filter='(objectClass=user)',
                    search_scope=SUBTREE,
                    attributes=['sAMAccountName', 'displayName', 'userAccountControl'])
        
        users = []
        for entry in conn.entries:
            uac = int(entry.userAccountControl.value)
            # 2 significa "Conta Desativada"
            status = "Inativo" if (uac & 2) else "Ativo" 
            
            users.append({
                "nome": str(entry.displayName),
                "cpf": str(entry.sAMAccountName),
                "status": status
            })
        print(f"Encontrados {len(users)} usuários.")
        return users
    except LDAPException as e:
        print(f"Erro ao listar usuários: {e}")
        return []

# --- FUNÇÃO 3: CRIAR/ATUALIZAR (Lógica "Ativado") ---
def create_or_update_user(conn, nome, username, password, fim_date: datetime):
    
    expiration_timestamp = _datetime_to_ldap_timestamp(fim_date)
    nome_parts = nome.split()
    givenName = nome_parts[0]
    sn = " ".join(nome_parts[1:]) if len(nome_parts) > 1 else nome_parts[0]

    # Remove o 'attributes=[]' para que possamos ler o 'dn'
    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE) 

    # SE O USUÁRIO JÁ EXISTE (LÓGICA DE REATIVAÇÃO / ATIVAÇÃO)
    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn 
        print(f"\n--- USUÁRIO EXISTENTE ENCONTRADO (Atualizando e Ativando) ---")
        
        changes = {
            'accountExpires': [(MODIFY_REPLACE, [expiration_timestamp])], 
            'displayName': [(MODIFY_REPLACE, [nome])], 
            'givenName': [(MODIFY_REPLACE, [givenName])], 
            'sn': [(MODIFY_REPLACE, [sn])]
        }
        
        try:
            print("  Etapa 1: Aplicando modificações (dados e data de expiração)...")
            conn.modify(user_dn, changes)
            if not conn.result['description'] == 'success':
                raise LDAPException(f"Falha na Etapa 1 (conn.modify dados): {conn.result}")

            # Etapa 2: Definir/Resetar a senha (Necessário para ativar)
            # Isto SÓ FUNCIONA se a 'conn' for LDAPS (Porta 636)
            print(f"  Etapa 2: Redefinindo senha para {nome}...")
            conn.modify(user_dn, {'unicodePwd': [(MODIFY_REPLACE, [f'"{password}"'.encode('utf-16-le')])]})
            if not conn.result['description'] == 'success':
                 print(f"  Aviso: Falha ao redefinir senha (Etapa 2): {conn.result}. Continuando para ativar...")
                 # Mesmo que a senha falhe (ex: por não ser LDAPS), tenta ativar

            # Etapa 3: Ativar o usuário (muda para 512 - Conta Normal Ativa)
            print(f"  Etapa 3: Ativando conta {nome}...")
            conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, ['512'])]})
            if not conn.result['description'] == 'success':
                raise LDAPException(f"Falha na Etapa 3 (conn.modify UAC): {conn.result}")

            print(f"Usuario {nome} atualizado e ATIVADO com sucesso!")
            return True
            
        except LDAPException as e:
             try:
                 print(f"  ... Falha na modificação ({e}), tentando renomear CN...")
                 conn.modify_dn(user_dn, f'CN={nome}')
                 # Reaplica tudo no novo DN
                 novo_dn = f"CN={nome},{BASE_DN}"
                 conn.modify(novo_dn, changes)
                 conn.modify(novo_dn, {'unicodePwd': [(MODIFY_REPLACE, [f'"{password}"'.encode('utf-16-le')])]})
                 conn.modify(novo_dn, {'userAccountControl': [(MODIFY_REPLACE, ['512'])]})
                 print(f"Usuario {nome} atualizado, RENOMEADO e ATIVADO com sucesso!")
                 return True
             except Exception as ex:
                 print(f"Erro ao reativar/atualizar usuario {nome}: {ex}")
                 return False

    # SE O USUÁRIO NÃO EXISTE (LÓGICA DE CRIAÇÃO)
    else:
        dn = f"CN={nome},{BASE_DN}" 
        # Define um UPN (User Principal Name) - Padrão comum
        upn = f"{username}@{DOMAIN_BASE_DN.replace('DC=', '').replace(',', '.')}"
        
        attributes = {
            "givenName": givenName,
            "sn": sn,
            "userPrincipalName": upn,
            "sAMAccountName": username,
            "displayName": nome,
            "accountExpires": expiration_timestamp, 
            "userAccountControl": 514 # 1. Cria como Desabilitado (512 + 2)
        }

        try:
            print("\n--- INICIANDO CREATE_USER (Novo) ---")
            
            # Etapa 1: Adiciona o usuário (desabilitado)
            print(f"  Etapa 1: Adicionando DN '{dn}'...")
            conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
            if not conn.result['description'] == 'success':
                raise LDAPException(f"Falha na Etapa 1 (conn.add): {conn.result}")
            
            # Etapa 2: Definir a senha (SÓ FUNCIONA se 'conn' for LDAPS)
            print(f"  Etapa 2: Definindo senha para {nome}...")
            conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [f'"{password}"'.encode('utf-16-le')])]})
            if not conn.result['description'] == 'success':
                # Se a senha falhar (ex: complexidade ou não for LDAPS), o usuário ficará desativado
                raise LDAPException(f"Falha ao definir senha (Etapa 2): {conn.result}. O usuário foi criado DESATIVADO.")

            # Etapa 3: Ativar o usuário (muda UAC de 514 para 512)
            print(f"  Etapa 3: Ativando conta {nome}...")
            conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, ['512'])]})
            if not conn.result['description'] == 'success':
                raise LDAPException(f"Falha na Etapa 3 (conn.modify UAC): {conn.result}")

            print(f"Usuario {nome} criado e ATIVADO com sucesso!")
            return True
            
        except LDAPException as e:
            print(f"Erro ao criar/ativar usuario: {e}")
            # Se falhou, tenta apagar o usuário fantasma que pode ter sido criado
            try:
                conn.delete(dn)
                print("  ... Usuário 'fantasma' removido.")
            except:
                pass # Ignora falha na limpeza
            return False

# --- FUNÇÃO 4: DELETAR (Para o Front-end) ---
def delete_user(conn, username):
    """ Deleta um usuário pelo sAMAccountName (username/cpf). """
    # Remove o 'attributes=[]' para que possamos ler o 'dn'
    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE) 
    
    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn
        try:
            conn.delete(user_dn)
            print(f"Usuario {username} deletado com sucesso!")
            return True
        except LDAPException as e:
            print(f"Erro ao deletar usuario: {e}")
            return False
    else:
        print(f"Erro: Usuário {username} não encontrado para deleção.")
        return False