# 🚀 COMECE AQUI - Guia Rápido

## ⚡ 5 Minutos para Começar

### 1️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2️⃣ Configurar Banco de Dados

Editar `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Interoperabilidade
DB_USER=postgres
DB_PASSWORD=postgres
```

Executar:
```bash
python scripts/init_db.py
```

### 3️⃣ Iniciar Sistema

```bash
python run_api.py
```

✅ Pronto! Acesse:
- 🌐 **Frontend**: http://localhost:8000/
- 📚 **API Docs**: http://localhost:8000/docs
- 💻 **ReDoc**: http://localhost:8000/redoc

---

## 📝 Estrutura do Projeto

```
✅ src/
   ├── api/               ← API REST (FastAPI)
   │   ├── app.py        ← App principal
   │   └── rotas_*.py    ← Endpoints
   ├── casos_de_uso.py   ← Lógica de negócio
   ├── repositorios.py   ← Acesso a dados
   └── schemas.py        ← Validação

✅ frontend/
   ├── static/
   │   ├── css/style.css
   │   └── js/
   │       ├── api-client.js
   │       └── app.js
   └── templates/
       └── dashboard.html

✅ scripts/              ← Utilitários
✅ xsds/               ← Schemas XML
```

---

## 🎯 O que Funciona

### ✅ Consultas
```bash
POST /api/estoque/consultar
{
  "codigo_medicamento": 789123,
  "quantidade": 5,
  "cpf_paciente": "12345678901"
}
```

### ✅ Reservas
```bash
POST /api/reservas
{
  "codigo_medicamento": 789123,
  "quantidade": 5,
  "lote": "LOTE123",
  "cpf_paciente": "12345678901"
}
```

### ✅ Baixas
```bash
POST /api/baixas
{
  "codigo_medicamento": 789123,
  "quantidade": 5,
  "lote": "LOTE123",
  "motivo": "Dispensado"
}
```

### ✅ Estoque
```bash
GET /api/estoque/{codigo_medicamento}
GET /api/estoque/lotes/{codigo_medicamento}
```

### ✅ Medicamentos
```bash
GET /api/medicamentos
GET /api/medicamentos/{codigo}
```

---

## 🧪 Testar API

### Com cURL
```bash
curl -X POST http://localhost:8000/api/estoque/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_medicamento": 789123,
    "quantidade": 5,
    "cpf_paciente": "12345678901"
  }'
```

### Com Script
```bash
python testar_api.py
```

### Com Swagger UI
1. Acesse http://localhost:8000/docs
2. Clique em "Try it out"
3. Preencha dados
4. Clique "Execute"

---

## 📚 Documentação Completa

- **API REST**: [README_API.md](README_API.md)
- **Arquitetura**: [ARQUITETURA.md](ARQUITETURA.md)
- **README Original**: [README.md](README.md)

---

## 🐛 Erros Comuns

| Problema | Solução |
|----------|---------|
| ❌ "Connection refused" | Verificar se PostgreSQL está rodando |
| ❌ "Porta 8000 em uso" | `netstat -an \| find ":8000"` e matar processo |
| ❌ "Database não encontrado" | Rodar `python scripts/init_db.py` |
| ❌ "CORS error" | Recarregar página (já está habilitado) |

---

## 💡 Próximos Passos

1. **Entender Arquitetura**
   - Ler [ARQUITETURA.md](ARQUITETURA.md)
   - Ver diagrama de camadas

2. **Explorar Código**
   - Abrir `src/api/app.py` (ponto de entrada)
   - Ver rotas em `src/api/rotas_*.py`
   - Lógica em `src/casos_de_uso.py`

3. **Adicionar Funcionalidade**
   - Criar novo endpoint
   - Seguir padrão do projeto
   - Usar schemas para validação

4. **Deploy**
   - Ver seção de deploy em README_API.md
   - Usar Docker ou Gunicorn

---

## 🎓 Arquitetura em 1 Minuto

```
┌─────────────────────────┐
│  Frontend (HTML/JS)     │ ← Você acessa aqui
├─────────────────────────┤
│  API REST (FastAPI)     │ ← Endpoints JSON
├─────────────────────────┤
│  Casos de Uso           │ ← Lógica de negócio
├─────────────────────────┤
│  Repositórios           │ ← Acesso a dados
├─────────────────────────┤
│  PostgreSQL             │ ← Banco de dados
└─────────────────────────┘
```

**Fluxo**: Frontend → API → Lógica → Banco de Dados → Resposta

---

## 📞 Precisa de Ajuda?

1. **Documentação**: Ler README_API.md e ARQUITETURA.md
2. **API Docs**: Acessar http://localhost:8000/docs
3. **Logs**: Verificar console de execução
4. **Código**: Ler comentários no código (bem documentado!)

---

## ✨ Características Principais

✅ **API REST** com FastAPI (documentação automática)  
✅ **Frontend moderno** - HTML/CSS/JS puro (sem dependências)  
✅ **Arquitetura limpa** - SOLID, DRY, KISS, Clean Code  
✅ **FEFO** - First Expiry First Out (ordem de vencimento)  
✅ **Processamento XML** - Em background (scheduler)  
✅ **CORS habilitado** - Para integração com outras apps  
✅ **Type hints** - Todo código tipado  
✅ **Documentação** - Completa e com exemplos  

---

## 🎉 Pronto!

Agora você está pronto para:
- 🏃 Rodar o sistema
- 💼 Usar a API
- 🧠 Entender a arquitetura
- 🚀 Estender funcionalidades

Boa sorte! 🚀
