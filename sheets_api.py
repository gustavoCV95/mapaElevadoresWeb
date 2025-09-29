import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json

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
                'https://www.googleapis.com/auth/drive'
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
    
    def obter_dados_elevadores(self, planilha_url):
        """Obtém dados da planilha do Google Sheets"""
        try:
            print(f"🔗 Tentando acessar: {planilha_url}")
            
            # Abre a planilha pela URL
            sheet = self.client.open_by_url(planilha_url)
            print(f"📋 Planilha aberta: {sheet.title}")
            
            # Lista as abas disponíveis
            worksheets = sheet.worksheets()
            print(f"📑 Abas encontradas: {[w.title for w in worksheets]}")
            
            # Pega a primeira aba
            worksheet = worksheets[0]
            print(f"📄 Usando aba: {worksheet.title}")
            
            # Obtém os dados
            dados = worksheet.get_all_records()
            print(f"📊 Registros encontrados: {len(dados)}")
            
            if len(dados) > 0:
                print(f"🔍 Colunas: {list(dados[0].keys())}")
            
            df = pd.DataFrame(dados)
            return df
            
        except gspread.exceptions.SpreadsheetNotFound:
            print("❌ Planilha não encontrada. Verifique a URL e permissões.")
            return pd.DataFrame()
        except gspread.exceptions.APIError as e:
            print(f"❌ Erro da API: {e}")
            print("💡 Dicas:")
            print("   - Verifique se a planilha foi compartilhada com o email de serviço")
            print("   - Confirme se a URL está correta")
            print("   - Tente aguardar alguns minutos e tente novamente")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return pd.DataFrame()
        
    def obter_dados_manutencao(self, planilha_url):
        """Obtém dados de manutenção da planilha específica"""
        try:
            print(f"🔧 Acessando planilha de manutenção: {planilha_url}")
            
            # Abre a planilha pela URL
            sheet = self.client.open_by_url(planilha_url)
            print(f"📋 Planilha de manutenção aberta: {sheet.title}")
            
            # Lista as abas disponíveis
            worksheets = sheet.worksheets()
            print(f"📑 Abas encontradas: {[w.title for w in worksheets]}")
            
            # Pega a primeira aba (ou específica se necessário)
            worksheet = worksheets[0]
            print(f"📄 Usando aba: {worksheet.title}")
            
            # Obtém os dados
            dados = worksheet.get_all_records()
            print(f"�� Registros de manutenção encontrados: {len(dados)}")
            
            if len(dados) > 0:
                print(f"🔍 Colunas manutenção: {list(dados[0].keys())}")
            
            df = pd.DataFrame(dados)
            return df
            
        except Exception as e:
            print(f"❌ Erro ao obter dados de manutenção: {e}")
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
                dados = api.obter_dados_manutencao(url_planilha)
                #dados = api.obter_dados_elevadores(url_planilha)
                
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