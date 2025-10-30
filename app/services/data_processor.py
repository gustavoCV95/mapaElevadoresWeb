# app/services/data_processor.py
"""
Processador de dados refatorado com models
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from app.utils.helpers import safe_int, safe_str, safe_float, validate_coordinates 
from app.models.elevator import Elevator
from app.models.building import Building
from app.models.kpi import KPI
import pytz
from collections import defaultdict
import numpy as np

class DataProcessor:
    def __init__(self, data=None):
        """Inicializa o processador com os dados brutos."""
        self.raw_data = data
        self.processed_data = None

    def process_all_elevators_and_buildings_data(self, df_detalhado: pd.DataFrame, df_info_elevadores: pd.DataFrame) -> Dict[str, Any]:
        """
        Processa dados de prédios e elevadores, correlaciona-os e cria objetos Building e Elevator.
        Gera GeoJSON agrupado por localização.
        """

        # --- PONTO DE INSPEÇÃO 0: Verificar 'montacarga' no df_info_elevadores original ---
        print("\nDEBUG: Verificando tipo 'montacarga' no df_info_elevadores original:")

        if df_detalhado.empty or df_info_elevadores.empty:
            print("❌ Um dos DataFrames de prédios ou elevadores está vazio. Não é possível processar.")
            return self._empty_processed_result()

        # --- 1. Criar objetos Building a partir de df_detalhado ---
        buildings: List[Building] = []
        # Garante que o ID do prédio é int ou None
        # df_detalhado['id'] = df_detalhado['id'].apply(safe_int) # Melhor usar apply para converter a coluna inteira
        # Remover linhas onde o id é None antes de processar os prédios
        df_detalhado_cleaned = df_detalhado.dropna(subset=['id']).copy()
        df_detalhado_cleaned['id'] = df_detalhado_cleaned['id'].astype(int) 
        df_detalhado_unique = df_detalhado_cleaned.drop_duplicates(subset=['id']).copy()

        print("\nProcessando 'Detalhado' para criar objetos Building...")
        for idx, row in df_detalhado_unique.iterrows():
            try:
                building_id = safe_int(row.get('id'))
                if building_id is None: # Pular prédios sem ID válido
                    print(f"Prédio sem ID válido na linha {idx}. Pulando.")
                    continue

                building_data = {
                    'id': building_id, # Já é Optional
                    'cidade': safe_str(row.get('cidade')),
                    'unidade': safe_str(row.get('unidade')),
                    'endereco': safe_str(row.get('endereco')),
                    'endereco_completo': safe_str(row.get('enderecoCompleto')),
                    'regiao': safe_str(row.get('regiao')),
                }
                buildings.append(Building.from_dict(building_data))
            except Exception as e:
                print(f"Erro ao criar modelo Building para registro {idx} (ID: {row.get('id')}): {e}")
                continue
        print(f"{len(buildings)} objetos Building criados.")

        # --- 2. Criar objetos Elevator a partir de df_info_elevadores e linkar com Building ---
        elevators: List[Elevator] = []
        building_map: Dict[Optional[int], Building] = {b.id: b for b in buildings if b.id is not None} # Mapear prédios por ID para acesso rápido

        # Garante que IDs são int ou None para o merge
        # df_info_elevadores['id'] = df_info_elevadores['id'].apply(safe_int)
        # df_info_elevadores['id_predio'] = df_info_elevadores['id_predio'].apply(safe_int)
        df_info_elevadores_cleaned = df_info_elevadores.dropna(subset=['id', 'id_predio']).copy() # Remover elevadores sem ID ou ID_predio
        df_info_elevadores_cleaned['id'] = df_info_elevadores_cleaned['id'].astype(int) 
        df_info_elevadores_cleaned['id_predio'] = df_info_elevadores_cleaned['id_predio'].astype(int) 


        print("\nProcessando 'info_elevadores' para criar objetos Elevator e correlacionar com Building...")
        for idx, row in df_info_elevadores_cleaned.iterrows():
            try:
                elevator_id = safe_int(row.get('id'))
                building_id = safe_int(row.get('id_predio'))

                if elevator_id is None:
                    print(f"Elevador sem ID válido na linha {idx}. Pulando.")
                    continue
                if building_id is None or building_id not in building_map:
                    print(f"Prédio com ID {building_id} não encontrado para elevador {elevator_id}. Pulando elevador.")
                    continue
                
                elevator_data = {
                    'id': elevator_id,
                    'id_predio': building_id,
                    'descricao': safe_str(row.get('descricao', f"Elevador {elevator_id}")),
                    'tipo': safe_str(row.get('tipo')),
                    'marca': safe_str(row.get('marca')),
                    'paradas': safe_int(row.get('paradas')), # Andares atendidos
                    'marca_licitacao': safe_str(row.get('marcaLicitacao')),
                    'status': safe_str(row.get('status', 'Em atividade')),
                    'latitude': safe_float(row.get('latitude')), # NOVO: direto do df_info_elevadores
                    'longitude': safe_float(row.get('longitude')), # NOVO: direto do df_info_elevadores
                    'empresa': safe_str(row.get('empresa')), # 'empresa' da info_elevadores
                    'capacidade_kg': safe_int(row.get('Capacidade (Kg)')),
                    'v_m_min': safe_int(row.get('V (m/min)')),
                    'no_break_resgate_automatico': safe_str(row.get('No-break / Resgate Automático')),
                    'periodicidade_manutencao_preventiva': safe_str(row.get('Periodicidade Manutenção Preventiva')),
                    'contrato': safe_str(row.get('Contrato')),
                    'data_de_parada': safe_str(row.get('DataDeParada')),
                    'previsao_de_retorno': safe_str(row.get('PrevisaoDeRetorno')),
                }
                
                elevator = Elevator.from_dict(elevator_data)
                
                # Injetar informações do Building no Elevator
                building_obj = building_map[building_id]
                elevator.cidade = building_obj.cidade
                elevator.unidade = building_obj.unidade
                elevator.endereco = building_obj.endereco
                elevator.endereco_completo = building_obj.endereco_completo
                elevator.regiao = building_obj.regiao
                elevator.building = building_obj # Referência ao objeto Building

                elevators.append(elevator)
                building_obj.elevators.append(elevator) # Adicionar elevador à lista do prédio
                
            except Exception as e:
                print(f"Erro ao criar modelo Elevator para registro {idx} (ID: {row.get('id')}): {e}")
                continue
        print(f"{len(elevators)} objetos Elevator individuais criados e correlacionados.")

        # --- 3. Calcular propriedades agregadas para Building ---
        print("\nCalculando propriedades agregadas para Buildings...")
        for building in buildings:
            building.total_elevadores = len(building.elevators)
            building.elevadores_parados = sum(1 for e in building.elevators if e.is_parado)
            building.elevadores_suspensos = sum(1 for e in building.elevators if e.is_suspenso)
            building.elevadores_ativos = building.total_elevadores - building.elevadores_parados - building.elevadores_suspensos
        
        # --- 4. Preparar saída para o dashboard (GeoJSON AGRUPADO) ---
        geojson_data = self._create_grouped_geojson(elevators)
 
        # Listas únicas para filtros da UI (baseados em elevadores)
        tipos_unicos = sorted(list(set([e.tipo for e in elevators])))
        regioes_unicas = sorted(list(set([e.regiao for e in elevators])))
        marcas_unicas = sorted(list(set([e.marca_licitacao for e in elevators])))
        empresas_unicas = sorted(list(set([e.empresa for e in elevators if e.empresa])))
        buildings_for_form = [b.to_dict() for b in buildings] # Chama o to_dict() atualizado do Building

        return {
            'geojson_data': geojson_data,
            'elevators': elevators, # Lista de modelos Elevator individuais
            'buildings': buildings, # Lista de modelos Building
            'tipos_unicos': tipos_unicos,
            'regioes_unicas': regioes_unicas,
            'marcas_unicas': marcas_unicas,
            'empresas_unicas': empresas_unicas,
            'buildings_for_form': buildings_for_form,
            'df_info_elevadores_current': df_info_elevadores # O DataFrame original da aba 'info_elevadores' (para salvar)
        }

    def _empty_processed_result(self) -> Dict[str, Any]:
        """Helper para retornar um dicionário de resultado vazio."""
        return {
            'geojson_data': {"type": "FeatureCollection", "features": []},
            'elevators': [],
            'buildings': [],
            'tipos_unicos': [],
            'regioes_unicas': [],
            'marcas_unicas': [],
            'empresas_unicas': [],
            'buildings_for_form': [],
            'df_info_elevadores_current': pd.DataFrame()
        }


    # NOVO: Método para criar GeoJSON agrupado por localização
    def _create_grouped_geojson(self, elevators: List[Elevator]) -> Dict[str, Any]:
        grouped_elevators = defaultdict(list)
        for elev in elevators:
            # Garante que latitude e longitude não são None ou np.nan antes de usar como chave
            if elev.latitude is not None and not np.isnan(elev.latitude) and \
               elev.longitude is not None and not np.isnan(elev.longitude):
                key = (elev.latitude, elev.longitude)
                grouped_elevators[key].append(elev)
            else:
                print(f"Elevador ID {elev.id} sem coordenadas válidas. Pulando no agrupamento GeoJSON.")


        features = []
        for (lat, lon), group in grouped_elevators.items():
            total_elevadores_grupo = len(group)
            
            status_prioritario = 'Em atividade'
            cor_marcador_grupo = '#28a745' # Verde
            
            if any(e.is_parado for e in group):
                status_prioritario = 'Parado'
                cor_marcador_grupo = '#dc3545' # Vermelho
            elif any(e.is_suspenso for e in group):
                status_prioritario = 'Suspenso'
                cor_marcador_grupo = '#ffc107' # Amarelo
            
            tamanho_marcador_grupo = 4
            if total_elevadores_grupo >= 5:
                tamanho_marcador_grupo = 8
            elif total_elevadores_grupo >= 3:
                tamanho_marcador_grupo = 6
            
            elevadores_no_grupo_details = []
            for e in group:
                elevadores_no_grupo_details.append({
                    'id': e.id,
                    'descricao': e.descricao,
                    'tipo': e.tipo,
                    'marca': e.marca_licitacao,
                    'status': e.status,
                    'data_de_parada': e.data_de_parada,
                    'previsao_de_retorno': e.previsao_de_retorno,
                    'empresa': e.empresa,
                })

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    'latitude': lat,
                    'longitude': lon,
                    'total_elevadores_grupo': total_elevadores_grupo,
                    'status_grupo_prioritario': status_prioritario,
                    'cor_marcador_grupo': cor_marcador_grupo,
                    'tamanho_marcador_grupo': tamanho_marcador_grupo,
                    'cidade': group[0].cidade, # Pegar cidade do primeiro elevador do grupo
                    'unidade': group[0].unidade, # Pegar unidade do primeiro elevador do grupo
                    'endereco': group[0].endereco,
                    'endereco_completo': group[0].endereco_completo,
                    'elevadores_no_grupo': elevadores_no_grupo_details 
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }

    # NOVO: Método para buscar elevador individual por ID único
    def get_elevator_by_id(self, elevators: List[Elevator], id_elevador: int) -> Optional[Elevator]:
        for e in elevators:
            if e.id == id_elevador:
                return e
        return None

    # NOVO: Método para buscar elevadores por localização do prédio
    def get_elevators_by_building_location(self, elevators: List[Elevator], cidade: str, unidade: str, endereco: str) -> List[Elevator]:
        filtered = [e for e in elevators if 
                    e.cidade.lower() == cidade.lower() and 
                    e.unidade.lower() == unidade.lower() and
                    e.endereco.lower() == endereco.lower()]
        return filtered

    def _format_date_string_for_sheet(self, date_value: Optional[str]) -> str:
        date_str = str(date_value) if date_value is not None else ''
        if '-' in date_str and len(date_str) == 10: # Heurística simples para YYYY-MM-DD
            try: return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%y')
            except ValueError: pass # Se falhar, use a string original
        return date_str

    # NOVO: Método para preparar o DataFrame 'info_elevadores' para escrita
    def prepare_df_info_elevadores_for_write(self, all_elevators: List[Elevator], original_df_info_elevadores: pd.DataFrame) -> pd.DataFrame:
        if original_df_info_elevadores.empty:
            raise ValueError("O DataFrame original de 'info_elevadores' está vazio. Não é possível atualizar.")

        df_updated = original_df_info_elevadores.copy()
        
        for elev_obj in all_elevators:
            # Verifica se o ID do elevador é None antes de tentar usá-lo
            if elev_obj.id is None:
                print(f"Elevador com ID None encontrado. Não será atualizado no DataFrame.")
                continue

            idx = df_updated[df_updated['id'] == elev_obj.id].index
            if not idx.empty:
                df_updated.loc[idx, 'status'] = elev_obj.status
                # Garante que None seja convertido para string vazia para a planilha
                #df_updated.loc[idx, 'DataDeParada'] = elev_obj.data_de_parada if elev_obj.data_de_parada is not None else '' 
                #df_updated.loc[idx, 'PrevisaoDeRetorno'] = elev_obj.previsao_de_retorno if elev_obj.previsao_de_retorno is not None else ''
                df_updated.loc[idx, 'DataDeParada'] = self._format_date_string_for_sheet(elev_obj.data_de_parada) if elev_obj.data_de_parada is not None else '' 
                df_updated.loc[idx, 'PrevisaoDeRetorno'] = self._format_date_string_for_sheet(elev_obj.previsao_de_retorno) if elev_obj.previsao_de_retorno is not None else ''
                
                if elev_obj.latitude is not None:
                    # Converte o float para string e substitui '.' por ','
                    df_updated.loc[idx, 'latitude'] = str(elev_obj.latitude)
                else:
                    df_updated.loc[idx, 'latitude'] = '' # Garante que seja string vazia se for None

                if elev_obj.longitude is not None:
                    # Converte o float para string e substitui '.' por ','
                    df_updated.loc[idx, 'longitude'] = str(elev_obj.longitude)
                else:
                    df_updated.loc[idx, 'longitude'] = '' # Garante que seja string vazia se for None            

            else:
                print(f"Elevador com ID {elev_obj.id} não encontrado no DataFrame original para atualização.")
        
        return df_updated
    
    def apply_filters(self, elevators: List[Elevator], tipos=None, regioes=None, 
                    marcas=None, empresas=None, situacoes=None) -> tuple[List[Elevator], List[str]]:
        """Aplica filtros à lista de elevadores individuais."""
        filtered = elevators.copy()
        
        if tipos:
            filtered = [e for e in filtered if e.tipo in tipos]
        
        if regioes:
            filtered = [e for e in filtered if e.regiao in regioes]
        
        if marcas:
            filtered = [e for e in filtered if e.marca_licitacao in marcas]
        
        if empresas:
            filtered = [e for e in filtered if e.empresa in empresas]
        
        situacoes_aplicadas = situacoes or []
        
        if situacoes:
            situacao_filtered_temp = []
            for situacao in situacoes:
                if situacao == 'suspensos':
                    situacao_filtered_temp.extend([e for e in filtered if e.is_suspenso])
                elif situacao == 'parados':
                    situacao_filtered_temp.extend([e for e in filtered if e.is_parado])
                elif situacao == 'ativos':
                    situacao_filtered_temp.extend([e for e in filtered if not e.is_parado and not e.is_suspenso])
            filtered = situacao_filtered_temp 
        
        print(f"Filtros aplicados resultaram em {len(filtered)} elevadores individuais.")
        
        return filtered, situacoes_aplicadas

    def calculate_stats(self, elevators: List[Elevator], situacoes_filtradas: List[str] = None) -> Dict[str, Any]:
        """Calcula estatísticas agregadas (agora com base em Elevators e Buildings)."""
        if not elevators:
            return {
                'total_elevadores': 0,
                'total_predios': 0,
                'cidades': 0,
                'regioes': 0,
                'em_atividade': 0,
                'elevadores_suspensos': 0,
                'elevadores_parados': 0
            }
        
        total_elevadores = len(elevators)
        elevadores_suspensos = sum(1 for e in elevators if e.is_suspenso)
        elevadores_parados = sum(1 for e in elevators if e.is_parado)
        elevadores_ativos = total_elevadores - elevadores_suspensos - elevadores_parados
        
        unique_predios = set(e.building.id for e in elevators) 
        unique_cidades = set(e.cidade for e in elevators)
        unique_regioes = set(e.regiao for e in elevators)

        stats = {
            'total_elevadores': total_elevadores,
            'total_predios': len(unique_predios),
            'cidades': len(unique_cidades),
            'regioes': len(unique_regioes),
            'em_atividade': elevadores_ativos,
            'elevadores_suspensos': elevadores_suspensos,
            'elevadores_parados': elevadores_parados
        }
        
        print(f"Stats calculados: Total={total_elevadores}, Ativos={elevadores_ativos}, Suspensos={elevadores_suspensos}, Parados={elevadores_parados}")
        
        return stats

    def calcular_estatisticas_detalhadas(self, elevators: List[Elevator], situacoes_filtradas: List[str] = None) -> Dict[str, Any]:
        """
        Calcula estatísticas detalhadas para elevadores individuais.
        A lista 'elevadores_parados' agora conterá Elevator.to_dict() de elevadores individuais.
        """
        if not elevators:
            return {
                'por_tipo': {}, 'por_regiao': {}, 'por_marca': {}, 'por_empresa': {}, 'por_status': {},
                'elevadores_parados': [] 
            }
        
        stats = {
            'por_tipo': defaultdict(int),
            'por_regiao': defaultdict(int),
            'por_marca': defaultdict(int),
            'por_status': defaultdict(int),
            'por_empresa': defaultdict(int),
            'elevadores_parados': []
        }
        
        for elevator in elevators:                
            if elevator.is_suspenso:
                stats['por_tipo'][elevator.tipo] += 1
                stats['por_regiao'][elevator.regiao] += 1
                stats['por_marca'][elevator.marca_licitacao] += 1
                stats['por_empresa'][elevator.empresa] += 1
                stats['por_status']['Suspensos'] += 1
            elif elevator.is_parado:
                stats['por_tipo'][elevator.tipo] += 1
                stats['por_regiao'][elevator.regiao] += 1
                stats['por_marca'][elevator.marca_licitacao] += 1
                stats['por_empresa'][elevator.empresa] += 1
                stats['por_status']['Parados'] += 1
                stats['elevadores_parados'].append(elevator.to_dict())
            else: # Em atividade
                stats['por_tipo'][elevator.tipo] += 1
                stats['por_regiao'][elevator.regiao] += 1
                stats['por_marca'][elevator.marca_licitacao] += 1
                stats['por_empresa'][elevator.empresa] += 1
                stats['por_status']['Em atividade'] += 1
        
        for categoria in ['por_tipo', 'por_regiao', 'por_marca', 'por_empresa', 'por_status']:
            stats[categoria] = dict(sorted(stats[categoria].items(), key=lambda x: x[1], reverse=True))
        
        print(f"Métricas detalhadas calculadas.")
        
        return stats

    def criar_geojson_manual(self, elevators: List[Elevator], situacoes_filtradas: List[str] = None):
        """Cria GeoJSON com base nos elevadores individuais filtrados (agora agrupado)."""
        # Este método agora simplesmente chama o método interno de agrupamento
        # Ele recebe os elevadores JÁ FILTRADOS
        return self._create_grouped_geojson(elevators)

    def process_kpis_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Processa dados de KPIs e calcula métricas
        NOVA IMPLEMENTAÇÃO com models
        """
        if data.empty:
            return {}
        
        print(f"Processando {len(data)} registros de KPIs...")
        
        kpis = []
        brt = pytz.timezone("America/Sao_Paulo")
        
        for idx, row in data.iterrows():
            try:
                # Converte datas
                data_solicitacao = None
                data_conclusao = None
                
                try:
                    data_solicitacao = pd.to_datetime(
                        row['data_solicitacao'], 
                        format='%d/%m/%Y %H:%M:%S', 
                        errors='coerce'
                    )
                except:
                    data_solicitacao = pd.to_datetime(row['data_solicitacao'], errors='coerce')
                
                try:
                    data_conclusao = pd.to_datetime(
                        row['data_conclusao'], 
                        format='%d/%m/%Y %H:%M:%S', 
                        errors='coerce'
                    )
                except:
                    data_conclusao = pd.to_datetime(row['data_conclusao'], errors='coerce')
                
                data_solicitacao_aware = brt.localize(data_solicitacao) if pd.notna(data_solicitacao) else None
                data_conclusao_aware = brt.localize(data_conclusao) if pd.notna(data_conclusao) else None
                
                if pd.isna(data_solicitacao_aware):
                    continue
                
                kpi_data = {
                    'edificio': safe_str(row.get('edificio')),
                    'categoria_problema': safe_str(row.get('categoria_problema')),
                    'status': safe_str(row.get('status')),
                    'data_solicitacao': data_solicitacao_aware,
                    'data_conclusao': data_conclusao_aware,
                    'equipamento': safe_str(row.get('equipamento'))
                }
                
                kpi = KPI(**kpi_data)
                kpis.append(kpi)
                
            except Exception as e:
                print(f"Erro ao processar KPI {idx}: {e}")
                continue
        
        # Calcula métricas usando os models
        return kpis
    
    def _calculate_kpi_metrics(self, kpis: List[KPI]) -> Dict[str, Any]:
        """Calcula métricas dos KPIs usando models"""
        if not kpis:
            return {}
        
        concluidos = [kpi for kpi in kpis if kpi.esta_concluido]
        
        # Métricas principais
        metricas = {
            'total_chamados': len(kpis),
            'chamados_concluidos': len(concluidos),
            'chamados_pendentes': len(kpis) - len(concluidos),
            'tempo_mediano_reparo': 0,
            'disponibilidade': (len(concluidos) / len(kpis) * 100) if kpis else 0,
        }
        
        # Tempo mediano de reparo
        tempos_reparo = [kpi.tempo_reparo_horas for kpi in concluidos if kpi.tempo_reparo_horas is not None]
        if tempos_reparo:
            import statistics
            metricas['tempo_mediano_reparo'] = statistics.median(tempos_reparo)
        
        # Chamados por mês
        chamados_por_mes = {}
        for kpi in kpis:
            mes = kpi.mes_ano
            chamados_por_mes[mes] = chamados_por_mes.get(mes, 0) + 1
        metricas['chamados_por_mes'] = chamados_por_mes
        
        # Chamados por edifí­cio
        chamados_por_edificio = {}
        for kpi in kpis:
            edificio = kpi.edificio
            chamados_por_edificio[edificio] = chamados_por_edificio.get(edificio, 0) + 1
        
        # Ordena e pega top 15
        chamados_por_edificio = dict(
            sorted(chamados_por_edificio.items(), key=lambda x: x[1], reverse=True)[:15]
        )
        metricas['chamados_por_edificio'] = chamados_por_edificio
        
        # Categorias de problema
        categorias_problema = {}
        for kpi in kpis:
            categoria = kpi.categoria_problema
            categorias_problema[categoria] = categorias_problema.get(categoria, 0) + 1
        metricas['categorias_problema'] = categorias_problema
        
        # Tempo por categoria
        tempo_por_categoria = {}
        for categoria in categorias_problema.keys():
            tempos_categoria = [
                kpi.tempo_reparo_horas for kpi in concluidos 
                if kpi.categoria_problema == categoria and kpi.tempo_reparo_horas is not None
            ]
            if tempos_categoria:
                import statistics
                tempo_por_categoria[categoria] = statistics.median(tempos_categoria)
        
        # Ordena por tempo decrescente
        tempo_por_categoria = dict(
            sorted(tempo_por_categoria.items(), key=lambda x: x[1], reverse=True)
        )
        metricas['tempo_por_categoria'] = tempo_por_categoria
        
        # Chamados por equipamento
        chamados_por_equipamento = {}
        for kpi in kpis:
            if kpi.equipamento:
                equipamento = str(kpi.equipamento)
                chamados_por_equipamento[equipamento] = chamados_por_equipamento.get(equipamento, 0) + 1
        
        # Ordena e pega top 20
        chamados_por_equipamento = dict(
            sorted(chamados_por_equipamento.items(), key=lambda x: x[1], reverse=True)[:20]
        )
        metricas['chamados_por_equipamento'] = chamados_por_equipamento
        
        # Tempo por equipamento
        tempo_por_equipamento = {}
        for equipamento in chamados_por_equipamento.keys():
            tempos_equipamento = [
                kpi.tempo_reparo_horas for kpi in concluidos 
                if str(kpi.equipamento) == equipamento and kpi.tempo_reparo_horas is not None
            ]
            if tempos_equipamento:
                import statistics
                tempo_por_equipamento[equipamento] = statistics.median(tempos_equipamento)
        
        # Ordena por tempo decrescente
        tempo_por_equipamento = dict(
            sorted(tempo_por_equipamento.items(), key=lambda x: x[1], reverse=True)[:20]
        )
        metricas['tempo_por_equipamento'] = tempo_por_equipamento
        
        print(f"Métricas processadas: {len(metricas)} categorias")
        return metricas

    def apply_kpi_filters(self, kpis: List['KPI'], data_inicio: datetime = None, data_fim: datetime = None, 
                          status: str = None, categoria: str = None, edificio: str = None, 
                          equipamento: str = None) -> List['KPI']:
        """
        Aplica filtros a uma lista de objetos KPI.
        """
        filtered_kpis = kpis

        if data_inicio:
            filtered_kpis = [k for k in filtered_kpis if k.data_solicitacao >= data_inicio]
        if data_fim:
            filtered_kpis = [k for k in filtered_kpis if k.data_solicitacao <= data_fim]
            
        if status:
            filtered_kpis = [k for k in filtered_kpis if k.status.lower() == status.lower()]
            
        if categoria:
            filtered_kpis = [k for k in filtered_kpis if k.categoria_problema.lower() == categoria.lower()]
            
        if edificio:
            filtered_kpis = [k for k in filtered_kpis if k.edificio.lower() == edificio.lower()]

        if equipamento:
            # Garante que 'equipamento' seja string para comparação, caso o model retorne outro tipo
            filtered_kpis = [k for k in filtered_kpis if str(k.equipamento).lower() == equipamento.lower()]
        
        print(f"KPIs: Filtros aplicados resultaram em {len(filtered_kpis)} KPIs.")
        return filtered_kpis