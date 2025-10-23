# app/utils/__init__.py
"""Módulo de utilitários e helpers"""

# AGORA IMPORTAMOS OS NOVOS DECORADORES DA V2
from .auth_decorators import login_required_v2, admin_required_v2, api_auth_required, json_response

from .helpers import (
    format_datetime, 
    is_valid_email, 
    safe_int, 
    safe_float, 
    safe_str,
    validate_coordinates,
    calculate_time_difference
)
from .auth_helpers import (
    verificar_tentativas_login,
    registrar_tentativa_login,
    limpar_tentativas_login,
    get_tempo_restante_bloqueio
)

__all__ = [
    # Decorators V2
    'login_required_v2', # NOVO: Decorador para rotas de UI
    'admin_required_v2', # NOVO: Decorador para rotas de admin (futuro)
    'api_auth_required', # NOVO: Decorador para APIs protegidas
    'json_response',     # NOVO: Decorador para padronizar respostas JSON
    
    # Helpers
    'format_datetime',
    'is_valid_email',
    'safe_int',
    'safe_float', 
    'safe_str',
    'validate_coordinates',
    'calculate_time_difference',
    
    # Auth helpers
    'verificar_tentativas_login',
    'registrar_tentativa_login',
    'limpar_tentativas_login',
    'get_tempo_restante_bloqueio'
]