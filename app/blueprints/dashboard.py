# app/blueprints/dashboard.py
from flask import Blueprint, render_template, jsonify, request, current_app
from app.utils.auth_decorators import login_required_v2, api_auth_required # Importa api_auth_required
from app.services.sheets_service import SheetsService
from app.services.data_processor import DataProcessor
from app.services.auth_service import AuthService
from app.models.elevator import Elevator
from typing import List
import time

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/v2')

# CACHE GLOBAL PARA DADOS PROCESSADOS
_dados_cache = {
    'dados_raw': None,
    'processed_data': None,
    'elevators': None,
    'timestamp': None
}

def obter_dados_cached():
    """Obtém dados com cache inteligente"""
    global _dados_cache
    
    # Verifica se cache é válido (5 minutos)
    cache_valido = (
        _dados_cache['timestamp'] and 
        (time.time() - _dados_cache['timestamp']) < 300
    )
    
    if cache_valido and _dados_cache['elevators']:
        print("ðŸ“¦ Usando dados do cache")
        return _dados_cache['elevators'], _dados_cache['processed_data']
    
    # Recarrega dados
    print("ðŸ”„ Recarregando dados (cache expirado)")
    planilha_url = current_app.config.get('PLANILHA_URL')
    if not planilha_url:
        raise ValueError("URL da planilha nÃ£o configurada")
    
    sheets_service = SheetsService()
    data_processor = DataProcessor()
    
    dados_raw = sheets_service.obter_dados_elevadores(planilha_url)
    if dados_raw.empty:
        raise ValueError("Nenhum dado encontrado")
    
    processed_data = data_processor.process_elevators_data(dados_raw)
    elevators = [Elevator.from_dict(props) for props in processed_data['registros_processados']]
    
    # Atualiza cache
    _dados_cache.update({
        'dados_raw': dados_raw,
        'processed_data': processed_data,
        'elevators': elevators,
        'timestamp': time.time()
    })
    
    print(f"âœ… Cache atualizado: {len(elevators)} elevadores")
    return elevators, processed_data


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required_v2 # Este é um endpoint de UI (renderiza HTML), então login_required_v2 é apropriado.
def index():
    """Dashboard principal da nova arquitetura"""
    try:
        print("Carregando dashboard...")
        elevators, processed_data = obter_dados_cached()
        
        data_processor = DataProcessor()
        stats = data_processor.calculate_stats(elevators)
        stats_detalhadas = calcular_estatisticas_detalhadas(elevators)
        
        print(f"âœ… Dashboard carregado: {len(elevators)} elevadores, {stats['total_predios']} prÃ©dios")
        
        return render_template('v2/dashboard.html',
                             geojson_data=processed_data['geojson_data'],
                             stats=stats,
                             stats_detalhadas=stats_detalhadas,
                             tipos_unicos=processed_data['tipos_unicos'],
                             regioes_unicas=processed_data['regioes_unicas'],
                             marcas_unicas=processed_data['marcas_unicas'],
                             empresas_unicas=processed_data['empresas_unicas'],
                             usuario=AuthService.get_current_user(),
                             total_elevadores=len(elevators))
                             
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        return render_template('v2/dashboard.html',
                             erro=f"Erro interno: {str(e)}",
                             usuario=AuthService.get_current_user())

@dashboard_bp.route('/api/dados-elevadores-filtrados')
@api_auth_required # Este Ã© um endpoint de API, entÃ£o api_auth_required Ã© mais apropriado.
def api_dados_elevadores_filtrados():
    """API OTIMIZADA para obter dados filtrados"""
    start_time = time.time()
    
    elevators, processed_data = obter_dados_cached()
    
    tipos = request.args.getlist('tipo')
    regioes = request.args.getlist('regiao')
    marcas = request.args.getlist('marca')
    empresas = request.args.getlist('empresa')
    situacoes = request.args.getlist('situacao')
    
    print(f"ðŸ” API Filtros: tipos={tipos}, regioes={regioes}, situacoes={situacoes}")
    
    data_processor = DataProcessor()
    elevators_filtered = data_processor.apply_filters(
        elevators,
        tipos=tipos,
        regioes=regioes,
        marcas=marcas,
        empresas=empresas,
        situacoes=situacoes
    )
    
    stats = data_processor.calculate_stats(elevators_filtered)
    stats_detalhadas = calcular_estatisticas_detalhadas(elevators_filtered)
    
    geojson_filtrado = criar_geojson_manual(elevators_filtered)
    
    elapsed_time = time.time() - start_time
    print(f"âœ… Filtros aplicados em {elapsed_time:.2f}s: {len(elevators_filtered)} elevadores")
    
    # Retorna um dicionÃ¡rio, que api_auth_required (via json_response) irÃ¡ converter para JSON e lidar com erros
    return {
        'success': True,
        'data': {
            'geojson': geojson_filtrado,
            'stats': stats,
            'stats_detalhadas': stats_detalhadas,
            'total_registros': len(elevators_filtered),
            'performance': {
                'tempo_processamento': f"{elapsed_time:.2f}s",
                'fonte_dados': 'cache'
            }
        }
    }
    
@dashboard_bp.route('/api/dados-elevadores')
@api_auth_required # Este Ã© um endpoint de API, entÃ£o api_auth_required Ã© mais apropriado.
def api_dados_elevadores():
    """
    API para obter TODOS os dados de elevadores (sem filtros)
    NOVA ROTA para suportar botÃ£o "Limpar Filtros"
    """
    start_time = time.time()
    print("ðŸ”„ API: Carregando todos os dados (sem filtros)...")
    
    elevators, processed_data = obter_dados_cached()
    
    data_processor = DataProcessor()
    stats = data_processor.calculate_stats(elevators)
    stats_detalhadas = calcular_estatisticas_detalhadas(elevators)
    
    elapsed_time = time.time() - start_time
    print(f"âœ… Todos os dados carregados em {elapsed_time:.2f}s: {len(elevators)} elevadores")
    
    # Retorna um dicionÃ¡rio, que api_auth_required (via json_response) irÃ¡ converter para JSON e lidar com erros
    return {
        'success': True,
        'data': {
            'geojson': processed_data['geojson_data'],
            'stats': stats,
            'stats_detalhadas': stats_detalhadas,
            'total_registros': len(elevators),
            'performance': {
                'tempo_processamento': f"{elapsed_time:.2f}s",
                'fonte_dados': 'cache'
            }
        }
    }
    
@dashboard_bp.route('/atualizar-dados', methods=['POST', 'GET'])
@api_auth_required # Este Ã© um endpoint de API, entÃ£o api_auth_required Ã© mais apropriado.
def atualizar_dados():
    """Atualiza cache de dados forÃ§adamente"""
    global _dados_cache
    
    _dados_cache = {
        'dados_raw': None,
        'processed_data': None,
        'elevators': None,
        'timestamp': None
    }
    
    elevators, processed_data = obter_dados_cached()
    
    # Retorna um dicionÃ¡rio, que api_auth_required (via json_response) irÃ¡ converter para JSON e lidar com erros
    return {
        'success': True,
        'message': f'Cache limpo e dados atualizados! {len(elevators)} registros processados.',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

def calcular_estatisticas_detalhadas(elevators):
    """
    Calcula estatÃ­sticas detalhadas CORRIGIDO
    IMPORTANTE: Usa a mesma lÃ³gica do calculate_stats para consistÃªncia
    """
    from collections import defaultdict
    
    if not elevators:
        return {
            'por_tipo': {},
            'por_regiao': {},
            'por_marca': {},
            'por_status': {},
            'elevadores_parados': []
        }
    
    # âœ… DETECTA TIPO DE FILTRO (mesma lÃ³gica do calculate_stats)
    filtro_parados = all(e.tem_elevador_parado for e in elevators)
    filtro_suspensos = all(e.status == 'Suspenso' for e in elevators)
    filtro_ativos = all(e.status == 'Em atividade' and not e.tem_elevador_parado for e in elevators)
    
    stats = {
        'por_tipo': defaultdict(int),
        'por_regiao': defaultdict(int),
        'por_marca': defaultdict(int),
        'por_status': defaultdict(int),
        'elevadores_parados': []
    }
    
    if filtro_parados:
        # âœ… FILTRO "PARADOS": Conta APENAS os parados
        for elevator in elevators:
            # Por tipo/regiÃ£o/marca: conta apenas elevadores parados
            stats['por_tipo'][elevator.tipo] += elevator.n_elevador_parado
            stats['por_regiao'][elevator.regiao] += elevator.n_elevador_parado
            stats['por_marca'][elevator.marca_licitacao] += elevator.n_elevador_parado
            
            # Por status: apenas parados
            stats['por_status']['Parados'] += elevator.n_elevador_parado
            
            # Detalhes dos elevadores parados
            stats['elevadores_parados'].append({
                'unidade': elevator.unidade,
                'cidade': elevator.cidade,
                'tipo': elevator.tipo,
                'regiao': elevator.regiao,
                'quantidade_parada': elevator.n_elevador_parado,
                'total_elevadores': elevator.quantidade,
                'marca': elevator.marca_licitacao
            })
            
    elif filtro_suspensos:
        # âœ… FILTRO "SUSPENSOS": Conta APENAS os suspensos
        for elevator in elevators:
            stats['por_tipo'][elevator.tipo] += elevator.quantidade
            stats['por_regiao'][elevator.regiao] += elevator.quantidade
            stats['por_marca'][elevator.marca_licitacao] += elevator.quantidade
            stats['por_status']['Suspensos'] += elevator.quantidade
            
    elif filtro_ativos:
        # âœ… FILTRO "ATIVOS": Conta APENAS os ativos
        for elevator in elevators:
            stats['por_tipo'][elevator.tipo] += elevator.quantidade
            stats['por_regiao'][elevator.regiao] += elevator.quantidade
            stats['por_marca'][elevator.marca_licitacao] += elevator.quantidade
            stats['por_status']['Em atividade'] += elevator.quantidade
            
    else:
        # âœ… SEM FILTRO ou FILTRO MISTO: LÃ³gica completa
        for elevator in elevators:
            # Por tipo/regiÃ£o/marca: soma total de elevadores
            stats['por_tipo'][elevator.tipo] += elevator.quantidade
            stats['por_regiao'][elevator.regiao] += elevator.quantidade
            stats['por_marca'][elevator.marca_licitacao] += elevator.quantidade
            
            # Por status: lÃ³gica completa
            if elevator.status == 'Suspenso':
                stats['por_status']['Suspensos'] += elevator.quantidade
            elif elevator.tem_elevador_parado:
                stats['por_status']['Parados'] += elevator.n_elevador_parado
                ativos_deste_predio = elevator.quantidade - elevator.n_elevador_parado
                stats['por_status']['Em atividade'] += ativos_deste_predio
                
                # Detalhes dos elevadores parados
                stats['elevadores_parados'].append({
                    'unidade': elevator.unidade,
                    'cidade': elevator.cidade,
                    'tipo': elevator.tipo,
                    'regiao': elevator.regiao,
                    'quantidade_parada': elevator.n_elevador_parado,
                    'total_elevadores': elevator.quantidade,
                    'marca': elevator.marca_licitacao
                })
            else:
                stats['por_status']['Em atividade'] += elevator.quantidade
    
    # Converte para dict normal e ordena
    for categoria in ['por_tipo', 'por_regiao', 'por_marca']:
        stats[categoria] = dict(sorted(stats[categoria].items(), key=lambda x: x[1], reverse=True))
    
    # Status mantÃ©m ordem especÃ­fica
    stats['por_status'] = dict(stats['por_status'])
    
    print(f"ðŸ“Š Stats detalhadas: {dict(stats['por_status'])}")
    
    return stats

@dashboard_bp.route('/atualizar-dados', methods=['POST', 'GET'])
@login_required_v2
def atualizar_dados():
    """Atualiza cache de dados forÃ§adamente"""
    try:
        global _dados_cache
        
        # âœ… OTIMIZAÃ‡ÃƒO: Limpa cache para forÃ§ar reload
        _dados_cache = {
            'dados_raw': None,
            'processed_data': None,
            'elevators': None,
            'timestamp': None
        }
        
        # ForÃ§a nova obtenÃ§Ã£o
        elevators, processed_data = obter_dados_cached()
        
        return jsonify({
            'success': True,
            'message': f'Cache limpo e dados atualizados! {len(elevators)} registros processados.',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"âŒ Erro ao atualizar dados: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })

def criar_geojson_manual(elevators: List[Elevator]):
    """Cria GeoJSON otimizado"""
    features = []
    
    for elevator in elevators:
        if hasattr(elevator, 'latitude') and hasattr(elevator, 'longitude'):
            try:
                lat = float(elevator.latitude)
                lng = float(elevator.longitude)
                
                # Pula coordenadas invÃ¡lidas
                if lat == 0 or lng == 0:
                    continue
                    
                feature = elevator.to_geojson_feature()

                # Adicione uma validaÃ§Ã£o extra caso to_geojson_feature retorne None por algum motivo
                if feature:
                    features.append(feature)

            except (ValueError, TypeError):
                continue
    
    return {
        "type": "FeatureCollection",
        "features": features
    }