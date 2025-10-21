# app/factory.py
from flask import Flask
from flask_caching import Cache
import os

# Importa as configuraçÃµes do seu aplicativo
from app.config import get_config
# Importa o CacheService
from app.services.cache_service import CacheService # Adicionado import

cache = Cache()

def create_app():
    """Factory para criar instÃ¢ncia da aplicação Flask"""
    print("ðŸ—ï¸ Criando aplicação (Fase 4)...")
    
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    print(f"ðŸ“ Template dir: {template_dir}")
    print(f"ðŸ“ Static dir: {static_dir}")
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    print("âš™ï¸ Carregando configuração...")
    config = get_config()
    app.config.from_object(config)
    
    app.config['SESSION_PERMANENT'] = True
    
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-key-for-testing'
    
    planilha_url = app.config.get('PLANILHA_URL')
    if planilha_url:
        print(f"âœ… PLANILHA_URL configurada: {planilha_url[:50]}...")
    else:
        print("âš ï¸ PLANILHA_URL não configurada - dashboard pode não funcionar")
    
    print(f"DEBUG mode: {app.config.get('DEBUG', False)}")
    
    print("Inicializando extensÃµes...")
    init_extensions(app)
    
    print("Registrando blueprints...")
    register_blueprints(app) # Chama a função que registra TODOS os blueprints
    
    print("Registrando context processors...")
    register_context_processors(app)
    
    print("âœ… Aplicação criada com sucesso (Fase 4)!")
    return app

# A função get_config jÃ¡ estava OK no seu factory.py
def get_config():
    """ObtÃ©m configuração"""
    try:
        from app.config import get_config as get_app_config
        return get_app_config()
    except ImportError as e:
        print(f"âš ï¸ Erro ao importar config: {e}")
        class MinimalConfig:
            DEBUG = True
            SECRET_KEY = 'dev-key-minimal'
            CACHE_TIMEOUT = 300
            USUARIOS_AUTORIZADOS = {}
            SESSION_PERMANENT = True
            PERMANENT_SESSION_LIFETIME = 3600
            PLANILHA_URL = None
            PLANILHA_KPIS_URL = None # Adicionado para evitar erro se kpis_api_bp for ativado
        return MinimalConfig()

def init_extensions(app):
    """Inicializa extensÃµes"""
    cache.init_app(app)
    try:
        if not hasattr(app, 'cache_service'):
            app.cache_service = CacheService(app.config.get('CACHE_TIMEOUT', 300))
        print("âœ… Cache service inicializado")
    except Exception as e:
        print(f"âš ï¸ Erro ao inicializar cache: {e}")

# CORRIGIDO: Registro de TODOS os Blueprints
def register_blueprints(app):
    """Registra todos os blueprints"""
    blueprints_registered = 0
    
    # BLUEPRINTS (app/blueprints)
    try:
        from app.blueprints.test import test_bp
        app.register_blueprint(test_bp)
        blueprints_registered += 1
        print("âœ… Blueprint 'test' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'test': {e}")
    
    try:
        from app.blueprints.test_services import test_services_bp
        app.register_blueprint(test_services_bp, url_prefix='/test/services')
        blueprints_registered += 1
        print("âœ… Blueprint 'test_services' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'test_services': {e}")
    
    try:
        from app.blueprints.auth import auth_bp
        app.register_blueprint(auth_bp)
        blueprints_registered += 1
        print("âœ… Blueprint 'auth' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'auth': {e}")
    
    try:
        from app.blueprints.test_auth import test_auth_bp
        app.register_blueprint(test_auth_bp)
        blueprints_registered += 1
        print("âœ… Blueprint 'test_auth' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'test_auth': {e}")
    
    try:
        from app.blueprints.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp)
        blueprints_registered += 1
        print("âœ… Blueprint 'dashboard' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'dashboard': {e}")

    # BLUEPRINTS DE API (app/api) - ADICIONADOS AQUI
    try:
        from app.api.elevators import elevators_api_bp
        app.register_blueprint(elevators_api_bp, url_prefix='/api')
        blueprints_registered += 1
        print("âœ… Blueprint 'elevators_api' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'elevators_api': {e}")

    # BLUEPRINT DE KPIS (UI)
    try:
        from app.blueprints.kpis import kpis_bp
        app.register_blueprint(kpis_bp) # Sem prefixo, usa o url_prefix definido no Blueprint (/v2/kpis)
        blueprints_registered += 1
        print("âœ… Blueprint 'kpis' (UI) registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'kpis' (UI): {e}")

    # BLUEPRINT DE KPIS (API)
    try:
        from app.api.kpis import kpis_api_bp
        app.register_blueprint(kpis_api_bp, url_prefix='/api') # Registra a API de KPIs sob /api
        blueprints_registered += 1
        print("âœ… Blueprint 'kpis_api' registrado")
    except Exception as e:
        print(f"âŒ Erro ao registrar blueprint 'kpis_api': {e}")
    
    print(f"ðŸ“Š Total de blueprints registrados: {blueprints_registered}")

# A função register_context_processors jÃ¡ estava OK no seu factory.py
def register_context_processors(app):
    """Context processors globais"""
    @app.context_processor
    def inject_user_info():
        from flask import session
        return {
            'usuario_logado': session.get('usuario_logado'),
            'login_timestamp': session.get('login_timestamp')
        }
    print("âœ… Context processors registrados")