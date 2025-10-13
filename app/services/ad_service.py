from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException


# configuração do AD
AD_SERVER = "172.16.58." # IP DO WINDOWS Server
AD_USER = "XUPISCO\\Administrador" # Usuario com permissao
AD_PASSWORD = "Senai@134"
BASE_DN = "DC=xupisco,DC=com,DC=br" # Base do dominio

def connect_ad():
    try:
        Server = Server(AD_SERVER, get_info=ALL)
        conn = Connection(Server, user=AD_USER, password=AD_PASSWORD, authentication=NTLM, auto_bind=True)
        return conn
    except LDAPException as e:
        print(f"Erro ao conectar ao AD: {e}")
        return None

 # Criar Usuario no AD   

def create_user(conn, nome, username, password):
    dn = f"CN={nome}, {BASE_DN}" 
    attributes = {
        "givenName": nome.split()[0],
        "sn": nome.split()[-1],
        "userPrincipalName": f"{username}@dominio.com.br",
        "sAMAccountName": username,
        "displayName": nome,
        "accountExpires": 0,
        "userAccountControl": 512 # Conta Habilitada
    }

    try:
        conn.add(dn, ['top', 'person', 'organizationalPerson', 'user'], attributes)
        # Define Senha
        conn.extend.microsoft.modify_password(dn, password)
        # Habilita conta
        conn.modify(dn, {'userAccontControl': [(MODIFY_REPLACE, [512])]})
        print(f"Usuario {nome} criado com sucesso!")
    except LDAPException as e:
        print(f"Erro ao criar usuario: {e}")

# Deletar usuario no AD

def delete_user(conn, username):
    dn = f"CN={username}, {BASE_DN}"
    try:
        conn.delete(dn)
        print(f"Usuario {username} deletado com sucesso!")
    except LDAPException as e:
        print(f"Erro ao deletar usuario: {e}")


 