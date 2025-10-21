# app/config/development.py
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Configurações para ambiente de desenvolvimento"""
    
    DEBUG = True
    TESTING = False
    
    def __init__(self):
        super().__init__()
        # Cache mais curto em desenvolvimento
        self.CACHE_TIMEOUT = 60  # 1 minuto
        
        # Logs mais verbosos
        self.LOG_LEVEL = 'DEBUG'
    
    @classmethod
    def listar_usuarios(cls):
        """Sobrescreve para mostrar informações de desenvolvimento"""
        print("🔧 AMBIENTE DE DESENVOLVIMENTO")
        instance = cls()
        usuarios = instance.USUARIOS_AUTORIZADOS
        for usuario in usuarios.keys():
            print(f"   - {usuario}")
        print("   💡 Senhas padrão: admin123, senha123")