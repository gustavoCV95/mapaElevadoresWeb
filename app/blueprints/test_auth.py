# app/blueprints/test_auth.py
from flask import Blueprint, jsonify, request, session
from app.services.auth_service import AuthService
from app.utils.auth_decorators import login_required_v2, api_auth_required, json_response # Importa json_response

test_auth_bp = Blueprint('test_auth', __name__, url_prefix='/test/auth')

@test_auth_bp.route('/debug-session')
@api_auth_required # Protege este endpoint que revela informaÃ§Ãµes de sessÃ£o e padroniza a saÃ­da JSON
def debug_session():
    """Debug completo da sessão"""
    # Retorna um dicionÃ¡rio, api_auth_required (via json_response) irÃ¡ jsonify
    return {
        'session_data': dict(session),
        'session_keys': list(session.keys()),
        'usuario_logado': session.get('usuario_logado'),
        'auth_v2': session.get('auth_v2'),
        'login_timestamp': session.get('login_timestamp'),
        'session_permanent': session.permanent,
        'is_authenticated': AuthService.is_authenticated(),
        'current_user': AuthService.get_current_user()
    }

@test_auth_bp.route('/public')
@json_response # Endpoint pÃºblico, mas que deve ter resposta JSON padronizada
def public_endpoint():
    """Endpoint público (sem autenticação)"""
    # Retorna um dicionÃ¡rio, json_response irÃ¡ jsonify
    return {
        'status': 'OK',
        'message': 'Endpoint público funcionando',
        'authenticated': AuthService.is_authenticated(),
        'user': AuthService.get_current_user() if AuthService.is_authenticated() else None,
        'session_info': {
            'has_usuario_logado': 'usuario_logado' in session,
            'has_auth_v2': 'auth_v2' in session,
            'session_keys': list(session.keys())
        }
    }

@test_auth_bp.route('/protected')
@login_required_v2 # Endpoint protegido de UI (embora retorne JSON, o propÃ³sito do teste Ã© UI-like protection)
def protected_endpoint():
    """Endpoint protegido (com autenticação)"""
    return jsonify({ # JÃ¡ retorna jsonify, entÃ£o json_response nÃ£o Ã© estritamente necessÃ¡rio aqui se login_required_v2 cuida apenas do auth.
        'status': 'OK',
        'message': 'Endpoint protegido acessado com sucesso!',
        'user': AuthService.get_current_user(),
        'session_info': {
            'login_timestamp': session.get('login_timestamp'),
            'permanent': session.permanent,
            'auth_v2': session.get('auth_v2')
        }
    })

@test_auth_bp.route('/api-protected')
@api_auth_required # JÃ¡ usa e estÃ¡ correto.
def api_protected_endpoint():
    """Endpoint de API protegido"""
    # Retorna um dicionÃ¡rio, api_auth_required (via json_response) irÃ¡ jsonify
    return {
        'success': True,
        'message': 'API protegida acessada com sucesso!',
        'user': AuthService.get_current_user(),
        'timestamp': session.get('login_timestamp')
    }

@test_auth_bp.route('/login-test', methods=['POST'])
@json_response # Endpoint de API para login, nÃ£o protegido por auth_required (pois Ã© o login), mas precisa de JSON padronizado
def login_test():
    """Endpoint para testar login via API"""
    if not request.is_json:
        return {'success': False, 'message': 'JSON required'}, 400 # json_response irÃ¡ jsonify
    
    data = request.get_json()
    usuario = data.get('usuario')
    senha = data.get('senha')
    ip_cliente = request.environ.get('REMOTE_ADDR', 'test')
    
    print(f"Tentativa de login: {usuario}")
    
    sucesso, mensagem = AuthService.authenticate(usuario, senha, ip_cliente)
    
    print(f"Resultado do login: {sucesso}")
    
    # Retorna um dicionÃ¡rio, json_response irÃ¡ jsonify
    return {
        'success': sucesso,
        'message': mensagem,
        'user': AuthService.get_current_user() if sucesso else None,
        'session_after_login': {
            'usuario_logado': session.get('usuario_logado'),
            'auth_v2': session.get('auth_v2'),
            'session_keys': list(session.keys())
        }
    }

@test_auth_bp.route('/logout-test', methods=['POST'])
@json_response # Endpoint de API para logout, nÃ£o protegido por auth_required, mas precisa de JSON padronizado
def logout_test():
    """Endpoint para testar logout via API"""
    print(f"Tentativa de logout")
    mensagem = AuthService.logout()
    
    # Retorna um dicionÃ¡rio, json_response irÃ¡ jsonify
    return {
        'success': True,
        'message': mensagem,
        'session_after_logout': {
            'session_keys': list(session.keys()),
            'is_authenticated': AuthService.is_authenticated()
        }
    }

@test_auth_bp.route('/session-info')
@api_auth_required # Este endpoint revela informaÃ§Ãµes de sessÃ£o, entÃ£o deve ser protegido.
def session_info():
    """Informações da sessão atual"""
    # Retorna um dicionÃ¡rio, api_auth_required (via json_response) irÃ¡ jsonify
    return {
        'session_data': dict(session),
        'authenticated': AuthService.is_authenticated(),
        'user': AuthService.get_current_user(),
        'session_permanent': session.permanent
    }