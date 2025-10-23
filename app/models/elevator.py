#app/models/elevator.py
"""
Modelo para representar um elevador
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class Elevator:
    """Modelo para representar um elevador"""
    cidade: str
    unidade: str
    endereco: str
    endereco_completo: str
    tipo: str
    quantidade: int
    marca: str
    marca_licitacao: str
    paradas: int
    regiao: str
    status: str
    empresa: str
    latitude: float
    longitude: float
    n_elevador_parado: int = 0
    data_de_parada: Optional[str] = None
    previsao_de_retorno: Optional[str] = None
    
    @property
    def tem_elevador_parado(self) -> bool:
        """Verifica se hÃ¡ elevadores parados"""
        return self.n_elevador_parado > 0
    
    @property
    def esta_suspenso(self) -> bool:
        """Verifica se estÃ¡ suspenso"""
        return 'suspenso' in self.status.lower()
    
    @property
    def elevadores_ativos(self) -> int:
        """Calcula elevadores ativos"""
        if self.esta_suspenso:
            return 0
        return max(0, self.quantidade - self.n_elevador_parado)
    
    @property
    def cor_marcador(self) -> str:
        """Define cor do marcador baseado no status"""
        if self.tem_elevador_parado:
            return '#dc3545'  # Vermelho para parados
        elif self.esta_suspenso:
            return '#ffc107'  # Amarelo para suspensos
        elif 'atividade' in self.status.lower():
            return '#28a745'  # Verde para ativos
        return '#6c757d'  # Cinza padrÃ£o
    
    @property
    def tamanho_marcador(self) -> int:
        """Define tamanho do marcador baseado na quantidade"""
        if self.quantidade >= 5:
            return 10
        elif self.quantidade >= 3:
            return 8
        return 6
    
    def to_dict(self) -> Dict[str, Any]:
        output_dict = asdict(self)
        
        keys_to_remove = [
            'quantidade',
            'endereco_completo',
            'marca_licitacao',
            'n_elevador_parado',
            'data_de_parada',
            'previsao_de_retorno',
        ]
        for key in keys_to_remove:
            output_dict.pop(key, None)

        output_dict.update({
            'qtd_elev': self.quantidade,
            'enderecoCompleto': self.endereco_completo,
            'marcaLicitacao': self.marca_licitacao,
            'nElevadorParado': self.n_elevador_parado,
            'dataDeParada': self.data_de_parada,
            'previsaoDeRetorno': self.previsao_de_retorno,
            'temElevadorParado': self.tem_elevador_parado,
            'corMarcador': self.cor_marcador,
            'tamanhoMarcador': self.tamanho_marcador
        })
        return output_dict
    
    def to_geojson_feature(self) -> Dict[str, Any]:
        """Converte para feature GeoJSON"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": self.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Elevator':
        """Cria instancia a partir de dicionário"""
        # Mapeia campos com nomes diferentes
        field_mapping = {
            'qtd_elev': 'quantidade',
            'enderecoCompleto': 'endereco_completo',
            'marcaLicitacao': 'marca_licitacao',
            'nElevadorParado': 'n_elevador_parado',
            'dataDeParada': 'data_de_parada',
            'previsaoDeRetorno': 'previsao_de_retorno',
            'NElevadorParado': 'n_elevador_parado',
            'DataDeParada': 'data_de_parada',
            'PrevisaoDeRetorno': 'previsao_de_retorno'
        }
        
        # Normaliza os dados
        normalized_data = {}
        for key, value in data.items():
            new_key = field_mapping.get(key, key)
            normalized_data[new_key] = value
        
        # Remove campos que não existem no modelo
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in normalized_data.items() if k in valid_fields}
        
        return cls(**filtered_data)