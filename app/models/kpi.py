#app/models/kpi.py
"""
Modelo para representar um KPI de manutenÃ§Ã£o
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

@dataclass
class KPI:
    """Modelo para representar um KPI de manutenÃ§Ã£o"""
    edificio: str
    categoria_problema: str
    status: str
    data_solicitacao: datetime
    data_conclusao: Optional[datetime] = None
    equipamento: Optional[str] = None
    
    @property
    def tempo_reparo_horas(self) -> Optional[float]:
        """Calcula tempo de reparo em horas"""
        if self.data_conclusao and self.data_solicitacao:
            return (self.data_conclusao - self.data_solicitacao).total_seconds() / 3600
        return None
    
    @property
    def esta_concluido(self) -> bool:
        """Verifica se está concluído"""
        return self.status.lower() == 'concluída'
    
    @property
    def mes_ano(self) -> str:
        """Retorna período mês/ano"""
        return self.data_solicitacao.strftime('%Y-%m')
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        # Converte datas para string para JSON
        if self.data_solicitacao:
            data['data_solicitacao'] = self.data_solicitacao.isoformat()
        if self.data_conclusao:
            data['data_conclusao'] = self.data_conclusao.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KPI':
        """Cria instância a partir de dicionÃ¡rio"""
        # Converte strings de data para datetime
        if isinstance(data.get('data_solicitacao'), str):
            try:
                data['data_solicitacao'] = pd.to_datetime(data['data_solicitacao'])
            except:
                data['data_solicitacao'] = datetime.now()
        
        if isinstance(data.get('data_conclusao'), str):
            try:
                data['data_conclusao'] = pd.to_datetime(data['data_conclusao'])
            except:
                data['data_conclusao'] = None
        
        # Remove campos que não existem no modelo
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)