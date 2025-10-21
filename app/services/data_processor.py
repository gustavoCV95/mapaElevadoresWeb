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
                
                if pd.isna(data_solicitacao):
                    continue
                
                kpi_data = {
                    'edificio': safe_str(row.get('edificio')),
                    'categoria_problema': safe_str(row.get('categoria_problema')),
                    'status': safe_str(row.get('status')),
                    'data_solicitacao': data_solicitacao,
                    'data_conclusao': data_conclusao if not pd.isna(data_conclusao) else None,
                    'equipamento': safe_str(row.get('equipamento'))
                }
                
                kpi = KPI(**kpi_data)
                kpis.append(kpi)
                
            except Exception as e:
                print(f"Erro ao processar KPI {idx}: {e}")
                continue
        
        # Calcula mÃ©tricas usando os models
        return kpis
    
    def _calculate_kpi_metrics(self, kpis: List[KPI]) -> Dict[str, Any]:
        """Calcula métricas dos KPIs usando models"""
        if not kpis:
            return {}
        
        concluidos = [kpi for kpi in kpis if kpi.esta_concluido]
        
        # MÃ©tricas principais
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
        
        # Chamados por mÃªs
        chamados_por_mes = {}
        for kpi in kpis:
            mes = kpi.mes_ano
            chamados_por_mes[mes] = chamados_por_mes.get(mes, 0) + 1
        metricas['chamados_por_mes'] = chamados_por_mes
        
        # Chamados por edifÃ­cio
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
        
        print(f"âœ… Métricas processadas: {len(metricas)} categorias")
        return metricas

    def apply_filters(self, elevators: List[Elevator], tipos=None, regioes=None, 
                    marcas=None, empresas=None, situacoes=None) -> List[Elevator]:
        """
        Aplica filtros aos elevadores
        CORRIGIDO: LÃ³gica baseada na anÃ¡lise da planilha real
        """
        filtered = elevators.copy()
        
        if tipos:
            filtered = [e for e in filtered if e.tipo in tipos]
        
        if regioes:
            filtered = [e for e in filtered if e.regiao in regioes]
        
        if marcas:
            filtered = [e for e in filtered if e.marca_licitacao in marcas]
        
        if empresas:
            filtered = [e for e in filtered if e.empresa in empresas]
        
        if situacoes:
            situacao_filtered = []
            for situacao in situacoes:
                if situacao == 'suspensos':
                    # PrÃ©dios com status "Suspenso"
                    situacao_filtered.extend([e for e in filtered if e.status == 'Suspenso'])
                elif situacao == 'parados':
                    # âœ… CORRIGIDO: PrÃ©dios que tÃªm elevadores parados (NElevadorParado > 0)
                    situacao_filtered.extend([e for e in filtered if e.tem_elevador_parado])
                elif situacao == 'ativos':
                    # âœ… CORRIGIDO: PrÃ©dios com status "Em atividade" E sem elevadores parados
                    situacao_filtered.extend([e for e in filtered if e.status == 'Em atividade' and not e.tem_elevador_parado])
            
            # Remove duplicatas mantendo ordem
            seen = set()
            filtered = []
            for e in situacao_filtered:
                if e.endereco_completo not in seen:
                    seen.add(e.endereco_completo)
                    filtered.append(e)
        
        print(f"ðŸ” Filtros aplicados: {len(elevators)} -> {len(filtered)} elevadores")
        if situacoes:
            print(f"   SituaçÃµes filtradas: {situacoes}")
            for situacao in situacoes:
                count = sum(1 for e in filtered if (
                    (situacao == 'suspensos' and e.status == 'Suspenso') or
                    (situacao == 'parados' and e.tem_elevador_parado) or
                    (situacao == 'ativos' and e.status == 'Em atividade' and not e.tem_elevador_parado)
                ))
                print(f"   {situacao}: {count} elevadores")
        
        return filtered

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
            
            filtered_kpis = sorted(filtered_kpis, key = lambda k: k.data_conclusao or datetime.min, reverse = True)
        
        print(f"KPIs: Filtros aplicados resultaram em {len(filtered_kpis)} KPIs.")
        return filtered_kpis

    def calculate_stats(self, elevators: List[Elevator]) -> Dict[str, Any]:
        """
        Calcula estatÃ­sticas dos elevadores
        CORRIGIDO: Quando filtrado por "parados", conta apenas os parados
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
        
        # âœ… VERIFICAR SE Ã‰ UM FILTRO ESPECÃFICO
        # Se todos os elevators tÃªm parados, Ã© filtro "parados"
        filtro_parados = all(e.tem_elevador_parado for e in elevators)
        filtro_suspensos = all(e.status == 'Suspenso' for e in elevators)
        filtro_ativos = all(e.status == 'Em atividade' and not e.tem_elevador_parado for e in elevators)
        
        total_elevadores = 0
        elevadores_suspensos = 0
        elevadores_parados = 0
        elevadores_ativos = 0
        
        if filtro_parados:
            # âœ… FILTRO "PARADOS": Conta APENAS os parados
            for elevator in elevators:
                elevadores_parados += elevator.n_elevador_parado
            total_elevadores = elevadores_parados
            
        elif filtro_suspensos:
            # âœ… FILTRO "SUSPENSOS": Conta APENAS os suspensos
            for elevator in elevators:
                elevadores_suspensos += elevator.quantidade
            total_elevadores = elevadores_suspensos
            
        elif filtro_ativos:
            # âœ… FILTRO "ATIVOS": Conta APENAS os ativos
            for elevator in elevators:
                elevadores_ativos += elevator.quantidade
            total_elevadores = elevadores_ativos
            
        else:
            # âœ… SEM FILTRO ou FILTRO MISTO: LÃ³gica completa
            for elevator in elevators:
                total_elevadores += elevator.quantidade
                
                if elevator.status == 'Suspenso':
                    elevadores_suspensos += elevator.quantidade
                elif elevator.tem_elevador_parado:
                    elevadores_parados += elevator.n_elevador_parado
                    elevadores_ativos += (elevator.quantidade - elevator.n_elevador_parado)
                else:
                    elevadores_ativos += elevator.quantidade
        
        stats = {
            'total_elevadores': total_elevadores,
            'total_predios': len(set(e.endereco_completo for e in elevators)),
            'cidades': len(set(e.cidade for e in elevators)),
            'regioes': len(set(e.regiao for e in elevators)),
            'em_atividade': elevadores_ativos,
            'elevadores_suspensos': elevadores_suspensos,
            'elevadores_parados': elevadores_parados
        }
        
        print(f"ðŸ“Š Stats calculados: Total={total_elevadores}, Ativos={elevadores_ativos}, Suspensos={elevadores_suspensos}, Parados={elevadores_parados}")
        
        return stats