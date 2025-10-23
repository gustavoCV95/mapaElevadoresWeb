# 🏢 Sistema de Mapeamento de Elevadores - TJ/MG

Sistema web interativo para visualização e análise dos elevadores do Tribunal de Justiça de Minas Gerais, com mapa dinâmico e filtros avançados.
 
 <br><br><br>
📋 Índice
1. Visão Geral
2. Funcionalidades
3. Tecnologias
4. Instalação
5. Configuração
6. Uso
7. Estrutura do Projeto
8. API
<br><br><br>

1.🎯 **Visão Geral**<br>
O Sistema de Mapeamento de Elevadores TJ/MG é uma aplicação web desenvolvida para centralizar e visualizar informações sobre todos os elevadores instalados nas unidades do Tribunal de Justiça de Minas Gerais.O sistema oferece uma interface intuitiva com mapa interativo e sistema de filtros avançados para análise dos dados.

🎥 Demonstração<br>
- Mapa Interativo: Visualização geográfica de todos os elevadores<br>
- Filtros Dinâmicos: Filtragem por tipo, região, marca e empresa<br>
- Dashboard Responsivo: Estatísticas em tempo real<br>
- Integração com Google Sheets: Dados sempre atualizados<br><br><br>


2.✨ **Funcionalidades**<br><br>
🗺️ **Mapa Interativo**<br>
- Visualização Geográfica: Todos os elevadores plotados no mapa de Minas Gerais<br>
- Marcadores Dinâmicos: Cores e tamanhos baseados no status e quantidade<br>
- Tooltips Informativos: Informações rápidas ao passar o mouse<br>
- Popups Detalhados: Dados completos ao clicar nos marcadores<br>

📣 **Sistema de Filtros**<br>
- Filtro por Tipo: Montacarga, Passageiro, Plataforma<br>
- Filtro por Região: 11 regiões administrativas de MG<br>
- Filtro por Marca: Atlas Schindler, Otis, Thyssenkrupp, etc.<br>
- Filtro por Empresa: Empresas responsáveis pela manutenção<br>
- Filtros Combinados: Múltiplos filtros simultâneos<br>
- Contador Dinâmico: Resultados atualizados em tempo real<br>

📊 **Dashboard Analítico**<br>
- Cards Estatísticos: Visão geral dos números principais<br>
- Estatísticas Detalhadas: Distribuição por categorias<br>
- Atualização Automática: Dados sincronizados com os filtros<br>
- Interface Responsiva: Adaptável a diferentes dispositivos<br>

🔄 **Integração de Dados**<br>
- Google Sheets API: Conexão direta com planilha de dados<br>
- Cache Inteligente: Otimização de performance<br>
- Atualização Manual: Botão para forçar atualização dos dados<br>
- Validação de Dados: Verificação de coordenadas e consistência<br><br><br>


3.🛠️ **Tecnologias**<br>

**Backend**<br>
- Python 3.8+: Linguagem principal<br>
- Flask 2.0+: Framework web<br>
- Pandas: Manipulação de dados<br>
- Google Sheets API: Integração com planilhas<br>
- JSON: Formato de dados<br>

**Frontend**<br>
- HTML5/CSS3: Estrutura e estilização<br>
- JavaScript ES6+: Interatividade<br>
- Bootstrap 5: Framework CSS responsivo<br>
- Leaflet.js: Biblioteca de mapas interativos<br>
- Font Awesome: Ícones<br>

**Infraestrutura**<br>
- Google Cloud Platform: Autenticação e APIs<br>
- CartoDB: Tiles do mapa base<br>
- Git: Controle de versão<br><br><br>


4.💻**Instalação**<br>

**Pré-requisitos**<br>
- Python 3.8 ou superior<br>
- pip (gerenciador de pacotes Python)<br>
- Conta Google Cloud Platform<br>
- Git<br>
1. **Clone o Repositório**<br>
```
git clone https://github.com/seu-usuario/mapa-elevadores-tjmg.git
cd mapa-elevadores-tjmg
```

 2. **Crie um Ambiente Virtual**<br>
   ```
   python -m venv .venv`<br>

   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate
   ```

  3. **Instale as Dependências**<br>
   ```
   pip install -r requirements.txt
   ```

  5. **Configure as Credenciais**<br>
   ```
   #Crie o arquivo de configuração
   cp config.py.example config.py
   
   #Adicione suas credenciais do Google Cloud
   #Veja a seção de Configuração abaixo
   ```
<br>

5. ⚙️ **Configuração**<br><br>
   1.**Google Cloud Platform**
      - **Criar Projeto e Habilitar APIs**
        1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
        2. Crie um novo projeto ou selecione um existente
        3. Habilite a Google Sheets API
        4. Habilite a Google Drive API

      - **Criar Conta de Serviço**
        1. Vá para IAM & Admin > Service Accounts
        2. Clique em **Create Service Account**
        3. Preencha os dados da conta
        4. Baixe o arquivo JSON de credenciais
        5. Renomeie para `credentials.json` e coloque na pasta raiz<br><br>

   2.**Configurar Permissões**<br>
        1. Abra sua planilha no Google Sheets<br>
        2. Clique em **Compartilhar**<br>
        3. Adicione o email da conta de serviço com permissão de **Visualizador**<br><br>
  
     3.**Arquivo de Configuração**<br><br>
          Edite o arquivo config.py:
   ```
          import os
          
          class Config:
              # URL da planilha do Google Sheets
              PLANILHA_URL = 'https://docs.google.com/spreadsheets/d/SEU_ID_DA_PLANILHA/edit'
              
              # Configurações de cache (em segundos)
              CACHE_TIMEOUT = 300  # 5 minutos
              
              # Configurações do Flask
              SECRET_KEY = 'sua-chave-secreta-aqui'
              DEBUG = True
   ```
<br><br>
   4.**Estrutura da Planilha**<br><br>
Sua planilha deve conter as seguintes colunas:<br><br>

| cidade | unidade | endereco | enderecoCompleto | tipo | quantidade | marca | paradas | regiao | status | latitude | longitude | empresa |
| ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| Nome da cidade | Nome da unidade | Endereço | Endereço + cidade | Tipo do elevador | Número de elevadores | Marca do elevador | Numero de paradas | Região administrativa | Status atual | Coordenada latitude | Coordenada longitude | Empresa responsável |


<br><br><br>6.🎮 **Uso**<br><br>
**Executar a Aplicação**<br><br>
`python app.py`<br>

A aplicação estará disponível em: http://localhost:5000<br><br>

**Funcionalidades Principais**<br>
🗺️ Navegação no Mapa
- Zoom: Use a roda do mouse ou botões +/-
- Pan: Clique e arraste para mover o mapa
- Marcadores: Clique para ver detalhes completos
- Tooltip: Passe o mouse para informações rápidas
🔍 Uso dos Filtros
- Selecionar Filtros: Marque as opções desejadas
- Aplicação Automática: Filtros são aplicados instantaneamente
- Múltiplos Filtros: Combine diferentes categorias
- Limpar Filtros: Use o botão "Limpar" para resetar
- Selecionar Todos: Use o botão "Todos" para marcar tudo
📊 Análise de Dados
- Cards Principais: Visão geral no topo da página
- Contador de Filtros: Resultados atuais no painel de filtros
- Estatísticas Detalhadas: Distribuições na parte inferior
🔄 Atualização de Dados
- Automática: Cache atualizado a cada 5 minutos
- Manual: Clique no botão "Atualizar Dados"
- Indicador: Mensagem de confirmação após atualização
<br>

7.📁 Estrutura do Projeto
```text
mapa-elevadores-tjmg/
├── 📄 app.py                 # Aplicação principal Flask
├── 📄 sheets_api.py          # Integração com Google Sheets
├── 📄 config.py              # Configurações da aplicação
├── 📄 requirements.txt       # Dependências Python
├── 📄 credentials.json       # Credenciais Google Cloud (não versionado)
├── 📁 templates/             # Templates HTML
│   ├── 📄 base.html         # Template base
│   └── 📄 index_nativo.html # Página principal
├── 📁 static/               # Arquivos estáticos
│   ├── 📁 css/             # Estilos CSS
│   │   └── 📄 style.css    # Estilos customizados
│   └── 📁 js/              # Scripts JavaScript
│       └── 📄 filtros_mapa.js # Lógica dos filtros (se usado)
└── 📄 README.md             # Este arquivo
```


<br><br>8.🔌 **API**<br><br>
Endpoints Disponíveis:<br><br>
**Página principal da aplicação**<br>
`GET /`<br><br>

**Filtra dados baseado nos parâmetros fornecidos**<br>
`GET /api/filtrar`
<br><br>

**Parâmetros**<br>
```
tipo[]: Array de tipos de elevador
regiao[]: Array de regiões
marca[]: Array de marcas
empresa[]: Array de empresas


{
  "success": true,
  "stats": {
    "total_elevadores": 150,
    "total_predios": 45,
    "cidades": 30,
    "regioes": 5,
    "em_atividade": 140,
    "suspensos": 10,
    "por_tipo": {...},
    "por_regiao": {...},
    "por_marca": {...},
    "por_status": {...}
  },
  "total_registros": 45
}
```
**Força atualização dos dados da planilha**<br>
`GET /atualizar`

```
{
  "success": true,
  "message": "Dados atualizados! 243 registros carregados.",
  "timestamp": "30/08/2025 10:30:00"
}
```
