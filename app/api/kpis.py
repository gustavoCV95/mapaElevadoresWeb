# app/api/kpis.py
from flask import Blueprint, jsonify, request, current_app
from app.utils.auth_decorators import api_auth_required
from app.services.sheets_service import SheetsService
from app.services.data_processor import DataProcessor
from app.blueprints.kpis import obter_kpis_cached # Importa a funÃ§Ã£o de cache do Blueprint UI
from datetime import datetime, timedelta
import pytz

kpis_api_bp = Blueprint('kpis_api', __name__)

@kpis_api_bp.route('/kpis-filtrados')
@api_auth_required
def api_kpis_filtrados():
    """API para obter dados de KPIs filtrados."""
    start_time = datetime.now()
    
    try:
        # ObtÃ©m a lista completa de objetos KPI do cache
        all_kpis, _ = obter_kpis_cached()
        
        # Extrai parÃ¢metros de filtro da requisiÃ§Ã£o
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        periodo_predefinido = request.args.get('periodo_predefinido')
        status_filtro = request.args.get('status')
        categoria_filtro = request.args.get('categoria')
        edificio_filtro = request.args.get('edificio')
        equipamento_filtro = request.args.get('equipamento')

        # Converte strings de data para objetos datetime (ajustado para BRT)
        brt = pytz.timezone("America/Sao_Paulo")
        data_inicio = None
        data_fim = None

        if data_inicio_str:
            data_inicio = brt.localize(datetime.strptime(data_inicio_str, '%Y-%m-%d'))
        if data_fim_str:
            data_fim = brt.localize(datetime.strptime(data_fim_str, '%Y-%m-%d')) + timedelta(days=1, seconds=-1) # Inclui o dia todo

        # Aplica perÃ­odo predefinido se nÃ£o houver datas especÃ­ficas
        if periodo_predefinido and not (data_inicio_str or data_fim_str):
            hoje = brt.localize(datetime.now())
            if periodo_predefinido == 'ultima-semana':
                data_inicio = hoje - timedelta(weeks=1)
            elif periodo_predefinido == 'ultimo-mes':
                data_inicio = hoje - timedelta(days=30)
            elif periodo_predefinido == 'ultimos-3-meses':
                data_inicio = hoje - timedelta(days=90)
            elif periodo_predefinido == 'ultimos-6-meses':
                data_inicio = hoje - timedelta(days=180)
            elif periodo_predefinido == 'ultimo-ano':
                data_inicio = hoje - timedelta(days=365)
            elif periodo_predefinido == 'ultimos-2-anos':
                data_inicio = hoje - timedelta(days=730)
            elif periodo_predefinido == 'ultimos-5-anos':
                data_inicio = hoje - timedelta(days=1825)
            # 'todo-periodo' nÃ£o requer ajuste de data

            # Garante que data_fim esteja definida para filtros predefinidos
            if data_inicio and not data_fim:
                data_fim = hoje # AtÃ© hoje

        # Cria um DataProcessor para aplicar os filtros
        data_processor = DataProcessor()
        
        # Filtra a lista de objetos KPI
        kpis_filtrados = data_processor.apply_kpi_filters(
            all_kpis,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status=status_filtro,
            categoria=categoria_filtro,
            edificio=edificio_filtro,
            equipamento=equipamento_filtro
        )
        
        # Calcula as mÃ©tricas dos KPIs filtrados
        metricas_filtradas = data_processor._calculate_kpi_metrics(kpis_filtrados)
        
        # Prepara um resumo para a tabela (se necessário, os 20 primeiros, como no JS)
        resumo_tabela = [kpi.to_dict() for kpi in kpis_filtrados[:20]]

        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"âœ… KPIs: Filtros aplicados em {elapsed_time:.2f}s: {len(kpis_filtrados)} KPIs.")
        
        return {
            'success': True,
            'metricas': metricas_filtradas,
            'resumo': resumo_tabela,
            'total_kpis': len(kpis_filtrados),
            'performance': {
                'tempo_processamento': f"{elapsed_time:.2f}s",
                'fonte_dados': 'cache'
            }
        }
    except ValueError as ve:
        current_app.logger.warning(f"Erro de validaÃ§Ã£o na API de KPIs: {ve}")
        return {'success': False, 'message': str(ve)}, 400
    except Exception as e:
        current_app.logger.exception(f"Erro na API de KPIs: {e}")
        return {'success': False, 'message': 'Ocorreu um erro interno ao processar os KPIs.'}, 500