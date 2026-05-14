# 📊 Diagrama da Arquitetura

## 🏗️ Visão Geral do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                   │
│                   Frontend (HTML/CSS/JS)                    │
│         Tabs: Consultas | Reservas | Baixas | Estoque     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Requests/Responses
                         │ JSON
┌────────────────────────▼────────────────────────────────────┐
│                    CAMADA DE API (FastAPI)                  │
│  /api/medicamentos  /api/estoque  /api/reservas /api/baixas│
│              com Documentação automática (Swagger)          │
└────────────────────────┬────────────────────────────────────┘
                         │ Dependency Injection
┌────────────────────────▼────────────────────────────────────┐
│                  CAMADA DE CASOS DE USO                     │
│  CasoDeUsoConsulta | Reserva | Baixa | Estoque            │
│          (Lógica de Negócio - FEFO)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Repositórios
┌────────────────────────▼────────────────────────────────────┐
│                  CAMADA DE REPOSITÓRIOS                     │
│  RepositorioMedicamento | Lote | Reserva                  │
│         (Data Access Layer - SQL Queries)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
┌────────────────────────▼────────────────────────────────────┐
│                   BANCO DE DADOS                            │
│               PostgreSQL (Schema: projeto)                  │
│         Tabelas: medicamentos, lotes, reservas             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Fluxo de Requisição (Exemplo: Consultar Disponibilidade)

```
1. USUÁRIO
   └─> Preenche formulário no frontend
       ├─ Código: 789123
       ├─ Quantidade: 5
       └─ CPF: 12345678901

2. FRONTEND
   └─> Faz POST /api/estoque/consultar
       └─> JSON: {codigo_medicamento: 789123, ...}

3. API (rotas_estoque.py)
   └─> consultar_disponibilidade()
       ├─ Recebe ConsultaRequestSchema (validado)
       ├─ Injeta CasoDeUsoConsulta via Depends()
       └─> Chama caso_de_uso.processar_consulta()

4. CASO DE USO (casos_de_uso.py)
   └─> CasoDeUsoConsulta.processar_consulta()
       ├─ Valida medicamento (repositorio_medicamento.buscar_por_codigo())
       ├─ Busca lote disponível FEFO (repositorio_lote.buscar_disponivel())
       └─> Retorna resultado com detalhes

5. REPOSITÓRIOS (repositorios.py)
   └─> Executam SQL
       └─> db.execute("SELECT FROM lotes WHERE ... ORDER BY data_validade")

6. BANCO DE DADOS (PostgreSQL)
   └─> Retorna dados

7. API
   └─> Formata como ConsultaResponseSchema
       └─> Return JSON com sucesso e dados

8. FRONTEND
   └─> Recebe JSON
       ├─ Parse resposta
       ├─ Renderiza resultado
       └─> Mostra: "✅ Disponível: LOTE123, Preço: R$ XX,XX"

9. USUÁRIO
   └─> Vê resultado no dashboard
```

## 📁 Estrutura de Arquivos

```
projeto_estoque-farmacia_xml_rest/
│
├── 📂 src/
│   │
│   ├── 📂 api/                          ← 🆕 Nova: API REST
│   │   ├── app.py                       ← Aplicação FastAPI
│   │   ├── rotas_medicamentos.py        ← GET /api/medicamentos
│   │   ├── rotas_estoque.py             ← GET/POST estoque
│   │   ├── rotas_reservas.py            ← CRUD reservas
│   │   ├── rotas_baixas.py              ← POST baixas
│   │   └── __init__.py
│   │
│   ├── 📂 config/
│   │   ├── database.py                  ← Conexão BD (mantida)
│   │   └── ftp.py
│   │
│   ├── 📂 processors/                   ← Processadores XML (mantidos)
│   │   ├── consulta_processor.py
│   │   ├── reserva_processor.py
│   │   ├── baixa_processor.py
│   │   └── ...
│   │
│   ├── 📂 models/                       ← Modelos (mantidos)
│   │   ├── medicamento.py
│   │   ├── lote.py
│   │   └── reserva_ativa.py
│   │
│   ├── 📂 services/
│   │   └── estoque_service.py
│   │
│   ├── 📂 utils/                        ← Utilitários (mantidos)
│   │   ├── xml_utils.py
│   │   ├── xml_validator.py
│   │   └── xml_normalizer.py
│   │
│   ├── schemas.py                       ← 🆕 Validação Pydantic (14 schemas)
│   ├── repositorios.py                  ← 🆕 Repository Pattern (4 repos)
│   ├── casos_de_uso.py                  ← 🆕 Lógica de Negócio (4 casos)
│   ├── main.py                          ← Loop processamento (mantido)
│   └── __init__.py
│
├── 📂 frontend/                         ← 🆕 Frontend moderno
│   ├── 📂 static/
│   │   ├── 📂 css/
│   │   │   └── style.css                ← Design profissional (500+ linhas)
│   │   └── 📂 js/
│   │       ├── api-client.js            ← Cliente API (DRY)
│   │       └── app.js                   ← Lógica frontend (500+ linhas)
│   │
│   ├── 📂 templates/
│   │   ├── index.html                   ← Antigo (mantido)
│   │   └── dashboard.html               ← 🆕 Novo dashboard
│   │
│   └── app.py                           ← Flask antigo (pode remover)
│
├── 📂 scripts/                          ← Scripts utilitários (mantidos)
│   ├── init_db.py
│   ├── gerar_consulta.py
│   ├── gerar_reserva.py
│   ├── gerar_baixa.py
│   └── ...
│
├── 📂 xsds/                             ← Schemas XML (mantidos)
│   ├── consulta.xsd
│   ├── reserva.xsd
│   ├── baixa.xsd
│   └── ...
│
├── 📂 logs/                             ← Logs do sistema
│
├── 📂 data/
│   ├── entrada/
│   ├── processados/
│   └── saida/
│
├── 🆕 run_api.py                        ← Inicializador principal
├── 🆕 testar_api.py                     ← Script de teste
├── 🆕 requirements.txt                  ← Dependências atualizadas
├── 🆕 COMECE_AQUI.md                    ← Guia rápido
├── 🆕 README_API.md                     ← Documentação completa
├── 🆕 ARQUITETURA.md                    ← Padrões SOLID
├── 🆕 RESUMO_IMPLEMENTACAO.md           ← What's new
│
├── .env                                 ← Configuração (expandido)
├── .gitignore
├── README.md                            ← README antigo (mantido)
└── LICENSE
```

## 🔌 Endpoints da API

```
GET    /                              # Página inicial
GET    /health                        # Health check
GET    /api                           # Info da API

GET    /api/medicamentos              # Listar todos
GET    /api/medicamentos/{codigo}     # Obter um

GET    /api/estoque/{codigo}          # Ver estoque
POST   /api/estoque/consultar         # Consultar disponibilidade
GET    /api/estoque/lotes/{codigo}    # Listar lotes

POST   /api/reservas                  # Criar reserva
GET    /api/reservas                  # Listar ativas
GET    /api/reservas/{id}             # Obter uma
DELETE /api/reservas/{id}             # Cancelar

POST   /api/baixas                    # Registrar baixa

GET    /docs                          # Swagger UI
GET    /redoc                         # ReDoc
```

## 🎯 Camadas e Responsabilidades

```
┌─────────────────────────────────────────────┐
│  FRONTEND (frontend/static/)                │
│  ├─ Apresentação (HTML/CSS)                 │
│  ├─ Interatividade (JavaScript)             │
│  └─ Chamadas HTTP (api-client.js)           │
└──────────────┬──────────────────────────────┘

┌──────────────▼──────────────────────────────┐
│  API LAYER (src/api/)                       │
│  ├─ HTTP Routing                            │
│  ├─ Request Validation (Schemas)            │
│  ├─ Response Formatting                     │
│  └─ Error Handling                          │
└──────────────┬──────────────────────────────┘

┌──────────────▼──────────────────────────────┐
│  USE CASES (src/casos_de_uso.py)            │
│  ├─ Lógica de Negócio                       │
│  ├─ Validações                              │
│  ├─ FEFO Implementation                     │
│  └─ Orquestração de Dados                   │
└──────────────┬──────────────────────────────┘

┌──────────────▼──────────────────────────────┐
│  DATA ACCESS (src/repositorios.py)          │
│  ├─ SQL Queries                             │
│  ├─ Database Transactions                   │
│  ├─ Data Mapping                            │
│  └─ CRUD Operations                         │
└──────────────┬──────────────────────────────┘

┌──────────────▼──────────────────────────────┐
│  DATABASE (PostgreSQL)                      │
│  ├─ Tabelas (medicamentos, lotes, reservas) │
│  ├─ Índices para performance                │
│  └─ Transações ACID                         │
└──────────────────────────────────────────────┘
```

## 🔐 Segurança

```
Frontend Input
    ↓
Pydantic Validation (Schemas)  ← Valida tipo, range, padrão
    ↓
SQL Parameterized Queries      ← Previne SQL Injection
    ↓
Type Hints                      ← Detecta erros de tipo
    ↓
Exception Handling              ← Tratamento robusto
    ↓
CORS Enabled                    ← Acesso controlado
```

## 📊 Fluxo de Dados (Criar Reserva)

```
┌─────────────────────────────────────────┐
│   FRONTEND                              │
│   POST /api/reservas                    │
│   {                                     │
│     "codigo_medicamento": 789123,       │
│     "quantidade": 5,                    │
│     "lote": "LOTE123",                  │
│     "cpf_paciente": "12345678901"       │
│   }                                     │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   API VALIDATION (Pydantic)             │
│   ✓ CPF matches regex \d{11}            │
│   ✓ Quantidade > 0                      │
│   ✓ Todos campos obrigatórios           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   CASO DE USO - VALIDAÇÕES              │
│   1. Medicamento existe?                │
│      → repo_med.buscar_por_codigo()     │
│   2. Lote existe?                       │
│      → repo_lote.buscar_por_numero()    │
│   3. Estoque suficiente?                │
│      → quantidade_atual >= solicitado?  │
│   4. Não expirou?                       │
│      → data_validade >= hoje?           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   DATABASE                              │
│   INSERT INTO reservas_ativas (...)     │
│   RETURNING id_reserva                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   RESPOSTA                              │
│   {                                     │
│     "success": true,                    │
│     "id_reserva": "12345",              │
│     "mensagem": "Reserva criada",       │
│     "timestamp": "2026-05-13T..."       │
│   }                                     │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   FRONTEND                              │
│   ✅ Mostra sucesso                     │
│   ✅ ID da reserva                      │
│   ✅ Recarrega lista de reservas        │
└─────────────────────────────────────────┘
```

## 🚀 Inicialização do Sistema

```
┌─────────────────────────────────────────┐
│   python run_api.py                     │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌────────────────────┐  ┌────────────────────┐
│   THREAD 1         │  │   THREAD MAIN      │
│   Processamento    │  │   API FastAPI      │
│   XML              │  │                    │
│                    │  │   Uvicorn Server   │
│ ├─ Loop schedule   │  │   :8000            │
│ ├─ Consultas       │  │                    │
│ ├─ Reservas        │  │ Endpoints:         │
│ ├─ Baixas          │  │ ✅ /api/*          │
│ └─ Gera consumo    │  │ ✅ /docs           │
│                    │  │ ✅ / (frontend)    │
└────────────────────┘  └────────────────────┘
    │                          │
    └──────────┬───────────────┘
               │
               ▼
         PostgreSQL
          (Shared DB)
```

---

Este diagrama mostra como tudo funciona junto! 🎯
