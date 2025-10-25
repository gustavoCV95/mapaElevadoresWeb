# app/services/sheets_service.py
from app.models.sheets_api import SheetsAPI

class SheetsService:
    """Serviço para interação com Google Sheets usando a API existente"""
    
    def __init__(self):
        self.sheets_api = SheetsAPI()
    
    def obter_dados_elevadores(self, planilha_url):
        """Obtém dados de elevadores da planilha"""
        print(f"Tentando acessar: {planilha_url}")
        return self.sheets_api.obter_dados_elevadores(planilha_url)
    
    def obter_dados_kpis(self, planilha_url):
        """Obtém dados de KPIs da planilha"""
        print(f"Tentando acessar KPIs: {planilha_url}")
        return self.sheets_api.obter_dados_kpis(planilha_url)
    
    def get_sheet_data(self, url, range_name='A1:Z1000'):
        """Método genérico para obter dados de planilha"""
        # Usa o mÃ©todo apropriado baseado no contexto
        return self.sheets_api.obter_dados_elevadores(url)
    
    def update_sheet_data(self, url, range_name, values):
        """Atualiza dados na planilha (funcionalidade futura)"""
        print(f"Funcionalidade de atualização não implementada ainda")
        return None