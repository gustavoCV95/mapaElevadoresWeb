# app/config/base.py
import os
from datetime import timedelta
from werkzeug.security import generate_password_hash

class BaseConfig:
    """Configurações base compartilhadas entre ambientes"""
    
    # ConfiguraÃ§Ãµes Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # URLs das planilhas - USANDO VARIÃVEIS DE AMBIENTE
    PLANILHA_URL = os.environ.get('PLANILHA_URL')
    PLANILHA_KPIS_URL = os.environ.get('PLANILHA_KPIS_URL')
    
    # Cache
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', '300'))  # 5 minutos
    
    # SeguranÃ§a
    MAX_TENTATIVAS_LOGIN = int(os.environ.get('MAX_TENTATIVAS_LOGIN', '5'))
    BLOQUEIO_TEMPO = int(os.environ.get('BLOQUEIO_TEMPO', '900'))  # 15 minutos
    
    def __init__(self):
        """Inicializa configurações que dependem de métodos"""
        self.USUARIOS_AUTORIZADOS = self._get_usuarios_autorizados()
        
        # VALIDAÇÃO DAS URLs OBRIGATÓRIAS
        if not self.PLANILHA_URL:
            raise ValueError("PLANILHA_URL deve ser definida como variÃ¡vel de ambiente")
        if not self.PLANILHA_KPIS_URL:
            raise ValueError("PLANILHA_KPIS_URL deve ser definida como variÃ¡vel de ambiente")
    
    def _get_usuarios_autorizados(self):
        """Carrega usurios das variáveis de ambiente"""
        usuarios = {}
        
        # Formato: USUARIO_1=nome:senha, USUARIO_2=nome:senha, etc.
        for i in range(1, 11):  # Suporta até 10 usuários
            user_env = os.environ.get(f'USUARIO_{i}')
            if user_env and ':' in user_env:
                nome, senha = user_env.split(':', 1)
                usuarios[nome] = generate_password_hash(senha)
        
        # Fallback para desenvolvimento
        if not usuarios:
            usuarios = {
                'admin': generate_password_hash('admin123'),
                'usuario': generate_password_hash('senha123')
            }
            
        print(f"{len(usuarios)} usuário(s) carregado(s)")
        return usuarios
    
    @classmethod
    def listar_usuarios(cls):
        """Lista usuários cadastrados (para debug)"""
        instance = cls()
        usuarios = instance.USUARIOS_AUTORIZADOS
        for usuario in usuarios.keys():
            print(f"   - {usuario}")