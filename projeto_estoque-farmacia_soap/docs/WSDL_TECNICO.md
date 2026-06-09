# Documentação Técnica WSDL - Estoque Farmácia v1.0

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Namespaces](#namespaces)
3. [Tipos de Dados](#tipos-de-dados)
4. [4 Serviços SOAP](#4-serviços-soap)
5. [Exemplos de Requisição/Resposta](#exemplos-de-requisição-resposta)
6. [Estrutura do Envelope SOAP](#estrutura-do-envelope-soap)
7. [Assinatura HMAC-SHA256](#assinatura-hmac-sha256)
8. [Tratamento de Falhas (Faults)](#tratamento-de-falhas-faults)
9. [URL e Endpoints](#url-e-endpoints)

---

## Visão Geral

**WSDL**: `estoque_farmacia.wsdl`  
**Versão**: 1.0  
**Protocolo**: SOAP 1.1 (RPC/Literal)  
**Transporte**: HTTP/HTTPS  
**Assinatura**: HMAC-SHA256 no header SOAP  
**Operações**: 16 (em 4 serviços temáticos)  
**Compatibilidade**: XSDs existentes (consulta, reserva, baixa, resposta.xsd)

**Objetivo**: Substituir REST API completamente com modelo SOAP para interoperabilidade com Grupo 1 e Grupo 2.

---

## Namespaces

```xml
<!-- Namespaces padrão -->
xmlns:soap = "http://schemas.xmlsoap.org/wsdl/soap/"
xmlns:tns = "http://estoque-farmacia.projeto.interop/v1"
xmlns:tipos = "http://estoque-farmacia.projeto.interop/v1/tipos"
xmlns:xsd = "http://www.w3.org/2001/XMLSchema"
```

**Versionamento**: O namespace `/v1` permite versionamento futuro (`/v2`, `/v3`, etc)

---

## Tipos de Dados

### 1. MedicamentoType

```xml
<tipos:MedicamentoType>
    <tns:id xsd:type="int">1</tns:id>
    <tns:codigo xsd:type="int">789123</tns:codigo>
    <tns:nome xsd:type="string">Paracetamol 500mg</tns:nome>
</tipos:MedicamentoType>
```

### 2. LoteType (alinhado com resposta.xsd)

```xml
<tipos:LoteType>
    <tns:id_lote xsd:type="int">5</tns:id_lote>
    <tns:numero_lote xsd:type="string">LOTE123</tns:numero_lote>
    <tns:codigo_medicamento xsd:type="int">789123</tns:codigo_medicamento>
    <tns:quantidade_atual xsd:type="int">50</tns:quantidade_atual>
    <tns:quantidade_inicial xsd:type="int">100</tns:quantidade_inicial>
    <tns:data_validade xsd:type="date">2026-12-31</tns:data_validade>
    <tns:preco_venda xsd:type="decimal">5.50</tns:preco_venda>
</tipos:LoteType>
```

### 3. RespostaItemType (baseado em resposta.xsd)

```xml
<tipos:RespostaItemType>
    <tns:codigo_medicamento xsd:type="int">789123</tns:codigo_medicamento>
    <tns:disponivel xsd:type="int">1</tns:disponivel>  <!-- 0 ou 1 -->
    <tns:observacao xsd:type="string">Disponível em LOTE123 - Validade: 2026-12-31</tns:observacao>
</tipos:RespostaItemType>
```

### 4. ReservaType (baseado em reserva.xsd)

```xml
<tipos:ReservaType>
    <tns:id_reserva xsd:type="string">RES_001_2026_05_13</tns:id_reserva>
    <tns:id_prescricao xsd:type="int">12345</tns:id_prescricao>
    <tns:cpf_paciente xsd:type="string">12345678901</tns:cpf_paciente>
    <tns:codigo_medicamento xsd:type="int">789123</tns:codigo_medicamento>
    <tns:quantidade xsd:type="int">5</tns:quantidade>
    <tns:numero_lote xsd:type="string">LOTE123</tns:numero_lote>
    <tns:data_validade xsd:type="date">2026-12-31</tns:data_validade>
    <tns:preco xsd:type="decimal">27.50</tns:preco>
    <tns:status xsd:type="string">ativa</tns:status>
    <tns:data_criacao xsd:type="dateTime">2026-05-13T10:30:00</tns:data_criacao>
</tipos:ReservaType>
```

### 5. BaixaType (baseado em baixa.xsd)

```xml
<tipos:BaixaType>
    <tns:id_baixa xsd:type="string">BAIXA_001_2026_05_13</tns:id_baixa>
    <tns:id_prescricao xsd:type="int">12345</tns:id_prescricao>
    <tns:cpf_paciente xsd:type="string">12345678901</tns:cpf_paciente>
    <tns:codigo_medicamento xsd:type="int">789123</tns:codigo_medicamento>
    <tns:quantidade xsd:type="int">5</tns:quantidade>
    <tns:numero_lote xsd:type="string">LOTE123</tns:numero_lote>
    <tns:motivo xsd:type="string">Dispensação ao paciente</tns:motivo>
    <tns:data_uso xsd:type="int">130526</tns:data_uso>  <!-- DDMMYY -->
    <tns:quantidade_restante xsd:type="int">45</tns:quantidade_restante>
    <tns:timestamp xsd:type="dateTime">2026-05-13T11:15:00</tns:timestamp>
</tipos:BaixaType>
```

### 6. EstoqueType (resposta de estoque)

```xml
<tipos:EstoqueType>
    <tns:codigo_medicamento xsd:type="int">789123</tns:codigo_medicamento>
    <tns:nome_medicamento xsd:type="string">Paracetamol 500mg</tns:nome_medicamento>
    <tns:quantidade_total xsd:type="int">150</tns:quantidade_total>
    <tns:lotes maxOccurs="unbounded">
        <!-- Lista de LoteType -->
    </tns:lotes>
</tipos:EstoqueType>
```

### 7. AssinaturaType (HMAC-SHA256)

```xml
<tipos:AssinaturaType>
    <tns:hash xsd:type="string">a1b2c3d4e5f6...</tns:hash>
    <tns:timestamp xsd:type="dateTime">2026-05-13T10:30:00Z</tns:timestamp>
    <tns:grupo_origem xsd:type="string">GRUPO_3</tns:grupo_origem>
    <tns:algoritmo xsd:type="string">HMAC-SHA256</tns:algoritmo>
</tipos:AssinaturaType>
```

### 8. ErroType (Fault)

```xml
<tipos:ErroType>
    <tns:codigo xsd:type="string">MEDICAMENTO_NAO_ENCONTRADO</tns:codigo>
    <tns:mensagem xsd:type="string">Medicamento 999 não existe</tns:mensagem>
    <tns:detalhes xsd:type="string">Stack trace ou contexto adicional</tns:detalhes>
</tipos:ErroType>
```

### 9. ResultadoType (status genérico)

```xml
<tipos:ResultadoType>
    <tns:success xsd:type="boolean">true</tns:success>
    <tns:mensagem xsd:type="string">Operação realizada com sucesso</tns:mensagem>
    <tns:timestamp xsd:type="dateTime">2026-05-13T10:30:00</tns:timestamp>
</tipos:ResultadoType>
```

---

## 4 Serviços SOAP

### Serviço 1: ServiceMedicamentos (3 operações)

**Responsabilidade**: Gerenciar dados de medicamentos (CRUD de leitura + sincronização)

#### Operação 1.1: listarMedicamentos
- **Entrada**: Nenhuma
- **Saída**: Lista de `MedicamentoType[]`
- **Exceção**: ErroFault (erro BD)
- **Caso de uso**: Listar todos os medicamentos cadastrados

```xml
<!-- Requisição -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:listarMedicamentos/>
  </soap:Body>
</soap:Envelope>

<!-- Resposta -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:listarMedicamentosResponse>
      <medicamentos>
        <id>1</id>
        <codigo>789123</codigo>
        <nome>Paracetamol 500mg</nome>
      </medicamentos>
      <medicamentos>
        <id>2</id>
        <codigo>789124</codigo>
        <nome>Ibuprofen 400mg</nome>
      </medicamentos>
    </tns:listarMedicamentosResponse>
  </soap:Body>
</soap:Envelope>
```

#### Operação 1.2: obterMedicamento
- **Entrada**: `codigo` (int)
- **Saída**: `MedicamentoType`
- **Exceção**: ErroFault (não encontrado, erro BD)
- **Caso de uso**: Buscar medicamento específico por código

```xml
<!-- Requisição -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:obterMedicamento>
      <codigo>789123</codigo>
    </tns:obterMedicamento>
  </soap:Body>
</soap:Envelope>

<!-- Resposta -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:obterMedicamentoResponse>
      <medicamento>
        <id>1</id>
        <codigo>789123</codigo>
        <nome>Paracetamol 500mg</nome>
      </medicamento>
    </tns:obterMedicamentoResponse>
  </soap:Body>
</soap:Envelope>
```

#### Operação 1.3: sincronizarMedicamentos
- **Entrada**: `arquivo_xml` (string), `grupo_origem` (string)
- **Saída**: `ResultadoType`
- **Exceção**: ErroFault (XML inválido, erro de processamento)
- **Caso de uso**: Receber atualização de medicamentos do Grupo 1 ou 2

---

### Serviço 2: ServiceEstoque (5 operações)

**Responsabilidade**: Gerenciar estoque, lotes e disponibilidade

#### Operação 2.1: obterEstoque
- **Entrada**: `codigo_medicamento` (int)
- **Saída**: `EstoqueType`
- **Exceção**: ErroFault (não encontrado)
- **Caso de uso**: Ver estoque total + detalhes de lotes

#### Operação 2.2: listarLotes
- **Entrada**: `codigo_medicamento` (int)
- **Saída**: Lista de `LoteType[]` (ordenado por FEFO)
- **Exceção**: ErroFault
- **Caso de uso**: Listar todos os lotes de um medicamento

#### Operação 2.3: consultarDisponibilidade ⭐
- **Entrada**: `codigo_medicamento`, `quantidade`, `cpf_paciente`
- **Saída**: `RespostaType` (baseado em resposta.xsd)
- **Exceção**: ErroFault
- **Caso de uso**: Verificar se há disponibilidade (usado pelo Grupo 2)
- **Alinhamento**: Direto com consumo dos XML de consulta

```xml
<!-- Requisição (equivalente a consulta.xml do Grupo 2) -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:consultarDisponibilidade>
      <codigo_medicamento>789123</codigo_medicamento>
      <quantidade>5</quantidade>
      <cpf_paciente>12345678901</cpf_paciente>
    </tns:consultarDisponibilidade>
  </soap:Body>
</soap:Envelope>

<!-- Resposta (estrutura de resposta.xsd) -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <tns:assinatura>
      <hash>a1b2c3d4...</hash>
      <timestamp>2026-05-13T10:30:00Z</timestamp>
      <grupo_origem>GRUPO_3</grupo_origem>
    </tns:assinatura>
  </soap:Header>
  <soap:Body>
    <tns:consultarDisponibilidadeResponse>
      <resposta>
        <respostas>
          <codigo_medicamento>789123</codigo_medicamento>
          <disponivel>1</disponivel>
          <observacao>Disponível em LOTE123 - Validade: 2026-12-31</observacao>
        </respostas>
      </resposta>
    </tns:consultarDisponibilidadeResponse>
  </soap:Body>
</soap:Envelope>
```

#### Operação 2.4: verificarReservas
- **Entrada**: `codigo_medicamento` (int)
- **Saída**: Lista de `ReservaType[]`
- **Exceção**: ErroFault
- **Caso de uso**: Listar reservas ativas para um medicamento

#### Operação 2.5: gerarAlerta
- **Entrada**: `codigo_medicamento`, `quantidade_minima`
- **Saída**: `ResultadoType`
- **Exceção**: ErroFault
- **Caso de uso**: Gerar alerta se estoque < quantidade mínima

---

### Serviço 3: ServiceTransacoes (5 operações)

**Responsabilidade**: Gerenciar reservas e baixas (transações críticas)

#### Operação 3.1: criarReserva ⭐
- **Entrada**: `codigo_medicamento`, `quantidade`, `cpf_paciente`
- **Saída**: `ReservaType` (com lote selecionado via FEFO)
- **Exceção**: ErroFault (medicamento não existe, estoque insuficiente)
- **Caso de uso**: Criar reserva automática (FEFO)

```xml
<!-- Requisição -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:criarReserva>
      <codigo_medicamento>789123</codigo_medicamento>
      <quantidade>5</quantidade>
      <cpf_paciente>12345678901</cpf_paciente>
    </tns:criarReserva>
  </soap:Body>
</soap:Envelope>

<!-- Resposta -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:criarReservaResponse>
      <reserva>
        <id_reserva>RES_001_2026_05_13</id_reserva>
        <numero_lote>LOTE123</numero_lote>
        <data_validade>2026-12-31</data_validade>
        <preco>27.50</preco>
        <!-- ...mais campos... -->
      </reserva>
    </tns:criarReservaResponse>
  </soap:Body>
</soap:Envelope>
```

#### Operação 3.2: obterReserva
- **Entrada**: `id_reserva`
- **Saída**: `ReservaType`
- **Exceção**: ErroFault (não encontrada)

#### Operação 3.3: cancelarReserva
- **Entrada**: `id_reserva`
- **Saída**: `ResultadoType`
- **Exceção**: ErroFault (não encontrada, já cancelada)

#### Operação 3.4: registrarBaixa ⭐
- **Entrada**: `codigo_medicamento`, `quantidade`, `numero_lote`, `cpf_paciente`, `motivo` (opt)
- **Saída**: `BaixaType`
- **Exceção**: ErroFault (lote não existe, quantidade insuficiente)
- **Caso de uso**: Dar baixa em estoque (reduz quantidade)

```xml
<!-- Requisição (equivalente a baixa.xml do Grupo 2) -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:registrarBaixa>
      <codigo_medicamento>789123</codigo_medicamento>
      <quantidade>5</quantidade>
      <numero_lote>LOTE123</numero_lote>
      <cpf_paciente>12345678901</cpf_paciente>
      <motivo>Dispensação ao paciente</motivo>
    </tns:registrarBaixa>
  </soap:Body>
</soap:Envelope>

<!-- Resposta -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:registrarBaixaResponse>
      <baixa>
        <id_baixa>BAIXA_001_2026_05_13</id_baixa>
        <quantidade_restante>45</quantidade_restante>
        <!-- ...mais campos... -->
      </baixa>
    </tns:registrarBaixaResponse>
  </soap:Body>
</soap:Envelope>
```

#### Operação 3.5: listarBaixas
- **Entrada**: `data_inicio` (opt), `data_fim` (opt)
- **Saída**: Lista de `BaixaType[]`
- **Exceção**: ErroFault
- **Caso de uso**: Relatório de baixas em período

---

### Serviço 4: ServiceIntegracao (3 operações)

**Responsabilidade**: Integração com Grupo 1 (consolidação) e Grupo 2 (status financeiro)

#### Operação 4.1: gerarRelatorioConsumo
- **Entrada**: `data_inicio` (opt), `data_fim` (opt)
- **Saída**: `arquivo_xml` (string XML assinado), `ResultadoType`
- **Exceção**: ErroFault (erro ao gerar)
- **Caso de uso**: G3 → G1 (relatório de consumo para consolidação)
- **Alinhamento**: Gera XML consumo.xsd assinado com HMAC-SHA256

```xml
<!-- Resposta com XML consumo encapsulado -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:gerarRelatorioConsumoResponse>
      <arquivo_xml>
        &lt;?xml version="1.0"?&gt;
        &lt;consumo&gt;
          &lt;header&gt;...&lt;/header&gt;
          &lt;itens&gt;...&lt;/itens&gt;
          &lt;assinatura&gt;...&lt;/assinatura&gt;
        &lt;/consumo&gt;
      </arquivo_xml>
      <resultado>
        <success>true</success>
        <timestamp>2026-05-13T10:30:00</timestamp>
      </resultado>
    </tns:gerarRelatorioConsumoResponse>
  </soap:Body>
</soap:Envelope>
```

#### Operação 4.2: consultarStatusPaciente
- **Entrada**: `cpf_paciente`
- **Saída**: `status_financeiro`, `permite_atendimento`
- **Exceção**: ErroFault (CPF não encontrado, erro BD)
- **Caso de uso**: Verificar status financeiro do paciente (cache de dados do G1)

#### Operação 4.3: sincronizarStatusFinanceiro
- **Entrada**: `arquivo_xml` (string XML de status), `grupo_origem`
- **Saída**: `ResultadoType`
- **Exceção**: ErroFault (XML inválido, erro ao processar)
- **Caso de uso**: Receber status_financeiro.xml do Grupo 1, validar XSD, armazenar

---

## Estrutura do Envelope SOAP

### Requisição SOAP com Header (Autenticação + Assinatura)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1"
    xmlns:tipos="http://estoque-farmacia.projeto.interop/v1/tipos">
  
  <!-- HEADER: Autenticação e Assinatura HMAC-SHA256 -->
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4e5f6g7h8i9j0...</tns:hash>
      <tns:timestamp>2026-05-13T10:30:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  
  <!-- BODY: Operação e Parâmetros -->
  <soap:Body>
    <tns:criarReserva>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>5</tns:quantidade>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
    </tns:criarReserva>
  </soap:Body>
  
</soap:Envelope>
```

### Resposta SOAP com Header de Assinatura

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1"
    xmlns:tipos="http://estoque-farmacia.projeto.interop/v1/tipos">
  
  <!-- HEADER: Assinatura da resposta -->
  <soap:Header>
    <tns:assinatura>
      <tns:hash>z9y8x7w6v5u4t3s2r1q0...</tns:hash>
      <tns:timestamp>2026-05-13T10:30:15Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_3</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:assinatura>
  </soap:Header>
  
  <!-- BODY: Resultado tipado -->
  <soap:Body>
    <tns:criarReservaResponse>
      <reserva>
        <tns:id_reserva>RES_001_2026_05_13</tns:id_reserva>
        <tns:id_prescricao>12345</tns:id_prescricao>
        <tns:cpf_paciente>12345678901</tns:cpf_paciente>
        <tns:codigo_medicamento>789123</tns:codigo_medicamento>
        <tns:quantidade>5</tns:quantidade>
        <tns:numero_lote>LOTE123</tns:numero_lote>
        <tns:data_validade>2026-12-31</tns:data_validade>
        <tns:preco>27.50</tns:preco>
        <tns:status>ativa</tns:status>
        <tns:data_criacao>2026-05-13T10:30:00</tns:data_criacao>
      </reserva>
    </tns:criarReservaResponse>
  </soap:Body>
  
</soap:Envelope>
```

---

## Assinatura HMAC-SHA256

**Localização**: `soap:Header/tns:autenticacao/tns:hash` (requisição) ou `soap:Header/tns:assinatura/tns:hash` (resposta)

**Algoritmo**: HMAC-SHA256

**Chave Secreta**: `chave_secreta_compartilhada_entre_grupos_2026` (conforme projeto XML existente)

**Cálculo**:
```python
import hashlib
import hmac

# Serializar XML do BODY sem assinatura
conteudo = "<tns:criarReserva>...</tns:criarReserva>"

# Calcular HMAC-SHA256
hash_valor = hmac.new(
    b"chave_secreta_compartilhada_entre_grupos_2026",
    conteudo.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Resultado: "a1b2c3d4e5f6..." (64 caracteres)
```

**Validação**: Servidor recebe requisição, calcula hash, compara com header. Se diferentes → reject com Fault.

---

## Tratamento de Falhas (Faults)

### SOAP Fault Padrão

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <soap:Fault>
      <faultcode>MEDICAMENTO_NAO_ENCONTRADO</faultcode>
      <faultstring>Medicamento 999 não existe no banco de dados</faultstring>
      <detail>
        <erro>Nenhum registro encontrado para código: 999</erro>
      </detail>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>
```

### Códigos de Erro Comuns

| Código | Mensagem | Detalhes |
|--------|----------|----------|
| `MEDICAMENTO_NAO_ENCONTRADO` | Medicamento não existe | Código informado não está cadastrado |
| `ESTOQUE_INSUFICIENTE` | Estoque insuficiente | Quantidade solicitada > quantidade disponível |
| `LOTE_NAO_ENCONTRADO` | Lote não encontrado | Número de lote inválido |
| `RESERVA_NAO_ENCONTRADA` | Reserva não encontrada | ID de reserva não existe |
| `CPF_INVALIDO` | CPF inválido | CPF não tem 11 dígitos ou é inválido |
| `ASSINATURA_INVALIDA` | Assinatura inválida | HMAC-SHA256 não confere |
| `XML_INVALIDO` | XML de sincronização inválido | Não valida contra XSD esperado |
| `ERRO_BANCO_DADOS` | Erro ao acessar banco de dados | Erro interno de conexão/query |
| `OPERACAO_NAO_AUTORIZADA` | Operação não autorizada | Grupo não tem permissão |
| `TIMEOUT` | Timeout na operação | Operação demorou mais que tempo máximo |

---

## URL e Endpoints

### Produção

```
URL Base: http://estoque-farmacia.servidor.com/soap
WSDL: http://estoque-farmacia.servidor.com/soap?wsdl
```

### Desenvolvimento Local

```
URL Base: http://localhost:8000/soap
WSDL: http://localhost:8000/soap?wsdl
```

### Protocolo

- **HTTP Method**: POST
- **Content-Type**: `text/xml; charset=utf-8`
- **SOAPAction Header**: Nome da operação (ex: `criarReserva`)

---

## Fluxos de Integração

### Fluxo 1: Consulta de Disponibilidade (G2 → G3)

```
1. Grupo 2 envia SOAP request: consultarDisponibilidade()
2. G3 recebe, valida header (assinatura HMAC-SHA256)
3. G3 executa lógica (busca estoque FEFO)
4. G3 retorna SOAP response: RespostaType (baseado em resposta.xsd)
5. Grupo 2 parseia resposta, exibe ao usuário
```

**Equivalência com XML direto**:
- Antes: XML consulta → arquivo → processador → XML resposta → arquivo
- Agora: SOAP request → handler SOAP → lógica → SOAP response

### Fluxo 2: Consolidação de Consumo (G3 → G1)

```
1. G3 invoca: gerarRelatorioConsumo(data_inicio, data_fim)
2. G3 coleta dados de consumo do BD
3. G3 gera XML consumo (formato consumo.xsd)
4. G3 assina XML com HMAC-SHA256
5. G3 encapsula XML no SOAP body
6. G3 envia SOAP response com arquivo_xml encapsulado
7. Grupo 1 recebe, extrai XML, processa, armazena
```

### Fluxo 3: Sincronização de Status Financeiro (G1 → G3)

```
1. Grupo 1 invoca: sincronizarStatusFinanceiro(arquivo_xml, "GRUPO_1")
2. G3 recebe XML status_financeiro encapsulado no SOAP
3. G3 valida XSD (status_financeiro.xsd)
4. G3 valida assinatura HMAC-SHA256
5. G3 armazena dados em cache (CPF → status_financeiro)
6. G3 retorna ResultadoType (success=true)
7. Operação consultarStatusPaciente() agora retorna dados cached
```

---

## Exemplos de Teste com curl

### Teste 1: listarMedicamentos

```bash
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: listarMedicamentos" \
  -d '@listar_medicamentos_request.xml'
```

### Teste 2: consultarDisponibilidade (com assinatura)

```bash
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: consultarDisponibilidade" \
  -d '@consultar_disponibilidade_request.xml'
```

### Teste 3: criarReserva

```bash
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: criarReserva" \
  -d '@criar_reserva_request.xml'
```

---

## Referências

- **WSDL**: `src/wsdl/estoque_farmacia.wsdl`
- **XSDs**: `xsds/consulta.xsd`, `xsds/reserva.xsd`, `xsds/baixa.xsd`, etc
- **Tipos SOAP**: `src/soap/types.py`
- **Envelope**: `src/soap/handlers/envelope.py`
- **Servidor SOAP**: `src/soap/server.py` (implementação próxima)
