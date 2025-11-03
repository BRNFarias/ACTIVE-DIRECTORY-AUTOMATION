from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE, SUBTREE
from ldap3.core.exceptions import LDAPException
from datetime import datetime

# --- CONFIGURAÇÃO (igual a antes) ---
AD_SERVER = "172.16.58.43" # IP DO WINDOWS Server
AD_PASSWORD = "Senai@134"
AD_USER = "SKYNEX\\breno" # Usuario com permissao
BASE_DN = "OU=Usuarios Ativos,DC=skynex,DC=local" 

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

# --- NOVA FUNÇÃO ---
def list_users(conn):
    """
    Lista os usuários da OU base, retornando nome, cpf e status.
    """
    try:
        # Procura por 'user' e pede os 3 atributos que precisamos
        conn.search(search_base=BASE_DN,
                    search_filter='(objectClass=user)',
                    search_scope=SUBTREE,
                    attributes=['sAMAccountName', 'displayName', 'userAccountControl'])
        
        users = []
        for entry in conn.entries:
            # O status "Ativo" ou "Inativo" é determinado pelo atributo userAccountControl
            # 2 é a "flag" que significa "Desativado"
            uac = int(entry.userAccountControl.value)
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
        return [] # Retorna lista vazia em caso de erro

# --- FUNÇÃO ATUALIZADA (create_or_update_user) ---
# (Esta função permanece igual à nossa última versão que cria o usuário desativado)
def create_or_update_user(conn, nome, username, password, fim_date: datetime):
    
    expiration_timestamp = _datetime_to_ldap_timestamp(fim_date)
    nome_parts = nome.split()
    givenName = nome_parts[0]
    sn = " ".join(nome_parts[1:]) if len(nome_parts) > 1 else nome_parts[0]

    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE,
                attributes=[]) 

    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn 
        print(f"\n--- USUÁRIO EXISTENTE ENCONTRADO (Atualizando) ---")
        
        changes = {
            'accountExpires': [(MODIFY_REPLACE, [expiration_timestamp])], 
            'displayName': [(MODIFY_REPLACE, [nome])], 
            'givenName': [(MODIFY_REPLACE, [givenName])], 
            'sn': [(MODIFY_REPLACE, [sn])]
        }
        
        try:
            print("  ... Aplicando modificações (dados e data de expiração)...")
            conn.modify(user_dn, changes)
            if not conn.result['description'] == 'success':
                raise LDAPException(f"Falha na Etapa 2 (conn.modify): {conn.result}")
            
            print(f"Usuario {nome} atualizado com sucesso! (Conta permanece desativada)")
            return True
        except LDAPException as e:
             try:
                 print(f"  ... Falha na modificação ({e}), tentando renomear CN...")
                 conn.modify_dn(user_dn, f'CN={nome}')
                 conn.modify(f"CN={nome},{BASE_DN}", changes)
                 print(f"Usuario {nome} atualizado e RENOMEADO com sucesso!")
                 return True
             except Exception as ex:
                 print(f"Erro ao reativar/atualizar usuario {nome}: {ex}")
                 return False
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
            
            print(f"  Etapa 1: Adicionando DN '{dn}'...")
            conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
            if not conn.result['description'] == 'success':
                raise LDAPException(f"Falha na Etapa 1 (conn.add): {conn.result}")
            
            print(f"Usuario {nome} criado com sucesso! (Estado: Desativado)")
            return True
        except LDAPException as e:
            print(f"Erro ao criar usuario: {e}")
            return False

# --- FUNÇÃO ATUALIZADA (delete_user) ---
def delete_user(conn, username):
    conn.search(search_base=BASE_DN,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE, 
                attributes=[]) 
    
    if len(conn.entries) > 0:
        user_dn = conn.entries[0].dn
        try:
            print(f"Tentando deletar DN: {user_dn}")
            conn.delete(user_dn)
            print(f"Usuario {username} deletado com sucesso!")
            return True # <-- MUDANÇA: Retorna sucesso
        except LDAPException as e:
            print(f"Erro ao deletar usuario: {e}")
            return False # <-- MUDANÇA: Retorna falha
    else:
        print(f"Erro: Usuário {username} não encontrado para deleção.")
        return False # <-- MUDANÇA: Retorna falha
    

    # (Mantenha todos os imports e funções existentes no topo...)

# --- ADICIONE ESTA NOVA FUNÇÃO NO FINAL DO FICHEIRO ---

def check_user_credentials(user_email, user_password):
    """
    Tenta autenticar um usuário no AD com as credenciais fornecidas.
    """
    # Se a senha estiver vazia, o bind anônimo pode ter sucesso, o que é errado.
    if not user_password:
        return None

    try:
        # Tenta conectar (bind) como o usuário.
        # O 'user_email' (ex: admin@senai.local) é o UserPrincipalName.
        conn = Connection(
            Server(AD_SERVER, get_info=ALL), 
            user=user_email, 
            password=user_password, 
            authentication="SIMPLE", 
            auto_bind=True
        )
        
        # Se o bind foi bem-sucedido, 'conn' é válido.
        # Agora, buscamos os detalhes desse usuário para retornar ao front-end.
        
        # NOTA: Precisamos de procurar em todo o domínio, não apenas na OU 'Usuarios Ativos'
        # Por isso, mudamos o 'search_base' para a raiz do domínio.
        domain_base_dn = BASE_DN.split(',', 1)[-1] # Pega 'DC=skynex,DC=local'
        
        conn.search(search_base=domain_base_dn, 
                    search_filter=f'(userPrincipalName={user_email})',
                    search_scope=SUBTREE,
                    attributes=['displayName', 'sAMAccountName'])
        
        if not conn.entries:
            # O bind funcionou, mas não encontramos o usuário?
            # Isto pode acontecer se o 'user_email' não for o UserPrincipalName
            # Tenta com o sAMAccountName (ex: 'breno' em vez de 'breno@skynex.local')
             conn.search(search_base=domain_base_dn, 
                    search_filter=f'(sAMAccountName={user_email})',
                    search_scope=SUBTREE,
                    attributes=['displayName', 'userPrincipalName'])
             
             if not conn.entries:
                print(f"Login bem sucedido para {user_email}, mas não foi possível encontrar os detalhes da conta.")
                return None
        
        user_entry = conn.entries[0]
        
        # Retorna os detalhes para o front-end
        return {
            "nome": str(user_entry.displayName),
            "email": str(user_entry.userPrincipalName) if 'userPrincipalName' in user_entry else user_email,
            "cpf": str(user_entry.sAMAccountName)
            # NÃO retorne a senha!
        }

    except LDAPException as e:
        # Se o bind falhar (ex: senha errada), uma exceção LDAP é lançada.
        print(f"Falha na tentativa de login para {user_email}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado no login: {e}")
        return None