# app/services/cache_service.py
import time
from datetime import datetime
from flask import current_app

class CacheService:
    def __init__(self, default_expiration=300):
        """Inicializa o serviço de cache com um tempo de expiração padrão de 5 minutos."""
        self.cache = {}
        self.default_expiration = default_expiration

    def set(self, key, value, expiration=None):
        """Armazena um valor no cache com a chave especificada."""
        if expiration is None:
            expiration = self.default_expiration
            
        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'expiration': expiration
        }
        print(f"ðŸ“¦ Cache SET: {key} (expira em {expiration}s)")

    def get(self, key):
        """Recupera um valor do cache se ainda for vÃ¡lido."""
        if key in self.cache:
            entry = self.cache[key]
            age = time.time() - entry['timestamp']
            
            if age < entry['expiration']:
                print(f"ðŸ“¦ Cache HIT: {key} (idade: {age:.1f}s)")
                return entry['value']
            else:
                # Expirado
                print(f"ðŸ“¦ Cache EXPIRED: {key} (idade: {age:.1f}s)")
                del self.cache[key]
        
        print(f"ï¿½ï¿½ Cache MISS: {key}")
        return None

    def delete(self, key):
        """Remove uma chave especÃ­fica do cache."""
        if key in self.cache:
            del self.cache[key]
            print(f"ðŸ“¦ Cache DELETE: {key}")

    def clear(self):
        """Limpa todo o cache."""
        keys_count = len(self.cache)
        self.cache.clear()
        print(f"ï¿½ï¿½ Cache CLEAR: {keys_count} chaves removidas")

    def get_stats(self):
        """Retorna estatÃ­sticas do cache."""
        now = time.time()
        active_keys = []
        expired_keys = []
        
        for key, entry in self.cache.items():
            age = now - entry['timestamp']
            if age < entry['expiration']:
                active_keys.append({
                    'key': key,
                    'age': age,
                    'expires_in': entry['expiration'] - age
                })
            else:
                expired_keys.append(key)
        
        # Remove chaves expiradas
        for key in expired_keys:
            del self.cache[key]
        
        return {
            'active_keys': len(active_keys),
            'expired_keys_removed': len(expired_keys),
            'keys_detail': active_keys
        }

    def is_expired(self, key):
        """Verifica se uma chave especÃ­fica estÃ¡ expirada."""
        if key not in self.cache:
            return True
        
        entry = self.cache[key]
        age = time.time() - entry['timestamp']
        return age >= entry['expiration']