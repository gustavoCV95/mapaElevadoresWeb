// static/js/kpis_script.js

// Acessa as variáveis globais definidas no HTML
// const dadosKPIsOriginais; // Já definida no HTML
// let dadosKPIsFiltrados; // Já definida no HTML
// ... e assim por diante


console.log('Script de KPIs externo carregado.');


// Inicializa gráficos quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, criando gráficos de KPIs...');
    preencherFiltros();
    criarGraficos();
});

function preencherFiltros() {
    // Preenche filtro de categorias
    const selectCategoria = document.getElementById('filtro-categoria');
    categoriasUnicas.forEach(categoria => {
        const option = document.createElement('option');
        option.value = categoria;
        option.textContent = categoria;
        selectCategoria.appendChild(option);
    });
    
    // Preenche filtro de edifÃ­cios
    const selectEdificio = document.getElementById('filtro-edificio');
    edificiosUnicos.forEach(edificio => {
        const option = document.createElement('option');
        option.value = edificio;
        option.textContent = edificio.length > 50 ? edificio.substring(0, 50) + '...' : edificio;
        selectEdificio.appendChild(option);
    });

    // NOVO: Preenche filtro de equipamentos (Elevadores)
    const selectEquipamento = document.getElementById('filtro-equipamento');
    equipamentosUnicos.forEach(equipamento => {
        const option = document.createElement('option');
        option.value = equipamento;
        option.textContent = equipamento;
        selectEquipamento.appendChild(option);
    });
}

// NOVA FUNÇÃO: Selecionar período predefinido
function selecionarPeriodoPredefinido() {
    const periodo = document.getElementById('filtro-periodo').value;
    
    if (periodo && periodo !== 'todo-periodo') {
        // Limpa datas personalizadas quando seleciona perí­odo predefinido
        document.getElementById('data-inicio').value = '';
        document.getElementById('data-fim').value = '';
    }
    
    console.log('Período predefinido selecionado:', periodo);
}

function criarGraficos() {
    // Destroi grÃ¡ficos existentes
    Object.values(graficos).forEach(grafico => {
        if (grafico) grafico.destroy();
    });
    
    // Cria novos grÃ¡ficos
    criarGraficoChamadosPorMes();
    criarGraficoCategorias();
    criarGraficoEdificios();
    criarGraficoTempoPorCategoria();
    
    // NOVOS GRÃFICOS DE ELEVADORES
    criarGraficoChamadosPorElevador();
    criarGraficoTempoMedianoPorElevador();
}

function criarGraficoChamadosPorMes() {
    const ctx = document.getElementById('grafico-chamados-mes');
    if (!ctx) return;
    
    const dados = dadosKPIsFiltrados.chamados_por_mes || {};
    const labels = Object.keys(dados).sort();
    const values = labels.map(label => dados[label]);
    
    graficos.chamadosMes = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Chamados',
                data: values,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#007bff',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        tooltipFormat: 'MMM yyyy'
                    },
                    adapters: {
                        date: {
                            // Certifique-se de que o locale 'pt-BR' estÃ¡ disponÃ­vel para date-fns
                            // Se não estiver funcionando, pode ser necessÃ¡rio importar explicitamente o locale do date-fns
                            // No entanto, Chart.js adapta globalmente, então deve funcionar.
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const mesAno = labels[index];
                    filtrarPorMes(mesAno);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

function criarGraficoCategorias() {
    const ctx = document.getElementById('grafico-categorias');
    if (!ctx) return;
    
    const dados = dadosKPIsFiltrados.categorias_problema || {};
    
    // ORDENAÇÃO DECRESCENTE
    const entries = Object.entries(dados).sort((a, b) => b[1] - a[1]);
    const labels = entries.map(entry => entry[0]);
    const values = entries.map(entry => entry[1]);
    
    const cores = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
        '#E0BBE4', '#957DAD', '#D291BC', '#FFC72C'
    ];
    
    graficos.categorias = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: cores.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff',
                hoverBorderWidth: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const categoria = labels[index];
                    filtrarPorCategoria(categoria);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

// MODIFICADO: Gráfico de Edifí­cios com ordenação decrescente garantida
function criarGraficoEdificios() {
    const ctx = document.getElementById('grafico-edificios');
    if (!ctx) return;
    
    const dados = dadosKPIsFiltrados.chamados_por_edificio || {};
    
    // ORDENAÇÃO DECRESCENTE EXPLÍCITA (garantindo que funcione mesmo se backend não ordenar)
    const entries = Object.entries(dados)
        .sort((a, b) => b[1] - a[1])  // Ordena por valor decrescente
        .slice(0, 10); // Top 10
    
    const labels = entries.map(entry => entry[0]);
    const values = entries.map(entry => entry[1]);
    
    console.log('Dados de edifícios ordenados:', entries);
    
    graficos.edificios = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(label => label.length > 20 ? label.substring(0, 20) + '...' : label),
            datasets: [{
                label: 'Chamados',
                data: values,
                backgroundColor: '#28a745',
                borderColor: '#1e7e34',
                borderWidth: 1,
                hoverBackgroundColor: '#34ce57'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const edificio = labels[index];
                    filtrarPorEdificio(edificio);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

// MODIFICADO: Gráfico de Tempo por Categoria com ordenação decrescente garantida
function criarGraficoTempoPorCategoria() {
    const ctx = document.getElementById('grafico-tempo-categoria');
    if (!ctx) return;
    
    const dados = dadosKPIsFiltrados.tempo_por_categoria || {};
    
    // ðŸ”„ ORDENAÃ‡ÃƒO DECRESCENTE EXPLÃCITA (garantindo que funcione mesmo se backend não ordenar)
    const entries = Object.entries(dados)
        .sort((a, b) => b[1] - a[1]); // Ordena por valor decrescente
    
    const labels = entries.map(entry => entry[0]);
    const values = entries.map(entry => Math.round(entry[1] * 10) / 10);
    
    console.log('Dados de tempo por categoria ordenados:', entries);
    
    graficos.tempoCategoria = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tempo Mediano (horas)',
                data: values,
                backgroundColor: '#ffc107',
                borderColor: '#e0a800',
                borderWidth: 1,
                hoverBackgroundColor: '#ffcd39'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + 'h';
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const categoria = labels[index];
                    filtrarPorCategoria(categoria);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

// NOVO: GrÃ¡fico de Chamados por Elevador
function criarGraficoChamadosPorElevador() {
    const ctx = document.getElementById('grafico-chamados-elevador');
    if (!ctx) return;
    
    const dados = dadosKPIsFiltrados.chamados_por_equipamento || {};
    
    // Ordenação decrescente e limitação aos top 15 elevadores
    const entries = Object.entries(dados)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15); // Top 15 elevadores
    
    const labels = entries.map(entry => String(entry[0]));
    const values = entries.map(entry => entry[1]);
    
    console.log('Dados de chamados por elevador ordenados:', entries);
    
    graficos.chamadosElevador = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Chamados',
                data: values,
                backgroundColor: '#007bff',
                borderColor: '#0056b3',
                borderWidth: 1,
                hoverBackgroundColor: '#0056b3'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Elevador: ' + context[0].label;
                        },
                        label: function(context) {
                            return 'Chamados: ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        font: {
                            size: 10
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const elevador = String(labels[index]);
                    filtrarPorEquipamento(elevador);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

// NOVO: GrÃ¡fico de Tempo Mediano por Elevador
function criarGraficoTempoMedianoPorElevador() {
    const ctx = document.getElementById('grafico-tempo-elevador');
    if (!ctx) return;
    
    const dados = dadosKPIsFiltrados.tempo_por_equipamento || {};
    
    // Ordenação decrescente e limitação aos top 15 elevadores
    const entries = Object.entries(dados)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15); // Top 15 elevadores
    
    const labels = entries.map(entry => String(entry[0]));
    const values = entries.map(entry => Math.round(entry[1] * 10) / 10);
    
    console.log('Dados de tempo por elevador ordenados:', entries);
    
    graficos.tempoElevador = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tempo Mediano (horas)',
                data: values,
                backgroundColor: '#17a2b8',
                borderColor: '#138496',
                borderWidth: 1,
                hoverBackgroundColor: '#138496'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Elevador: ' + context[0].label;
                        },
                        label: function(context) {
                            return 'Tempo Mediano: ' + context.parsed.y + 'h';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + 'h';
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        font: {
                            size: 10
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const elevador = String(labels[index]);
                    filtrarPorEquipamento(elevador);
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

// FunçÃµes de filtro por clique nos grÃ¡ficos
function filtrarPorMes(mesAno) {
    console.log('ðŸ“… Filtrando por mÃªs:', mesAno);
    // Para filtro por mÃªs, precisamos ajustar data_inicio e data_fim
    const [ano, mes] = mesAno.split('-');
    const dataInicioMes = `${ano}-${mes}-01`;
    const ultimoDiaMes = new Date(ano, parseInt(mes), 0).getDate();
    const dataFimMes = `${ano}-${mes}-${ultimoDiaMes}`;

    document.getElementById('data-inicio').value = dataInicioMes;
    document.getElementById('data-fim').value = dataFimMes;
    document.getElementById('filtro-periodo').value = ''; // Limpa período predefinido

    filtrosAtivos.data_inicio = dataInicioMes;
    filtrosAtivos.data_fim = dataFimMes;
    delete filtrosAtivos.periodo_predefinido;
    delete filtrosAtivos.mes; // Remove filtro de mÃªs para evitar conflito

    aplicarFiltrosInterativos();
}

function filtrarPorCategoria(categoria) {
    console.log('ðŸ·ï¸ Filtrando por categoria:', categoria);
    document.getElementById('filtro-categoria').value = categoria;
    filtrosAtivos.categoria = categoria;
    aplicarFiltrosInterativos();
}

function filtrarPorEdificio(edificio) {
    console.log('ðŸ¢ Filtrando por edifÃ­cio:', edificio);
    document.getElementById('filtro-edificio').value = edificio;
    filtrosAtivos.edificio = edificio;
    aplicarFiltrosInterativos();
}

// NOVO: Filtrar por elevador especÃ­fico (equipamento)
function filtrarPorEquipamento(equipamento) {
    console.log('ðŸ—ï¸ Filtrando por equipamento:', equipamento);
    document.getElementById('filtro-equipamento').value = equipamento;
    filtrosAtivos.equipamento = equipamento;
    aplicarFiltrosInterativos();
}

function aplicarFiltros() {
    const dataInicio = document.getElementById('data-inicio').value;
    const dataFim = document.getElementById('data-fim').value;
    const periodo = document.getElementById('filtro-periodo').value;
    const status = document.getElementById('filtro-status').value;
    const categoria = document.getElementById('filtro-categoria').value;
    const edificio = document.getElementById('filtro-edificio').value;
    const equipamento = document.getElementById('filtro-equipamento').value;
    
    console.log('ðŸ” Aplicando filtros:', {
        dataInicio, dataFim, periodo, status, categoria, edificio, equipamento
    });
    
    // ðŸ“… VALIDAÃ‡ÃƒO DE DATAS
    if (dataInicio && dataFim && new Date(dataInicio) > new Date(dataFim)) {
        alert('A data de início não pode ser posterior a data de fim.');
        return;
    }
    
    // MAPEAMENTO CORRETO DOS PARÃ‚METROS
    filtrosAtivos = {
        data_inicio: dataInicio,
        data_fim: dataFim,
        periodo_predefinido: periodo,
        status: status,
        categoria: categoria,
        edificio: edificio,
        equipamento: equipamento
    };
    
    // Remove filtros vazios
    Object.keys(filtrosAtivos).forEach(key => {
        if (!filtrosAtivos[key]) {
            delete filtrosAtivos[key];
        }
    });
    
    console.log('Filtros ativos após limpeza:', filtrosAtivos);
    
    aplicarFiltrosInterativos();
}

function aplicarFiltrosInterativos() {
    console.log('Aplicando filtros interativos:', filtrosAtivos);
    
    // Monta parâmetros para API
    const params = new URLSearchParams();
    Object.keys(filtrosAtivos).forEach(key => {
        if (filtrosAtivos[key]) {
            params.append(key, filtrosAtivos[key]);
        }
    });
    
    // Mostra loading
    const loadingElement = document.getElementById('loading-resumo');
    if (loadingElement) loadingElement.style.display = 'block';
    
    // Faz requisição para API
    fetch('/api/kpis-filtrados?' + params.toString())
        .then(response => {
            if (!response.ok) {
                // Se a resposta não for 2xx, tenta ler como JSON de erro
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'Erro na API');
                });
            }
            return response.json();
        })
        .then(data => {
            if (loadingElement) loadingElement.style.display = 'none';
            
            if (data.success) {
                // Atualiza dados filtrados
                dadosKPIsFiltrados = data.metricas;
                
                // Atualiza cards
                atualizarCards(data.metricas);
                
                // Recria grÃ¡ficos
                criarGraficos();
                
                // Mostra indicador de filtros ativos
                mostrarFiltrosAtivos();
                
                // Atualiza tabela de resumo
                atualizarTabelaResumo(data.resumo);
            } else {
                alert('Erro ao aplicar filtros: ' + (data.message || 'Erro desconhecido.'));
                console.error('API Error:', data);
            }
        })
        .catch(error => {
            if (loadingElement) loadingElement.style.display = 'none';
            console.error('âŒ Erro ao aplicar filtros:', error);
            alert('Erro na requisição de filtros: ' + error.message + '. Verifique o console para mais detalhes.');
        });
}

function atualizarCards(metricas) {
    document.getElementById('total-chamados').textContent = metricas.total_chamados || 0;
    document.getElementById('chamados-concluidos').textContent = metricas.chamados_concluidos || 0;
    document.getElementById('tempo-mediano').textContent = (metricas.tempo_mediano_reparo || 0).toFixed(1) + 'h';
    document.getElementById('disponibilidade').textContent = (metricas.disponibilidade || 0).toFixed(1) + '%';
}

function mostrarFiltrosAtivos() {
    const filtrosAtivosDiv = document.getElementById('filtros-ativos');
    const descricaoFiltros = document.getElementById('descricao-filtros');
    
    const filtrosTexto = [];
    
    // MELHORIA: Descrição mais clara dos filtros
    const dataInicio = document.getElementById('data-inicio').value;
    const dataFim = document.getElementById('data-fim').value;
    const periodo = document.getElementById('filtro-periodo').value;
    
    if (dataInicio || dataFim) {
        let textoData = 'Período: ';
        if (dataInicio && dataFim) {
            textoData += `${dataInicio} a ${dataFim}`;
        } else if (dataInicio) {
            textoData += `a partir de ${dataInicio}`;
        } else {
            textoData += `até ${dataFim}`;
        }
        filtrosTexto.push(textoData);
    } else if (periodo) {
        const periodos = {
            'ultima-semana': 'Última Semana',
            'ultimo-mes': 'Último Mês',
            'ultimos-3-meses': 'Últimos 3 Meses',
            'ultimos-6-meses': 'Últimos 6 Meses',
            'ultimo-ano': 'Último Ano',
            'ultimos-2-anos': 'Últimos 2 Anos',
            'ultimos-5-anos': 'Últimos 5 Anos',
            'todo-periodo': 'Todo o Período'
        };
        filtrosTexto.push(`Período: ${periodos[periodo]}`);
    }
    
    Object.keys(filtrosAtivos).forEach(key => {
        if (filtrosAtivos[key] && !['data_inicio', 'data_fim', 'periodo_predefinido'].includes(key)) {
             const nomesFiltros = {
                'equipamento': 'Elevador', // NOVO
                'categoria': 'Categoria',
                'edificio': 'EdifÃ­cio',
                'status': 'Status'
            };
            const nomeAmigavel = nomesFiltros[key] || key;
            filtrosTexto.push(`${nomeAmigavel}: ${filtrosAtivos[key]}`);
        }
    });
    
    if (filtrosTexto.length > 0) {
        descricaoFiltros.textContent = filtrosTexto.join(' | ');
        filtrosAtivosDiv.style.display = 'block';
    } else {
        filtrosAtivosDiv.style.display = 'none';
    }
}

function atualizarTabelaResumo(resumo) {
    const container = document.getElementById('tabela-resumo');
    if (!resumo || resumo.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Nenhum dado encontrado com os filtros aplicados.</p>';
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Categoria</th>
                        <th>EdifÃ­cio</th>
                        <th>Equipamento</th> {# NOVO: Coluna adicionada #}
                        <th>Status</th>
                        <th>Data Solicitação</th>
                        <th>Tempo Reparo (h)</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    resumo.slice(0, 20).forEach(item => { // Mostra apenas os primeiros 20
        html += `
            <tr>
                <td><span class="badge bg-secondary">${item.categoria_problema}</span></td>
                <td>${item.edificio}</td>
                <td>${item.equipamento || '-'}</td> {# NOVO: Dados do equipamento #}
                <td><span class="badge ${item.status === 'ConcluÃ­da' ? 'bg-success' : 'bg-warning'}">${item.status}</span></td>
                <td>${item.data_solicitacao}</td>
                <td>${item.tempo_reparo_horas ? item.tempo_reparo_horas.toFixed(1) : '-'}</td> {# CORRIGIDO: Usar tempo_reparo_horas #}
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        ${resumo.length > 20 ? `<p class="text-muted text-center">Mostrando 20 de ${resumo.length} registros</p>` : ''}
    `;
    
    container.innerHTML = html;
}

function limparFiltrosKPIs() {
    // ðŸ“… LIMPA TODOS OS FILTROS (incluindo datas)
    document.getElementById('data-inicio').value = '';
    document.getElementById('data-fim').value = '';
    document.getElementById('filtro-periodo').value = '';
    document.getElementById('filtro-status').value = '';
    document.getElementById('filtro-categoria').value = '';
    document.getElementById('filtro-edificio').value = '';
    document.getElementById('filtro-equipamento').value = '';
    
    // Limpa filtros ativos
    filtrosAtivos = {};
    
    // Restaura dados originais
    dadosKPIsFiltrados = dadosKPIsOriginais;
    
    // Atualiza cards
    atualizarCards(dadosKPIsOriginais);
    
    // Recria grÃ¡ficos
    criarGraficos();
    
    // Esconde indicador de filtros
    document.getElementById('filtros-ativos').style.display = 'none';
    
    // Limpa tabela de resumo
    document.getElementById('tabela-resumo').innerHTML = '<p class="text-muted text-center">Use os filtros acima ou clique nos grÃ¡ficos para ver dados especÃ­ficos.</p>';
    
    console.log('ðŸ§¹ Filtros de KPIs limpos');
}

function atualizarDados() {
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
    btn.disabled = true;
    
    // Chamada para a API do Blueprint de KPIs para atualizar o cache
    fetch('/v2/kpis/atualizar-kpis', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'Erro na API');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Dados de KPIs atualizados!\n' + data.message);
                // ApÃ³s atualizar o cache, recarregar a pÃ¡gina para buscar os novos dados
                location.reload(); 
            } else {
                alert('Erro ao atualizar KPIs: ' + data.message);
            }
        })
        .catch(error => alert('Erro na requisição de atualização de KPIs: ' + error.message))
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function debugFiltros() {
    console.log('ðŸ” DEBUG - Estado atual dos filtros:');
    console.log('   Data inÃ­cio:', document.getElementById('data-inicio').value);
    console.log('   Data fim:', document.getElementById('data-fim').value);
    console.log('   PerÃ­odo:', document.getElementById('filtro-periodo').value);
    console.log('   Status:', document.getElementById('filtro-status').value);
    console.log('   Categoria:', document.getElementById('filtro-categoria').value);
    console.log('   EdifÃ­cio:', document.getElementById('filtro-edificio').value);
    console.log('   Equipamento:', document.getElementById('filtro-equipamento').value);
    console.log('   Filtros ativos:', filtrosAtivos);
    console.log('   Dados originais:', dadosKPIsOriginais);
    console.log('   Dados filtrados:', dadosKPIsFiltrados);
}
