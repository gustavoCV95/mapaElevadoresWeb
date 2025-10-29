# app/blueprints/dashboard.py
from flask import Blueprint, render_template, jsonify, request, current_app
from app.utils.auth_decorators import login_required_v2, api_auth_required
from app.services.sheets_service import SheetsService
from app.services.data_processor import DataProcessor
from app.services.auth_service import AuthService
from app.models.elevator import Elevator
from app.models.building import Building # NOVO
from typing import List
import time
import pandas as pd # Adicionado para uso com DataFrames
from typing import Optional

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/v2')

# CACHE GLOBAL PARA DADOS PROCESSADOS
_dados_cache = {
    'df_detalhado': None,
    'df_info_elevadores': None,
    'elevators': None,  # Lista de objetos Elevator
    'buildings': None,  # Lista de objetos Building
    'processed_data': None, # Resultado completo do processamento do DataProcessor
    'timestamp': None
}

def obter_dados_cached():
    """Obtém dados com cache inteligente"""
    global _dados_cache
    
    # Verifica se cache é válido (5 minutos)
    cache_valido = (
        _dados_cache['timestamp'] and 
        (time.time() - _dados_cache['timestamp']) < current_app.config.get('CACHE_TIMEOUT', 300) and
        _dados_cache['elevators'] is not None and
        _dados_cache['buildings'] is not None
    )
    
    if cache_valido:
        print("Usando dados de elevadores e prédios do cache (multi-abas)")
        return _dados_cache['elevators'], _dados_cache['buildings'], _dados_cache['processed_data']
    
    # Recarrega dados
    print("Recarregando dados de elevadores e prédios (cache expirado ou inexistente - multi-abas)")
    planilha_url = current_app.config.get('PLANILHA_URL')
    if not planilha_url:
        raise ValueError("URL da planilha não configurada. Defina PLANILHA_URL nas variáveis de ambiente.")
    
    sheets_service = SheetsService()
    data_processor = DataProcessor()
    
    df_detalhado = sheets_service.obter_dados_detalhado(planilha_url)
    df_info_elevadores = sheets_service.obter_dados_elevadores_individuais(planilha_url)
    
    if df_detalhado.empty or df_info_elevadores.empty:
        raise ValueError("Nenhum dado encontrado em uma ou ambas as abas de elevadores. Verifique a planilha e os nomes das abas.")

    processed_result = data_processor.process_all_elevators_and_buildings_data(df_detalhado, df_info_elevadores)
    
    elevators = processed_result['elevators']
    buildings = processed_result['buildings']
    processed_data = processed_result # Contém geojson, listas únicas, df_info_elevadores_current, etc.
    
    _dados_cache.update({
        'df_detalhado': df_detalhado,
        'df_info_elevadores': df_info_elevadores, # DataFrame RAW da info_elevadores
        'elevators': elevators,
        'buildings': buildings,
        'processed_data': processed_data,
        'timestamp': time.time()
    })
    
    print(f"Cache de elevadores atualizado: {len(elevators)} elevadores individuais e {len(buildings)} prédios processados.")
    return elevators, buildings, processed_data

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required_v2 # Este é um endpoint de UI (renderiza HTML), então login_required_v2 é apropriado.
def index():
    """Dashboard principal da nova arquitetura"""
    try:
        print("Carregando dashboard...")
        all_elevators, all_buildings, processed_data = obter_dados_cached()
        
        data_processor = DataProcessor()
        stats = data_processor.calculate_stats(all_elevators, [])
        stats_detalhadas = data_processor.calcular_estatisticas_detalhadas(all_elevators, [])
        
        print(f"Dashboard carregado: {len(all_elevators)} elevadores, {len(all_buildings)} prédios")
        
        return render_template('dashboard.html',
                             geojson_data=processed_data['geojson_data'],
                             stats=stats,
                             stats_detalhadas=stats_detalhadas,
                             tipos_unicos=processed_data['tipos_unicos'],
                             regioes_unicas=processed_data['regioes_unicas'],
                             marcas_unicas=processed_data['marcas_unicas'],
                             empresas_unicas=processed_data['empresas_unicas'],
                             buildings_for_form=[b.to_dict() for b in all_buildings], # Passa dicts de Building
                             all_elevators_individual_json=[e.to_dict() for e in all_elevators], # Passa dicts de Elevator
                             usuario=AuthService.get_current_user(),
                             total_elevadores=len(all_elevators))
                             
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        current_app.logger.exception(f"Erro ao carregar dashboard: {e}") # Loga a exceção completa
        
        return render_template('dashboard.html',
                             erro=f"Erro interno: {str(e)}",
                             usuario=AuthService.get_current_user())

@dashboard_bp.route('/api/dados-elevadores-filtrados')
@api_auth_required
def api_dados_elevadores_filtrados():
    """API OTIMIZADA para obter dados filtrados"""
    start_time = time.time()
    
    all_elevators, _, _ = obter_dados_cached()
    
    tipos = request.args.getlist('tipo')
    regioes = request.args.getlist('regiao')
    marcas = request.args.getlist('marca')
    empresas = request.args.getlist('empresa')
    situacoes = request.args.getlist('situacao')
    
    print(f"API Filtros: tipos={tipos}, regioes={regioes}, marcas={marcas},empresas={empresas}, situacoes={situacoes}")
    
    data_processor = DataProcessor()
    elevators_filtered, situacoes_aplicadas = data_processor.apply_filters(
        all_elevators, 
        tipos=tipos,
        regioes=regioes,
        marcas=marcas,
        empresas=empresas,
        situacoes=situacoes
    )
    
    stats = data_processor.calculate_stats(elevators_filtered, situacoes_aplicadas)
    stats_detalhadas = data_processor.calcular_estatisticas_detalhadas(elevators_filtered, situacoes_aplicadas)
    
    geojson_filtrado = data_processor.criar_geojson_manual(elevators_filtered, situacoes_aplicadas)
    
    elapsed_time = time.time() - start_time
    print(f"Filtros aplicados em {elapsed_time:.2f}s: {len(elevators_filtered)} elevadores")
    
    # Retorna um dicionário, que api_auth_required (via json_response) irá converter para JSON e lidar com erros
    return jsonify({
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
    })
    
@dashboard_bp.route('/api/dados-elevadores')
def api_dados_elevadores():
    """
    API para obter TODOS os dados de elevadores (sem filtros)
    NOVA ROTA para suportar botão "Limpar Filtros"
    """
    start_time = time.time()
    print("API: Carregando todos os dados (sem filtros)...")
    
    all_elevators, _, processed_data = obter_dados_cached()
    
    data_processor = DataProcessor()
    stats = data_processor.calculate_stats(all_elevators, [])
    stats_detalhadas = data_processor.calcular_estatisticas_detalhadas(all_elevators, [])
    
    elapsed_time = time.time() - start_time
    print(f"Todos os dados carregados em {elapsed_time:.2f}s: {len(all_elevators)} elevadores")
    
    # Retorna um dicionário, que api_auth_required (via json_response) irá converter para JSON e lidar com erros
    return jsonify({
        'success': True,
        'data': {
            'geojson': processed_data['geojson_data'],
            'stats': stats,
            'stats_detalhadas': stats_detalhadas,
            'total_registros': len(all_elevators),
            'performance': {
                'tempo_processamento': f"{elapsed_time:.2f}s",
                'fonte_dados': 'cache'
            }
        }
    })
    
@dashboard_bp.route('/atualizar-dados', methods=['POST', 'GET'])
@login_required_v2
def atualizar_dados():
    """Atualiza cache de dados forçadamente"""
    try:
        global _dados_cache
        
        # OTIMIZAÇÃO: Limpa cache para forçar reload
        _dados_cache = {
            'dados_raw': None,
            'processed_data': None,
            'elevators': None,
            'timestamp': None
        }
        
        # Força nova obtenção
        elevators, processed_data = obter_dados_cached()
        
        return jsonify({
            'success': True,
            'message': f'Cache limpo e dados atualizados! {len(elevators)} registros processados.',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"Erro ao atualizar dados: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })

@dashboard_bp.route('/api/elevadores/gerenciar', methods=['POST'])
@api_auth_required 
def gerenciar_elevador():
    """
    API para gerenciar o status de elevadores individuais (marcar como parado/ativo/suspenso).
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Dados JSON ausentes.'}), 400

    acao = data.get('acao') # 'adicionar', 'editar', 'remover' (remover do status de parado)
    id_elevador = data.get('id') # ID do elevador individual
    
    planilha_url = current_app.config.get('PLANILHA_URL')
    if not planilha_url:
        return jsonify({'success': False, 'message': 'URL da planilha não configurada.'}), 500

    sheets_service = SheetsService()
    data_processor = DataProcessor()

    try:
        # Carregamos a versão mais recente dos dados da aba 'info_elevadores' do cache
        # O cache guarda o df_info_elevadores_current que representa o estado atual da planilha
        # e a lista de objetos Elevator (all_elevators_current) que é o estado atual em memória.
        all_elevators_current, _, processed_data_current = obter_dados_cached()
        df_info_elevadores_original = processed_data_current['df_info_elevadores_current'] 

        if not all_elevators_current or df_info_elevadores_original.empty:
            return jsonify({'success': False, 'message': 'Dados de elevadores não carregados no cache ou planilha vazia.'}), 500

        elevador_a_modificar: Optional[Elevator] = None

        if acao in ['adicionar', 'editar']:
            if id_elevador is None:
                return jsonify({'success': False, 'message': 'ID do elevador é obrigatório para adicionar/editar.'}), 400
            
            elevador_a_modificar = data_processor.get_elevator_by_id(all_elevators_current, id_elevador)
            if not elevador_a_modificar:
                 return jsonify({'success': False, 'message': f'Elevador com ID {id_elevador} não encontrado.'}), 404
            
            new_status = data.get('status','Parado')
            original_status = elevador_a_modificar.status # Pega o status atual do elevador ANTES da mudança

            if new_status.lower() == 'parado' and original_status.lower() == 'parado':
                # Permitir a edição se o status *não mudou* para 'parado'
                # mas o elevador já está parado. Apenas avançar e permitir atualização de datas.
                pass 
            elif new_status.lower() == 'suspenso' and original_status.lower() == 'suspenso':
                # Similar para "Suspenso"
                pass
            elif (new_status.lower() == 'parado' or new_status.lower() == 'suspenso') and \
                 (original_status.lower() == 'parado' or original_status.lower() == 'suspenso'):
                # Caso o usuário tente mudar de "Parado" para "Suspenso" ou vice-versa,
                # E ele já está em um desses estados, isso é uma edição válida.
                # Não bloqueamos aqui.
                pass
            elif (new_status.lower() == 'parado' or new_status.lower() == 'suspenso') and \
                 (original_status.lower() != 'parado' and original_status.lower() != 'suspenso'):
                pass     

            # Atualiza o status e as datas no objeto Elevator em memória
            elevador_a_modificar.status = new_status
            elevador_a_modificar.data_de_parada = data.get('data_de_parada')
            elevador_a_modificar.previsao_de_retorno = data.get('previsao_de_retorno')

            message = f"Elevador ID {id_elevador} (Prédio ID: {elevador_a_modificar.id_predio}) atualizado para status '{elevador_a_modificar.status}'."

        elif acao == 'remover': # Alterar de "Parado" para "Em atividade"
            if id_elevador is None:
                return jsonify({'success': False, 'message': 'ID do elevador é obrigatório para remover.'}), 400
            
            elevador_a_modificar = data_processor.get_elevator_by_id(all_elevators_current, id_elevador)
            if not elevador_a_modificar:
                return jsonify({'success': False, 'message': f'Elevador com ID {id_elevador} não encontrado.'}), 404
            
            elevador_a_modificar.status = 'Em atividade'
            elevador_a_modificar.data_de_parada = None
            elevador_a_modificar.previsao_de_retorno = None
            message = f"Elevador ID {id_elevador} (Prédio ID: {elevador_a_modificar.id_predio}) alterado para 'Em atividade' e datas limpas."

        else:
            return jsonify({'success': False, 'message': 'Ação inválida.'}), 400
        
        # Prepara o DataFrame atualizado para escrita na planilha 'info_elevadores'
        df_to_save = data_processor.prepare_df_info_elevadores_for_write(all_elevators_current, df_info_elevadores_original)

        # Salva o DataFrame modificado de volta na planilha
        if sheets_service.salvar_elevadores_individuais(planilha_url, df_to_save):
            # Limpa o cache para forçar a recarga dos dados atualizados na próxima requisição
            global _dados_cache
            _dados_cache = {k: None for k in _dados_cache} # Limpa tudo
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': 'Falha ao salvar dados na planilha.'}), 500

    except Exception as e:
        current_app.logger.exception(f"Erro na API de gerenciar elevador: {e}")
        return jsonify({'success': False, 'message': f'Ocorreu um erro interno: {str(e)}'}), 500
