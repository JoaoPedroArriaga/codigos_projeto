# Documentação — Sistema de Estoque e Farmácia (SOAP)

Projeto de interoperabilidade do **Grupo 3** com protocolo **SOAP/XML**, WSDL formal e autenticação **HMAC-SHA256**.

> Comparação de performance com REST: use o benchmark na pasta `benchmarks/` na raiz do repositório, apontando para `projeto_estoque-farmacia_xml_rest` (porta 8001) e este projeto (porta 8000).

---

## Visão geral

| Item | Valor |
|------|-------|
| Protocolo | SOAP 1.1 + XML |
| Endpoint único | `POST /soap` |
| Contrato | `GET /soap?wsdl` |
| Porta padrão | `8000` |
| Dashboard | `GET /` (browser) |
| REST JSON | **Removido** — integração apenas via SOAP |

O servidor unificado (`run_api.py`) sobe três componentes em paralelo:

1. **Processamento XML** em background (`src/main.py`) — leitura de arquivos, consumo, jobs agendados
2. **Servidor SOAP** — FastAPI + rotas em `src/soap/routes.py`
3. **Dashboard web** — HTML/JS em `frontend/`, consumindo SOAP via `soap-client.js`

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  run_api.py (porta 8000)                                    │
├─────────────────────────────────────────────────────────────┤
│  Thread background    │  Thread principal (uvicorn)         │
│  src/main.py          │  src/api/app.py                    │
│  (XML + PostgreSQL)   │    ├── POST /soap  (16 operações)  │
│                       │    ├── GET  /soap?wsdl             │
│                       │    ├── GET  /soap/health           │
│                       │    └── GET  /  → dashboard.html    │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
   Arquivos XML                   Grupos G1/G2 + Dashboard
   (entrada/saída)                (envelope SOAP + HMAC)
```

### Camadas

| Camada | Pasta | Responsabilidade |
|--------|-------|------------------|
| Rotas SOAP | `src/soap/routes.py` | Roteamento, HMAC, WSDL, Faults |
| Serviços | `src/soap/services/` | Regras de negócio SOAP |
| Envelope | `src/soap/handlers/envelope.py` | Montagem e parsing XML |
| Domínio | `src/repositorios.py`, `src/casos_de_uso.py` | Banco, FEFO, consultas |
| Frontend | `frontend/static/js/` | `soap-client.js` + `api-client.js` |
| WSDL/XSD | `src/wsdl/`, `xsds/` | Contrato formal |

---

## Como executar

### Pré-requisitos

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Configure o `.env` (PostgreSQL):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_SCHEMA=projeto
```

### Servidor completo (recomendado)

```bash
python run_api.py
```

URLs disponíveis:

| URL | Descrição |
|-----|-----------|
| http://localhost:8000/ | Dashboard |
| http://localhost:8000/soap?wsdl | WSDL |
| http://localhost:8000/soap | Endpoint SOAP |
| http://localhost:8000/soap/health | Health check SOAP + banco |
| http://localhost:8000/health | Health check do servidor |

### Apenas SOAP (sem background/dashboard)

```bash
python -m src.soap.app
```

---

## Operações SOAP

Todas as operações usam **uma única URL** (`POST /soap`). A operação é identificada pelo elemento raiz dentro de `<soap:Body>`.

### Medicamentos (`ServiceMedicamentos`)

| Operação | Parâmetros | Descrição |
|----------|------------|-----------|
| `listarMedicamentos` | — | Lista todos os medicamentos |
| `obterMedicamento` | `codigo` | Detalhe de um medicamento |
| `sincronizarMedicamentos` | `arquivo_xml`, `grupo_origem` | Importa catálogo via XML |

### Estoque (`ServiceEstoque`)

| Operação | Parâmetros | Descrição |
|----------|------------|-----------|
| `obterEstoque` | `codigo_medicamento` | Estoque total + lotes |
| `listarLotes` | `codigo_medicamento` | Lotes do medicamento |
| `consultarDisponibilidade` | `codigo_medicamento`, `quantidade`, `cpf_paciente` | Consulta crítica (Grupo 2) |
| `verificarReservas` | `codigo_medicamento` | Reservas ativas do item |
| `gerarAlerta` | `codigo_medicamento`, `quantidade_minima` | Alerta de estoque baixo |

### Transações (`ServiceTransacoes`)

| Operação | Parâmetros | Descrição |
|----------|------------|-----------|
| `criarReserva` | `codigo_medicamento`, `quantidade`, `cpf_paciente` | Reserva com FEFO |
| `obterReserva` | `id_reserva` | Detalhe da reserva |
| `cancelarReserva` | `id_reserva` | Cancela reserva ativa |
| `listarReservas` | — | Lista reservas ativas |
| `registrarBaixa` | `codigo_medicamento`, `quantidade`, `numero_lote`, `cpf_paciente`, `motivo` | Baixa de estoque |
| `listarBaixas` | `data_inicio`, `data_fim` (opcionais) | Histórico de baixas |

### Integração (`ServiceIntegracao`)

| Operação | Parâmetros | Descrição |
|----------|------------|-----------|
| `gerarRelatorioConsumo` | `data_inicio`, `data_fim` | Relatório para Grupo 1 |
| `consultarStatusPaciente` | `cpf` | Status do paciente |
| `sincronizarStatusFinanceiro` | `arquivo_xml`, `grupo_origem` | Sync financeiro via XML |

---

## Autenticação HMAC-SHA256

Toda requisição SOAP deve incluir no `<soap:Header>`:

```xml
<tns:autenticacao>
  <tns:hash>HMAC_DO_BODY</tns:hash>
  <tns:timestamp>2026-06-12T10:00:00</tns:timestamp>
  <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
  <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
</tns:autenticacao>
```

- **Chave compartilhada**: `chave_secreta_compartilhada_entre_grupos_2026` (variável em `src/utils/hash_utils.py`)
- **Hash**: HMAC-SHA256 do elemento de operação dentro de `<soap:Body>` (canonicalização via lxml)
- **Grupos**: `GRUPO_1`, `GRUPO_2`, `GRUPO_DASHBOARD`, etc.

Erro de assinatura inválida retorna SOAP Fault com código `ASSINATURA_INVALIDA`.

### Exemplo de envelope

```xml
<?xml version='1.0' encoding='utf-8'?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1"
               xmlns:tipos="http://estoque-farmacia.projeto.interop/v1/tipos">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>...</tns:hash>
      <tns:timestamp>2026-06-12T10:00:00</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:consultarDisponibilidade>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>1</tns:quantidade>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
    </tns:consultarDisponibilidade>
  </soap:Body>
</soap:Envelope>
```

Headers HTTP:

```
Content-Type: text/xml; charset=utf-8
SOAPAction: consultarDisponibilidade
```

---

## Dashboard (frontend SOAP)

O painel em `frontend/templates/dashboard.html` **não usa REST**. A cadeia é:

```
app.js  →  api-client.js (fachada)  →  soap-client.js  →  POST /soap
```

| Arquivo | Função |
|---------|--------|
| `soap-client.js` | Monta envelope XML, calcula HMAC (Web Crypto), envia e parseia resposta |
| `api-client.js` | Interface estável (`api.listar_medicamentos()`, etc.) para o `app.js` |
| `app.js` | UI, formulários, tabelas |

Health check do dashboard: `GET /soap/health`.

---

## Testes

```bash
pytest tests/soap/ -v
```

Cobertura principal:

- Envelope e HMAC (`test_envelope.py`)
- Serviços de estoque, transações e integração
- Fixtures em `tests/conftest.py`

### Cliente de exemplo

```bash
python exemplos_soap.py
python exemplos_soap.py --hash-only listarMedicamentos
bash exemplos_curl.sh
```

---

## Benchmark REST vs SOAP

A pasta `benchmarks/` fica na **raiz do repositório** (`codigos_projeto/benchmarks/`), separada deste projeto.

```bash
# Terminal 1 — SOAP (este projeto)
cd projeto_estoque-farmacia_soap
python run_api.py

# Terminal 2 — REST (projeto irmão)
cd projeto_estoque-farmacia_xml_rest
python run_api.py

# Terminal 3 — Benchmark
cd benchmarks
python benchmark_comparison.py          # 20 iterações (padrão)
python benchmark_comparison.py --quick  # 10 iterações (rápido)
python benchmark_comparison.py -n 50    # mais preciso, mais lento
```

| Projeto | Protocolo | Porta padrão |
|---------|-----------|--------------|
| `projeto_estoque-farmacia_soap` | SOAP | 8000 |
| `projeto_estoque-farmacia_xml_rest` | REST JSON | 8001 |

O benchmark compara latência, tamanho de payload e taxa de sucesso em 4 cenários equivalentes (160 requisições no padrão, 400 com `-n 50`).

---

## Estrutura de pastas

```
projeto_estoque-farmacia_soap/
├── run_api.py                 # Entrada principal
├── exemplos_soap.py           # Cliente Python de teste
├── exemplos_curl.sh           # Exemplos curl
├── DOCUMENTACAO.md            # Este arquivo
├── frontend/
│   ├── templates/dashboard.html
│   └── static/js/
│       ├── soap-client.js
│       ├── api-client.js
│       └── app.js
├── src/
│   ├── api/app.py             # Host FastAPI (SOAP + dashboard)
│   ├── main.py                # Processamento XML em background
│   ├── repositorios.py
│   ├── casos_de_uso.py
│   ├── soap/
│   │   ├── routes.py          # Rotas /soap
│   │   ├── app.py             # Servidor SOAP isolado
│   │   ├── handlers/envelope.py
│   │   ├── services/          # 4 serviços, 17 operações
│   │   └── types.py
│   ├── wsdl/estoque_farmacia.wsdl
│   └── utils/hash_utils.py
├── xsds/                      # Schemas XML
└── tests/soap/
```

---

## Regras de negócio críticas

### FEFO (First Expiry, First Out)

`criarReserva` seleciona automaticamente o lote com **menor data de validade** entre os disponíveis.

### Consulta de disponibilidade

`consultarDisponibilidade` é a operação usada pelo **Grupo 2** para verificar se há estoque antes da prescrição.

### Códigos de erro SOAP

| Código | Situação |
|--------|----------|
| `ASSINATURA_INVALIDA` | HMAC incorreto ou expirado |
| `MEDICAMENTO_NAO_ENCONTRADO` | Código inexistente |
| `ESTOQUE_INSUFICIENTE` | Quantidade indisponível |
| `LOTE_NAO_ENCONTRADO` | Lote inválido |
| `LOTE_VENCIDO` | Lote fora da validade |
| `RESERVA_NAO_ENCONTRADA` | ID de reserva inválido |
| `CPF_INVALIDO` | CPF sem 11 dígitos |
| `ERRO_BANCO_DADOS` | Falha no PostgreSQL |

---

## Integração entre grupos (SOAP + REST conectados)

Usamos **dois servidores G3** na disciplina de interoperabilidade — mesma regra de negócio, protocolos diferentes:

| Servidor | Projeto | Porta |
|----------|---------|-------|
| G3 SOAP | `projeto_estoque-farmacia_soap` (este) | 8000 |
| G3 REST | `projeto_estoque-farmacia_xml_rest` | 8001 |

Visão completa: [`../INTEROPERABILIDADE.md`](../INTEROPERABILIDADE.md)

| Grupo | Papel | SOAP (este projeto) | REST (xml_rest) |
|-------|-------|---------------------|-----------------|
| G1 | Financeiro | Puxa `gerarRelatorioConsumo`; envia `sincronizarStatusFinanceiro` | `GET /api/relatorios/consumo`; `POST /api/integracao/status-financeiro` |
| G2 | Prescrição | `consultarDisponibilidade`, `criarReserva` | `POST /api/estoque/consultar`, `POST /api/reservas` |
| G3 | Estoque | Este servidor | Servidor REST paralelo |
| Dashboard | UI local | `GRUPO_DASHBOARD` via SOAP | — |

**Subir ambos:** `..\iniciar_sistema.ps1` na raiz do repositório.

### Relatório de consumo — G1 puxa no começo do dia (pull)

Modelo acordado: **G3 não empurra o arquivo**; **G1 busca de manhã** o consumo do dia anterior.

```
23:00  G3 consolida baixas → banco (+ XML em data/saida/consumos/ como backup)
08:00  G1 chama G3 e recebe o relatório pronto
```

| Protocolo | Quem chama | Endpoint | Operação / rota |
|-----------|-----------|----------|------------------|
| **SOAP** (este projeto) | G1 → G3 | `POST http://IP_G3:8000/soap` | `gerarRelatorioConsumo` |
| **REST** (projeto `xml_rest`) | G1 → G3 | `GET http://IP_G3:8001/api/relatorios/consumo` | XML `consumo.xsd` + headers HMAC |

**REST — headers obrigatórios:**

```
X-Grupo-Origem: GRUPO_1
X-Hash: HMAC-SHA256 de "data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD"
```

**Exemplos (simular G1):**

```bash
# SOAP (este projeto)
python exemplos_pull_g1.py

# REST (projeto xml_rest, porta 8001)
cd ../projeto_estoque-farmacia_xml_rest
python exemplos_pull_g1.py
```

**Parâmetros SOAP** (período — normalmente o dia anterior):

```xml
<tns:gerarRelatorioConsumo>
  <tns:data_inicio>2026-06-11</tns:data_inicio>
  <tns:data_fim>2026-06-11</tns:data_fim>
</tns:gerarRelatorioConsumo>
```

Header: `grupo_origem: GRUPO_1` + HMAC válido.

**Resposta:** XML de consumo assinado em `arquivo_xml` dentro do envelope SOAP.

**Teste simulando o G1:**

```bash
python exemplos_soap.py gerarRelatorioConsumo
# ou editar SOAP_URL para o IP do G3 e usar grupo_origem GRUPO_1
```

O arquivo em `data/saida/consumos/` é **cópia local/backup** da consolidação das 23h — na integração ao vivo o G1 usa a **API**, não essa pasta.

Mais detalhes: `CONEXAO_GRUPOS.md`, `docs/WSDL_TECNICO.md`.

---

## Referência rápida de comandos

```bash
# Subir sistema
python run_api.py

# Testar SOAP
python exemplos_soap.py

# Testes automatizados
pytest tests/soap/ -v

# Ver WSDL
curl http://localhost:8000/soap?wsdl

# Health
curl http://localhost:8000/soap/health
```
