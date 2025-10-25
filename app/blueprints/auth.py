# app/blueprints/auth.py
from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, flash, jsonify, session
from app.services.auth_service import AuthService
from app.utils.auth_decorators import json_response, api_auth_required

auth_bp = Blueprint('auth', __name__, url_prefix='/v2/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login da nova arquitetura"""
    if request.method == 'POST':
        if request.is_json:
            return handle_login_api()
        else:
            return handle_login_form()
    
    return render_template('login.html')

def handle_login_form():
    """Processa login via formulário"""
    usuario = request.form.get('usuario', '').strip()
    senha = request.form.get('senha', '')
    ip_cliente = request.environ.get('REMOTE_ADDR', 'unknown')
    
    if not usuario or not senha:
        flash('Usuário e senha são obrigatórios.', 'danger')
        return render_template('login.html')
    
    sucesso, mensagem = AuthService.authenticate(usuario, senha, ip_cliente)
    
    if sucesso:
        flash(mensagem, 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index')) # Redireciona para o novo dashboard
    else:
        flash(mensagem, 'danger')
        return render_template('login.html')

# Agora usa o novo json_response (não exige autenticação, mas padroniza a saí­da JSON)
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
        # Usa json_response aqui também, pois é uma API de logout que deve ter saí­da padronizada
        return json_response(lambda: {'success': True, 'message': mensagem})()
    else:
        flash(mensagem, 'info')
        return redirect(url_for('auth.login'))

@auth_bp.route('/status')
@api_auth_required # Agora protegida e com saí­da JSON padronizada
def auth_status():
    """Status da autenticação (API)"""
    # Retorna um dicionário, que api_auth_required (via json_response) irÃ¡ converter para JSON e lidar com erros
    return {
        'authenticated': AuthService.is_authenticated(),
        'user': AuthService.get_current_user(),
        'session_data': {
            'login_timestamp': session.get('login_timestamp'),
            'permanent': session.permanent
        }
    }

