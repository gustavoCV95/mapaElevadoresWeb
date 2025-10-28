# app/utils/helpers.py
from datetime import datetime, timedelta
from flask import current_app
import pandas as pd
import numpy as np

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Formata um objeto datetime para uma string"""
    if not value:
        return ''
    return value.strftime(format)

def is_valid_email(email):
    """Valida se o email fornecido tem um formato válido"""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+'
    return re.match(pattern, email) is not None

def safe_int(value, default=None):
    try:
        if pd.isna(value) or (isinstance(value, float) and np.isnan(value)) or str(value).strip() == '': 
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=None):
    try:
        if pd.isna(value) or (isinstance(value, float) and np.isnan(value)) or str(value).strip() == '': 
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default=''):
    try:
        if pd.isna(value) or (isinstance(value, float) and np.isnan(value)): # Considera np.nan como vazio
            return default
        return str(value)
    except (ValueError, TypeError):
        return default
    
def validate_coordinates(lat, lon):
    """Valida se as coordenadas são válidas"""
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        # Valida range geral
        if not (-90 <= lat_float <= 90 and -180 <= lon_float <= 180):
            return False, None, None
        
        # Valida range do Brasil
        if not (-35 <= lat_float <= 5 and -75 <= lon_float <= -30):
            return False, None, None
            
        return True, lat_float, lon_float
    except (ValueError, TypeError):
        return False, None, None

def calculate_time_difference(start_date, end_date, unit='hours'):
    """Calcula diferença entre duas datas"""
    if not start_date or not end_date:
        return None
    
    try:
        diff = end_date - start_date
        
        if unit == 'hours':
            return diff.total_seconds() / 3600
        elif unit == 'days':
            return diff.days
        elif unit == 'minutes':
            return diff.total_seconds() / 60
        else:
            return diff.total_seconds()
    except:
        return None