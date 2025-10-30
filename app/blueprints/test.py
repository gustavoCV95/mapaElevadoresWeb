# app/blueprints/test.py
"""
Blueprint de teste - VERSÃO CORRIGIDA COM PREFIXO
"""
from flask import Blueprint, jsonify, redirect, url_for # <-- Adicione redirect e url_for
from datetime import datetime
from app.services.auth_service import AuthService # <-- Adicione a importação do AuthService

# Cria o blueprint
test_bp = Blueprint('test', __name__)

@test_bp.route('/')
def index():
    """
    Página inicial temporária que agora redireciona para o login ou dashboard.
    """
    if AuthService.is_authenticated():
        # Redireciona para o dashboard se o usuário estiver autenticado
        # 'dashboard.index' refere-se à função 'index' dentro do blueprint 'dashboard'
        return redirect(url_for('dashboard.index'))
    else:
        # Redireciona para a página de login se o usuário não estiver autenticado
        # 'auth.login' refere-se à função 'login' dentro do blueprint 'auth'
        return redirect(url_for('auth.login'))

# ✅ MUDANÇA: Adicionar prefixo /test/ nas rotas
@test_bp.route('/test/health')
def health_check():
    """Health check"""
    return jsonify({
        'status': 'OK',
        'message': 'Health check passou!',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-corrigido'
    })

@test_bp.route('/test/config')
def test_config():
    """Teste de config"""
    from flask import current_app
    return jsonify({
        'status': 'OK',
        'debug': current_app.config.get('DEBUG'),
        'secret_key_set': bool(current_app.config.get('SECRET_KEY')),
        'cache_active': hasattr(current_app, 'cache_service')
    })

# ✅ ROTA ADICIONAL: Status geral
@test_bp.route('/test/status')
def status():
    """Status completo da aplicaÃ§Ã£o"""
    from flask import current_app
    
    # Lista todas as rotas
    routes = []
    with current_app.app_context():
        for rule in current_app.url_map.iter_rules():
            if not rule.rule.startswith('/static'):
                routes.append({
                    'rule': rule.rule,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    'endpoint': rule.endpoint
                })
    
    return jsonify({
        'status': 'OK',
        'message': 'AplicaÃ§Ã£o funcionando perfeitamente!',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-fase2',
        'blueprints': list(current_app.blueprints.keys()),
        'routes': routes,
        'config': {
            'debug': current_app.config.get('DEBUG'),
            'cache_timeout': current_app.config.get('CACHE_TIMEOUT'),
            'users_count': len(current_app.config.get('USUARIOS_AUTORIZADOS', {}))
        }
    })