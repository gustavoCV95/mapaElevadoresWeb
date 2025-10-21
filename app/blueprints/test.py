# app/blueprints/test.py
"""
Blueprint de teste - VERSÃƒO CORRIGIDA COM PREFIXO
"""
from flask import Blueprint, jsonify
from datetime import datetime

# Cria o blueprint
test_bp = Blueprint('test', __name__)

@test_bp.route('/')
def index():
    """PÃ¡gina inicial temporÃ¡ria"""
    return jsonify({
        'message': 'Nova arquitetura funcionando!',
        'timestamp': datetime.now().isoformat(),
        'routes_available': [
            '/ (esta pÃ¡gina)',
            '/test/health',
            '/test/config',
            '/test/services/models',
            '/test/services/data-processor',
            '/test/services/auth-service'
        ]
    })

# âœ… MUDANÃ‡A: Adicionar prefixo /test/ nas rotas
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

# âœ… ROTA ADICIONAL: Status geral
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