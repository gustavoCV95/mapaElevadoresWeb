# app.py
from flask import Flask, render_template, jsonify, request
import pandas as pd
from sheets_api import SheetsAPI
from config import Config
import json
from datetime import datetime

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
    
    return {}, [], [], [], []

@app.route('/')
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
            'em_atividade': len([r for r in registros_processados if r['status'] == 'Em atividade']),
            'suspensos': len([r for r in registros_processados if r['status'] == 'Suspenso'])
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
        'em_atividade': len([r for r in dados_filtrados if r['status'] == 'Em atividade']),
        'suspensos': len([r for r in dados_filtrados if r['status'] == 'Suspenso']),
        'por_tipo': {},
        'por_regiao': {},
        'por_marca': {},
        'por_status': {}
    }
    
    # Conta por categoria
    from collections import Counter
    stats_filtradas['por_tipo'] = dict(Counter([r['tipo'] for r in dados_filtrados]))
    stats_filtradas['por_regiao'] = dict(Counter([r['regiao'] for r in dados_filtrados]))
    stats_filtradas['por_marca'] = dict(Counter([r['marcaLicitacao'] for r in dados_filtrados]))
    stats_filtradas['por_status'] = dict(Counter([r['status'] for r in dados_filtrados]))
    
    print(f"📊 API: Stats calculadas - {stats_filtradas['total_elevadores']} elevadores em {stats_filtradas['total_predios']} locais")
    
    return jsonify({
        'success': True,
        'stats': stats_filtradas,
        'total_registros': len(dados_filtrados)
    })

@app.route('/atualizar')
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)