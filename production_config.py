import os
from werkzeug.security import generate_password_hash

class ProductionConfig:
    # URL da planilha do Google Sheets
    PLANILHA_URL = os.environ.get('PLANILHA_URL', 'https://docs.google.com/spreadsheets/d/1I46gVcTqvE9JjHIrbeqZhNLvvd4OZbGb7iTVkcHAhf0/edit?gid=0#gid=0')
    
    # Configurações de cache (em segundos)
    CACHE_TIMEOUT = 300  # 5 minutos
    
    # ========== CONFIGURAÇÕES DO FLASK ==========
    
    # SECRET_KEY obrigatória via variável de ambiente
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("FLASK_SECRET_KEY deve ser definida como variável de ambiente!")
    
    DEBUG = False  # NUNCA True em produção
    
    # ========== CONFIGURAÇÕES DE AUTENTICAÇÃO ==========
    
    # Configurações de sessão - AJUSTADAS PARA FUNCIONAR SEM HTTPS
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    SESSION_COOKIE_SECURE = False   # MUDANÇA: False para HTTP (não HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Usuários autorizados - carregados de variáveis de ambiente
    USUARIOS_AUTORIZADOS = {}
    
    @staticmethod
    def carregar_usuarios():
        """Carrega usuários das variáveis de ambiente"""
        # Formato: USER_ADMIN=senha123,USER_TJMG=elevadores2024
        for key, value in os.environ.items():
            if key.startswith('USER_'):
                username = key[5:].lower()  # Remove 'USER_' e converte para minúsculo
                ProductionConfig.USUARIOS_AUTORIZADOS[username] = generate_password_hash(value)
        
        # Usuário padrão se nenhum for definido
        if not ProductionConfig.USUARIOS_AUTORIZADOS:
            admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
            ProductionConfig.USUARIOS_AUTORIZADOS['admin'] = generate_password_hash(admin_pass)
    
    # Configurações de segurança
    MAX_TENTATIVAS_LOGIN = 5
    BLOQUEIO_TEMPO = 300  # 5 minutos

# Carrega usuários ao importar
ProductionConfig.carregar_usuarios()
