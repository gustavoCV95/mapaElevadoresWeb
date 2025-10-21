# app/config/__init__.py
import os

# ✅ CARREGA .env ANTES DE TUDO
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️ python-dotenv não instalado, usando apenas variáveis do sistema")

from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig

def get_config():
    """Retorna a configuração baseada no ambiente"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()

# Para compatibilidade com o código atual
Config = get_config()