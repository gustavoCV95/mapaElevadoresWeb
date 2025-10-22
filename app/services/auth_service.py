# app/services/auth_service.py
"""
Serviço de autenticação - VERSÃO CORRIGIDA
"""
from datetime import datetime, timedelta
from flask import current_app, session
from werkzeug.security import check_password_hash
from typing import Tuple
import pytz

class AuthService:
    """Serviço de autenticação"""
    
    @staticmethod
    def authenticate(usuario: str, senha: str, ip_cliente: str) -> Tuple[bool, str]:
        """
        Autentica usuÃ¡rio
        Returns: (sucesso, mensagem)
        """
        from app.utils.auth_helpers import (
            verificar_tentativas_login, 
            registrar_tentativa_login,
            limpar_tentativas_login
        )
        
        # Verifica tentativas
        pode_tentar, bloqueado_ate = verificar_tentativas_login(ip_cliente)
        if not pode_tentar:
            tempo_restante = int((bloqueado_ate - datetime.now()).seconds / 60)
            return False, f'Muitas tentativas. Tente em {tempo_restante} minutos.'
        
        # Valida credenciais
        usuarios_autorizados = current_app.config['USUARIOS_AUTORIZADOS']
        if usuario in usuarios_autorizados:
            if check_password_hash(usuarios_autorizados[usuario], senha):
                # Login bem-sucedido
                limpar_tentativas_login(ip_cliente)
                AuthService.create_session(usuario)
                return True, f'Bem-vindo, {usuario}!'
            else:
                registrar_tentativa_login(ip_cliente)
                return False, 'UsuÃ¡rio ou senha incorretos.'
        else:
            registrar_tentativa_login(ip_cliente)
            return False, 'UsuÃ¡rio ou senha incorretos.'
    
    @staticmethod
    def create_session(usuario: str):
        """Cria sessão do usuÃ¡rio"""
        session['usuario_logado'] = usuario
        session['auth_v2'] = True  # âœ… NOVO: Flag especÃ­fica para v2
        brt = pytz.timezone("America/Sao_Paulo")
        session['login_timestamp'] = datetime.now(brt).isoformat()
        session.permanent = True
        print(f"ðŸ”‘ Sessão criada para {usuario} - auth_v2: {session.get('auth_v2')}")
    
    @staticmethod
    def logout() -> str:
        """Faz logout do usuÃ¡rio"""
        usuario = session.get('usuario_logado', 'UsuÃ¡rio')
        print(f"ðŸšª Logout do usuÃ¡rio: {usuario}")
        session.clear()
        return f'Logout realizado. AtÃ© logo, {usuario}!'
    
    @staticmethod
    def is_authenticated() -> bool:
        """
        Verifica se usuÃ¡rio estÃ¡ autenticado
        âœ… CORRIGIDO: Verificação mais robusta
        """
        # Verifica se tem usuÃ¡rio logado E flag auth_v2
        has_user = 'usuario_logado' in session and session.get('usuario_logado')
        has_auth_flag = session.get('auth_v2', False)
        
        is_auth = has_user and has_auth_flag
        
        print(f"ðŸ” Verificando autenticação:")
        print(f"   - usuario_logado: {session.get('usuario_logado')}")
        print(f"   - auth_v2 flag: {session.get('auth_v2')}")
        print(f"   - is_authenticated: {is_auth}")
        
        return is_auth
    
    @staticmethod
    def get_current_user() -> str:
        """Retorna usuÃ¡rio atual"""
        if AuthService.is_authenticated():
            return session.get('usuario_logado', '')
        return ''