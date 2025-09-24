    // static/js/filtros_mapa.js - Versão com captura melhorada

    let dadosOriginais = null;
    let dadosFiltrados = null;
    let mapaLeaflet = null;
    let marcadoresOriginais = [];

    console.log('🔧 Script de filtros carregado');

    // Função para inicializar o sistema de filtros
    function inicializarFiltros(geojsonData) {
        console.log('🚀 Inicializando filtros...');
        console.log('📊 Dados recebidos:', geojsonData);
        
        dadosOriginais = geojsonData;
        dadosFiltrados = geojsonData;
        
        if (dadosOriginais && dadosOriginais.features) {
            console.log('✅ Features disponíveis:', dadosOriginais.features.length);
        } else {
            console.error('❌ Nenhuma feature encontrada nos dados');
            return;
        }
        
        // Captura o mapa Leaflet com múltiplas estratégias
        capturarMapaLeaflet();
    }

    // Função para capturar o mapa Leaflet - VERSÃO MELHORADA
    function capturarMapaLeaflet() {
        console.log('🗺️ Tentando capturar mapa Leaflet com múltiplas estratégias...');
        
        let tentativas = 0;
        const maxTentativas = 15;
        
        const verificarMapa = () => {
            tentativas++;
            console.log(`🔍 Tentativa ${tentativas}/${maxTentativas} de capturar mapa...`);
            
            // ESTRATÉGIA 1: Procurar por variáveis map_*
            const mapKeys = Object.keys(window).filter(key => key.startsWith('map_'));
            console.log('�� Chaves map_* encontradas:', mapKeys);
            
            for (let key of mapKeys) {
                const mapInstance = window[key];
                if (mapInstance && mapInstance._container) {
                    mapaLeaflet = mapInstance;
                    console.log('✅ Mapa capturado via map_*:', key);
                    finalizarCaptura();
                    return true;
                }
            }
            
            // ESTRATÉGIA 2: Procurar em todas as variáveis globais
            for (let key in window) {
                const obj = window[key];
                if (obj && typeof obj === 'object' && obj._container && obj.addLayer) {
                    mapaLeaflet = obj;
                    console.log('✅ Mapa capturado via varredura global:', key);
                    finalizarCaptura();
                    return true;
                }
            }
            
            // ESTRATÉGIA 3: Usar DOM + Leaflet API
            const mapContainers = document.querySelectorAll('.folium-map');
            console.log('�� Containers .folium-map encontrados:', mapContainers.length);
            
            for (let container of mapContainers) {
                if (container._leaflet_id && window.L) {
                    // Tenta acessar o mapa via container
                    const maps = window.L._layer ? Object.values(window.L._layer) : [];
                    for (let map of maps) {
                        if (map._container === container) {
                            mapaLeaflet = map;
                            console.log('✅ Mapa capturado via DOM/Leaflet:', container.id);
                            finalizarCaptura();
                            return true;
                        }
                    }
                    
                    // Tenta acessar via _leaflet_id
                    if (window.L && window.L.map && container._leaflet_id) {
                        try {
                            const mapInstance = window.L.map(container);
                            if (mapInstance && mapInstance._container) {
                                mapaLeaflet = mapInstance;
                                console.log('✅ Mapa capturado via L.map()');
                                finalizarCaptura();
                                return true;
                            }
                        } catch (e) {
                            console.log('⚠️ Erro ao tentar L.map():', e.message);
                        }
                    }
                }
            }
            
            // ESTRATÉGIA 4: Interceptar criação do mapa
            if (window.L && !window._mapInterceptorAdded) {
                window._mapInterceptorAdded = true;
                const originalMap = window.L.map;
                window.L.map = function(...args) {
                    const mapInstance = originalMap.apply(this, args);
                    console.log('🎯 Mapa interceptado na criação!');
                    mapaLeaflet = mapInstance;
                    finalizarCaptura();
                    return mapInstance;
                };
            }
            
            // ESTRATÉGIA 5: Procurar instâncias ativas do Leaflet
            if (window.L && window.L.Map) {
                const allMaps = [];
                
                // Tenta encontrar todas as instâncias de L.Map
                document.querySelectorAll('div').forEach(div => {
                    if (div._leaflet && div._leaflet instanceof window.L.Map) {
                        allMaps.push(div._leaflet);
                    }
                });
                
                if (allMaps.length > 0) {
                    mapaLeaflet = allMaps[0];
                    console.log('✅ Mapa encontrado via instância L.Map');
                    finalizarCaptura();
                    return true;
                }
            }
            
            if (tentativas < maxTentativas) {
                setTimeout(verificarMapa, 1000);
            } else {
                console.error('❌ Não foi possível capturar o mapa após', maxTentativas, 'tentativas');
                console.log('🔍 Debug - window.L:', window.L);
                console.log('🔍 Debug - document.querySelectorAll(".folium-map"):', document.querySelectorAll('.folium-map'));
                
                // Como último recurso, vamos trabalhar diretamente com o DOM
                usarFallbackDOM();
            }
        };
        
        verificarMapa();
    }

    // Função para finalizar a captura do mapa
    function finalizarCaptura() {
        if (mapaLeaflet) {
            console.log('🎉 Mapa capturado com sucesso!');
            console.log('📍 Container do mapa:', mapaLeaflet._container);
            
            // Salva marcadores originais
            salvarMarcadoresOriginais();
        }
    }

    // Função FALLBACK - trabalha diretamente com DOM se não conseguir capturar o mapa
    function usarFallbackDOM() {
        console.log('�� Usando fallback DOM...');
        
        // Se não conseguir capturar o mapa, pelo menos atualiza visualmente
        window.atualizarMapaFallback = function() {
            console.log('🔄 Atualizando mapa via fallback DOM...');
            
            const mapContainer = document.querySelector('.folium-map');
            if (mapContainer) {
                // Cria um overlay com informações dos filtros
                let overlay = document.getElementById('filtro-overlay');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'filtro-overlay';
                    overlay.style.cssText = `
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: rgba(0,0,0,0.8);
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                        z-index: 10000;
                        text-align: center;
                        font-family: Arial, sans-serif;
                    `;
                    mapContainer.style.position = 'relative';
                    mapContainer.appendChild(overlay);
                }
                
                const totalFiltrados = dadosFiltrados.features ? dadosFiltrados.features.length : 0;
                overlay.innerHTML = `
                    <h4>🔍 Filtros Ativos</h4>
                    <p>${totalFiltrados} locais selecionados</p>
                    <small>Mapa será recarregado automaticamente</small>
                `;
                
                // Remove o overlay após 3 segundos
                setTimeout(() => {
                    if (overlay) overlay.remove();
                }, 3000);
            }
        };
    }

    // Função para salvar referências dos marcadores originais
    function salvarMarcadoresOriginais() {
        console.log('💾 Salvando marcadores originais...');
        
        marcadoresOriginais = [];
        
        if (mapaLeaflet) {
            mapaLeaflet.eachLayer(function(layer) {
                // Ignora tiles e outras camadas não-marcador
                if (layer.feature || layer._latlng || (layer._layers && Object.keys(layer._layers).length > 0)) {
                    marcadoresOriginais.push(layer);
                    console.log('💾 Marcador salvo:', layer);
                }
            });
            
            console.log(`✅ ${marcadoresOriginais.length} marcadores originais salvos`);
        }
    }

    // Função para obter valores selecionados
    function obterSelecionados(categoria) {
        const checkboxes = document.querySelectorAll(`input[id^="check-${categoria}-"]:checked`);
        const valores = Array.from(checkboxes).map(cb => cb.value);
        console.log(`🔍 Filtros selecionados para ${categoria}:`, valores);
        return valores;
    }

    // Função para aplicar filtros - COM DEBUG
    function aplicarFiltros() {
        console.log('🎯 ========== APLICANDO FILTROS ==========');
        
        const tiposSelecionados = obterSelecionados('tipo');
        const regioesSelecionadas = obterSelecionados('regiao');
        const marcasSelecionadas = obterSelecionados('marca');
        const empresasSelecionadas = obterSelecionados('empresa');

        console.log('📋 Resumo dos filtros:', {
            tipos: tiposSelecionados,
            regioes: regioesSelecionadas,
            marcas: marcasSelecionadas,
            empresas: empresasSelecionadas
        });

        if (!dadosOriginais || !dadosOriginais.features) {
            console.error('❌ Dados originais não disponíveis');
            return;
        }

        // Filtra os dados
        const featuresOriginal = dadosOriginais.features.length;
        console.log(`📊 Dados originais: ${featuresOriginal} features`);
        
        dadosFiltrados = {
            ...dadosOriginais,
            features: dadosOriginais.features.filter(feature => {
                const props = feature.properties;
                
                const passaTipo = tiposSelecionados.length === 0 || tiposSelecionados.includes(props.tipo);
                const passaRegiao = regioesSelecionadas.length === 0 || regioesSelecionadas.includes(props.regiao);
                const passaMarca = marcasSelecionadas.length === 0 || marcasSelecionadas.includes(props.marcaLicitacao);
                const passaEmpresa = empresasSelecionadas.length === 0 || empresasSelecionadas.includes(props.empresa);
                
                return passaTipo && passaRegiao && passaMarca && passaEmpresa;
            })
        };

        const featuresFiltradas = dadosFiltrados.features.length;
        
        // DEBUG: Calcula totais do frontend
        const totalElevadoresFrontend = dadosFiltrados.features.reduce((total, feature) => {
            return total + feature.properties.qtd_elev;
        }, 0);
        
        console.log(`📊 FRONTEND - Filtragem: ${featuresOriginal} → ${featuresFiltradas} features`);
        console.log(`📊 FRONTEND - Total elevadores: ${totalElevadoresFrontend}`);
        console.log(`📊 FRONTEND - Total locais: ${featuresFiltradas}`);

        // Atualiza o mapa
        atualizarMapa();
        
        // Atualiza contador
        atualizarContadorFiltros();
        
        // Atualiza estatísticas
        atualizarEstatisticasDashboard();
        
        console.log('✅ ========== FILTROS APLICADOS ==========');
    }
    // Função para atualizar o mapa
    function atualizarMapa() {
        console.log('🗺️ ========== ATUALIZANDO MAPA ==========');
        
        if (!mapaLeaflet) {
            console.error('❌ Mapa Leaflet não disponível, usando fallback...');
            if (window.atualizarMapaFallback) {
                window.atualizarMapaFallback();
            }
            return;
        }

        // Remove marcadores existentes
        console.log('🧹 Removendo marcadores existentes...');
        
        let marcadoresRemovidos = 0;
        marcadoresOriginais.forEach(layer => {
            if (mapaLeaflet.hasLayer(layer)) {
                mapaLeaflet.removeLayer(layer);
                marcadoresRemovidos++;
            }
        });
        
        console.log(`🗑️ ${marcadoresRemovidos} marcadores removidos`);

        // Remove todas as camadas não-tile como backup
        mapaLeaflet.eachLayer(function(layer) {
            if (!layer._url && !layer.options.attribution) {
                mapaLeaflet.removeLayer(layer);
            }
        });

        // Adiciona novos marcadores
        if (dadosFiltrados.features && dadosFiltrados.features.length > 0) {
            console.log(`➕ Adicionando ${dadosFiltrados.features.length} novos marcadores...`);
            
            marcadoresOriginais = [];
            
            dadosFiltrados.features.forEach((feature, index) => {
                const marker = criarMarcador(feature);
                marker.addTo(mapaLeaflet);
                marcadoresOriginais.push(marker);
                
                if (index < 3) {
                    console.log(`➕ Marcador ${index + 1} adicionado:`, feature.properties.unidade);
                }
            });
            
            console.log(`✅ ${dadosFiltrados.features.length} marcadores adicionados com sucesso`);
        } else {
            console.log('⚠️ Nenhum marcador para exibir (dados filtrados vazios)');
        }
        
        console.log('✅ ========== MAPA ATUALIZADO ==========');
    }

    // Função para criar um marcador
    function criarMarcador(feature) {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        const latlng = [coords[1], coords[0]]; // Leaflet usa [lat, lng]
        
        // Define cor baseada no status
        const status = props.status.toLowerCase();
        let cor = '#6c757d';
        if (status.includes('atividade')) cor = '#28a745';
        else if (status.includes('suspenso')) cor = '#dc3545';
        
        // Define tamanho baseado na quantidade
        const radius = props.qtd_elev >= 5 ? 10 : (props.qtd_elev >= 3 ? 8 : 6);
        
        // Cria o marcador
        const marker = L.circleMarker(latlng, {
            radius: radius,
            fillColor: cor,
            color: cor,
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        // Adiciona tooltip
        marker.bindTooltip(
            `${props.cidade} - ${props.tipo}<br/>
            ${props.qtd_elev} elevadores - ${props.marcaLicitacao}<br/>
            ${props.regiao} - ${props.status}`,
            {sticky: true}
        );
        
        // Adiciona popup
        marker.bindPopup(
            `<div style="font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #333;">${props.unidade}</h4>
                <p><strong>Cidade:</strong> ${props.cidade}</p>
                <p><strong>Endereço:</strong> ${props.endereco}</p>
                <p><strong>Tipo:</strong> ${props.tipo}</p>
                <p><strong>Elevadores:</strong> ${props.qtd_elev}</p>
                <p><strong>Paradas:</strong> ${props.paradas}</p>
                <p><strong>Marca:</strong> ${props.marca}</p>
                <p><strong>Empresa:</strong> ${props.empresa}</p>
                <p><strong>Status:</strong> ${props.status}</p>
            </div>`,
            {maxWidth: 350}
        );
        
        return marker;
    }

    // Função para atualizar contador
    function atualizarContadorFiltros() {
        if (!dadosFiltrados.features) return;
        
        const totalElevadores = dadosFiltrados.features.reduce((total, feature) => {
            return total + feature.properties.qtd_elev;
        }, 0);

        const totalLocais = dadosFiltrados.features.length;

        const elemElevadores = document.getElementById('total-elevadores-filtro');
        const elemLocais = document.getElementById('total-locais-filtro');
        
        if (elemElevadores) elemElevadores.textContent = totalElevadores;
        if (elemLocais) elemLocais.textContent = totalLocais;

        const contadorElement = document.getElementById('contador-resultados');
        if (contadorElement) {
            if (totalElevadores === 0) {
                contadorElement.style.background = '#ffebee';
                contadorElement.style.color = '#c62828';
                contadorElement.style.borderColor = '#ef9a9a';
            } else {
                contadorElement.style.background = '#e8f5e8';
                contadorElement.style.color = '#2e7d32';
                contadorElement.style.borderColor = '#a5d6a7';
            }
        }
        
        console.log(`📊 Contador atualizado: ${totalElevadores} elevadores em ${totalLocais} locais`);
    }

    // Função para atualizar estatísticas da dashboard
    function atualizarEstatisticasDashboard() {
        const tiposSelecionados = obterSelecionados('tipo');
        const regioesSelecionadas = obterSelecionados('regiao');
        const marcasSelecionadas = obterSelecionados('marca');
        const empresasSelecionadas = obterSelecionados('empresa');

        // Se nenhum filtro ativo, não faz requisição
        if (tiposSelecionados.length === 0 && regioesSelecionadas.length === 0 && 
            marcasSelecionadas.length === 0 && empresasSelecionadas.length === 0) {
            console.log('⏭️ Nenhum filtro ativo, pulando atualização de estatísticas');
            return;
        }

        // Monta parâmetros
        const params = new URLSearchParams();
        tiposSelecionados.forEach(tipo => params.append('tipo', tipo));
        regioesSelecionadas.forEach(regiao => params.append('regiao', regiao));
        marcasSelecionadas.forEach(marca => params.append('marca', marca));
        empresasSelecionadas.forEach(empresa => params.append('empresa', empresa));

        console.log('📡 Fazendo requisição para API...');

        // Mostra loading
        const loadingElement = document.getElementById('loading-stats');
        if (loadingElement) loadingElement.style.display = 'block';

        // Faz requisição
        fetch('/api/filtrar?' + params.toString())
            .then(response => response.json())
            .then(data => {
                if (loadingElement) loadingElement.style.display = 'none';
                
                console.log('📡 Resposta da API:', data);
                
                if (data.success) {
                    // Atualiza cards
                    const elementos = {
                        'stat-predios': data.stats.total_predios,
                        'stat-elevadores': data.stats.total_elevadores,
                        'stat-cidades': data.stats.cidades,
                        'stat-regioes': data.stats.regioes,
                        'stat-ativos': data.stats.em_atividade,
                        'stat-suspensos': data.stats.suspensos
                    };
                    
                    for (let id in elementos) {
                        const elem = document.getElementById(id);
                        if (elem) {
                            elem.textContent = elementos[id];
                            console.log(`📊 Card ${id} atualizado para:`, elementos[id]);
                        }
                    }

                    // Atualiza estatísticas detalhadas
                    mostrarEstatisticasDetalhadas(data.stats);
                }
            })
            .catch(error => {
                if (loadingElement) loadingElement.style.display = 'none';
                console.error('❌ Erro ao carregar estatísticas:', error);
            });
    }

    // Função para mostrar estatísticas detalhadas
    function mostrarEstatisticasDetalhadas(stats) {
        const container = document.getElementById('stats-detalhadas');
        if (!container) return;
        
        let html = '<div class="row">';
        
        const categorias = [
            {titulo: 'Por Tipo', dados: stats.por_tipo},
            {titulo: 'Por Região', dados: stats.por_regiao},
            {titulo: 'Por Marca', dados: stats.por_marca},
            {titulo: 'Por Status', dados: stats.por_status}
        ];
        
        categorias.forEach(categoria => {
            html += `<div class="col-md-3"><h6>${categoria.titulo}</h6><ul class="list-unstyled">`;
            for (let [key, value] of Object.entries(categoria.dados)) {
                html += `<li><strong>${key}:</strong> ${value}</li>`;
            }
            html += '</ul></div>';
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    // Funções auxiliares
    function limparFiltros() {
        console.log('🧹 Limpando todos os filtros...');
        
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        
        dadosFiltrados = dadosOriginais;
        atualizarMapa();
        atualizarContadorFiltros();
        
        // Restaura valores originais dos cards
        const valoresOriginais = window.statsOriginais || {};
        for (let id in valoresOriginais) {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = valoresOriginais[id];
        }
        
        const statsContainer = document.getElementById('stats-detalhadas');
        if (statsContainer) {
            statsContainer.innerHTML = '<p class="text-muted">Use os filtros no mapa para ver estatísticas específicas.</p>';
        }
        
        console.log('✅ Filtros limpos');
    }

    function selecionarTodos() {
        console.log('✅ Selecionando todos os filtros...');
        
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = true);
        aplicarFiltros();
    }

    function toggleCategoria(categoria) {
        const div = document.getElementById(`filtros-${categoria}`);
        const button = document.getElementById(`toggle-${categoria}`);

        if (div && button) {
            if (div.style.display === 'none') {
                div.style.display = 'block';
                button.textContent = '➖';
            } else {
                div.style.display = 'none';
                button.textContent = '➕';
            }
        }
    }

    function atualizarDados() {
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
        btn.disabled = true;
        
        fetch('/atualizar')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Dados atualizados!\n' + data.message);
                    location.reload();
                } else {
                    alert('Erro: ' + data.message);
                }
            })
            .catch(error => {
                alert('Erro na requisição');
            })
            .finally(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
    }

    // Adiciona event listener para debug quando a página carrega
    document.addEventListener('DOMContentLoaded', function() {
        console.log('�� DOM carregado, aguardando inicialização...');
    });