# app/utils/auth_decorators.py
from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify
from app.services.auth_service import AuthService
import traceback # Importa para logging de erros detalhado

# NOVO: Decorador para padronizar respostas JSON e tratamento de erros para qualquer API
def json_response(f):
    """Decorator para padronizar respostas de API e tratamento de erros."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            if isinstance(result, dict):
                return jsonify(result)
            # Se a função jÃ¡ retornar um objeto Response (como jsonify), apenas o retorna.
            return result
        except Exception as e:
            # Loga o traceback completo para depuração
            print(f"âŒ Erro na API em {f.__name__}: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Ocorreu um erro interno na API.' # Mensagem amigÃ¡vel para o usuÃ¡rio
            }), 500
    return decorated_function

# Modificado: api_auth_required agora inclui a funcionalidade de json_response
def api_auth_required(f):
    """
    Decorator especÃ­fico para APIs que requer autenticação e padroniza a resposta JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"ðŸ”’ API Auth check para {request.endpoint}")
        
        is_authenticated = AuthService.is_authenticated()
        print(f"ðŸ” API Auth resultado: {is_authenticated}")
        
        if not is_authenticated:
            # Retorna uma resposta JSON padronizada para falha de autenticação
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Autenticação necessÃ¡ria para acessar este recurso.',
                'code': 'AUTH_REQUIRED',
                'login_url': url_for('auth.login'), # URL de login da v2
                'debug_info': {
                    'session_keys': list(session.keys()),
                    'usuario_logado': session.get('usuario_logado'),
                    'auth_v2': session.get('auth_v2')
                }
            }), 401
        
        # Se autenticado, aplica a lÃ³gica de json_response ao resultado da função
        # Isso garante a padronização JSON e tratamento de erros para respostas bem-sucedidas.
        return json_response(f)(*args, **kwargs)
    return decorated_function

# Os decoradores login_required_v2 e admin_required_v2 (se existir) permanecem inalterados,
# pois são projetados principalmente para rotas de UI que retornam HTML ou redirecionam.

# Mantenha os decoradores existentes abaixo, que são para UI:
def login_required_v2(f):
    """
    Decorator para autenticação da nova arquitetura - VERSÃƒO FINAL
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"ï¿½ï¿½ Verificando autenticação para {request.endpoint}")
        print(f"ðŸ” Request path: {request.path}")
        print(f"ðŸ” Request headers: {dict(request.headers)}")
        print(f"ï¿½ï¿½ Is JSON: {request.is_json}")
        print(f"ï¿½ï¿½ Content-Type: {request.content_type}")
        print(f"ðŸ” Accept: {request.headers.get('Accept', '')}")
        
        is_authenticated = AuthService.is_authenticated()
        print(f"ðŸ” Resultado da verificação: {is_authenticated}")
        
        if not is_authenticated:
            print(f"âŒ UsuÃ¡rio não autenticado, bloqueando acesso")
            
            is_api_request = (
                request.is_json or 
                request.path.startswith('/api/') or
                request.path.startswith('/test/auth/') or  # Nossos endpoints de teste
                'application/json' in request.headers.get('Accept', '') or
                'application/json' in request.headers.get('Content-Type', '')
            )
            
            print(f"ðŸ” Ã‰ requisição de API: {is_api_request}")
            
            if is_api_request:
                return jsonify({
                    'success': False,
                    'message': 'Autenticação necessÃ¡ria',
                    'login_url': url_for('auth.login'),
                    'debug_info': {
                        'session_keys': list(session.keys()),
                        'usuario_logado': session.get('usuario_logado'),
                        'auth_v2': session.get('auth_v2')
                    }
                }), 401
            else:
                flash('VocÃª precisa fazer login para acessar esta pÃ¡gina.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
        
        print(f"âœ… UsuÃ¡rio autenticado, permitindo acesso")
        return f(*args, **kwargs)
    return decorated_function

def admin_required_v2(f):
    """
    Decorator para verificar se Ã© admin (futuro)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            if request.is_json or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'message': 'Autenticação necessÃ¡ria'}), 401
            else:
                flash('Acesso negado.', 'danger')
                return redirect(url_for('auth.login'))
        
        # TODO: Implementar lÃ³gica de verificação de admin
        # Por enquanto, apenas garante que esteja autenticado
        
        return f(*args, **kwargs)
    return decorated_function