# app/api/elevators.py
from flask import Blueprint, jsonify, request
# Importaçõees antigas: from app.utils.decorators import login_required, api_response
# Nova importações:
from app.utils.auth_decorators import api_auth_required # Agora inclui autenticação E padronização JSON

from app.services.sheets_service import SheetsService
from app.services.data_processor import DataProcessor

elevators_api_bp = Blueprint('elevators_api', __name__)