# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import pandas as pd
from sheets_api import SheetsAPI
import json
import os
import pytz
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

# Adicionar cache para dados de manutenção
cache_manutencao = {
    'dados': None,
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
                    brt = pytz.timezone("America/Sao_Paulo")
                    session['login_timestamp'] = datetime.now(brt).isoformat()
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
        dados = sheets_api.obter_dados_elevadores(app.config['PLANILHA_ELEVADORES_URL'])
        
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
    """Processa dados para o mapa - VERSÃO COM ELEVADORES PARADOS"""
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
            
            # 🆕 PROCESSA DADOS DE ELEVADORES PARADOS
            n_elevador_parado = 0
            data_de_parada = None
            previsao_de_retorno = None
            
            try:
                n_elevador_parado = int(row.get('NElevadorParado', 0)) if pd.notna(row.get('NElevadorParado')) else 0
            except (ValueError, TypeError):
                n_elevador_parado = 0
            
            # Processa datas no formato DD/MM/AAAA
            try:
                if pd.notna(row.get('DataDeParada')) and str(row.get('DataDeParada')).strip():
                    data_de_parada = str(row['DataDeParada']).strip()
            except:
                data_de_parada = None
                
            try:
                if pd.notna(row.get('PrevisaoDeRetorno')) and str(row.get('PrevisaoDeRetorno')).strip():
                    previsao_de_retorno = str(row['PrevisaoDeRetorno']).strip()
            except:
                previsao_de_retorno = None
            
            # Dados processados
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
                'longitude': lon,
                # 🆕 NOVOS CAMPOS
                'nElevadorParado': n_elevador_parado,
                'dataDeParada': data_de_parada,
                'previsaoDeRetorno': previsao_de_retorno,
                'temElevadorParado': n_elevador_parado > 0  # Boolean para facilitar lógica no JS
            }
            
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
    print(f"🔴 Total de elevadores parados: {sum([f['properties']['nElevadorParado'] for f in features])}")
    
    if features:
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }
        
        cache_dados['registros_processados'] = registros_processados
        
        tipos_unicos = sorted(list(set([r['tipo'] for r in registros_processados])))
        regioes_unicas = sorted(list(set([r['regiao'] for r in registros_processados])))
        marcas_unicas = sorted(list(set([r['marcaLicitacao'] for r in registros_processados])))
        empresas_unicas = sorted(list(set([r['empresa'] for r in registros_processados if r['empresa'] != 'N/A'])))
        predios_unicos = sorted(list(set([r['enderecoCompleto'] for r in registros_processados])))
        
        return geojson_data, tipos_unicos, regioes_unicas, marcas_unicas, empresas_unicas, predios_unicos
    
    return {}, [], [], [], []

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
        
        # ✅ ESTATÍSTICAS CORRIGIDAS - MESMA LÓGICA DA API
        total_elevadores = 0
        elevadores_ativos = 0
        elevadores_suspensos = 0
        elevadores_parados_total = 0
        
        for r in registros_processados:
            total_elevadores += r['qtd_elev']
            elevadores_parados_registro = r.get('nElevadorParado', 0)
            elevadores_parados_total += elevadores_parados_registro
            
            if 'suspenso' in r['status'].lower():
                # Prédio suspenso: todos elevadores são suspensos
                elevadores_suspensos += r['qtd_elev']
            elif r['status'] == 'Em atividade':
                # Prédio ativo: só conta elevadores realmente ativos
                elevadores_ativos += (r['qtd_elev'] - elevadores_parados_registro)
        
        stats = {
            'total_elevadores': total_elevadores,
            'total_predios': len(set([r['enderecoCompleto'] for r in registros_processados])),
            'cidades': len(set([r['cidade'] for r in registros_processados])),
            'regioes': len(set([r['regiao'] for r in registros_processados])),
            'em_atividade': elevadores_ativos,  # ✅ CORRIGIDO
            'suspensos': elevadores_suspensos,  # ✅ CORRIGIDO
            'elevadores_parados': elevadores_parados_total
        }
        
        print(f"📊 Stats calculadas (CORRIGIDAS): {stats}")
        
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
    """API para filtrar dados - COM SITUAÇÃO DOS ELEVADORES"""
    
    registros_processados = cache_dados.get('registros_processados', [])
    
    if not registros_processados:
        return jsonify({'erro': 'Dados não disponíveis'})
    
    print(f"🔍 API: Usando {len(registros_processados)} registros processados")
    
    # Obtém filtros da requisição
    tipos = request.args.getlist('tipo')
    regioes = request.args.getlist('regiao')
    marcas = request.args.getlist('marca')
    empresas = request.args.getlist('empresa')
    situacoes = request.args.getlist('situacao')  # 🆕 NOVO FILTRO
    
    # ✅ APLICA TODOS OS FILTROS (INCLUINDO SITUAÇÃO)
    dados_filtrados = registros_processados.copy()
    
    if tipos:
        dados_filtrados = [r for r in dados_filtrados if r['tipo'] in tipos]
    if regioes:
        dados_filtrados = [r for r in dados_filtrados if r['regiao'] in regioes]
    if marcas:
        dados_filtrados = [r for r in dados_filtrados if r['marcaLicitacao'] in marcas]
    if empresas:
        dados_filtrados = [r for r in dados_filtrados if r['empresa'] in empresas]
    
    # 🆕 APLICA FILTRO POR SITUAÇÃO AOS DADOS
    if situacoes:
        def passa_situacao(registro):
            for situacao in situacoes:
                if situacao == 'ativos':
                    # Ativos: status ativo E sem elevadores parados
                    if (registro['status'].lower() == 'em atividade' and 
                        registro.get('nElevadorParado', 0) == 0):
                        return True
                elif situacao == 'suspensos':
                    # Suspensos: status suspenso
                    if 'suspenso' in registro['status'].lower():
                        return True
                elif situacao == 'parados':
                    # Parados: tem elevadores parados
                    if registro.get('nElevadorParado', 0) > 0:
                        return True
            return False
        
        dados_filtrados = [r for r in dados_filtrados if passa_situacao(r)]

    print(f"🔍 Dados após filtros: {len(dados_filtrados)} registros")

    # ✅ CALCULA STATS COM BASE NOS DADOS REALMENTE FILTRADOS
    if situacoes:
        # 🆕 LÓGICA ESPECIAL QUANDO HÁ FILTRO DE SITUAÇÃO
        stats_filtradas = {
            'total_elevadores': 0,
            'total_predios': len(set([r['enderecoCompleto'] for r in dados_filtrados])),  # ✅ AGORA CORRETO
            'cidades': len(set([r['cidade'] for r in dados_filtrados])),  # ✅ AGORA CORRETO
            'regioes': len(set([r['regiao'] for r in dados_filtrados])),  # ✅ AGORA CORRETO
            'em_atividade': 0,
            'suspensos': 0,
            'elevadores_parados': 0,
            'por_tipo': {},
            'por_regiao': {},
            'por_marca': {},
            'por_status': {}
        }
        
        # 🎯 CONTADORES POR CATEGORIA
        from collections import defaultdict
        por_tipo = defaultdict(int)
        por_regiao = defaultdict(int)
        por_marca = defaultdict(int)
        por_status = defaultdict(int)
        
        # 🔄 PROCESSA CADA REGISTRO FILTRADO
        for r in dados_filtrados:
            # Identifica a situação do prédio
            elevadores_parados = r.get('nElevadorParado', 0)
            elevadores_ativos = r['qtd_elev'] - elevadores_parados
            esta_suspenso = 'suspenso' in r['status'].lower()
            
            # 🎯 LÓGICA MUTUAMENTE EXCLUSIVA POR PRÉDIO
            if esta_suspenso:
                # PRÉDIO SUSPENSO: todos os elevadores são suspensos
                if 'suspensos' in situacoes:
                    stats_filtradas['total_elevadores'] += r['qtd_elev']
                    stats_filtradas['suspensos'] += r['qtd_elev']
                    por_tipo[r['tipo']] += r['qtd_elev']
                    por_regiao[r['regiao']] += r['qtd_elev']
                    por_marca[r['marcaLicitacao']] += r['qtd_elev']
                    por_status['Suspenso'] += r['qtd_elev']
            else:
                # PRÉDIO EM ATIVIDADE: divide entre ativos e parados
                elevadores_contados = 0
                
                # Conta elevadores ATIVOS (se solicitado)
                if 'ativos' in situacoes and elevadores_ativos > 0:
                    elevadores_contados += elevadores_ativos
                    stats_filtradas['em_atividade'] += elevadores_ativos
                    por_tipo[r['tipo']] += elevadores_ativos
                    por_regiao[r['regiao']] += elevadores_ativos
                    por_marca[r['marcaLicitacao']] += elevadores_ativos
                    por_status['Em atividade'] += elevadores_ativos
                
                # Conta elevadores PARADOS (se solicitado)
                if 'parados' in situacoes and elevadores_parados > 0:
                    elevadores_contados += elevadores_parados
                    stats_filtradas['elevadores_parados'] += elevadores_parados
                    por_tipo[r['tipo']] += elevadores_parados
                    por_regiao[r['regiao']] += elevadores_parados
                    por_marca[r['marcaLicitacao']] += elevadores_parados
                    por_status['Parados'] += elevadores_parados
                
                # Soma ao total geral
                stats_filtradas['total_elevadores'] += elevadores_contados
        
        # Define os dicionários finais
        stats_filtradas['por_tipo'] = dict(por_tipo)
        stats_filtradas['por_regiao'] = dict(por_regiao)
        stats_filtradas['por_marca'] = dict(por_marca)
        stats_filtradas['por_status'] = dict(por_status)

    else:
        # 🔄 LÓGICA ORIGINAL QUANDO NÃO HÁ FILTRO DE SITUAÇÃO
        stats_filtradas = {
            'total_elevadores': sum([r['qtd_elev'] for r in dados_filtrados]),
            'total_predios': len(set([r['enderecoCompleto'] for r in dados_filtrados])),
            'cidades': len(set([r['cidade'] for r in dados_filtrados])),
            'regioes': len(set([r['regiao'] for r in dados_filtrados])),
            'em_atividade': sum([r['qtd_elev'] for r in dados_filtrados if r['status'] == 'Em atividade']),
            'suspensos': sum([r['qtd_elev'] for r in dados_filtrados if r['status'] == 'Suspenso']),
            'elevadores_parados': sum([r.get('nElevadorParado', 0) for r in dados_filtrados]),
            'por_tipo': {},
            'por_regiao': {},
            'por_marca': {},
            'por_status': {}
        }
        
        # Contagem por categoria - LÓGICA ORIGINAL
        from collections import defaultdict

        # Soma de elevadores por tipo
        por_tipo = defaultdict(int)
        for r in dados_filtrados:
            por_tipo[r['tipo']] += r['qtd_elev']

        # Soma de elevadores por região
        por_regiao = defaultdict(int)
        for r in dados_filtrados:
            por_regiao[r['regiao']] += r['qtd_elev']

        # Soma de elevadores por marca
        por_marca = defaultdict(int)
        for r in dados_filtrados:
            por_marca[r['marcaLicitacao']] += r['qtd_elev']

        stats_filtradas['por_tipo'] = dict(por_tipo)
        stats_filtradas['por_regiao'] = dict(por_regiao)
        stats_filtradas['por_marca'] = dict(por_marca)
        
        # Contagem por status - elevadores
        stats_por_status_elevadores = {}
        for r in dados_filtrados:
            status = r['status']
            if status in stats_por_status_elevadores:
                stats_por_status_elevadores[status] += r['qtd_elev']
            else:
                stats_por_status_elevadores[status] = r['qtd_elev']
        
        stats_filtradas['por_status'] = stats_por_status_elevadores

    # 🔍 DEBUG
    print(f"📊 API DEBUG COM SITUAÇÃO:")
    print(f"   - Filtros situação: {situacoes}")
    print(f"   - Registros filtrados: {len(dados_filtrados)}")
    print(f"   - Total prédios: {stats_filtradas['total_predios']}")
    print(f"   - Total cidades: {stats_filtradas['cidades']}")
    print(f"   - Total regiões: {stats_filtradas['regioes']}")
    print(f"   - Total elevadores: {stats_filtradas['total_elevadores']}")
    print(f"   - Ativos: {stats_filtradas['em_atividade']}")
    print(f"   - Suspensos: {stats_filtradas['suspensos']}")
    print(f"   - Parados: {stats_filtradas['elevadores_parados']}")
    
    return jsonify({
        'success': True,
        'stats': stats_filtradas,
        'total_registros': len(dados_filtrados)
    })

@app.route('/api/elevadores-parados')
@login_required
def api_elevadores_parados():
    """API para obter lista de elevadores parados - COM FILTROS DE SITUAÇÃO"""
    
    registros_processados = cache_dados.get('registros_processados', [])
    
    if not registros_processados:
        return jsonify({'erro': 'Dados não disponíveis'})
    
    print(f"🔍 API Elevadores Parados: Usando {len(registros_processados)} registros")
    
    # Obtém filtros da requisição
    tipos = request.args.getlist('tipo')
    regioes = request.args.getlist('regiao')
    marcas = request.args.getlist('marca')
    empresas = request.args.getlist('empresa')
    situacoes = request.args.getlist('situacao')  # 🆕 NOVO FILTRO
    
    # Aplica filtros
    dados_filtrados = registros_processados.copy()
    
    if tipos:
        dados_filtrados = [r for r in dados_filtrados if r['tipo'] in tipos]
    if regioes:
        dados_filtrados = [r for r in dados_filtrados if r['regiao'] in regioes]
    if marcas:
        dados_filtrados = [r for r in dados_filtrados if r['marcaLicitacao'] in marcas]
    if empresas:
        dados_filtrados = [r for r in dados_filtrados if r['empresa'] in empresas]
    
    # 🆕 FILTRO POR SITUAÇÃO
    if situacoes:
        def passa_situacao(registro):
            for situacao in situacoes:
                if situacao == 'ativos':
                    if (registro['status'].lower() == 'em atividade' and 
                        registro.get('nElevadorParado', 0) == 0):
                        return True
                elif situacao == 'suspensos':
                    if 'suspenso' in registro['status'].lower():
                        return True
                elif situacao == 'parados':
                    if registro.get('nElevadorParado', 0) > 0:
                        return True
            return False
        
        dados_filtrados = [r for r in dados_filtrados if passa_situacao(r)]

    # Filtra apenas elevadores parados
    elevadores_parados = []
    for registro in dados_filtrados:
        if registro.get('nElevadorParado', 0) > 0:
            elevador_parado = {
                'cidade': registro['cidade'],
                'unidade': registro['unidade'],
                'tipo': registro['tipo'],
                'quantidade': registro['nElevadorParado'],
                'empresa': registro['empresa'],
                'dataDeParada': registro.get('dataDeParada'),
                'previsaoDeRetorno': registro.get('previsaoDeRetorno'),
                'qtd_total_elevadores': registro['qtd_elev']
            }
            elevadores_parados.append(elevador_parado)
    
    # Ordena por cidade e depois por unidade
    elevadores_parados.sort(key=lambda x: (x['cidade'], x['unidade']))
    
    print(f"🔴 {len(elevadores_parados)} elevadores parados encontrados com filtro de situação")
    
    return jsonify({
        'success': True,
        'elevadores_parados': elevadores_parados,
        'total': len(elevadores_parados)
    })


@app.route('/atualizar', methods=['POST', 'GET'])
@login_required
def atualizar_dados():
    """Atualiza dados forçando limpeza do cache"""
    try:
        print("🔄 Iniciando atualização forçada dos dados...")
        
        # Limpa o cache para forçar nova requisição
        cache_dados['dados'] = None
        cache_dados['geojson_data'] = None
        cache_dados['timestamp'] = None
        cache_dados['registros_processados'] = None
        
        # 🆕 LIMPA TAMBÉM O CACHE DE MANUTENÇÃO
        cache_manutencao['dados'] = None
        cache_manutencao['timestamp'] = None
        
        print("🧹 Cache limpo com sucesso")
        
        # Força nova obtenção dos dados
        dados = obter_dados_atualizados()
        
        if dados is not None and not dados.empty:
            registros_processados = cache_dados.get('registros_processados', [])
            total_registros = len(registros_processados)
            total_elevadores = sum([r['qtd_elev'] for r in registros_processados])
            elevadores_parados = sum([r.get('nElevadorParado', 0) for r in registros_processados])
            
            print(f"✅ Dados atualizados com sucesso!")
            print(f"📊 {total_registros} registros, {total_elevadores} elevadores, {elevadores_parados} parados")
            
            return jsonify({
                'success': True,
                'message': f"""Dados atualizados com sucesso!
                
📊 Resumo da atualização:
• {total_registros} locais processados
• {total_elevadores} elevadores mapeados  
• {elevadores_parados} elevadores parados
• Cache renovado às {datetime.now().strftime('%H:%M:%S')}""",
                'stats': {
                    'total_registros': total_registros,
                    'total_elevadores': total_elevadores,
                    'elevadores_parados': elevadores_parados,
                    'timestamp': datetime.now().isoformat()
                }
            })
        else:
            print("❌ Erro ao obter dados atualizados")
            return jsonify({
                'success': False,
                'message': 'Erro ao conectar com a planilha do Google Sheets. Verifique a conexão e tente novamente.'
            })
            
    except Exception as e:
        print(f"❌ Erro na atualização: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro interno durante a atualização: {str(e)}'
        })

# ========== SEÇÃO DE KPIs DE MANUTENÇÃO ==========

def obter_dados_manutencao_atualizados():
    """Obtém dados de manutenção com cache"""
    agora = datetime.now()
    
    if (cache_manutencao['dados'] is None or 
        cache_manutencao['timestamp'] is None or
        (agora - cache_manutencao['timestamp']).seconds > app.config['CACHE_TIMEOUT']):
        
        print("🔄 Atualizando dados de manutenção...")
        dados = sheets_api.obter_dados_manutencao(app.config['PLANILHA_MANUTENCAO_URL'])
        
        if not dados.empty:
            cache_manutencao['dados'] = dados
            cache_manutencao['timestamp'] = agora
            print(f"✅ {len(dados)} registros de manutenção carregados")
        else:
            print("❌ Erro ao carregar dados de manutenção")
    
    return cache_manutencao['dados']

@app.route('/kpis-manutencao')
@login_required
def kpis_manutencao():
    """Página de KPIs de Manutenção"""
    dados = obter_dados_manutencao_atualizados()
    
    if dados is not None and not dados.empty:
        # Extrai valores únicos para filtros
        cidades_unicas = sorted(dados['Cidade'].dropna().unique().tolist())
        unidades_unicas = sorted(dados['Unidade'].dropna().unique().tolist())
        tipos_atividade_unicos = sorted(dados['Tipo de Atividade'].dropna().unique().tolist())
        tipos_manutencao_unicos = sorted(dados['Tipo de manutenção'].dropna().unique().tolist())
        
        return render_template('kpis_manutencao.html',
                             cidades_unicas=cidades_unicas,
                             unidades_unicas=unidades_unicas,
                             tipos_atividade_unicos=tipos_atividade_unicos,
                             tipos_manutencao_unicos=tipos_manutencao_unicos)
    else:
        return render_template('kpis_manutencao.html', erro="Erro ao carregar dados de manutenção")

@app.route('/api/kpis-manutencao')
@login_required
def api_kpis_manutencao():
    """API para calcular KPIs de manutenção"""
    dados = obter_dados_manutencao_atualizados()
    
    if dados is None or dados.empty:
        return jsonify({'erro': 'Dados de manutenção não disponíveis'})
    
    # Obtém filtros
    cidades = request.args.getlist('cidade')
    unidades = request.args.getlist('unidade')
    tipos_atividade = request.args.getlist('tipo_atividade')
    tipos_manutencao = request.args.getlist('tipo_manutencao')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Aplica filtros
    dados_filtrados = dados.copy()
    
    if cidades:
        dados_filtrados = dados_filtrados[dados_filtrados['Cidade'].isin(cidades)]
    if unidades:
        dados_filtrados = dados_filtrados[dados_filtrados['Unidade'].isin(unidades)]
    if tipos_atividade:
        dados_filtrados = dados_filtrados[dados_filtrados['Tipo de Atividade'].isin(tipos_atividade)]
    if tipos_manutencao:
        dados_filtrados = dados_filtrados[dados_filtrados['Tipo de manutenção'].isin(tipos_manutencao)]
    
    # Filtro por data
    if data_inicio or data_fim:
        dados_filtrados = aplicar_filtro_data(dados_filtrados, data_inicio, data_fim)
    
    # Calcula KPIs
    kpis = calcular_kpis_manutencao_completos(dados_filtrados)
    
    return jsonify({
        'success': True,
        'kpis': kpis,
        'total_registros': len(dados_filtrados)
    })

def aplicar_filtro_data(dados, data_inicio, data_fim):
    """Aplica filtro de data nos dados"""
    try:
        # Converte coluna Data para datetime
        dados['Data'] = pd.to_datetime(dados['Data'], errors='coerce')
        
        if data_inicio:
            data_inicio_dt = pd.to_datetime(data_inicio)
            dados = dados[dados['Data'] >= data_inicio_dt]
        
        if data_fim:
            data_fim_dt = pd.to_datetime(data_fim)
            dados = dados[dados['Data'] <= data_fim_dt]
        
        return dados
    except Exception as e:
        print(f"❌ Erro ao aplicar filtro de data: {e}")
        return dados

def calcular_kpis_manutencao_completos(dados):
    """Calcula KPIs completos baseados nos dados de manutenção"""
    from collections import defaultdict
    import statistics  # 🆕 ADICIONAR ESTE IMPORT
    
    if dados.empty:
        return {}
    
    # Converte tempo de atendimento para horas (se necessário)
    dados['Tempo_Horas'] = pd.to_numeric(dados['Tempo de Atendimento'], errors='coerce')
    dados['Data'] = pd.to_datetime(dados['Data'], errors='coerce')
    
    # Remove registros com dados inválidos
    dados_limpos = dados.dropna(subset=['Tempo_Horas', 'Data'])
    
    # KPIs Gerais
    total_atendimentos = len(dados_limpos)
    tempo_medio_geral = dados_limpos['Tempo_Horas'].mean()
    tempo_mediano_geral = dados_limpos['Tempo_Horas'].median()
    
    # Separação por tipo de manutenção
    preventivas = dados_limpos[dados_limpos['Tipo de manutenção'].str.contains('Preventiva', case=False, na=False)]
    corretivas = dados_limpos[dados_limpos['Tipo de manutenção'].str.contains('Corretiva', case=False, na=False)]
    
    # KPIs por tipo
    kpis_preventivas = {
        'total': len(preventivas),
        'tempo_medio': preventivas['Tempo_Horas'].mean() if len(preventivas) > 0 else 0,
        'tempo_mediano': preventivas['Tempo_Horas'].median() if len(preventivas) > 0 else 0
    }
    
    kpis_corretivas = {
        'total': len(corretivas),
        'tempo_medio': corretivas['Tempo_Horas'].mean() if len(corretivas) > 0 else 0,
        'tempo_mediano': corretivas['Tempo_Horas'].median() if len(corretivas) > 0 else 0
    }
    
    # Equipamentos mais problemáticos
    equipamentos_stats = dados_limpos.groupby('Equipamento').agg({
        'Tempo_Horas': ['count', 'mean', 'sum'],
        'Tipo de manutenção': lambda x: (x.str.contains('Corretiva', case=False, na=False)).sum()
    }).round(2)
    
    equipamentos_stats.columns = ['Total_Atendimentos', 'Tempo_Medio', 'Tempo_Total', 'Manutencoes_Corretivas']
    equipamentos_problematicos = equipamentos_stats.nlargest(10, 'Manutencoes_Corretivas')
    
    # Performance por cidade
    performance_cidade = dados_limpos.groupby('Cidade').agg({
        'Tempo_Horas': ['count', 'mean'],
        'Equipamento': 'nunique'
    }).round(2)
    performance_cidade.columns = ['Total_Atendimentos', 'Tempo_Medio', 'Equipamentos_Unicos']
    
    # Performance por unidade
    performance_unidade = dados_limpos.groupby('Unidade').agg({
        'Tempo_Horas': ['count', 'mean'],
        'Equipamento': 'nunique'
    }).round(2)
    performance_unidade.columns = ['Total_Atendimentos', 'Tempo_Medio', 'Equipamentos_Unicos']
    
    # Análise temporal (por mês)
    dados_limpos['Mes_Ano'] = dados_limpos['Data'].dt.to_period('M').astype(str)
    timeline = dados_limpos.groupby('Mes_Ano').agg({
        'Tempo_Horas': ['count', 'mean']
    }).round(2)
    timeline.columns = ['Total_Atendimentos', 'Tempo_Medio']
    
    # Distribuição de tempos
    distribuicao_tempos = {
        '< 1h': len(dados_limpos[dados_limpos['Tempo_Horas'] < 1]),
        '1-2h': len(dados_limpos[(dados_limpos['Tempo_Horas'] >= 1) & (dados_limpos['Tempo_Horas'] < 2)]),
        '2-4h': len(dados_limpos[(dados_limpos['Tempo_Horas'] >= 2) & (dados_limpos['Tempo_Horas'] < 4)]),
        '4-8h': len(dados_limpos[(dados_limpos['Tempo_Horas'] >= 4) & (dados_limpos['Tempo_Horas'] < 8)]),
        '8h+': len(dados_limpos[dados_limpos['Tempo_Horas'] >= 8])
    }
    
    # Calcula percentuais
    percentual_preventivas = (len(preventivas) / total_atendimentos * 100) if total_atendimentos > 0 else 0
    percentual_corretivas = (len(corretivas) / total_atendimentos * 100) if total_atendimentos > 0 else 0
    
    # Monta resultado final
    resultado = {
        'resumo': {
            'total_atendimentos': total_atendimentos,
            'tempo_medio_geral': round(tempo_medio_geral, 2) if pd.notna(tempo_medio_geral) else 0,
            'tempo_mediano_geral': round(tempo_mediano_geral, 2) if pd.notna(tempo_mediano_geral) else 0,
            'equipamentos_unicos': dados_limpos['Equipamento'].nunique(),
            'periodo_analise': f"{dados_limpos['Data'].min().strftime('%d/%m/%Y')} a {dados_limpos['Data'].max().strftime('%d/%m/%Y')}"
        },
        
        'manutencoes': {
            'preventivas': {
                **kpis_preventivas,
                'percentual': round(percentual_preventivas, 1)
            },
            'corretivas': {
                **kpis_corretivas,
                'percentual': round(percentual_corretivas, 1)
            }
        },
        
        'equipamentos_problematicos': equipamentos_problematicos.reset_index().to_dict('records')[:10],
        
        'performance_cidade': performance_cidade.reset_index().to_dict('records'),
        'performance_unidade': performance_unidade.reset_index().to_dict('records'),
        
        'timeline': timeline.reset_index().to_dict('records'),
        
        'graficos': {
            'distribuicao_tempos': distribuicao_tempos,
            'preventiva_vs_corretiva': {
                'Preventiva': kpis_preventivas['total'],
                'Corretiva': kpis_corretivas['total']
            },
            'tempo_medio_cidade': dict(zip(performance_cidade.index, performance_cidade['Tempo_Medio'])),
            'timeline_atendimentos': dict(zip(timeline.index, timeline['Total_Atendimentos']))
        }
    }
    
    return resultado

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