// dashboard_v2.js

// ========== FASE 5: FILTROS INTERATIVOS ==========

// Variáveis globais
let dadosOriginais = initialGeojsonData; 
let mapaLeaflet = null;
let marcadoresAtuais = [];
let allElevators = allElevatorsLoaded; 
let allBuildings = buildingsForForm; 


// Eventos e inicializações
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard v2.0 carregado com gerenciamento de elevadores.');
    
    // NOVO: Iniciar o mapa SOMENTE UMA VEZ
    // A condição do setTimeout é para quando o elemento #mapa não está visível imediatamente (ex: em abas ocultas)
    // Se o mapa for visível, chame direto. Senão, use o setTimeout.
    const mapaElement = document.getElementById('mapa');
    if (mapaElement && (mapaElement.offsetWidth === 0 || mapaElement.offsetHeight === 0)) {
        setTimeout(function() {
            console.log('DEBUG: inicializarMapa() chamado via setTimeout');
            inicializarMapa();
            // Outras inicializações que dependem do mapa visível ou dados carregados
            configurarFiltrosAutomaticos();
            atualizarElevadoresParadosTabela(initialDetailedStats.elevadores_parados || []);
            setupElevadorManagement(); 
        }, 100); 
    } else if (mapaElement) { // Mapa visível e elemento existe
        console.log('DEBUG: inicializarMapa() chamado diretamente');
        inicializarMapa();
        // Outras inicializações que dependem do mapa visível ou dados carregados
        configurarFiltrosAutomaticos();
        atualizarElevadoresParadosTabela(initialDetailedStats.elevadores_parados || []);
        setupElevadorManagement(); 
    } else {
        console.error('ERRO: Elemento #mapa não encontrado no DOM!');
        // No caso de não haver mapa, ainda precisamos configurar outras partes
        configurarFiltrosAutomaticos();
        atualizarElevadoresParadosTabela(initialDetailedStats.elevadores_parados || []);
        setupElevadorManagement(); 
    }
});


// O seu `inicializarMapa` estava assim:
function inicializarMapa() {
    console.log('Inicializando mapa v2.0 com filtros...');
    
    // CORRIGIDO: Verifica se o mapa já foi inicializado para evitar o erro.
    if (mapaLeaflet) {
        console.warn('Mapa já inicializado. Pulando segunda inicialização.');
        return;
    }

    mapaLeaflet = L.map('mapa').setView([-19.92, -43.92], 7);

    console.log('Tamanho interno do mapa Leaflet (mapaLeaflet._size):', mapaLeaflet._size);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors, © CartoDB'
    }).addTo(mapaLeaflet);
    
    // CORRIGIDO: Usa a variável global dadosOriginais que agora foi definida
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
            radius: props.tamanho_marcador_grupo, 
            fillColor: props.cor_marcador_grupo,   
            color: props.cor_marcador_grupo,
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        // Tooltip
        let tooltipText = `${props.cidade} - ${props.unidade} (${props.total_elevadores_grupo} elevadores)<br/>
        Status Predominante: ${props.status_grupo_prioritario}`;
        marker.bindTooltip(tooltipText,{sticky:true});
        
        // Popup para grupos: lista os elevadores individuais do grupo
        let popupContent = `<div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0; color: #333;">${props.cidade} - ${props.unidade}</h4>
            <p><strong>Endereço:</strong> ${props.endereco}</p>
            <p><strong>Total de Elevadores:</strong> ${props.total_elevadores_grupo}</p>
            <p><strong>Status Predominante:</strong> <span style="color: ${props.cor_marcador_grupo};">${props.status_grupo_prioritario}</span></p>
            <hr>
            <h6>Elevadores Individuais:</h6>
            <ul style="list-style: none; padding-left: 0;">`;
        
        props.elevadores_no_grupo.forEach(elev => {
            const statusColor = elev.status.toLowerCase() === 'parado' ? '#dc3545' :
                                elev.status.toLowerCase() === 'suspenso' ? '#ffc107' :
                                '#28a745';
            popupContent += `
                <li style="margin-bottom: 5px;">
                    <strong>ID: ${elev.id}</strong> - ${elev.descricao}<br/>
                    Tipo: ${elev.tipo}, Marca: ${elev.marca}<br/>
                    Status: <span style="color: ${statusColor};">${elev.status}</span>`;
            if (elev.data_de_parada) {
                popupContent += `<br/>Parado desde: ${elev.data_de_parada}`;
            }
            if (elev.previsao_de_retorno) {
                popupContent += `<br/>Previsão: ${elev.previsao_de_retorno}`;
            }
            popupContent += `</li>`;
        });
        popupContent += `</ul></div>`;
        
        marker.bindPopup(popupContent, {maxWidth: 400});
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
                // GeoJSON agora vem agrupado
                adicionarMarcadores(data.data.geojson); 
                atualizarCards(data.data.stats);
                
                // elevadores_parados também são objetos Elevator
                atualizarElevadoresParadosTabela(data.data.stats_detalhadas.elevadores_parados || []);
                atualizarStatsDetalhadas(data.data.stats_detalhadas);
            } else {
                console.error('Erro ao limpar filtros via API:', data.message);
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

function atualizarElevadoresParadosTabela(elevadoresParadosList) {
    const tbody = document.getElementById('elevadores-parados-tbody');
    if (!tbody) return;
    
    let html = '';
    if (!elevadoresParadosList || elevadoresParadosList.length === 0) {
        html = `
            <tr>
                <td colspan="7" class="text-center text-muted py-3">
                    <i class="fas fa-check-circle text-success"></i> 
                    Nenhum elevador parado
                </td>
            </tr>
        `;
    } else {
        elevadoresParadosList.forEach(elevador => {
            html += `
                <tr class="elevador-row-hover">
                    <td>${elevador.unidade} - ${elevador.cidade}</td>
                    <td>${elevador.tipo}</td>
                    <td>${elevador.marca}</td>
                    <td>${elevador.descricao} (ID: ${elevador.id})</td>
                    <td style="text-align: center;">${elevador.DataDeParada || '-'}</td>
                    <td style="text-align: center;">${elevador.PrevisaoDeRetorno || '-'}</td>
                    <td>
                        <span class="acao-elevador-parado">
                            <button class="btn btn-sm btn-info btn-edit-elevador" data-id="${elevador.id}" title="Editar Status"><i class="fas fa-pencil-alt"></i></button>
                            <button class="btn btn-sm btn-danger btn-delete-elevador" data-id="${elevador.id}" title="Marcar como Em Atividade"><i class="fas fa-times"></i></button>
                        </span>
                    </td>
                </tr>
            `;
        });
    }
    tbody.innerHTML = html;

    // Adiciona event listeners aos novos botões de edição/exclusão
    document.querySelectorAll('.btn-edit-elevador').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation(); // Previne que o evento se propague para a linha
            abrirModalGerenciarElevador('editar', parseInt(this.dataset.id));
        });
    });
    document.querySelectorAll('.btn-delete-elevador').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation(); // Previne que o evento se propague para a linha
            confirmarRemocaoElevador(parseInt(this.dataset.id));
        });
    });
}

// ATUALIZADO: updateDatalistsAndCheckAutofill para usar Building e Elevator
function updateDatalistsAndCheckAutofill() {
    const cidadeInput = document.getElementById('form-cidade');
    const unidadeInput = document.getElementById('form-unidade');
    const enderecoInput = document.getElementById('form-endereco');
    const elevadoresList = document.getElementById('elevadores-list');

    const currentCidade = cidadeInput.value.toLowerCase().trim();
    const currentUnidade = unidadeInput.value.toLowerCase().trim();
    const currentEndereco = enderecoInput.value.toLowerCase().trim();

    let filteredBuildings = allBuildings.filter(b => {
        const matchesCidade = !currentCidade || b.cidade.toLowerCase().includes(currentCidade);
        const matchesUnidade = !currentUnidade || b.unidade.toLowerCase().includes(currentUnidade);
        const matchesEndereco = !currentEndereco || b.endereco.toLowerCase().includes(currentEndereco);
        return matchesCidade && matchesUnidade && matchesEndereco;
    });

    if (currentCidade && currentUnidade && currentEndereco && filteredBuildings.length === 1) {
        cidadeInput.value = filteredBuildings[0].cidade;
        unidadeInput.value = filteredBuildings[0].unidade;
        enderecoInput.value = filteredBuildings[0].endereco;
        populateElevadoresDatalistForBuilding(filteredBuildings[0].id);
    } else {
        elevadoresList.innerHTML = ''; // Limpa a lista de elevadores se o prédio não estiver único
        document.getElementById('form-elevador-descricao').value = '';
        document.getElementById('form-id-elevador-unico').value = '';

        // Se o usuário está digitando nos campos de localização, preenche a datalist de elevadores
        // com elevadores que correspondem aos critérios parciais.
        const filteredElevatorsByLocation = allElevators.filter(e => {
            const matchesCidade = !currentCidade || e.cidade.toLowerCase().includes(currentCidade);
            const matchesUnidade = !currentUnidade || e.unidade.toLowerCase().includes(currentUnidade);
            const matchesEndereco = !currentEndereco || e.endereco.toLowerCase().includes(currentEndereco);
            return matchesCidade && matchesUnidade && matchesEndereco;
        });
        const uniqueElevadoresLocais = new Set();
        filteredElevatorsByLocation.forEach(elev => uniqueElevadoresLocais.add(`${elev.descricao} (ID: ${elev.id})`));
        elevadoresList.innerHTML = Array.from(uniqueElevadoresLocais).map(e => `<option value="${e}">`).join('');
    }
}

function setupElevadorManagement() {
    const btnAdicionar = document.getElementById('btnAdicionarElevadorParado');
    const btnSalvar = document.getElementById('btnSalvarElevador'); // CORRIGIDO: Usar ID correto do HTML
    
    // Verifica se os botões existem antes de adicionar o listener
    if (btnAdicionar) {
        btnAdicionar.addEventListener('click', function() {
            abrirModalGerenciarElevador('adicionar');
        });
    } else {
        console.error('ERRO: Botão #btnAdicionarElevadorParado não encontrado.');
    }

    if (btnSalvar) {
        btnSalvar.addEventListener('click', salvarGerenciamentoElevador);
    } else {
        console.error('ERRO: Botão #btnSalvarElevador (dentro do modal) não encontrado.');
    }

    // Configurar listeners para autocompletar e auto-preencher para os campos do formulário do modal
    const formCidade = document.getElementById('form-cidade');
    const formUnidade = document.getElementById('form-unidade');
    const formEndereco = document.getElementById('form-endereco');
    const formElevadorId = document.getElementById('form-id-elevador'); // CORRIGIDO: ID no HTML é 'form-id-elevador'

    if (formCidade) formCidade.addEventListener('input', updateDatalistsAndCheckAutofill);
    else console.error('ERRO: Campo #form-cidade (modal) não encontrado.');
    if (formUnidade) formUnidade.addEventListener('input', updateDatalistsAndCheckAutofill);
    else console.error('ERRO: Campo #form-unidade (modal) não encontrado.');
    if (formEndereco) formEndereco.addEventListener('input', updateDatalistsAndCheckAutofill);
    else console.error('ERRO: Campo #form-endereco (modal) não encontrado.');
    if (formElevadorId) formElevadorId.addEventListener('input', autoPreencherElevadorInfo); // CORRIGIDO: ID correto
    else console.error('ERRO: Campo #form-id-elevador (modal) não encontrado.');
    
    preencherDatalistsLocais();
}

function preencherDatalistsLocais() {
    // CORRIGIDO: Verificar se as datalists existem antes de preenchê-las
    const datalists = {
        cidades: document.getElementById('cidades-list'),
        unidades: document.getElementById('unidades-list'),
        enderecos: document.getElementById('enderecos-list'),
        elevadores: document.getElementById('elevadores-list')
    };

    if (datalists.cidades) {
        const cidadesUnicas = [...new Set(allElevators.map(e => e.cidade))].sort();
        datalists.cidades.innerHTML = '';
        cidadesUnicas.forEach(cidade => {
            const option = document.createElement('option');
            option.value = cidade;
            datalists.cidades.appendChild(option);
        });
    }

    if (datalists.unidades) {
        const unidadesUnicas = [...new Set(allElevators.map(e => e.unidade))].sort();
        datalists.unidades.innerHTML = '';
        unidadesUnicas.forEach(unidade => {
            const option = document.createElement('option');
            option.value = unidade;
            datalists.unidades.appendChild(option);
        });
    }

    if (datalists.enderecos) {
        const enderecosUnicos = [...new Set(allElevators.map(e => e.endereco))].sort();
        datalists.enderecos.innerHTML = '';
        enderecosUnicos.forEach(endereco => {
            const option = document.createElement('option');
            option.value = endereco;
            datalists.enderecos.appendChild(option);
        });
    }

    if (datalists.elevadores) {
        datalists.elevadores.innerHTML = '';
        allElevators.forEach(elev => {
            const option = document.createElement('option');
            option.value = `${elev.descricao} (ID: ${elev.id})`;
            datalists.elevadores.appendChild(option);
        });
    }
}

function updateDatalistsAndCheckAutofill() {
    // CORRIGIDO: Verificar se os elementos existem antes de acessá-los
    const formCidade = document.getElementById('form-cidade');
    const formUnidade = document.getElementById('form-unidade');
    const formEndereco = document.getElementById('form-endereco');
    
    if (!formCidade || !formUnidade || !formEndereco) {
        console.error('ERRO: Elementos do formulário não encontrados em updateDatalistsAndCheckAutofill');
        return;
    }

    const cidade = formCidade.value.trim();
    const unidade = formUnidade.value.trim();
    const endereco = formEndereco.value.trim();

    // Atualizar datalists dinamicamente baseado na seleção atual
    const unidadesListDatalist = document.getElementById('unidades-list');
    const enderecosListDatalist = document.getElementById('enderecos-list');
    const elevadoresListDatalist = document.getElementById('elevadores-list');

    // Filtrar unidades por cidade
    if (cidade && unidadesListDatalist) {
        const unidadesFiltradas = [...new Set(
            allElevators
                .filter(e => e.cidade.toLowerCase().includes(cidade.toLowerCase()))
                .map(e => e.unidade)
        )];
        
        unidadesListDatalist.innerHTML = '';
        unidadesFiltradas.forEach(u => {
            const option = document.createElement('option');
            option.value = u;
            unidadesListDatalist.appendChild(option);
        });
    }

    // Filtrar endereços por cidade e unidade
    if (cidade && unidade && enderecosListDatalist) {
        const enderecosFiltrados = [...new Set(
            allElevators
                .filter(e => e.cidade.toLowerCase().includes(cidade.toLowerCase()) && 
                            e.unidade.toLowerCase().includes(unidade.toLowerCase()))
                .map(e => e.endereco)
        )];
        
        enderecosListDatalist.innerHTML = '';
        enderecosFiltrados.forEach(end => {
            const option = document.createElement('option');
            option.value = end;
            enderecosListDatalist.appendChild(option);
        });
    }

    // Filtrar elevadores por localização completa
    if (cidade && unidade && endereco && elevadoresListDatalist) {
        const elevadoresFiltrados = allElevators.filter(e => 
            e.cidade.toLowerCase().includes(cidade.toLowerCase()) && 
            e.unidade.toLowerCase().includes(unidade.toLowerCase()) && 
            e.endereco.toLowerCase().includes(endereco.toLowerCase())
        );
        
        elevadoresListDatalist.innerHTML = '';
        elevadoresFiltrados.forEach(elev => {
            const option = document.createElement('option');
            option.value = `${elev.descricao} (ID: ${elev.id})`;
            elevadoresListDatalist.appendChild(option);
        });
    }
}   

function populateElevadoresDatalistForBuilding(buildingId) {
    const elevadoresList = document.getElementById('elevadores-list');
    const elevadoresDoPredio = allElevators.filter(e => e.id_predio === buildingId);
    
    if (elevadoresDoPredio.length === 1) {
        // Auto-preenche se só houver 1 elevador no prédio
        const elev = elevadoresDoPredio[0];
        document.getElementById('form-elevador-descricao').value = `${elev.descricao} (ID: ${elev.id})`;
        document.getElementById('form-id-elevador-unico').value = elev.id;
    }

    elevadoresList.innerHTML = elevadoresDoPredio
        .map(elev => `<option value="${elev.descricao} (ID: ${elev.id})">`)
        .join('');
}

function autoPreencherElevadorInfo() {
    const formIdElevador = document.getElementById('form-id-elevador');
    if (!formIdElevador) {
        console.error('ERRO: Campo #form-id-elevador não encontrado em autoPreencherElevadorInfo');
        return;
    }

    const elevadorValue = formIdElevador.value;
    const idMatch = elevadorValue.match(/\(ID: (\d+)\)/);

    // CORRIGIDO: Verificar todos os elementos antes de acessá-los
    const formElements = {
        cidade: document.getElementById('form-cidade'),
        unidade: document.getElementById('form-unidade'),
        endereco: document.getElementById('form-endereco'),
        idElevadorUnico: document.getElementById('form-id-elevador-unico')
    };

    if (idMatch) {
        const idElevador = parseInt(idMatch[1]);
        const elevador = allElevators.find(e => e.id === idElevador);
        
        if (elevador) {
            if (formElements.cidade) formElements.cidade.value = elevador.cidade;
            if (formElements.unidade) formElements.unidade.value = elevador.unidade;
            if (formElements.endereco) formElements.endereco.value = elevador.endereco;
            if (formElements.idElevadorUnico) formElements.idElevadorUnico.value = elevador.id;
            
            // Desabilitar campos preenchidos automaticamente
            if (formElements.cidade) formElements.cidade.disabled = true;
            if (formElements.unidade) formElements.unidade.disabled = true;
            if (formElements.endereco) formElements.endereco.disabled = true;
            formIdElevador.disabled = true;
        }
    } else {
        // Limpar e reabilitar campos
        if (formElements.idElevadorUnico) formElements.idElevadorUnico.value = '';
        if (formElements.cidade) formElements.cidade.disabled = false;
        if (formElements.unidade) formElements.unidade.disabled = false;
        if (formElements.endereco) formElements.endereco.disabled = false;
        formIdElevador.disabled = false;
    }
}

function abrirModalGerenciarElevador(modo, idElevador = null) {
    const modalElement = document.getElementById('modalGerenciarElevador');
    const modal = new bootstrap.Modal(modalElement);
    const form = document.getElementById('formGerenciarElevador');
    form.reset(); // Limpa o formulário

    const modalTitle = document.getElementById('modalGerenciarElevadorLabel');
    const btnSalvar = document.getElementById('btnSalvarElevador');
    
    // Verificar se os elementos existem
    const formElements = {
        cidade: document.getElementById('form-cidade'),
        unidade: document.getElementById('form-unidade'),
        endereco: document.getElementById('form-endereco'),
        idElevador: document.getElementById('form-id-elevador'),
        idElevadorUnico: document.getElementById('form-id-elevador-unico'),
        dataParada: document.getElementById('form-data-parada'),
        previsaoRetorno: document.getElementById('form-previsao-retorno'),
        status: document.getElementById('form-status')
    };

    // Reabilita todos os campos por padrão para o modo 'adicionar'
    Object.values(formElements).forEach(element => {
        if (element) element.disabled = false;
    });
    
    if (modo === 'adicionar') {
        if (modalTitle) modalTitle.textContent = 'Inserir Elevador Parado';
        if (btnSalvar) {
            btnSalvar.textContent = 'Inserir';
            btnSalvar.dataset.acao = 'adicionar';
        }
        if (formElements.status) formElements.status.value = 'Parado'; 
        if (formElements.idElevadorUnico) formElements.idElevadorUnico.value = ''; 
        
        const elevadoresListDatalist = document.getElementById('elevadores-list');
        if (elevadoresListDatalist) elevadoresListDatalist.innerHTML = ''; 
        
        preencherDatalistsLocais();
        
    } else if (modo === 'editar') {
        if (modalTitle) modalTitle.textContent = 'Editar Elevador';
        if (btnSalvar) {
            btnSalvar.textContent = 'Salvar Edição';
            btnSalvar.dataset.acao = 'editar';
        }
        
        const elevador = allElevators.find(e => e.id === idElevador);
        if (elevador) {
            if (formElements.idElevadorUnico) formElements.idElevadorUnico.value = elevador.id;
            if (formElements.cidade) formElements.cidade.value = elevador.cidade;
            if (formElements.unidade) formElements.unidade.value = elevador.unidade;
            if (formElements.endereco) formElements.endereco.value = elevador.endereco;
            if (formElements.idElevador) formElements.idElevador.value = `${elevador.descricao} (ID: ${elevador.id})`;
            if (formElements.dataParada) formElements.dataParada.value = elevador.DataDeParada || '';
            if (formElements.previsaoRetorno) formElements.previsaoRetorno.value = elevador.PrevisaoDeRetorno || '';
            if (formElements.status) formElements.status.value = elevador.status;

            // Desabilitar campos de localização/elevador para edição de um existente
            if (formElements.cidade) formElements.cidade.disabled = true;
            if (formElements.unidade) formElements.unidade.disabled = true;
            if (formElements.endereco) formElements.endereco.disabled = true;
            if (formElements.idElevador) formElements.idElevador.disabled = true;
        } else {
            alert('Elevador não encontrado para edição.');
            return;
        }
    }
    modal.show();
}

function salvarGerenciamentoElevador() {
    console.log('DEBUG: salvarGerenciamentoElevador chamado');
    
    const btnSalvar = document.getElementById('btnSalvarElevador');
    if (!btnSalvar) {
        console.error('ERRO: Botão salvar não encontrado');
        return;
    }

    const acao = btnSalvar.dataset.acao || 'adicionar';
    console.log(`DEBUG: Ação detectada: ${acao}`);

    // Verificar todos os elementos do formulário antes de acessá-los
    const formElements = {
        cidade: document.getElementById('form-cidade'),
        unidade: document.getElementById('form-unidade'),
        endereco: document.getElementById('form-endereco'),
        idElevador: document.getElementById('form-id-elevador'),
        idElevadorUnico: document.getElementById('form-id-elevador-unico'),
        dataParada: document.getElementById('form-data-parada'),
        previsaoRetorno: document.getElementById('form-previsao-retorno'),
        status: document.getElementById('form-status')
    };

    // Verificar se todos os elementos necessários existem
    const missingElements = Object.entries(formElements).filter(([key, element]) => !element);
    if (missingElements.length > 0) {
        console.error('ERRO: Elementos do formulário não encontrados:', missingElements.map(([key]) => key));
        alert('Erro: Alguns campos do formulário não foram encontrados. Verifique o console para detalhes.');
        return;
    }

    // Validação básica
    if (!formElements.cidade.value.trim() || !formElements.unidade.value.trim() || 
        !formElements.endereco.value.trim() || !formElements.status.value) {
        alert('Por favor, preencha todos os campos obrigatórios: Cidade, Unidade, Endereço e Status.');
        return;
    }

    // CORRIGIDO: Preparar payload para corresponder à rota existente
    let elevadorId = null;
    
    // Se há um ID no campo oculto, usar esse (para elevadores existentes)
    if (formElements.idElevadorUnico.value.trim()) {
        elevadorId = parseInt(formElements.idElevadorUnico.value.trim());
    } else {
        // Se não há ID no campo oculto, tentar extrair do campo de descrição
        const elevadorValue = formElements.idElevador.value.trim();
        const idMatch = elevadorValue.match(/\(ID: (\d+)\)/);
        if (idMatch) {
            elevadorId = parseInt(idMatch[1]);
        }
    }

    // Verificar se conseguimos obter um ID válido para ações que requerem ID
    if ((acao === 'adicionar' || acao === 'editar') && !elevadorId) {
        alert('Erro: Não foi possível identificar o ID do elevador. Certifique-se de selecionar um elevador válido da lista.');
        return;
    }

    const payload = {
        acao: acao,
        id: elevadorId, // CORRIGIDO: Usar 'id' em vez de 'elevador.id_elevador_unico'
        status: formElements.status.value,
        data_de_parada: formElements.dataParada.value || null,
        previsao_de_retorno: formElements.previsaoRetorno.value || null
    };

    console.log('DEBUG: Payload para envio:', payload);

    // Desabilitar botão para evitar múltiplos cliques
    btnSalvar.disabled = true;
    btnSalvar.textContent = 'Salvando...';

    // CORRIGIDO: URL da rota
    fetch('/v2/api/elevadores/gerenciar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        console.log('DEBUG: Resposta do servidor:', data);
        
        // CORRIGIDO: Usar 'success' e 'message' conforme a rota existente
        if (data.success) {
            alert(data.message || 'Operação realizada com sucesso!');
            
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalGerenciarElevador'));
            if (modal) {
                modal.hide();
            }
            
            // Recarregar dados do dashboard
            setTimeout(() => {
                location.reload(); // Recarrega a página para atualizar os dados
            }, 1000);
            
        } else {
            alert('Erro: ' + (data.message || 'Erro desconhecido ao salvar.'));
        }
    })
    .catch(error => {
        console.error('ERRO na requisição:', error);
        alert('Erro de conexão: ' + error.message);
    })
    .finally(() => {
        // Reabilitar botão
        btnSalvar.disabled = false;
        btnSalvar.textContent = acao === 'adicionar' ? 'Inserir' : 'Salvar Edição';
    });
}

function confirmarRemocaoElevador(idElevador) {
    if (!confirm('Tem certeza de que deseja marcar este elevador como "Em atividade"?')) {
        return;
    }

    console.log(`DEBUG: Removendo elevador ID ${idElevador} do status parado`);

    const payload = {
        acao: 'remover',
        id: idElevador
    };

    fetch('/v2/api/elevadores/gerenciar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        console.log('DEBUG: Resposta do servidor:', data);
        
        if (data.success) {
            alert(data.message || 'Elevador marcado como ativo com sucesso!');
            
            // Recarregar dados do dashboard
            setTimeout(() => {
                location.reload();
            }, 1000);
            
        } else {
            alert('Erro: ' + (data.message || 'Erro desconhecido ao remover.'));
        }
    })
    .catch(error => {
        console.error('ERRO na requisição:', error);
        alert('Erro de conexão: ' + error.message);
    });
}