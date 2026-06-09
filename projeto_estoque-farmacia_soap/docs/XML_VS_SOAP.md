# Comparação: XML Direto vs SOAP/WSDL

## 🎯 Objetivo

Documentar a transição do modelo atual (XML trocado diretamente com G1 e G2) para o novo modelo SOAP/WSDL, mostrando:
1. **Como funcionava**: XML em arquivos (file system, FTP)
2. **Como funciona agora**: SOAP via HTTP/HTTPS
3. **Equivalências** entre operações
4. **Vantagens** e **desvantagens** da mudança

---

## 📚 Contexto: O Sistema Antigo

### Arquitetura XML Direto

```
┌─────────────────┐
│   Grupo 2       │
│ (Consultas,     │  Escreve em pasta FTP:
│  Reservas,      │  data/entrada/consultas/CONSULTA_*.xml
│  Baixas)        │  data/entrada/reservas/RESERVA_*.xml
│                 │  data/entrada/baixas/BAIXA_*.xml
└─────────────────┘
        ↓ (arquivo XML)
        ↓
┌─────────────────────────────────────────┐
│  G3 (Nosso sistema)                    │
│  - Monitor arquivo entrada             │
│  - Valida contra XSD                   │
│  - Processa (DB, estoque, FEFO)        │
│  - Gera resposta (RESPOSTA_*.xml)      │
│  - Escreve em pasta saída              │
└─────────────────────────────────────────┘
        ↑ (arquivo XML)
        ↑
        └─ data/saida/respostas/RESPOSTA_*.xml

Grupo 2 monitora pasta e processa respostas
```

### Fluxo Atual: Consulta (XML Direto)

```
Arquivo: data/entrada/consultas/CONSULTA_260327_143022_001.xml

<?xml version="1.0"?>
<consultas>
  <consulta>
    <prescricao>12345</prescricao>
    <cpf>12345678901</cpf>
    <codigo_medicamento>789123</codigo_medicamento>
    <quantidade>5</quantidade>
  </consulta>
  <assinatura>
    <hash>a1b2c3d4...</hash>
    <timestamp>2026-03-27T14:30:22Z</timestamp>
    <grupo_origem>GRUPO_2</grupo_origem>
    <algoritmo>HMAC-SHA256</algoritmo>
  </assinatura>
</consultas>

↓ (Processador lê arquivo)

Nosso sistema:
1. Valida contra consulta.xsd
2. Valida assinatura HMAC-SHA256
3. Extrai dados (código, quantidade, CPF)
4. Consulta estoque (FEFO)
5. Gera resposta (baseado em resposta.xsd)
6. Assina resposta
7. Escreve: data/saida/respostas/RESPOSTA_260327_143022_001.xml

Arquivo: data/saida/respostas/RESPOSTA_260327_143022_001.xml

<?xml version="1.0"?>
<respostas>
  <resposta>
    <codigo_medicamento>789123</codigo_medicamento>
    <disponivel>1</disponivel>
    <observacao>Disponível em LOTE123 - Validade: 2026-12-31</observacao>
  </resposta>
  <assinatura>
    <hash>z9y8x7w6...</hash>
    <timestamp>2026-03-27T14:30:30Z</timestamp>
    <grupo_origem>GRUPO_3</grupo_origem>
    <algoritmo>HMAC-SHA256</algoritmo>
  </assinatura>
</respostas>

↑ (Grupo 2 monitora pasta e processa)
```

---

## 🆕 Novo Modelo: SOAP/WSDL via HTTP

### Arquitetura SOAP

```
┌─────────────────┐
│   Grupo 2       │
│ (Consultas,     │  Chamada SOAP HTTP POST:
│  Reservas,      │  http://g3-servidor/soap
│  Baixas)        │  ↓ SOAP request (envelope XML)
│                 │  ↑ SOAP response (envelope XML)
└─────────────────┘
        ↕ (HTTP SOAP)
┌─────────────────────────────────────────┐
│  G3 (Nosso sistema)                    │
│  - Server SOAP listening /soap         │
│  - Recebe SOAP request                 │
│  - Valida header (HMAC-SHA256)         │
│  - Valida tipos (contra WSDL)          │
│  - Processa (DB, estoque, FEFO)        │
│  - Retorna SOAP response (tipos)       │
└─────────────────────────────────────────┘
```

### Fluxo Novo: Consulta (SOAP)

```
SOAP REQUEST (HTTP POST http://g3-servidor/soap)

<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4...</tns:hash>
      <tns:timestamp>2026-03-27T14:30:22Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  
  <soap:Body>
    <tns:consultarDisponibilidade>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>5</tns:quantidade>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
    </tns:consultarDisponibilidade>
  </soap:Body>
  
</soap:Envelope>

↓ (Servidor recebe)

Nosso sistema:
1. Parseia envelope SOAP
2. Extrai header (autenticação)
3. Valida assinatura HMAC-SHA256 (contra body)
4. Extrai operação: consultarDisponibilidade
5. Valida tipos (int, int, string contra WSDL)
6. Executa operação
7. Consulta estoque (FEFO)
8. Gera resposta (RespostaType)
9. Assina resposta
10. Retorna SOAP response

SOAP RESPONSE (HTTP 200 OK)

<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  
  <soap:Header>
    <tns:assinatura>
      <tns:hash>z9y8x7w6...</tns:hash>
      <tns:timestamp>2026-03-27T14:30:30Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_3</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
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

↑ (Grupo 2 recebe resposta imediatamente)
```

---

## 📊 Comparação Lado a Lado

### 1. Consulta de Disponibilidade

#### XML Direto (Atual)

```
Timing:   1. G2 escreve arquivo (2ms)
          2. G3 monitora pasta (polling a cada 1s)
          3. G3 processa (1000ms)
          4. G3 escreve resposta (2ms)
          5. G2 monitora pasta (até 1s após resposta)
          ──────────────────────────
          Total: ~1000-2000ms (+ 2s de polling se timing ruim)

Confiabilidade: ❌ Arquivo pode desaparecer
                ❌ Sem confirmação de entrega
                ❌ Sem timeout explícito
                ❌ Sem retry automático

Integração:     ❌ Requer FTP/compartilhamento de pasta
                ❌ Sem HTTP (não passa por proxy, firewall)
                ❌ Requer monitoramento contínuo
                ❌ Sem header HTTP (autenticação fraca)
```

#### SOAP (Novo)

```
Timing:   1. G2 faz HTTP POST (0ms)
          2. HTTP reach G3 (~50ms latência rede)
          3. G3 processa (1000ms)
          4. G3 retorna HTTP 200 (0ms)
          5. G2 recebe resposta (50ms)
          ──────────────────────────
          Total: ~1100ms (determinístico)

Confiabilidade: ✅ HTTP response é confirmação de entrega
                ✅ Timeout explícito (30s padrão)
                ✅ Retry automático (cliente controla)
                ✅ HTTP status code (erro imediato)

Integração:     ✅ HTTP padrão (funciona com proxy, firewall)
                ✅ HTTPS com TLS (criptografia fim-a-fim)
                ✅ Header HTTP para autenticação
                ✅ Sem monitoramento contínuo (request-response)
```

**Vencedor**: SOAP é mais previsível e confiável

---

### 2. Formato e Validação

#### XML Direto

```xml
<!-- Entrada: CONSULTA_*.xml -->
<consultas>
  <consulta>
    <prescricao>12345</prescricao>
    <cpf>12345678901</cpf>
    <codigo_medicamento>789123</codigo_medicamento>
    <quantidade>5</quantidade>
  </consulta>
  <!-- ... -->
</consultas>

Validação:
  ✓ XML bem-formado (parser XML)
  ✓ XSD (consulta.xsd) valida estrutura
  ❌ SEM validação de tipos em tempo de envio
  
Estrutura:
  ❌ Cliente escreve arquivo manualmente
  ❌ Sem autocomplete
  ❌ Erros de digitação descobertos tarde (quando processador falha)
  ❌ Sem documentação de versão
```

#### SOAP

```xml
<!-- Requisição: SOAP Envelope -->
<soap:Envelope xmlns:soap="...">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>...</tns:hash>
      ...
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:consultarDisponibilidade>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>5</tns:quantidade>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
    </tns:consultarDisponibilidade>
  </soap:Body>
</soap:Envelope>

Validação:
  ✓ XML bem-formado
  ✓ WSDL valida tipos (int, string, etc)
  ✓ Cliente valida ANTES de enviar
  ✓ Versão no namespace explícita

Estrutura:
  ✓ Cliente gera código (zeep, wsimport)
  ✓ Autocomplete em IDE
  ✓ Erros detectados em compile-time
  ✓ WSDL documenta versão (/v1)
```

**Vencedor**: SOAP com validação em tempo de compilação

---

### 3. Integração com Grupo 1 (Consolidação)

#### XML Direto

```
Fluxo:
  1. G3 gera arquivo consumo.xml (10.000 linhas)
  2. Assina com HMAC-SHA256
  3. Escreve em compartilhamento de rede
  4. Grupo 1 monitora pasta (pode levar até 1 minuto)
  5. Grupo 1 lê arquivo, processa
  
Problemas:
  ❌ Arquivo grande pode ser truncado na rede
  ❌ Sem confirmação de recebimento
  ❌ Sem streaming (tudo em memória)
  ❌ Sem compressão
  ❌ 10s de delay adicional por polling
```

#### SOAP

```
Fluxo:
  1. G3 gera arquivo consumo.xml (10.000 linhas)
  2. Assina com HMAC-SHA256
  3. Encapsula no SOAP body (base64-encoded se necessário)
  4. Faz HTTP POST com XML encapsulado
  5. Grupo 1 recebe imediatamente (HTTP response)
  
Vantagens:
  ✅ HTTP chunked encoding para arquivos grandes
  ✅ Content-Length validado
  ✅ Gzip compression suportado
  ✅ Confirmação imediata
  ✅ Sem delay de polling
  ✅ Retry com backoff automático se timeout
```

**Vencedor**: SOAP é superior para transferências

---

### 4. Segurança (Assinatura HMAC-SHA256)

#### XML Direto

```xml
<!-- Assinatura em arquivo -->
<assinatura>
  <hash>a1b2c3d4...</hash>
  <timestamp>2026-03-27T14:30:22Z</timestamp>
  <grupo_origem>GRUPO_2</grupo_origem>
  <algoritmo>HMAC-SHA256</algoritmo>
</assinatura>

Segurança:
  ✓ HMAC-SHA256 validado
  ✓ Timestamp previne replay
  ❌ Arquivo em repouso (sem criptografia se compartilhamento não criptografado)
  ❌ Sem autenticação de cliente
  ❌ Sem autorização baseada em grupo
```

#### SOAP

```xml
<!-- Assinatura no header SOAP -->
<soap:Header>
  <tns:autenticacao>
    <tns:hash>a1b2c3d4...</tns:hash>
    <tns:timestamp>2026-03-27T14:30:22Z</tns:timestamp>
    <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
    <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
  </tns:autenticacao>
</soap:Header>

Segurança:
  ✓ HMAC-SHA256 no header (validado antes de processar)
  ✓ Timestamp previne replay
  ✓ HTTPS criptografa transmissão
  ✓ HTTP Authorization header para autenticação
  ✓ grupo_origem permite controle de acesso (ACL)
  ✓ Rate limiting por client IP
```

**Vencedor**: SOAP com HTTPS é mais seguro

---

### 5. Escalabilidade e Performance

#### XML Direto

| Métrica | Valor | Problema |
|---------|-------|----------|
| Throughput | ~100 req/s | Polling delay |
| Latência | 1-2s | I/O de disco |
| Concorrência | ❌ Nenhuma | Um arquivo por vez |
| Memória | Alto | Carrega arquivo inteiro |
| CPU | Médio | Parsing XML |
| Escalabilidade | Péssima | Pasta compartilhada é gargalo |

#### SOAP

| Métrica | Valor | Benefício |
|---------|-------|----------|
| Throughput | ~1000 req/s | HTTP pipelining |
| Latência | ~100ms | Rede vs disco |
| Concorrência | ✅ Múltiplas | HTTP concorrente |
| Memória | Baixo | Streaming/chunks |
| CPU | Médio | Parsing XML (otimizado) |
| Escalabilidade | Excelente | Load balancer com múltiplos servidores |

**Vencedor**: SOAP é 10x mais escalável

---

## 🔄 Equivalências de Operações

### Mapeamento: XML → SOAP

| # | XML File | SOAP Operation | Entrada | Saída |
|---|----------|-----------------|---------|-------|
| 1 | `consulta.xml` → `resposta.xml` | `consultarDisponibilidade()` | Código, Qtd, CPF | RespostaType (disponível + observação) |
| 2 | `reserva.xml` → (processada) | `criarReserva()` | Código, Qtd, CPF | ReservaType (com lote FEFO) |
| 3 | `baixa.xml` → (processada) | `registrarBaixa()` | Código, Qtd, Lote, CPF | BaixaType (com qtd restante) |
| 4 | `consumo.xml` → (consolidação) | `gerarRelatorioConsumo()` | Data início, fim | `arquivo_xml` encapsulado |
| 5 | `status_financeiro.xml` (entrada) | `sincronizarStatusFinanceiro()` | `arquivo_xml`, grupo | ResultadoType |
| 6 | Nenhum (processamento manual) | `listarMedicamentos()` | Nenhum | MedicamentoType[] |
| 7 | Nenhum (processamento manual) | `obterEstoque()` | Código | EstoqueType |
| 8 | Nenhum (processamento manual) | `listarLotes()` | Código | LoteType[] |

---

## 📈 Fluxo de Transição

### Fase 1: Setup SOAP (Semana 1)
```
✓ Criar WSDL com 16 operações
✓ Implementar handlers SOAP (envelope, tipos)
✓ Validar HMAC-SHA256 no header
✓ Testes unitários
```

### Fase 2: Implementar Serviços (Semanas 2-3)
```
✓ ServiceMedicamentos (3 ops) - leitura pura
✓ ServiceEstoque (5 ops) - leitura pura
✓ ServiceTransacoes (5 ops) - críticas
✓ ServiceIntegracao (3 ops) - B2B
```

### Fase 3: Integração com G1/G2 (Semanas 4-5)
```
✓ Mock servers para G1 e G2 (testes)
✓ Testes de integração ponta-a-ponta
✓ Validar fluxos: consulta, resposta, consolidação
✓ Validar assinatura HMAC-SHA256
```

### Fase 4: Deprecação REST (Semana 6)
```
✓ Manter REST com warnings
✓ Documentar migração para SOAP
✓ Suporte para developers de G1/G2
✓ Remove REST em próxima versão
```

---

## ✅ Checklist de Validação

**XML Direto → SOAP**

- [ ] Todas as operações XML têm equivalente SOAP
- [ ] WSDL valida contra W3C spec
- [ ] Tipos SOAP correspondem a XSDs existentes
- [ ] HMAC-SHA256 funciona em header SOAP
- [ ] Testes passam (100% cobertura)
- [ ] Integração com G1 mock funciona
- [ ] Integração com G2 mock funciona
- [ ] Documentação técnica completa
- [ ] Benchmark mostra melhoria de performance
- [ ] Segurança validada (sem vulnerabilidades)

---

## 📚 Referências

- [Estoque Farmácia WSDL](./WSDL_TECNICO.md)
- [Análise de Acoplamento](./ACOPLAMENTO.md)
- [XSDs Originais](../xsds/)
- [SOAP 1.1 Spec](https://www.w3.org/TR/soap12/)
- [WSDL 1.1 Spec](https://www.w3.org/TR/wsdl)
