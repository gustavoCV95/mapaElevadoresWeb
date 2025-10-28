#app/models/__init__.py

"""
Models da aplicação
"""
from .building import Building
from .elevator import Elevator
from .kpi import KPI

__all__ = ['Elevator', 'KPI']