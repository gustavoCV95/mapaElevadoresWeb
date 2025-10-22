# app/api/blueprints.py
"""
Blueprints da aplicação
"""
# Importa todos os blueprints para garantir que sejam registrados
from .test import test_bp
from .test_services import test_services_bp

__all__ = ['test_bp', 'test_services_bp']