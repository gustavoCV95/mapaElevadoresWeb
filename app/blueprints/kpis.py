# app/blueprints/kpis.py
from flask import Blueprint, render_template, current_app, jsonify, request
from app.utils.auth_decorators import login_required_v2, api_auth_required # Importamos os decoradores da v2
from app.services.sheets_service import SheetsService
from app.services.data_processor import DataProcessor
from app.services.auth_service import AuthService
from datetime import datetime
import time
import pytz # Para fusos horÃ¡rios

kpis_bp = Blueprint('kpis', __name__, url_prefix='/v2/kpis')

# âœ… CACHE GLOBAL PARA DADOS RAW DE KPIS
_kpi_dados_cache = {
    'dados_raw': None,
    'kpis_processed_list': None, # Lista de objetos KPI processados
    'metricas_calculadas': None, # MÃ©tricas gerais calculadas a partir de todos os KPIs
    'timestamp': None
}

def obter_kpis_cached():
    """ObtÃ©m dados de KPIs com cache inteligente."""
    global _kpi_dados_cache
    
    # Verifica se cache Ã© vÃ¡lido (5 minutos)
    # Converta para o fuso horÃ¡rio BRT para comparaÃ§Ãµes de tempo, se necessÃ¡rio
    brt = pytz.timezone("America/Sao_Paulo")
    
    cache_valido = (
        _kpi_dados_cache['timestamp'] and 
        (time.time() - _kpi_dados_cache['timestamp']) < 300 # 5 minutos
    )
    
    if cache_valido and _kpi_dados_cache['kpis_processed_list']:
        print("ðŸ“¦ KPIs: Usando dados do cache")
        return _kpi_dados_cache['kpis_processed_list'], _kpi_dados_cache['metricas_calculadas']
    
    # Recarrega dados
    print("ðŸ”„ KPIs: Recarregando dados (cache expirado)")
    planilha_kpis_url = current_app.config.get('PLANILHA_KPIS_URL')
    if not planilha_kpis_url:
        raise ValueError("âŒ PLANILHA_KPIS_URL deve ser definida como variÃ¡vel de ambiente")
    
    sheets_service = SheetsService()
    data_processor = DataProcessor()
    
    dados_raw = sheets_service.obter_dados_kpis(planilha_kpis_url)
    if dados_raw.empty:
        raise ValueError("âŒ Nenhum dado de KPIs encontrado")
    
    # process_kpis_data agora retorna List[KPI]
    kpis_processed_list = data_processor.process_kpis_data(dados_raw) 
    # _calculate_kpi_metrics espera uma List[KPI]
    metricas_calculadas = data_processor._calculate_kpi_metrics(kpis_processed_list) 
    
    # Atualiza cache
    _kpi_dados_cache.update({
        'dados_raw': dados_raw,
        'kpis_processed_list': kpis_processed_list,
        'metricas_calculadas': metricas_calculadas,
        'timestamp': time.time()
    })
    
    print(f"âœ… KPIs: Cache atualizado com {len(kpis_processed_list)} registros.")
    return kpis_processed_list, metricas_calculadas

@kpis_bp.route('/')
@login_required_v2
def index():
    """Dashboard principal de KPIs"""
    try:
        print("ðŸ“Š KPIs: Carregando dashboard...")
        
        # Apenas chamamos obter_kpis_cached. NÃ£o precisamos da lista completa aqui,
        # apenas das mÃ©tricas iniciais para popular os cards e filtros.
        _, metricas_iniciais = obter_kpis_cached() 
        
        # Obter listas Ãºnicas para preencher filtros, como categorias e edifÃ­cios
        # Podemos pegar isso das metricas_iniciais ou processar a lista completa de KPIs.
        # Para evitar processamento extra na UI, vamos extrair dos kpis_processed_list
        kpis_list, _ = obter_kpis_cached() # Obtem a lista completa para filtros
        
        categorias_unicas = sorted(list(set(k.categoria_problema for k in kpis_list if k.categoria_problema)))
        edificios_unicos = sorted(list(set(k.edificio for k in kpis_list if k.edificio)))
        equipamentos_unicos = sorted(list(set(k.equipamento for k in kpis_list if k.equipamento)))

        print(f"âœ… KPIs: Dashboard carregado. Total chamados: {metricas_iniciais.get('total_chamados', 0)}")
        
        return render_template('v2/kpis.html',
                             metricas=metricas_iniciais,
                             categorias_unicas=categorias_unicas,
                             edificios_unicos=edificios_unicos,
                             equipamentos_unicos=equipamentos_unicos,
                             usuario=AuthService.get_current_user())
                             
    except Exception as e:
        print(f"âŒ KPIs: Erro no dashboard: {e}")
        current_app.logger.exception(f"Erro ao carregar dashboard de KPIs: {e}") # Usando o logger
        return render_template('v2/kpis.html',
                             erro=f"Erro interno ao carregar KPIs: {str(e)}",
                             usuario=AuthService.get_current_user())

@kpis_bp.route('/atualizar-kpis', methods=['POST', 'GET'])
@api_auth_required # Protege e padroniza a resposta para esta API
def atualizar_dados_kpis():
    """Atualiza cache de dados de KPIs forÃ§adamente."""
    global _kpi_dados_cache
    
    # Limpa cache para forÃ§ar reload
    _kpi_dados_cache = {
        'dados_raw': None,
        'kpis_processed_list': None,
        'metricas_calculadas': None,
        'timestamp': None
    }
    
    # ForÃ§a nova obtenÃ§Ã£o
    try:
        kpis_list, _ = obter_kpis_cached()
        return {
            'success': True,
            'message': f'Cache de KPIs limpo e dados atualizados! {len(kpis_list)} registros processados.',
            'timestamp': datetime.now(pytz.timezone("America/Sao_Paulo")).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        current_app.logger.exception(f"Erro ao atualizar cache de KPIs: {e}")
        return {
            'success': False,
            'message': f'Erro interno ao atualizar KPIs: {str(e)}'
        }, 500