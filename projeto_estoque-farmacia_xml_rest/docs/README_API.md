# 🏥 Sistema de Estoque e Farmácia - v2.0.0

## 📋 Visão Geral

Sistema completo de gerenciamento de estoque e farmácia com:
- ✅ **API REST profissional** com FastAPI
- ✅ **Frontend moderno** e responsivo
- ✅ **Processamento XML em background** (FEFO - First Expiry First Out)
- ✅ **Banco de dados PostgreSQL**
- ✅ **Arquitetura SOLID e Clean Code**

## 🚀 Início Rápido

### 1. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados

Editar `.env` com suas credenciais do PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Interoperabilidade
DB_USER=postgres
DB_PASSWORD=postgres
DB_SCHEMA=projeto
```

Executar script de inicialização:

```bash
python scripts/init_db.py
```

### 3. Iniciar o Sistema

```bash
python run_api.py
```

Isso vai:
- ✅ Iniciar a API REST em `http://localhost:8000`
- ✅ Iniciar processamento XML em background
- ✅ Servir o frontend em `http://localhost:8000/`

## 📚 API REST - Endpoints

### Medicamentos

```bash
# Listar todos
GET /api/medicamentos

# Obter específico
GET /api/medicamentos/{codigo}
```

### Estoque

```bash
# Obter estoque total
GET /api/estoque/{codigo_medicamento}

# Consultar disponibilidade
POST /api/estoque/consultar
{
  "codigo_medicamento": 789123,
  "quantidade": 5,
  "cpf_paciente": "12345678901"
}

# Listar lotes
GET /api/estoque/lotes/{codigo_medicamento}
```

### Reservas

```bash
# Criar reserva
POST /api/reservas
{
  "codigo_medicamento": 789123,
  "quantidade": 5,
  "lote": "LOTE123",
  "cpf_paciente": "12345678901"
}

# Listar reservas ativas
GET /api/reservas

# Obter reserva específica
GET /api/reservas/{id_reserva}

# Cancelar reserva
DELETE /api/reservas/{id_reserva}
```

### Baixas

```bash
# Registrar baixa
POST /api/baixas
{
  "codigo_medicamento": 789123,
  "quantidade": 5,
  "lote": "LOTE123",
  "motivo": "Dispensado ao paciente"
}
```

## 🌐 Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Estrutura de Diretórios

```
projeto_estoque-farmacia_xml_rest/
├── src/
│   ├── api/
│   │   ├── app.py              # Aplicação FastAPI
│   │   ├── rotas_medicamentos.py
│   │   ├── rotas_estoque.py
│   │   ├── rotas_reservas.py
│   │   └── rotas_baixas.py
│   ├── casos_de_uso.py          # Lógica de negócio
│   ├── repositorios.py          # Camada de dados
│   ├── schemas.py               # Validação Pydantic
│   ├── config/
│   │   ├── database.py
│   │   └── ftp.py
│   ├── processors/              # Processadores XML
│   ├── services/
│   ├── utils/
│   └── main.py                  # Loop de processamento
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── api-client.js
│   │       └── app.js
│   └── templates/
│       └── dashboard.html
├── scripts/                     # Scripts utilitários
├── xsds/                        # Schemas XML
├── logs/                        # Logs do sistema
├── requirements.txt
├── .env
└── run_api.py                   # Inicializador principal
```

## 🏗️ Arquitetura

### Camadas

```
┌─────────────────────────────┐
│     Frontend (HTML/CSS/JS)  │
├─────────────────────────────┤
│     API REST (FastAPI)      │
├─────────────────────────────┤
│   Casos de Uso (Business)   │
├─────────────────────────────┤
│  Repositórios (Data Access) │
├─────────────────────────────┤
│   Database (PostgreSQL)     │
└─────────────────────────────┘
```

### Princípios SOLID

- **S**ingle Responsibility: Cada classe tem uma única responsabilidade
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Subclasses são substituíveis
- **I**nterface Segregation: Interfaces específicas ao cliente
- **D**ependency Inversion: Depender de abstrações

### Padrões de Design

- **Repository Pattern**: Abstração da camada de dados
- **Use Case Pattern**: Lógica de negócio isolada
- **Dependency Injection**: Desacoplamento via FastAPI Depends()
- **MVC-like**: Separação de responsabilidades

## 🔄 Fluxos Principais

### Consulta de Disponibilidade

```
1. Usuário submete formulário de consulta
2. Frontend faz POST /api/estoque/consultar
3. API valida CPF e código
4. CasoDeUsoConsulta busca lote disponível (FEFO)
5. Retorna disponibilidade, lote sugerido e preço
```

### Criação de Reserva

```
1. Usuário preenche formulário de reserva
2. Frontend faz POST /api/reservas
3. API valida medicamento, lote e CPF
4. CasoDeUsoReserva verifica:
   - Medicamento existe
   - Lote existe e não expirou
   - Estoque suficiente
5. Cria reserva no banco
6. Retorna ID da reserva
```

### Baixa de Estoque

```
1. Usuário registra baixa via formulário
2. Frontend faz POST /api/baixas
3. API valida dados
4. CasoDeUsoBaixa reduz quantidade do lote
5. Retorna quantidade restante
```

## 🔧 Configurações Importantes

### Ambiente (.env)

```env
# Banco de Dados
DB_HOST=localhost          # Host do PostgreSQL
DB_PORT=5432              # Porta
DB_NAME=Interoperabilidade # Nome do banco
DB_USER=postgres          # Usuário
DB_PASSWORD=postgres      # Senha
DB_SCHEMA=projeto         # Schema

# Pastas
PASTA_CONSULTAS=entrada/consultas
PASTA_RESERVAS=entrada/reservas
PASTA_BAIXAS=entrada/baixas

# Processamento
PROCESSAMENTO_INTERVALO=10      # Segundos entre processamentos
CONSUMO_HORA_GERACAO=23         # Hora para gerar relatório (0-23)
```

## 📊 Modelagem de Dados

### Tabelas Principais

```sql
-- Medicamentos
medicamentos (id, codigo, nome)

-- Lotes
lotes (id_lote, numero_lote, codigo_medicamento, 
       quantidade_inicial, quantidade_atual, 
       data_validade, preco_venda)

-- Reservas Ativas
reservas_ativas (id_reserva, codigo_medicamento, 
                 quantidade, numero_lote, cpf_paciente, 
                 status, data_criacao)
```

## 🧪 Testando a API

### Com cURL

```bash
# Listar medicamentos
curl http://localhost:8000/api/medicamentos

# Consultar disponibilidade
curl -X POST http://localhost:8000/api/estoque/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_medicamento": 789123,
    "quantidade": 5,
    "cpf_paciente": "12345678901"
  }'

# Criar reserva
curl -X POST http://localhost:8000/api/reservas \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_medicamento": 789123,
    "quantidade": 5,
    "lote": "LOTE123",
    "cpf_paciente": "12345678901"
  }'
```

### Com Swagger UI

1. Acesse http://localhost:8000/docs
2. Clique em "Try it out" em qualquer endpoint
3. Preencha os dados
4. Clique "Execute"

## 🔍 Logs e Debug

Logs estão em:
- `logs/` - Logs gerais do sistema
- Console - Output durante execução

Para mais detalhes:

```python
# Em qualquer arquivo, use logging
import logging
logger = logging.getLogger(__name__)
logger.info("Mensagem de informação")
logger.error("Mensagem de erro")
```

## 🐛 Troubleshooting

### Erro: "Não consegue conectar ao banco"
- Verificar se PostgreSQL está rodando
- Verificar credenciais em `.env`
- Verificar se o schema foi criado

### Erro: "Porta 8000 já está em uso"
- Mudar porta em `run_api.py`: `uvicorn.run(app, port=8001)`

### Erro: CORS no frontend
- CORS já está habilitado para todos em `app.py`
- Verificar console do navegador para mais detalhes

## 📝 Desenvolvendo

### Adicionar novo endpoint

1. Criar método em `src/casos_de_uso.py`
2. Criar rota em `src/api/rotas_*.py`
3. Adicionar schema em `src/schemas.py`
4. Testar em http://localhost:8000/docs

### Exemplo: Novo endpoint

```python
# 1. schemas.py
class NovoSchema(BaseModel):
    campo: str

# 2. casos_de_uso.py
class CasoDeUsoNovo:
    def processar(self, dados):
        # lógica
        return resultado

# 3. rotas_novo.py
@router.post("")
async def criar_novo(dados: NovoSchema):
    resultado = caso_de_uso.processar(dados)
    return resultado

# 4. app.py
from src.api.rotas_novo import router as router_novo
app.include_router(router_novo)
```

## 📦 Deploy

### Docker (futuro)

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_api.py"]
```

### Gunicorn (produção)

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 src.api.app:app
```

## 📄 Licença

Ver arquivo LICENSE

## 👥 Autores

Grupo 3 - Projeto de Interoperabilidade

## 📞 Suporte

Para dúvidas, abra uma issue ou consulte a documentação em `/docs`
