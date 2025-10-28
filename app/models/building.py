# app/models/building.py
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from app.utils.helpers import safe_int # Importar safe_int

if TYPE_CHECKING:
    from .elevator import Elevator 

@dataclass
class Building:
    id: Optional[int]  # ID único do prédio (da aba Detalhado)
    cidade: str
    unidade: str
    endereco: str
    endereco_completo: str
    regiao: str

    # Propriedades calculadas que serão populadas pelo DataProcessor
    total_elevadores: int = 0
    elevadores_parados: int = 0
    elevadores_suspensos: int = 0 # Adicionado para estatísticas
    elevadores_ativos: int = 0    # Adicionado para estatísticas
    
    # Lista de objetos Elevator que pertencem a este prédio
    elevators: List['Elevator'] = field(default_factory=list, repr=False) 

    def to_dict(self) -> Dict[str, Any]:
        # CONSTRÓI O DICIONÁRIO MANUALMENTE PARA EVITAR RECURSÃO INFINITA
        # E INCLUI APENAS OS CAMPOS NECESSÁRIOS PARA O FRONTEND (buildings_for_form)
        return {
            'id': self.id,
            'cidade': self.cidade,
            'unidade': self.unidade,
            'endereco': self.endereco,
            'endereco_completo': self.endereco_completo,
            'regiao': self.regiao,
            # As propriedades calculadas 'total_elevadores', etc., não são necessárias para `buildings_for_form`
            # e não devem ser incluídas aqui para evitar o TypeError no asdict(self) recursivo.
            # Se forem necessárias em outro contexto, crie um método `to_full_dict()` ou similar.
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Building':
        # Garante que o 'id' é tratado como Optional[int]
        data['id'] = safe_int(data.get('id'))
        
        valid_fields = {f.name for f in cls.__dataclass_fields__.values() if f.init}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)