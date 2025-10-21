# app/config/production.py
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Configurações para ambiente de produção"""
    
    DEBUG = False
    TESTING = False
    
    def __init__(self):
        super().__init__()
        # Cache mais longo em produção
        self.CACHE_TIMEOUT = 600  # 10 minutos
        
        # Logs menos verbosos
        self.LOG_LEVEL = 'INFO'
        
        # Segurança reforçada
        self.MAX_TENTATIVAS_LOGIN = 3
        self.BLOQUEIO_TEMPO = 1800  # 30 minutos
    
    @classmethod
    def listar_usuarios(cls):
        """Sobrescreve para não mostrar informações sensíveis"""
        instance = cls()
        usuarios = instance.USUARIOS_AUTORIZADOS
        print("🔒 AMBIENTE DE PRODUÇÃO")
        print(f"   👥 {len(usuarios)} usuário(s) carregado(s)")