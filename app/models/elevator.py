#app/models/elevator.py
"""
Modelo para representar um elevador
"""
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, TYPE_CHECKING
import pandas as pd
from app.utils.helpers import safe_int, safe_str, safe_float

if TYPE_CHECKING:
    from .building import Building

@dataclass
class Elevator:
    """Modelo para representar um elevador"""

    id: Optional[int]  # ID único deste elevador físico (coluna 'id' da info_elevadores)
    id_predio: Optional[int]  # FK para Building.id (coluna 'id_predio' da info_elevadores)
    descricao: str  # Ex: "Elevador A", "Serviço" (coluna 'descricao')
    tipo: str # (coluna 'tipo')
    marca: str # (coluna 'marca')
    paradas: Optional[int]  # Número de andares/paradas que o elevador atende (coluna 'paradas')
    marca_licitacao: str # (coluna 'marcaLicitacao')
    status: str  # "Em atividade", "Parado", "Suspenso" (coluna 'status')
    latitude: Optional[float] # NOVO: Latitude do elevador individual
    longitude: Optional[float] # NOVO: Longitude do elevador individual
    empresa: Optional[str] = field(default=None) # Coluna 'empresa' da info_elevadores
    capacidade_kg: Optional[int] = None  # Coluna 'Capacidade (Kg)'
    v_m_min: Optional[int] = None  # Coluna 'V (m/min)'
    no_break_resgate_automatico: Optional[str] = None  # Coluna 'No-break / Resgate Automático'
    periodicidade_manutencao_preventiva: Optional[str] = None  # Coluna 'Periodicidade Manutenção Preventiva'
    contrato: Optional[str] = None  # Coluna 'Contrato'
    data_de_parada: Optional[str] = None  # Coluna 'DataDeParada' (DESTE elevador)
    previsao_de_retorno: Optional[str] = None  # Coluna 'PrevisaoDeRetorno' (DESTE elevador)
    
    # Atributos do prédio que serão INJETADOS (populados) pelo DataProcessor
    cidade: str = field(init=False)
    unidade: str = field(init=False)
    endereco: str = field(init=False)
    endereco_completo: str = field(init=False)
    regiao: str = field(init=False)


    # Referência ao objeto Building pai, para acesso mais fácil (optional, mas boa prática OO)
    building: Optional['Building'] = field(default=None, repr=False, init=False)


    def __post_init__(self):
        # Convertendo strings para int de forma segura para campos opcionais numéricos
        self.capacidade_kg = safe_int(self.capacidade_kg)
        self.v_m_min = safe_int(self.v_m_min)
        self.paradas = safe_int(self.paradas)

        # Assegura que DataDeParada/PrevisaoDeRetorno são strings ou None
        self.data_de_parada = str(self.data_de_parada) if pd.notna(self.data_de_parada) else None
        self.previsao_de_retorno = str(self.previsao_de_retorno) if pd.notna(self.previsao_de_retorno) else None


    @property
    def is_parado(self) -> bool:
        """Verifica se há elevadores parados"""
        return self.status.lower() == 'parado'if self.status else False
    
    @property
    def is_suspenso(self) -> bool:
        """Verifica se está suspenso"""
        return self.status.lower() == 'suspenso' if self.status else False
    
    def to_dict(self) -> Dict[str, Any]:
        # Para evitar a recursão infinita, criamos uma cópia do objeto SÓ DOS DADOS
        # e removemos o atributo 'building' ANTES de chamar asdict.
        # asdict(self) aqui tentará serializar tudo, incluindo building, mesmo que seja field(repr=False) se não for removido.
        # Vamos construir o dicionário manualmente para ter controle total:
        data = {attr: getattr(self, attr) for attr in self.__dataclass_fields__ if attr != 'building'}
        
        # Converte o dict de volta para um dataclass para usar asdict nele
        # (isso é um truque para usar asdict em todos os outros campos, mas é melhor construir manualmente)
        # return asdict(self) # <-- ISSO É O QUE ESTAVA CAUSANDO A RECURSÃO

        # OPÇÃO MAIS SEGURA: Construir o dicionário manualmente para o Elevator,
        # e então preencher os campos injetados do building.
        output_dict = {
            'id': self.id,
            'id_predio': self.id_predio,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'marca': self.marca,
            'paradas': self.paradas,
            'marca_licitacao': self.marca_licitacao,
            'status': self.status,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'empresa': self.empresa,
            'capacidade_kg': self.capacidade_kg,
            'v_m_min': self.v_m_min,
            'no_break_resgate_automatico': self.no_break_resgate_automatico,
            'periodicidade_manutencao_preventiva': self.periodicidade_manutencao_preventiva,
            'contrato': self.contrato,
            'data_de_parada': self.data_de_parada,
            'previsao_de_retorno': self.previsao_de_retorno,
            
            # Atributos injetados do Building (agora copiados diretamente)
            'cidade': self.cidade,
            'unidade': self.unidade,
            'endereco': self.endereco,
            'endereco_completo': self.endereco_completo,
            'regiao': self.regiao,
        }
        
        output_dict['temElevadorParado'] = self.is_parado
        output_dict['qtd_elev'] = 1 
        output_dict['nElevadorParado'] = 1 if self.is_parado else 0
        output_dict['DataDeParada'] = self.data_de_parada # Nomes usados no JS
        output_dict['PrevisaoDeRetorno'] = self.previsao_de_retorno # Nomes usados no JS
        
        return output_dict
    
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Elevator':
        field_mapping = {
            'Capacidade (Kg)': 'capacidade_kg',
            'V (m/min)': 'v_m_min',
            'No-break / Resgate Automático': 'no_break_resgate_automatico',
            'Periodicidade Manutenção Preventiva': 'periodicidade_manutencao_preventiva',
            'Contrato': 'contrato',
            'DataDeParada': 'data_de_parada',
            'PrevisaoDeRetorno': 'previsao_de_retorno',
            'empresa': 'empresa' # A coluna 'empresa' da info_elevadores
        }
        
        normalized_data = {}
        for key, value in data.items():
            mapped_key = field_mapping.get(key, key)
            normalized_data[mapped_key] = value

        init_fields = {f.name for f in cls.__dataclass_fields__.values() if f.init}
        filtered_data = {k: v for k, v in normalized_data.items() if k in init_fields}
        
        # Converter latitude/longitude para float de forma segura
        filtered_data['id'] = safe_int(filtered_data.get('id'))
        filtered_data['id_predio'] = safe_int(filtered_data.get('id_predio'))
        filtered_data['paradas'] = safe_int(filtered_data.get('paradas'))
        filtered_data['latitude'] = safe_float(filtered_data.get('latitude'))
        filtered_data['longitude'] = safe_float(filtered_data.get('longitude'))
        filtered_data['capacidade_kg'] = safe_int(filtered_data.get('capacidade_kg'))
        filtered_data['v_m_min'] = safe_int(filtered_data.get('v_m_min'))

        return cls(**filtered_data)