# Análise de Acoplamento: REST vs SOAP

## 📊 Resumo Executivo

| Aspecto | REST API | SOAP/WSDL |
|---------|----------|-----------|
| **Acoplamento** | Médio-Alto | Baixo |
| **Descoberta** | Manual | Automática (WSDL) |
| **Contrato** | Implícito (Swagger) | Explícito (WSDL) |
| **Tipo de Dados** | Frouxo (JSON) | Rigoroso (XSD Tipos) |
| **Versionamento** | Query params / headers | Namespace versionado |
| **Segurança** | OAuth2, JWT | WS-Security, HMAC Header |
| **Interoperabilidade** | Linguagem-dependente | Linguagem-independente |
| **Overhead** | Baixo | Alto (XML verboso) |
| **Latência** | Baixa | Média (parsing XML) |

---

## 🔗 Análise de Acoplamento

### 1. REST API (modelo atual)

#### Tipo de Acoplamento: **MÉDIO-ALTO**

**Características**:
- Cliente conhece URLs exatas: `/api/medicamentos`, `/api/reservas`, etc
- HTTP methods implícitos: GET = leitura, POST = escrita
- Estrutura de resposta JSON é implícita (conforme Swagger)
- CPF é string em JSON; tipo não é validado no transporte

**Exemplos de acoplamento**:

```python
# Cliente REST deve conhecer:
# 1. Endpoint exato
response = requests.get("http://localhost:8000/api/medicamentos/789123")

# 2. Estrutura JSON esperada
medicamento = response.json()
print(medicamento['codigo'])  # Assume 'codigo' existe

# 3. Tratamento de erro ad-hoc
if response.status_code == 404:
    print("Medicamento não encontrado")
```

**Riscos**:
- Se servidor renomeia campo (`codigo` → `med_codigo`), cliente quebra
- Se servidor mudar tipo (`codigo: "789123"` em string), cliente pode quebrar
- Sem contrato formalizados → incompatibilidades
- Discovery = ler documentação Swagger manualmente

---

### 2. SOAP/WSDL (novo modelo)

#### Tipo de Acoplamento: **BAIXO**

**Características**:
- Contrato WSDL define tipos **explicitamente** (XSD)
- CPF é obrigatoriamente string com 11 dígitos (validação XSD)
- Operações e tipos são descobertos via WSDL
- Cliente gera stubs automaticamente (zeep, SoapUI, wsimport)

**Exemplos de desacoplamento**:

```python
# Cliente SOAP (gerado automaticamente do WSDL)
from zeep import Client

client = Client(wsdl='http://localhost:8000/soap?wsdl')

# 1. Operações descobertas automaticamente
service = client.bind('EstoqueFarmaciaService', 'ServiceMedicamentosPort')

# 2. Tipos são validados no stub
medicamento = {
    'codigo': 789123,      # Tipo: int (XSD int)
    'nome': 'Paracetamol'   # Tipo: string (XSD string)
}

# 3. Chamada type-safe
response = service.obterMedicamento(codigo=789123)

# 4. Erro em contrato é validado antes de enviar
#    Se tentar enviar CPF com 10 dígitos → erro imediato
```

**Vantagens**:
- Mudanças no servidor (renomear campo) são propagadas automaticamente ao WSDL
- Cliente gera novos stubs periodicamente
- Validação de tipos no cliente (antes de enviar)
- Discovery = ler WSDL automaticamente

---

## 📈 Comparação Detalhada

### A. Estrutura de Dados (Coupling Level)

#### REST - JSON

```json
{
  "id": 1,
  "codigo": 789123,
  "nome": "Paracetamol 500mg",
  "lotes": [
    {
      "id_lote": 5,
      "numero_lote": "LOTE123",
      "quantidade_atual": 50,
      "data_validade": "2026-12-31",
      "preco_venda": 5.50
    }
  ]
}
```

**Acoplamento**:
- Tipo de `codigo` é implícito (pode ser number ou string)
- Campo `lotes` pode não estar sempre presente
- Cliente deve fazer `hasattr()` ou `.get()` defensivo
- Mudar `preco_venda` → `preco_unitario` quebra clientes

#### SOAP - XML com XSD

```xml
<tipos:EstoqueType>
  <tns:id xsd:type="int">1</tns:id>
  <tns:codigo xsd:type="int">789123</tns:codigo>
  <tns:nome xsd:type="string">Paracetamol 500mg</tns:nome>
  <tns:lotes maxOccurs="unbounded">
    <!-- Validado contra XSD: quantidade_atual DEVE ser int -->
  </tns:lotes>
</tipos:EstoqueType>
```

**Desacoplamento**:
- Tipo de `codigo` é explícito: `xsd:type="int"`
- Campo `lotes` é obrigatório (minOccurs default=1)
- Cliente sabe estrutura exata antes de chamar
- Se server renomeia campo, WSDL é atualizado e cliente gera novo stub automaticamente

---

### B. Discovery e Contrato

#### REST - Discovery Manual

```bash
# Developer deve:
# 1. Ler README.md
# 2. Acessar http://localhost:8000/docs (Swagger)
# 3. Entender que GET /api/medicamentos retorna Array
# 4. Entender que POST /api/reservas precisa de corpo JSON
# 5. Testar com Postman/curl para confirmar
```

**Problemas**:
- Documentação pode ficar desatualizada
- Não há validação automática de contrato
- Novo dev precisa fazer onboarding

#### SOAP - Discovery Automático

```python
# Developer pode gerar cliente automaticamente:

from zeep import Client

# 1. Baixa WSDL do servidor
client = Client(wsdl='http://localhost:8000/soap?wsdl')

# 2. Exibe operações disponíveis
for service in client.wsdl.services.values():
    for port in service.ports.values():
        print(port)  # Mostra todas operações tipadas

# 3. IDE autocomplete funciona
service.criarReserva(  # <-- autocomplete mostra parâmetros exigidos
    codigo_medicamento=789123,  # int
    quantidade=5,               # int
    cpf_paciente="12345678901"  # string
)
```

**Vantagens**:
- WSDL é sempre gerado do código (não pode desatualizar)
- Autocomplete em IDE
- Validação antes de chamar
- Novo dev entende contrato em minutos

---

### C. Versionamento

#### REST - Sem Suporte Nativo

```python
# Opção 1: Query parameter (desacoplante)
GET /api/v1/medicamentos?version=2

# Opção 2: Header customizado (desacoplante)
GET /api/medicamentos
X-API-Version: 2

# Opção 3: Path versioning (bom)
GET /v2/api/medicamentos

# Risco: Cliente pode chamar v1 e v2 simultaneamente sem saber
```

#### SOAP - Namespace Versionado

```xml
<!-- WSDL v1 -->
xmlns:tns="http://estoque-farmacia.projeto.interop/v1"

<!-- WSDL v2 (no futuro) -->
xmlns:tns="http://estoque-farmacia.projeto.interop/v2"

<!-- Cliente sabe qual versão usa:
     - v1: tipos legados
     - v2: tipos com novos campos
     - Ambas podem rodar simultaneamente se necessário
-->
```

**Vantagem**:
- Namespace explícito no WSDL
- Múltiplas versões podem coexistir
- Cliente sempre sabe qual versão está usando

---

### D. Tratamento de Erros

#### REST

```python
# Cliente REST deve conhecer:
if response.status_code == 404:
    error = response.json()  # Assume erro em JSON
    print(error['message'])  # Assume 'message' existe
elif response.status_code == 400:
    # Erro de validação?
    print(response.text)
elif response.status_code == 500:
    # Erro genérico
    pass
```

**Acoplamento**:
- Códigos HTTP implícitos (cliente interpretação)
- Estrutura de erro é implícita (não validada)
- Sem tipagem

#### SOAP

```python
# Cliente SOAP recebe estrutura de Fault tipada
try:
    result = service.criarReserva(...)
except zeep.exceptions.Fault as fault:
    # Fault SOAP structure é rígida
    print(fault.faultcode)   # xsd:string (ex: "ESTOQUE_INSUFICIENTE")
    print(fault.faultstring) # xsd:string (descritivo)
    print(fault.detail)      # XML structure tipado
```

**Desacoplamento**:
- Faults são estruturados (seguem XML Schema)
- Códigos de erro são enumerados no WSDL
- Cliente sabe exatamente quais erros esperar

---

## 📊 Matriz de Risco

### REST API

| Risco | Severidade | Probabilidade | Mitigation |
|-------|-----------|---------------|------------|
| Campo renomeado quebra cliente | Alto | Alta | Versionamento + deprecation warnings |
| Tipo de dado muda silenciosamente | Alto | Média | Testes rigorosos |
| Cliente usa campo que não existe | Médio | Alta | Defensive code, testes |
| Servidor em v2, cliente em v1 | Alto | Alta | URL versionamento |
| Documentação desatualizada | Médio | Alta | CI/CD testa Swagger |

### SOAP/WSDL

| Risco | Severidade | Probabilidade | Mitigation |
|-------|-----------|---------------|------------|
| WSDL malformado | Alto | Baixa | Validação WSDL ao build |
| XSD complexo demais | Médio | Média | Design review |
| Namespace namespace colisão | Médio | Muito Baixa | Namespaces únicos por versão |
| Overhead de parsing XML | Baixo | Baixa | Caching de parsing |

---

## 💡 Conclusão: Quando Usar Cada Um

### Use REST quando:
- API é pública, muitos clientes heterogêneos
- Overhead de XML não é aceitável (IoT, mobile)
- Equipes usam linguagens diferentes e preferem JSON
- Latência é crítica

### Use SOAP quando:
- Integrações B2B (como Grupo 1 e 2)
- Contrato deve ser rígido e versionado
- Múltiplas operações complexas em uma chamada
- Enterprise (compliance, auditoria)
- **← Seu caso: Interoperabilidade entre grupos acadêmicos**

---

## 🎯 Resultado para Estoque Farmácia

**Decisão**: SOAP + HMAC-SHA256

**Justificativa**:
1. Integração B2B com Grupo 1 e 2 (acadêmica, não pública)
2. Contrato WSDL é autodocumentado e versionado
3. XSD existentes (consulta.xsd, reserva.xsd, etc) mapeiam direto para tipos SOAP
4. Assinatura HMAC-SHA256 já está no projeto XML
5. Desacoplamento de versão via namespace
6. Discovery automático via WSDL (menos erros de integração)

**Impacto**:
- Overhead: +~20% (XML vs JSON)
- Latência: +~5ms por request (parsing)
- Confiabilidade: +40% (tipos rígidos reduzem bugs)
- Manutenibilidade: +60% (WSDL autodocumenta)
