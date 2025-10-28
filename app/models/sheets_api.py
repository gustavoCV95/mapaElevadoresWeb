import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os

class SheetsAPI:
    def __init__(self, credenciais_path='credenciais.json'):
        try:
            # Mostra o email de serviço para verificação
            with open(credenciais_path, 'r') as f:
                creds_data = json.load(f)
                print(f"🔑 Email de serviço: {creds_data['client_email']}")
            
            # Configuração das credenciais
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/spreadsheets' 
            ]
            
            creds = Credentials.from_service_account_file(
                credenciais_path, scopes=scope
            )
            self.client = gspread.authorize(creds)
            print("✅ Autenticação realizada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            raise
    
    def testar_conexao(self):
        """Testa se consegue listar planilhas"""
        try:
            planilhas = self.client.list_spreadsheet_files()
            print(f"📊 Planilhas acessíveis: {len(planilhas)}")
            for p in planilhas[:3]:  # Mostra apenas as 3 primeiras
                print(f"   - {p['name']}")
            return True
        except Exception as e:
            print(f"❌ Erro ao listar planilhas: {e}")
            return False

    def obter_dados(self, planilha_url: str, sheet_name: str) -> pd.DataFrame:
        """Obtém dados de uma aba específica da planilha do Google Sheets."""
        try:
            print(f"Tentando acessar aba '{sheet_name}' em: {planilha_url}")
            sheet = self.client.open_by_url(planilha_url)
            worksheet = sheet.worksheet(sheet_name) # Busca a aba pelo nome
            dados = worksheet.get_all_records()
            print(f"Registros encontrados na aba '{sheet_name}': {len(dados)}")
            df = pd.DataFrame(dados)
            return df
        except gspread.exceptions.WorksheetNotFound:
            print(f"Aba '{sheet_name}' não encontrada na planilha. Retornando DataFrame vazio.")
            return pd.DataFrame()
        except gspread.exceptions.APIError as e:
            print(f"Erro da API ao obter dados da aba '{sheet_name}': {e}")
            print("Dicas: Verifique permissões ou URL.")
            return pd.DataFrame()
        except Exception as e:
            print(f"Erro inesperado ao obter dados da aba '{sheet_name}': {e}")
            return pd.DataFrame()

    def escrever_dados(self, planilha_url: str, df: pd.DataFrame, sheet_name: str):
        """Escreve/substitui os dados de um DataFrame em uma aba específica da planilha do Google Sheets."""
        try:
            print(f"Tentando escrever na aba '{sheet_name}' em: {planilha_url}")
            sheet = self.client.open_by_url(planilha_url)
            
            worksheet = None
            try:
                worksheet = sheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"   - Aba '{sheet_name}' não encontrada. Criando nova aba.")
                # gspread.add_worksheet requer rows/cols, use o tamanho do DF + 1 para cabeçalho
                # Cuidado: max 2M células por sheet.
                worksheet = sheet.add_worksheet(title=sheet_name, rows=df.shape[0] + 1, cols=df.shape[1])
            
            # Limpa o conteúdo existente da aba (se já existia) ou da nova aba
            worksheet.clear() 
            
            # Converte o DataFrame para uma lista de listas (incluindo cabeçalhos)
            data_to_write = [df.columns.values.tolist()] + df.values.tolist()
            # Atualiza a partir da célula A1
            worksheet.update('A1', data_to_write)
            print(f"Escrita concluída na aba '{sheet_name}'. {df.shape[0]} registros escritos.")
            return True
        except Exception as e:
            print(f"Erro ao escrever dados na aba '{sheet_name}': {e}")
            return False

    def obter_dados_kpis(self, planilha_url):
        """Obtém dados de KPIs de manutenção da planilha do Google Sheets"""
        try:
            print(f"🔗 Tentando acessar planilha de KPIs: {planilha_url}")
            
            # Abre a planilha pela URL
            sheet = self.client.open_by_url(planilha_url)
            print(f"📋 Planilha de KPIs aberta: {sheet.title}")
            
            # Lista as abas disponíveis
            worksheets = sheet.worksheets()
            print(f"Abas encontradas: {[w.title for w in worksheets]}")
            
            # Pega a primeira aba
            worksheet = worksheets[0]
            print(f"📄 Usando aba: {worksheet.title}")
            
            # Obtém os dados
            dados = worksheet.get_all_records()
            print(f"📊 Registros de KPIs encontrados: {len(dados)}")
            
            if len(dados) > 0:
                print(f"🔍 Colunas KPIs: {list(dados[0].keys())}")
            
            df = pd.DataFrame(dados)
            return df
            
        except gspread.exceptions.SpreadsheetNotFound:
            print("❌ Planilha de KPIs não encontrada. Verifique a URL e permissões.")
            return pd.DataFrame()
        except gspread.exceptions.APIError as e:
            print(f"❌ Erro da API ao acessar KPIs: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Erro inesperado ao acessar KPIs: {e}")
            return pd.DataFrame()


# Teste da conexão
if __name__ == "__main__":
    print("🚀 Iniciando teste da API...")
    
    try:
        api = SheetsAPI()
        
        # Primeiro, testa a conexão geral
        if api.testar_conexao():
            print("\n" + "="*50)
            print("✅ Conexão com Google Sheets funcionando!")
            print("="*50)
            
            # Agora testa com sua planilha específica
            url_planilha = input("\n📝 Cole a URL da sua planilha aqui: ").strip()
            
            if url_planilha and url_planilha != "SUA_URL_DA_PLANILHA_AQUI":
                print(f"\n🔄 Testando acesso à planilha...")
                dados = api.obter_dados_elevadores(url_planilha)
                
                if not dados.empty:
                    print(f"\n🎉 SUCESSO! Dados carregados:")
                    print(f"   - {len(dados)} registros")
                    print(f"   - {len(dados.columns)} colunas")
                    print(f"\n📋 Primeiras 3 linhas:")
                    print(dados.head(3))
                else:
                    print("\n❌ Nenhum dado foi carregado.")
            else:
                print("\n⚠️  URL não fornecida. Teste manual necessário.")
        else:
            print("\n❌ Falha na conexão básica com Google Sheets.")
            
    except Exception as e:
        print(f"\n💥 Erro crítico: {e}")