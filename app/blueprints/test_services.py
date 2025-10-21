# app/blueprints/test_services.py
"""
Blueprint para testar os novos serviÃ§os
"""
from flask import Blueprint, jsonify
from app.services.data_processor import DataProcessor
from app.services.auth_service import AuthService
from app.models.elevator import Elevator
from app.models.kpi import KPI
import pandas as pd

test_services_bp = Blueprint('test_services', __name__)

@test_services_bp.route('/models')
def test_models():
    """Testa os models"""
    try:
        # Testa Elevator
        elevator_data = {
            'cidade': 'Belo Horizonte',
            'unidade': 'FÃ³rum Central',
            'endereco': 'Rua Teste, 123',
            'endereco_completo': 'Rua Teste, 123 - Centro',
            'tipo': 'Passageiro',
            'quantidade': 3,
            'marca': 'Atlas',
            'marca_licitacao': 'Atlas Schindler',
            'paradas': 10,
            'regiao': 'Metropolitana',
            'status': 'Em atividade',
            'empresa': 'Empresa Teste',
            'latitude': -19.92,
            'longitude': -43.92,
            'n_elevador_parado': 1
        }
        
        elevator = Elevator(**elevator_data)
        
        return jsonify({
            'status': 'OK',
            'elevator_test': {
                'tem_parado': elevator.tem_elevador_parado,
                'esta_suspenso': elevator.esta_suspenso,
                'elevadores_ativos': elevator.elevadores_ativos,
                'cor_marcador': elevator.cor_marcador,
                'geojson': elevator.to_geojson_feature()
            }
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@test_services_bp.route('/data-processor')
def test_data_processor():
    """Testa o DataProcessor"""
    try:
        # Cria dados de teste
        test_data = pd.DataFrame([
            {
                'cidade': 'Belo Horizonte',
                'unidade': 'FÃ³rum Central',
                'endereco': 'Rua Teste, 123',
                'enderecoCompleto': 'Rua Teste, 123 - Centro',
                'tipo': 'Passageiro',
                'quantidade': 3,
                'marca': 'Atlas',
                'marcaLicitacao': 'Atlas Schindler',
                'paradas': 10,
                'regiao': 'Metropolitana',
                'status': 'Em atividade',
                'empresa': 'Empresa Teste',
                'latitude': '-19.92',
                'longitude': '-43.92',
                'NElevadorParado': 1
            }
        ])
        
        processor = DataProcessor()
        result = processor.process_elevators_data(test_data)
        
        return jsonify({
            'status': 'OK',
            'processed_count': len(result['elevators']),
            'geojson_features': len(result['geojson_data']['features']),
            'compatibility_count': len(result['registros_processados'])
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@test_services_bp.route('/auth-service')
def test_auth_service():
    """Testa o AuthService (sem fazer login real)"""
    try:
        # Testa apenas se o serviÃ§o estÃ¡ funcionando
        is_auth = AuthService.is_authenticated()
        current_user = AuthService.get_current_user()
        
        return jsonify({
            'status': 'OK',
            'is_authenticated': is_auth,
            'current_user': current_user,
            'service_loaded': True
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500