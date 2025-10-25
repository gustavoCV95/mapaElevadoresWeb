// dashboard_v2.js

// ========== FASE 5: FILTROS INTERATIVOS ==========

// Variáveis globais
let dadosOriginais = initialGeojsonData;
let mapaLeaflet = null;
let marcadoresAtuais = []; // NOVO: Controla marcadores atuais
let stats_detalhadas_inicial = initialDetailedStats

// Inicializa o mapa
function inicializarMapa() {
    console.log('Inicializando mapa v2.0 com filtros...');
    
    mapaLeaflet = L.map('mapa').setView([-19.92, -43.92], 7);

    console.log('Tamanho interno do mapa Leaflet (mapaLeaflet._size):', mapaLeaflet._size);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors, © CartoDB'
    }).addTo(mapaLeaflet);
    
    adicionarMarcadores(dadosOriginais);
}

// NOVO: Remove todos os marcadores
function limparMarcadores() {
    marcadoresAtuais.forEach(marker => {
        mapaLeaflet.removeLayer(marker);
    });
    marcadoresAtuais = [];
}

// ATUALIZADO: Adiciona marcadores ao mapa
function adicionarMarcadores(geojsonData) {
    // Limpa marcadores existentes
    limparMarcadores();
    
    if (!geojsonData || !geojsonData.features || geojsonData.features.length === 0) {
        console.warn("Nenhum dado GeoJSON ou features para adicionar marcadores.");
        return;
    }    

    // if (!geojsonData || !geojsonData.features) return;
    
    console.log(`Adicionando ${geojsonData.features.length} marcadores...`);


    geojsonData.features.forEach((feature, index) => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;

        if (!Array.isArray(coords) || coords.length !== 2 || 
            typeof coords[0] !== 'number' || typeof coords[1] !== 'number' || 
            isNaN(coords[0]) || isNaN(coords[1])) 
        {
            console.error(`ERRO: Coordenadas inválidas para feature no índice ${index}. Pulando este marcador.`);
            console.error('Coordenadas:', coords);
            console.error('Feature completa:', feature);
            // Retorna para pular este marcador problemático e continuar com os outros
            return; 
        }

        const latlng = [coords[1], coords[0]];      

        const marker = L.circleMarker(latlng,{
            radius: props.tamanhoMarcador,
            fillColor: props.corMarcador,
            color: props.corMarcador,
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        })
        
        // Tooltip
        let tooltipText = `${props.cidade} - ${props.tipo}<br/>
        ${props.qtd_elev} elevadores - ${props.marcaLicitacao}<br/>
        ${props.regiao} - ${props.status}`;
        if(props.nElevadorParado && props.nElevadorParado > 0){
            tooltipText += `<br/><strong style="color: ${props.corMarcador ||'#dc3545'};">${props.nElevadorParado} parado(s)</strong>`;
        }
        marker.bindTooltip(tooltipText,{sticky:true});
        
        // Popup
        let popupContent = `<div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0; color: #333;">${props.unidade}</h4>
            <p><strong>Cidade:</strong> ${props.cidade}</p>
            <p><strong>Endereço:</strong> ${props.endereco}</p>
            <p><strong>Tipo:</strong> ${props.tipo}</p>
            <p><strong>Elevadores:</strong> ${props.qtd_elev}</p>
            <p><strong>Paradas:</strong> ${props.paradas}</p>
            <p><strong>Marca:</strong> ${props.marca}</p>
            <p><strong>Empresa:</strong> ${props.empresa}</p>
            <p><strong>Status:</strong> <span style="color: ${props.corMarcador};">${props.status}</span></p>`;
        
        if ((props.nElevadorParado && props.nElevadorParado > 0) || props.status && props.status.toLowerCase().includes('suspenso')) {    
            if (props.nElevadorParado && props.nElevadorParado > 0) {
                popupContent += `<hr style="margin: 10px 0;"><p style="color: #dc3545;"><strong>⚠️ Elevadores Parados:</strong> ${props.nElevadorParado}</p>`;
            }
            if (props.dataDeParada) {
                popupContent += `<p style="color: #dc3545;"><strong>📅 Data da Parada:</strong> ${props.dataDeParada}</p>`;
            }
            if (props.previsaoDeRetorno) {
                popupContent += `<p style="color: #dc3545;"><strong>🔄 Previsão de Retorno:</strong> ${props.previsaoDeRetorno}</p>`;
            }
        }
        popupContent += '</div>';
        
        marker.bindPopup(popupContent, {maxWidth: 350});
        marker.addTo(mapaLeaflet);
        marcadoresAtuais.push(marker);
    });
}

// NOVO: Aplica filtros E atualiza o mapa
function aplicarFiltros() {
    console.log('Aplicando filtros v2.0 com atualização do mapa...');
    
    const tipos = obterSelecionados('tipo');
    const regioes = obterSelecionados('regiao');
    const marcas = obterSelecionados('marca')
    const empresas = obterSelecionados('empresa')
    const situacoes = obterSelecionados('situacao');

    
    console.log('Filtros selecionados:', {tipos, regioes, marcas, empresas, situacoes});
    
    // Mostra loading
    mostrarLoading(true);
    
    const params = new URLSearchParams();
    tipos.forEach(tipo => params.append('tipo', tipo));
    regioes.forEach(regiao => params.append('regiao', regiao));
    marcas.forEach(marca => params.append('marca', marca));
    empresas.forEach(empresa => params.append('empresa', empresa));
    situacoes.forEach(situacao => params.append('situacao', situacao));
    
    // NOVO: Chama API que retorna dados filtrados
    fetch(`/v2/api/dados-elevadores-filtrados?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Atualiza estaí­sticas
                atualizarCards(data.data.stats);
                
                // NOVO: Atualiza estatísticas detalhadas
                if (data.data.stats_detalhadas) {
                    atualizarStatsDetalhadas(data.data.stats_detalhadas);
                }
                
                // NOVO: Atualiza o mapa com dados filtrados
                adicionarMarcadores(data.data.geojson);
                
                // Ajusta zoom se necessÃ¡rio
                if (data.data.geojson.features.length > 0) {
                    ajustarZoomParaDados(data.data.geojson);
                }
                
                console.log('Filtros aplicados e mapa atualizado');
            } else {
                alert('Erro ao aplicar filtros: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erro ao aplicar filtros:', error);
            alert('Erro na requisição de filtros');
        })
        .finally(() => {
            mostrarLoading(false);
        });
}

// NOVO: Ajusta zoom para mostrar todos os dados
function ajustarZoomParaDados(geojsonData) {
    if (!geojsonData.features || geojsonData.features.length === 0) return;
    
    const group = new L.featureGroup(marcadoresAtuais);
    mapaLeaflet.fitBounds(group.getBounds(), {padding: [20, 20]});
}

// NOVO: Mostra/esconde loading
function mostrarLoading(mostrar) {
    const btn = document.querySelector('button[onclick="aplicarFiltros()"]');
    if (btn) {
        if (mostrar) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Filtrando...';
            btn.disabled = true;
        } else {
            btn.innerHTML = '<i class="fas fa-search"></i> Aplicar Filtros';
            btn.disabled = false;
        }
    }
}

// Obtém valores selecionados
function obterSelecionados(categoria) {
    const checkboxes = document.querySelectorAll(`input[id^="check-${categoria}-"]:checked`);
    return Array.from(checkboxes).map(cb => cb.value);
}

// Atualiza cards de estatí­sticas
function atualizarCards(stats) {
    const elementos = {
        'stat-predios': stats.total_predios || 0,
        'stat-elevadores': stats.total_elevadores || 0,
        'stat-cidades': stats.cidades || 0,
        'stat-regioes': stats.regioes || 0,
        'stat-ativos': stats.em_atividade || 0,
        'stat-parados': stats.elevadores_parados || 0,
        'stat-suspensos': stats.elevadores_suspensos || 0
    };
    
    for (let id in elementos) {
        const elem = document.getElementById(id);
        if (elem) {
            // NOVO: Animação nos números
            animarNumero(elem, parseInt(elem.textContent) || 0, elementos[id]);
        }
    }
    
    // Atualiza contador
    document.getElementById('total-elevadores-filtro').textContent = stats.total_elevadores || 0;
    document.getElementById('total-locais-filtro').textContent = stats.total_predios || 0;
}

// NOVO: Animação de números
function animarNumero(elemento, valorInicial, valorFinal) {
    const duracao = 500; // ms
    const passos = 20;
    const incremento = (valorFinal - valorInicial) / passos;
    let valorAtual = valorInicial;
    let passo = 0;
    
    const timer = setInterval(() => {
        passo++;
        valorAtual += incremento;
        
        if (passo >= passos) {
            elemento.textContent = valorFinal;
            clearInterval(timer);
        } else {
            elemento.textContent = Math.round(valorAtual);
        }
    }, duracao / passos);
}

// NOVO: Seleciona todos os filtros
function selecionarTodos() {
    console.log('Selecionando todos os filtros...');
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
    aplicarFiltros(); // Aplica automaticamente
}

// ATUALIZADO: Limpa filtros e restaura dados originais
function limparFiltros() {
    console.log('Limpando filtros e restaurando mapa...');
    
    // Limpa checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    
    // Restaura dados originais no mapa
    adicionarMarcadores(dadosOriginais);
    
    // Restaura estatí­sticas originais
    fetch('/v2/api/dados-elevadores')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                atualizarCards(data.data.stats);
                ajustarZoomParaDados(data.data.geojson);
                atualizarElevadoresParados(data.data.stats_detalhadas.elevadores_parados || []);
                atualizarStatsDetalhadas(data.data.stats_detalhadas);
            }
        })
        .catch(error => console.error('Erro ao restaurar dados:', error));
}

// ATUALIZADO: Atualiza estatí­sticas detalhadas
function atualizarStatsDetalhadas(statsDetalhadas) {
    // Atualiza por tipo
    atualizarListaStats('stats-por-tipo', statsDetalhadas.por_tipo);
    
    // Atualiza por região
    atualizarListaStats('stats-por-regiao', statsDetalhadas.por_regiao);
    
    // Atualiza por marca
    atualizarListaStats('stats-por-marca', statsDetalhadas.por_marca);
    
    // Atualiza por status
    atualizarListaStatsComCor('stats-por-status', statsDetalhadas.por_status);
    
    // Atualiza elevadores parados
    atualizarElevadoresParados(statsDetalhadas.elevadores_parados);
}

function atualizarListaStats(elementId, dados) {
    const elemento = document.getElementById(elementId);
    if (!elemento || !dados) return;
    
    let html = '';
    for (const [chave, valor] of Object.entries(dados)) {
        html += `<div class="d-flex justify-content-between">
            <span>${chave}:</span>
            <strong>${valor}</strong>
        </div>`;
    }
    
    elemento.innerHTML = html || '<div class="text-muted">Nenhum dado</div>';
}

function atualizarListaStatsComCor(elementId, dados) {
    const elemento = document.getElementById(elementId);
    if (!elemento || !dados) return;
    
    let html = '';
    for (const [chave, valor] of Object.entries(dados)) {
        let classe = '';
        if (chave === 'Em atividade') classe = 'text-success';
        else if (chave === 'Parados') classe = 'text-danger';
        else classe = 'text-warning';
        
        html += `<div class="d-flex justify-content-between">
            <span class="${classe}">${chave}:</span>
            <strong>${valor}</strong>
        </div>`;
    }
    
    elemento.innerHTML = html || '<div class="text-muted">Nenhum dado</div>';
}

function atualizarElevadoresParados(elevadoresParados) {
    const tbody = document.getElementById('elevadores-parados-tbody');
    const section = document.getElementById('elevadores-parados-section');
    
    if (!tbody || !section) return;
    
    // Sempre mostra a seção
    section.style.display = 'block';
    
    // Se não há elevadores parados, mostra a mensagem "Nenhum elevador parado"
    if (!elevadoresParados || elevadoresParados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-3">
                    <i class="fas fa-check-circle text-success"></i> 
                    Nenhum elevador parado
                </td>
            </tr>
        `;
        return;
    }
    
    // Se há elevadores parados, mostra a tabela normalmente
    let html = '';
    elevadoresParados.forEach(elevador => {
        html += `<tr>
            <td>${elevador.unidade}</td>
            <td>${elevador.cidade}</td>
            <td>${elevador.tipo}</td>
            <td>${elevador.regiao}</td>
            <td class="text-danger"><strong>${elevador.quantidade_parada}</strong></td>
            <td>${elevador.total_elevadores}</td>
            <td>${elevador.marca}</td>
        </tr>`;
    });
    
    tbody.innerHTML = html;
}

// NOVO: Aplicar filtros automaticamente quando checkbox muda
function configurarFiltrosAutomaticos() {
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Aplica filtros automaticamente após 500ms de inatividade
            clearTimeout(window.filtroTimeout);
            window.filtroTimeout = setTimeout(aplicarFiltros, 500);
        });
    });
}

// Atualiza dados
function atualizarDados() {
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
    btn.disabled = true;
    
    fetch('/v2/atualizar-dados')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Dados atualizados!\n' + data.message);
                location.reload();
            } else {
                alert('Erro: ' + data.message);
            }
        })
        .catch(error => alert('Erro na requisição'))
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// ATUALIZADO: Inicializa quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard v2.0 carregado com filtros interativos');
    const mapaElement = document.getElementById('mapa');
    if (mapaElement) {
        // Verifique as dimensões do mapaElement ANTES de inicializar
        console.log('Dimensões do elemento #mapa:', mapaElement.offsetWidth, mapaElement.offsetHeight);
        if (mapaElement.offsetWidth === 0 || mapaElement.offsetHeight === 0) {
            console.error('Elemento #mapa está com dimensões zero. Isso pode causar problemas de renderização do Leaflet.');
            // Tente forçar um pequeno delay para a inicialização do mapa
            setTimeout(function() {
                inicializarMapa();
                configurarFiltrosAutomaticos();
                atualizarElevadoresParados(stats_detalhadas_inicial.elevadores_parados || []);
            }, 100); // Pequeno delay
        } else {
            inicializarMapa();
            configurarFiltrosAutomaticos();
            atualizarElevadoresParados(stats_detalhadas_inicial.elevadores_parados || []);
        }
    } else {
        console.error('Elemento #mapa não encontrado no DOM!');
    }
});