# app/blueprints/auth.py
from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, flash, jsonify, session
from app.services.auth_service import AuthService
from app.utils.auth_decorators import json_response, api_auth_required

auth_bp = Blueprint('auth', __name__, url_prefix='/v2/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """PÃ¡gina de login da nova arquitetura"""
    if request.method == 'POST':
        if request.is_json:
            return handle_login_api()
        else:
            return handle_login_form()
    
    return render_template_string(LOGIN_TEMPLATE)

def handle_login_form():
    """Processa login via formulÃ¡rio"""
    usuario = request.form.get('usuario', '').strip()
    senha = request.form.get('senha', '')
    ip_cliente = request.environ.get('REMOTE_ADDR', 'unknown')
    
    if not usuario or not senha:
        flash('Usuário e senha são obrigatórios.', 'danger')
        return render_template_string(LOGIN_TEMPLATE)
    
    sucesso, mensagem = AuthService.authenticate(usuario, senha, ip_cliente)
    
    if sucesso:
        flash(mensagem, 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index')) # Redireciona para o novo dashboard
    else:
        flash(mensagem, 'danger')
        return render_template_string(LOGIN_TEMPLATE)

# Agora usa o novo json_response (nÃ£o exige autenticaÃ§Ã£o, mas padroniza a saÃ­da JSON)
@json_response 
def handle_login_api():
    """Processa login via API"""
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    senha = data.get('senha', '')
    ip_cliente = request.environ.get('REMOTE_ADDR', 'unknown')
    
    if not usuario or not senha:
        return {'success': False, 'message': 'Usuário e senha são obrigatórios.'}, 400
    
    sucesso, mensagem = AuthService.authenticate(usuario, senha, ip_cliente)
    
    if sucesso:
        return {
            'success': True, 
            'message': mensagem,
            'user': AuthService.get_current_user(),
            'redirect': url_for('dashboard.index') # Redireciona para o novo dashboard
        }
    else:
        return {'success': False, 'message': mensagem}, 401

@auth_bp.route('/logout')
def logout():
    """Logout da nova arquitetura"""
    mensagem = AuthService.logout()
    
    if request.is_json:
        # Usa json_response aqui tambÃ©m, pois Ã© uma API de logout que deve ter saÃ­da padronizada
        return json_response(lambda: {'success': True, 'message': mensagem})()
    else:
        flash(mensagem, 'info')
        return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
# Este endpoint agora serÃ¡ protegido pelo login_required_v2
# Importante: o `auth.py` original nÃ£o tinha proteÃ§Ã£o, mas o `dashboard.py` jÃ¡ tem.
# Se este Ã© um dashboard temporÃ¡rio que serÃ¡ substituÃ­do, esta rota deve ser deprecada.
# Por consistÃªncia, sugiro protegÃª-la com login_required_v2 se ainda estiver em uso.
# No entanto, a descriÃ§Ã£o sugere que `app/blueprints/dashboard.py` Ã© o dashboard principal.
# Vou assumir que este `auth_bp.route('/dashboard')` serÃ¡ removido no futuro,
# e o dashboard real Ã© em `app/blueprints/dashboard.py` (que jÃ¡ usa `login_required_v2`).
# Se vocÃª decidir mantÃª-lo, adicione: `@login_required_v2`.
def dashboard():
    """Dashboard temporÃ¡rio da nova arquitetura"""
    if not AuthService.is_authenticated():
        if request.is_json:
            return jsonify({'success': False, 'message': 'NÃ£o autenticado'}), 401
        else:
            flash('VocÃª precisa fazer login.', 'warning')
            return redirect(url_for('auth.login'))
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                usuario=AuthService.get_current_user())

@auth_bp.route('/status')
@api_auth_required # Agora protegida e com saÃ­da JSON padronizada
def auth_status():
    """Status da autenticaÃ§Ã£o (API)"""
    # Retorna um dicionÃ¡rio, que api_auth_required (via json_response) irÃ¡ converter para JSON e lidar com erros
    return {
        'authenticated': AuthService.is_authenticated(),
        'user': AuthService.get_current_user(),
        'session_data': {
            'login_timestamp': session.get('login_timestamp'),
            'permanent': session.permanent
        }
    }

# ========== TEMPLATES INLINE (temporÃ¡rios) ==========

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Nova Arquitetura</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; }
        .login-container { background: white; border-radius: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 400px; width: 100%; margin: 20px; }
        .login-header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 2rem; text-align: center; border-radius: 15px 15px 0 0; }
        .version-badge { position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container d-flex justify-content-center">
        <div class="login-container">
            <div class="login-header position-relative">
                <div class="version-badge">v2.0</div>
                <i class="fas fa-building fa-3x mb-3"></i>
                <h3>Nova Arquitetura</h3>
                <p class="mb-0">Sistema Modular</p>
            </div>
            
            <div class="p-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'danger' else 'warning' if category == 'warning' else 'success' }} alert-dismissible fade show">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label"><i class="fas fa-user"></i> Usuário</label>
                        <input type="text" class="form-control" name="usuario" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label"><i class="fas fa-lock"></i> Senha</label>
                        <input type="password" class="form-control" name="senha" required>
                    </div>
                    
                    <button type="submit" class="btn btn-success w-100">
                        <i class="fas fa-sign-in-alt"></i> Entrar
                    </button>
                </form>
                
                <hr>
                <div class="text-center">
                    <small class="text-muted">
                        <i class="fas fa-info-circle"></i>
                        Sistema atual: <a href="http://localhost:5000/login" >localhost:5000</a>
                    </small>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Nova Arquitetura</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-building"></i> Nova Arquitetura v2.0
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">
                    <i class="fas fa-user"></i> {{ usuario }}
                </span>
                <a class="nav-link" href="{{ url_for('auth.logout') }}">
                    <i class="fas fa-sign-out-alt"></i> Sair
                </a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="alert alert-success">
                    <h4><i class="fas fa-check-circle"></i> AutenticaÃ§Ã£o Funcionando!</h4>
                    <p>Bem-vindo ao dashboard da nova arquitetura modular.</p>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> InformaÃ§Ãµes da SessÃ£o</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>UsuÃ¡rio:</strong> {{ usuario }}</p>
                        <p><strong>Sistema:</strong> Nova Arquitetura v2.0</p>
                        <p><strong>Fase:</strong> 3 - AutenticaÃ§Ã£o Modular</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-link"></i> Links Ãšteis</h5>
                    </div>
                    <div class="card-body">
                        <p><a href="http://localhost:5000"  class="btn btn-primary btn-sm">
                            <i class="fas fa-external-link-alt"></i> Sistema Atual
                        </a></p>
                        <p><a href="{{ url_for('test.status') }}" class="btn btn-info btn-sm">
                            <i class="fas fa-cog"></i> Status do Sistema
                        </a></p>
                        <p><a href="{{ url_for('auth.auth_status') }}" class="btn btn-secondary btn-sm">
                            <i class="fas fa-shield-alt"></i> Status da Auth
                        </a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""