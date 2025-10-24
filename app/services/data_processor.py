# app/services/data_processor.py
"""
Processador de dados refatorado com models
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from app.utils.helpers import safe_int, safe_str, safe_float, validate_coordinates
from app.models.elevator import Elevator
from app.models.kpi import KPI
import pytz

class DataProcessor:
    def __init__(self, data=None):
        """Inicializa o processador com os dados brutos."""
        self.raw_data = data
        self.processed_data = None

    def process_elevators_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Processa dados de elevadores para o mapa
        MANTÉM COMPATIBILIDADE com código atual
        """
        elevators = []
        registros_processados = []
        
        print(f"Processando {len(data)} registros para o mapa...")
        
        for idx, row in data.iterrows():
            try:
                # Valida coordenadas
                lat_str = safe_str(row.get('latitude', '')).strip()
                lon_str = safe_str(row.get('longitude', '')).strip()
                
                if not lat_str or not lon_str or lat_str == 'nan' or lon_str == 'nan':
                    continue
                
                is_valid, lat, lon = validate_coordinates(lat_str, lon_str)
                if not is_valid:
                    continue
                
                # Cria modelo Elevator
                elevator_data = {
                    'cidade': safe_str(row.get('cidade')),
                    'unidade': safe_str(row.get('unidade')),
                    'endereco': safe_str(row.get('endereco')),
                    'endereco_completo': safe_str(row.get('enderecoCompleto')),
                    'tipo': safe_str(row.get('tipo')),
                    'quantidade': safe_int(row.get('quantidade')),
                    'marca': safe_str(row.get('marca')),
                    'marca_licitacao': safe_str(row.get('marcaLicitacao', row.get('marca', ''))),
                    'paradas': safe_int(row.get('paradas')),
                    'regiao': safe_str(row.get('regiao')),
                    'status': safe_str(row.get('status')),
                    'empresa': safe_str(row.get('empresa', 'N/A')),
                    'latitude': lat,
                    'longitude': lon,
                    'n_elevador_parado': safe_int(row.get('NElevadorParado', 0)),
                    'data_de_parada': safe_str(row.get('DataDeParada')),
                    'previsao_de_retorno': safe_str(row.get('PrevisaoDeRetorno'))
                }
                
                elevator = Elevator(**elevator_data)
                elevators.append(elevator)
                
                # MANTÉM COMPATIBILIDADE: converte de volta para dict
                registro_processado = elevator.to_dict()
                registros_processados.append(registro_processado)
                
            except Exception as e:
                print(f"Erro ao processar registro {idx}: {e}")
                continue
        
        print(f"{len(elevators)} elevators processados")
        
        if elevators:
            # Cria GeoJSON usando os models
            features = [elevator.to_geojson_feature() for elevator in elevators]
            geojson_data = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # Extrai listas Ãºnicas
            tipos_unicos = sorted(list(set([e.tipo for e in elevators])))
            regioes_unicas = sorted(list(set([e.regiao for e in elevators])))
            marcas_unicas = sorted(list(set([e.marca_licitacao for e in elevators])))
            empresas_unicas = sorted(list(set([e.empresa for e in elevators if e.empresa != 'N/A'])))
            predios_unicos = sorted(list(set([e.endereco_completo for e in elevators])))
            
            return {
                'geojson_data': geojson_data,
                'registros_processados': registros_processados,  # COMPATIBILIDADE
                'elevators': elevators,  # NOVO: lista de models
                'tipos_unicos': tipos_unicos,
                'regioes_unicas': regioes_unicas,
                'marcas_unicas': marcas_unicas,
                'empresas_unicas': empresas_unicas,
                'predios_unicos': predios_unicos
            }
        
        return {
            'geojson_data': {"type": "FeatureCollection", "features": []},
            'registros_processados': [],
            'elevators': [],
            'tipos_unicos': [],
            'regioes_unicas': [],
            'marcas_unicas': [],
            'empresas_unicas': [],
            'predios_unicos': []
        }

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

    def apply_filters(self, elevators: List[Elevator], tipos=None, regioes=None, 
                    marcas=None, empresas=None, situacoes=None) -> tuple[List[Elevator], List[str]]:
        """
        Aplica filtros aos elevadores
        RESPONSABILIDADE: Apenas filtrar dados, sem lógica de cálculo
        RETORNA: (elevators_filtrados, situacoes_aplicadas)
        """
        filtered = elevators.copy()
        
        # Filtros básicos
        if tipos:
            filtered = [e for e in filtered if e.tipo in tipos]
        
        if regioes:
            filtered = [e for e in filtered if e.regiao in regioes]
        
        if marcas:
            filtered = [e for e in filtered if e.marca_licitacao in marcas]
        
        if empresas:
            filtered = [e for e in filtered if e.empresa in empresas]
        
        situacoes_aplicadas = situacoes or []
        
        # Filtros de situação
        if situacoes:
            situacao_filtered = []
            for situacao in situacoes:
                if situacao == 'suspensos':
                    situacao_filtered.extend([e for e in filtered if e.status == 'Suspenso'])
                elif situacao == 'parados':
                    situacao_filtered.extend([e for e in filtered if e.tem_elevador_parado])
                elif situacao == 'ativos':
                    situacao_filtered.extend([e for e in filtered if e.status == 'Em atividade'])
            
            def criar_id(elevator):
                return f"{elevator.cidade}_{elevator.unidade}_{elevator.endereco}_{elevator.tipo}_{elevator.quantidade}_{elevator.paradas}_{elevator.latitude}_{elevator.longitude}"

            ids_vistos = set()
            filtered = []
            for elevator in situacao_filtered:
                elevator_id = criar_id(elevator)
                if elevator_id not in ids_vistos:
                    ids_vistos.add(elevator_id)
                    filtered.append(elevator)
            
        #df = pd.DataFrame(filtered)
        #df.to_excel(r"C:\Users\gusta\OneDrive\Área de Trabalho\DadosFiltrados.xlsx",index=False)
        print(f"Filtros aplicados: {sum(e.quantidade for e in elevators)} -> {sum(e.quantidade for e in filtered)} elevadores")
        
        return filtered, situacoes_aplicadas

    def apply_kpi_filters(self, kpis: List['KPI'], data_inicio: datetime = None, data_fim: datetime = None, 
                          status: str = None, categoria: str = None, edificio: str = None, 
                          equipamento: str = None) -> List['KPI']:
        """
        Aplica filtros a uma lista de objetos KPI.
        """
        filtered_kpis = kpis
        
        brt = pytz.timezone("America/Sao_Paulo")

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

    def calculate_stats(self, elevators: List[Elevator], situacoes_filtradas: List[str] = None) -> Dict[str, Any]:
        """
        Calcula estatísticas dos elevadores
        RESPONSABILIDADE: Apenas calcular, assumindo que dados já estão filtrados
        """
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
        
        situacoes_filtradas = situacoes_filtradas or []
        
        # Contadores
        total_elevadores = 0
        elevadores_suspensos = 0
        elevadores_parados = 0
        elevadores_ativos = 0
        
        # Lógica de cálculo baseada nos filtros aplicados
        if situacoes_filtradas == ['parados']:
            # FILTRO "PARADOS" ÚNICO: Conta APENAS os parados
            for elevator in elevators:
                elevadores_parados += elevator.n_elevador_parado
            total_elevadores = elevadores_parados
            
        elif situacoes_filtradas == ['suspensos']:
            # FILTRO "SUSPENSOS" ÚNICO: Conta APENAS os suspensos
            for elevator in elevators:
                elevadores_suspensos += elevator.quantidade
            total_elevadores = elevadores_suspensos
            
        elif situacoes_filtradas == ['ativos']:
            # FILTRO "ATIVOS" ÚNICO: Conta APENAS os ativos
            for elevator in elevators:
                ativos_neste_predio = elevator.quantidade - elevator.n_elevador_parado
                elevadores_ativos += ativos_neste_predio
            total_elevadores = elevadores_ativos
        
        elif set(situacoes_filtradas) == {'ativos', 'suspensos'}:
            # FILTRO MISTO: "ATIVOS" + "SUSPENSOS"
            for elevator in elevators:
                if elevator.status == 'Suspenso':
                    elevadores_suspensos += elevator.quantidade
                    total_elevadores += elevator.quantidade
                else:  # Em atividade
                    ativos_neste_predio = elevator.quantidade - elevator.n_elevador_parado
                    elevadores_ativos += ativos_neste_predio
                    total_elevadores += ativos_neste_predio
        
        elif set(situacoes_filtradas) == {'ativos', 'parados'}:
            # FILTRO MISTO: "ATIVOS" + "PARADOS"
            for elevator in elevators:
                ativos_neste_predio = elevator.quantidade - elevator.n_elevador_parado
                elevadores_ativos += ativos_neste_predio
                elevadores_parados += elevator.n_elevador_parado
                total_elevadores += elevator.quantidade
        
        elif set(situacoes_filtradas) == {'parados', 'suspensos'}:
            # FILTRO MISTO: "PARADOS" + "SUSPENSOS"
            for elevator in elevators:
                if elevator.status == 'Suspenso':
                    elevadores_suspensos += elevator.quantidade
                    total_elevadores += elevator.quantidade
                else:  # Em atividade com parados
                    elevadores_parados += elevator.n_elevador_parado
                    total_elevadores += elevator.n_elevador_parado
        
        else:
            # SEM FILTRO ou FILTRO COMPLETO: Lógica completa
            for elevator in elevators:                
                if elevator.status == 'Suspenso':
                    elevadores_suspensos += elevator.quantidade
                    total_elevadores += elevator.quantidade
                else:
                    elevadores_ativos += elevator.quantidade - elevator.n_elevador_parado
                    elevadores_parados += elevator.n_elevador_parado
                    total_elevadores += elevator.quantidade
        
        # Estatísticas gerais (sempre calculadas sobre dados filtrados)
        stats = {
            'total_elevadores': total_elevadores,
            'total_predios': len(set(e.endereco_completo for e in elevators)),
            'cidades': len(set(e.cidade for e in elevators)),
            'regioes': len(set(e.regiao for e in elevators)),
            'em_atividade': elevadores_ativos,
            'elevadores_suspensos': elevadores_suspensos,
            'elevadores_parados': elevadores_parados
        }
        
        print(f"Stats calculados: Total={total_elevadores}, Ativos={elevadores_ativos}, Suspensos={elevadores_suspensos}, Parados={elevadores_parados}")
        
        return stats