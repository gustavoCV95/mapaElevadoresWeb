# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import pandas as pd
from sheets_api import SheetsAPI
import json
import os
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from functools import wraps

# Configuração dinâmica baseada no ambiente
if os.environ.get('FLASK_ENV') == 'production':
    from production_config import ProductionConfig as Config
else:
    from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Instância global da API
sheets_api = SheetsAPI()

# Cache simples em memória
cache_dados = {
    'dados': None,
    'geojson_data': None,
    'timestamp': None
}

# Cache para controle de tentativas de login
tentativas_login = {}

# ========== SISTEMA DE AUTENTICAÇÃO ==========

def login_required(f):
    """Decorator para proteger rotas que precisam de autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def verificar_tentativas_login(ip):
    """Verifica se o IP não excedeu o limite de tentativas"""
    agora = datetime.now()
    
    if ip in tentativas_login:
        tentativas = tentativas_login[ip]
        
        # Remove tentativas antigas (mais de BLOQUEIO_TEMPO segundos)
        tentativas['historico'] = [
            t for t in tentativas['historico'] 
            if (agora - t).seconds < app.config['BLOQUEIO_TEMPO']
        ]
        
        # Verifica se excedeu o limite
        if len(tentativas['historico']) >= app.config['MAX_TENTATIVAS_LOGIN']:
            return False, tentativas['historico'][0] + timedelta(seconds=app.config['BLOQUEIO_TEMPO'])
    
    return True, None

def registrar_tentativa_login(ip):
    """Registra uma tentativa de login falhada"""
    agora = datetime.now()
    
    if ip not in tentativas_login:
        tentativas_login[ip] = {'historico': []}
    
    tentativas_login[ip]['historico'].append(agora)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if 'usuario_logado' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '')
        ip_cliente = request.environ.get('REMOTE_ADDR', 'unknown')
        
        # Verifica tentativas de login
        pode_tentar, bloqueado_ate = verificar_tentativas_login(ip_cliente)
        
        if not pode_tentar:
            tempo_restante = int((bloqueado_ate - datetime.now()).seconds / 60)
            flash(f'Muitas tentativas de login. Tente novamente em {tempo_restante} minutos.', 'danger')
            return render_template('login.html')
        
        # Valida credenciais
        if usuario and senha:
            if usuario in app.config['USUARIOS_AUTORIZADOS']:
                if check_password_hash(app.config['USUARIOS_AUTORIZADOS'][usuario], senha):
                    # Login bem-sucedido
                    session['usuario_logado'] = usuario
                    session['login_timestamp'] = datetime.now().isoformat()
                    session.permanent = True
                    
                    # Limpa tentativas de login para este IP
                    if ip_cliente in tentativas_login:
                        del tentativas_login[ip_cliente]
                    
                    flash(f'Bem-vindo, {usuario}!', 'success')
                    
                    # Redireciona para a página solicitada ou dashboard
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                else:
                    # Senha incorreta
                    registrar_tentativa_login(ip_cliente)
                    flash('Usuário ou senha incorretos.', 'danger')
            else:
                # Usuário não existe
                registrar_tentativa_login(ip_cliente)
                flash('Usuário ou senha incorretos.', 'danger')
        else:
            flash('Por favor, preencha todos os campos.', 'warning')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout do usuário"""
    usuario = session.get('usuario_logado', 'Usuário')
    session.clear()
    flash(f'Logout realizado com sucesso. Até logo, {usuario}!', 'info')
    return redirect(url_for('login'))

# ========== ROTAS PROTEGIDAS ==========

def obter_dados_atualizados():
    """Obtém dados da planilha com cache"""
    agora = datetime.now()
    
    if (cache_dados['dados'] is None or 
        cache_dados['timestamp'] is None or
        (agora - cache_dados['timestamp']).seconds > app.config['CACHE_TIMEOUT']):
        
        print("🔄 Atualizando dados da planilha...")
        dados = sheets_api.obter_dados_elevadores(app.config['PLANILHA_URL'])
        
        if not dados.empty:
            cache_dados['dados'] = dados
            cache_dados['timestamp'] = agora
            
            # Processa dados para GeoJSON e armazena no cache
            geojson_data, tipos, regioes, marcas, empresas, predios = processar_dados_para_mapa(dados)
            cache_dados['geojson_data'] = geojson_data
            cache_dados['tipos_unicos'] = tipos
            cache_dados['regioes_unicas'] = regioes
            cache_dados['marcas_unicas'] = marcas
            cache_dados['empresas_unicas'] = empresas
            cache_dados['predios_unicos'] = predios
            
            print(f"✅ {len(dados)} registros carregados")
            print(f"📊 {len(geojson_data.get('features', []))} features GeoJSON criadas")
        else:
            print("❌ Erro ao carregar dados")
    
    return cache_dados['dados']

def processar_dados_para_mapa(dados):
    """Processa dados para o mapa - VERSÃO CONSISTENTE"""
    features = []
    registros_processados = []
    
    print(f"🗺️ Processando {len(dados)} registros para o mapa...")
    
    for idx, row in dados.iterrows():
        try:
            lat_str = str(row['latitude']).strip()
            lon_str = str(row['longitude']).strip()
            
            if not lat_str or not lon_str or lat_str == 'nan' or lon_str == 'nan':
                continue
            
            lat = float(lat_str)
            lon = float(lon_str)
            
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            
            if not (-35 <= lat <= 5 and -75 <= lon <= -30):
                continue
            
            # Dados processados de forma consistente
            registro_processado = {
                'cidade': str(row['cidade']),
                'unidade': str(row['unidade']),
                'endereco': str(row['endereco']),
                'enderecoCompleto': str(row['enderecoCompleto']),
                'tipo': str(row['tipo']),
                'qtd_elev': int(row['quantidade']) if pd.notna(row['quantidade']) else 0,
                'marca': str(row['marca']),
                'marcaLicitacao': str(row.get('marcaLicitacao', row['marca'])),
                'paradas': int(row['paradas']) if pd.notna(row['paradas']) else 0,
                'regiao': str(row['regiao']),
                'status': str(row['status']),
                'empresa': str(row.get('empresa', 'N/A')),
                'latitude': lat,
                'longitude': lon
            }
            
            # Armazena registro processado para uso na API
            registros_processados.append(registro_processado)
            
            # Cria feature GeoJSON
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": registro_processado
            }
            
            features.append(feature)
            
        except (ValueError, TypeError) as e:
            print(f"❌ Erro ao processar registro {idx}: {e}")
            continue
    
    print(f"✅ {len(features)} features válidas criadas")
    print(f"📊 Total de elevadores processados: {sum([f['properties']['qtd_elev'] for f in features])}")
    
    if features:
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Armazena registros processados no cache para uso da API
        cache_dados['registros_processados'] = registros_processados
        
        # Extrai valores únicos dos dados processados (mesma fonte)
        predios_unicos = sorted(list(set([r['enderecoCompleto'] for r in registros_processados])))
        tipos_unicos = sorted(list(set([r['tipo'] for r in registros_processados])))
        regioes_unicas = sorted(list(set([r['regiao'] for r in registros_processados])))
        marcas_unicas = sorted(list(set([r['marcaLicitacao'] for r in registros_processados])))
        empresas_unicas = sorted(list(set([r['empresa'] for r in registros_processados if r['empresa'] != 'N/A'])))
        
        return geojson_data, tipos_unicos, regioes_unicas, marcas_unicas, empresas_unicas, predios_unicos
    
    return {}, [], [], [], [], []

@app.route('/')
@login_required
def index():
    """Página principal com mapa nativo"""
    dados = obter_dados_atualizados()
    
    if dados is not None and not dados.empty:
        # Usa dados do cache para garantir consistência
        geojson_data = cache_dados.get('geojson_data', {})
        tipos_unicos = cache_dados.get('tipos_unicos', [])
        regioes_unicas = cache_dados.get('regioes_unicas', [])
        marcas_unicas = cache_dados.get('marcas_unicas', [])
        empresas_unicas = cache_dados.get('empresas_unicas', [])
        predios_unicos = cache_dados.get('predios_unicos', [])
        registros_processados = cache_dados.get('registros_processados', [])
        
        # Estatísticas baseadas nos MESMOS dados processados
        stats = {
            'total_elevadores': sum([r['qtd_elev'] for r in registros_processados]),
            'total_predios': len(set([r['enderecoCompleto'] for r in registros_processados])),
            'cidades': len(set([r['cidade'] for r in registros_processados])),
            'regioes': len(set([r['regiao'] for r in registros_processados])),
            'em_atividade': sum([r['qtd_elev'] for r in registros_processados if r['status'] == 'Em atividade']),
            'suspensos': sum([r['qtd_elev'] for r in registros_processados if r['status'] == 'Suspenso'])
        }
        
        print(f"📊 Stats calculadas: {stats}")
        
        return render_template('index_nativo.html', 
                             geojson_data=json.dumps(geojson_data),
                             tipos_unicos=tipos_unicos,
                             regioes_unicas=regioes_unicas,
                             marcas_unicas=marcas_unicas,
                             empresas_unicas=empresas_unicas,
                             predios_unicos = predios_unicos,
                             stats=stats)
    else:
        return render_template('index_nativo.html', erro="Erro ao carregar dados")

@app.route('/api/filtrar')
@login_required
def api_filtrar():
    """API para filtrar dados - USA MESMA FONTE DOS DADOS FRONTEND"""
    # Usa os registros processados (mesma fonte do frontend)
    registros_processados = cache_dados.get('registros_processados', [])
    
    if not registros_processados:
        return jsonify({'erro': 'Dados não disponíveis'})
    
    print(f"🔍 API: Filtrando {len(registros_processados)} registros processados...")
    
    # Obtém filtros da requisição
    tipos = request.args.getlist('tipo')
    regioes = request.args.getlist('regiao')
    marcas = request.args.getlist('marca')
    empresas = request.args.getlist('empresa')
    
    print(f"🔍 API: Filtros recebidos - tipos: {tipos}, regioes: {regioes}, marcas: {marcas}, empresas: {empresas}")
    
    # Aplica filtros nos registros processados
    dados_filtrados = registros_processados.copy()
    
    if tipos:
        dados_filtrados = [r for r in dados_filtrados if r['tipo'] in tipos]
        print(f"🔍 API: Após filtro tipo: {len(dados_filtrados)} registros")
    
    if regioes:
        dados_filtrados = [r for r in dados_filtrados if r['regiao'] in regioes]
        print(f"🔍 API: Após filtro região: {len(dados_filtrados)} registros")
    
    if marcas:
        dados_filtrados = [r for r in dados_filtrados if r['marcaLicitacao'] in marcas]
        print(f"🔍 API: Após filtro marca: {len(dados_filtrados)} registros")
    
    if empresas:
        dados_filtrados = [r for r in dados_filtrados if r['empresa'] in empresas]
        print(f"�� API: Após filtro empresa: {len(dados_filtrados)} registros")
    
    # Calcula estatísticas filtradas usando MESMA LÓGICA
    stats_filtradas = {
        'total_elevadores': sum([r['qtd_elev'] for r in dados_filtrados]),
        'total_predios': len(set([r['enderecoCompleto'] for r in dados_filtrados])),
        'cidades': len(set([r['cidade'] for r in dados_filtrados])),
        'regioes': len(set([r['regiao'] for r in dados_filtrados])),
        'em_atividade': sum([r['qtd_elev'] for r in dados_filtrados if r['status'] == 'Em atividade']),
        'suspensos': sum([r['qtd_elev'] for r in dados_filtrados if r['status'] == 'Suspenso']),
        'por_tipo': {},
        'por_regiao': {},
        'por_marca': {},
        'por_status': {}
    }
    
    # Conta por categoria
    stats_filtradas['por_tipo'] = {tipo: sum(r['qtd_elev'] for r in dados_filtrados if r['tipo'] == tipo) 
                               for tipo in set(r['tipo'] for r in dados_filtrados)}

    stats_filtradas['por_regiao'] = {regiao: sum(r['qtd_elev'] for r in dados_filtrados if r['regiao'] == regiao) 
                                 for regiao in set(r['regiao'] for r in dados_filtrados)}

    stats_filtradas['por_marca'] = {marca: sum(r['qtd_elev'] for r in dados_filtrados if r['marcaLicitacao'] == marca) 
                                for marca in set(r['marcaLicitacao'] for r in dados_filtrados)}

    stats_filtradas['por_status'] = {status: sum(r['qtd_elev'] for r in dados_filtrados if r['status'] == status) 
                                 for status in set(r['status'] for r in dados_filtrados)}
    
    '''from collections import Counter
    stats_filtradas['por_tipo'] = dict(Counter([r['tipo'] for r in dados_filtrados]))
    stats_filtradas['por_regiao'] = dict(Counter([r['regiao'] for r in dados_filtrados]))
    stats_filtradas['por_marca'] = dict(Counter([r['marcaLicitacao'] for r in dados_filtrados]))
    stats_filtradas['por_status'] = {'Em atividade': sum([r['qtd_elev'] for r in dados_filtrados if r['status'] == 'Em atividade']),
                                     'Suspenso': sum([r['qtd_elev'] for r in dados_filtrados if r['status'] == 'Suspenso'])}                                     
    #stats_filtradas['por_status'] = dict(Counter([r['status'] for r in dados_filtrados]))'''
    
    print(f"📊 API: Stats calculadas - {stats_filtradas['total_elevadores']} elevadores em {stats_filtradas['total_predios']} locais")
    
    return jsonify({
        'success': True,
        'stats': stats_filtradas,
        'total_registros': len(dados_filtrados)
    })

@app.route('/atualizar')
@login_required
def atualizar_dados():
    """Força atualização dos dados"""
    cache_dados['dados'] = None
    cache_dados['geojson_data'] = None
    cache_dados['timestamp'] = None
    dados = obter_dados_atualizados()
    
    if dados is not None and not dados.empty:
        return jsonify({
            'success': True,
            'message': f'Dados atualizados! {len(dados)} registros carregados.',
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Erro ao atualizar dados'
        })

# ========== INFORMAÇÕES DO SISTEMA ==========

@app.context_processor
def inject_user_info():
    """Injeta informações do usuário em todos os templates"""
    return {
        'usuario_logado': session.get('usuario_logado'),
        'login_timestamp': session.get('login_timestamp')
    }

# ========== HEALTH CHECK ==========

@app.route('/health')
def health_check():
    """Health check para AWS Load Balancer"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

if __name__ == '__main__':
    print("🚀 Iniciando Sistema de Mapeamento de Elevadores TJ/MG")
    print(f"🌍 Ambiente: {os.environ.get('FLASK_ENV', 'development')}")
    print("🔐 Sistema de autenticação ativado")
    
    if hasattr(Config, 'listar_usuarios'):
        print("👥 Usuários cadastrados:")
        Config.listar_usuarios()
    else:
        print("👥 Usuários carregados via variáveis de ambiente")
    
    print("="*50)
    
    # Configuração para produção vs desenvolvimento
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        app.run(debug=True, port=5000)