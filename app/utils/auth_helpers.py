# app/utils/auth_helpers.py
from datetime import datetime, timedelta
from flask import current_app

# Cache para controle de tentativas de login
tentativas_login = {}

def verificar_tentativas_login(ip):
    """Verifica se o IP não excedeu o limite de tentativas"""
    agora = datetime.now()
    
    if ip in tentativas_login:
        tentativas = tentativas_login[ip]
        
        # Remove tentativas antigas (mais de BLOQUEIO_TEMPO segundos)
        tentativas['historico'] = [
            t for t in tentativas['historico'] 
            if (agora - t).seconds < current_app.config['BLOQUEIO_TEMPO']
        ]
        
        # Verifica se excedeu o limite
        if len(tentativas['historico']) >= current_app.config['MAX_TENTATIVAS_LOGIN']:
            return False, tentativas['historico'][0] + timedelta(seconds=current_app.config['BLOQUEIO_TEMPO'])
    
    return True, None

def registrar_tentativa_login(ip):
    """Registra uma tentativa de login falhada"""
    agora = datetime.now()
    
    if ip not in tentativas_login:
        tentativas_login[ip] = {'historico': []}
    
    tentativas_login[ip]['historico'].append(agora)

def limpar_tentativas_login(ip):
    """Limpa tentativas de login para um IP específico"""
    if ip in tentativas_login:
        del tentativas_login[ip]

def get_tempo_restante_bloqueio(ip):
    """Retorna tempo restante de bloqueio em minutos"""
    if ip not in tentativas_login:
        return 0
    
    agora = datetime.now()
    tentativas = tentativas_login[ip]
    
    if tentativas['historico']:
        ultimo_bloqueio = tentativas['historico'][0] + timedelta(seconds=current_app.config['BLOQUEIO_TEMPO'])
        if ultimo_bloqueio > agora:
            return int((ultimo_bloqueio - agora).seconds / 60)
    
    return 0