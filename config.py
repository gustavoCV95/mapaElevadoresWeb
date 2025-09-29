import os
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    # URL da planilha do Google Sheets
    PLANILHA_ELEVADORES_URL = 'https://docs.google.com/spreadsheets/d/1I46gVcTqvE9JjHIrbeqZhNLvvd4OZbGb7iTVkcHAhf0/edit?gid=0#gid=0'
    PLANILHA_MANUTENCAO_URL = 'https://docs.google.com/spreadsheets/d/1XxW_lZipATG-06ku7ZPyw34bPE93E-iTEDNVAiVeSf4/edit?gid=1630268405#gid=1630268405'
    
    # Configurações de cache (em segundos)
    CACHE_TIMEOUT = 300  # 5 minutos
    
    # Configurações do Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'chave-desenvolvimento-insegura')
    DEBUG = True
    
    # ========== CONFIGURAÇÕES DE AUTENTICAÇÃO ==========
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora em segundos
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Usuários autorizados (usuário: senha_hash)
    # IMPORTANTE: Altere estes usuários e senhas!
    USUARIOS_AUTORIZADOS = {
        'comep1': generate_password_hash('tjmg1'),
        'comep2': generate_password_hash('tjmg1'),
        'compe3': generate_password_hash('tjmg1'),
        # Adicione mais usuários conforme necessário
    }
    
    # Configurações de segurança
    MAX_TENTATIVAS_LOGIN = 5  # Máximo de tentativas de login
    BLOQUEIO_TEMPO = 300  # 5 minutos de bloqueio após exceder tentativas
    
    @staticmethod
    def adicionar_usuario(usuario, senha):
        """Método para adicionar novos usuários programaticamente"""
        Config.USUARIOS_AUTORIZADOS[usuario] = generate_password_hash(senha)
        print(f"✅ Usuário '{usuario}' adicionado com sucesso!")
    
    @staticmethod
    def listar_usuarios():
        """Lista todos os usuários cadastrados"""
        print("👥 Usuários cadastrados:")
        for usuario in Config.USUARIOS_AUTORIZADOS.keys():
            print(f"   - {usuario}")

# Exemplo de uso para adicionar usuários:
# Config.adicionar_usuario('novo_usuario', 'nova_senha')