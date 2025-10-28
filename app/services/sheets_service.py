# app/services/sheets_service.py
from app.models.sheets_api import SheetsAPI
import pandas as pd

class SheetsService:
    """Serviço para interação com Google Sheets usando a API existente"""
    
    def __init__(self):
        self.sheets_api = SheetsAPI()

    def obter_dados_detalhado(self, planilha_url: str) -> pd.DataFrame: # Nome mais específico
        """Obtém dados da aba 'Detalhado'"""
        print(f"Tentando acessar 'Detalhado' em: {planilha_url}")
        return self.sheets_api.obter_dados(planilha_url, sheet_name='Detalhado')
    
    def obter_dados_elevadores_individuais(self, planilha_url: str) -> pd.DataFrame: # Nome mais específico
        """Obtém dados da aba 'info_elevadores' (agora a base de elevadores individuais)"""
        print(f"Tentando acessar 'info_elevadores' em: {planilha_url}")
        return self.sheets_api.obter_dados(planilha_url, sheet_name='info_elevadores')
        
    # NOVO: Método para escrever dados na aba de elevadores individuais
    def salvar_elevadores_individuais(self, planilha_url: str, df: pd.DataFrame):
        print(f"✍️ Solicitando escrita para aba 'info_elevadores' em: {planilha_url}")
        return self.sheets_api.escrever_dados(planilha_url, df, sheet_name='info_elevadores')
    
    def obter_dados_kpis(self, planilha_url):
        """Obtém dados de KPIs da planilha"""
        print(f"Tentando acessar KPIs: {planilha_url}")
        return self.sheets_api.obter_dados_kpis(planilha_url)