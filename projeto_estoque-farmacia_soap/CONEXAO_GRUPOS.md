# 🌐 Conexão com Outros Grupos (G1 & G2)

## 📋 Endpoints de Integração

### ✅ Seu Servidor (G3) - URL BASE
```
http://seu-servidor:8000/soap
```

---

## 🔄 G2 → G3 (Grupo 2 faz requisições para você)

### Operação: consultarDisponibilidade ⭐
**Usado por**: Grupo 2 (Consulta paciente)  
**Endpoint**: POST /soap  
**Frequência**: On-demand (cada consulta de paciente)

#### Request (G2 envia)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>HASH_SHA256_64_CHARS</tns:hash>
      <tns:timestamp>2026-06-09T10:30:00Z</tns:timestamp>
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
```

#### Response (você retorna)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:assinatura>
      <tns:hash>HASH_RESPOSTA</tns:hash>
      <tns:timestamp>2026-06-09T10:30:01Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_3</tns:grupo_origem>
    </tns:assinatura>
  </soap:Header>
  <soap:Body>
    <tns:consultarDisponibilidadeResponse>
      <tns:respostas>
        <tns:resposta>
          <tns:codigo_medicamento>789123</tns:codigo_medicamento>
          <tns:quantidade_disponivel>10</tns:quantidade_disponivel>
          <tns:disponivel>1</tns:disponivel>  <!-- 0 ou 1 -->
        </tns:resposta>
      </tns:respostas>
    </tns:consultarDisponibilidadeResponse>
  </soap:Body>
</soap:Envelope>
```

#### Fluxo no Código
```python
# No seu app.py linha 150
# Quando G2 chama consultarDisponibilidade:
1. Valida HMAC (falha → SOAP Fault)
2. Extrai parametros
3. Chama ServiceEstoque.consultar_disponibilidade()
4. Retorna com hash assinado
```

---

## 📤 G3 → G1 (você envia para Grupo 1)

### Operação: gerarRelatorioConsumo ⭐
**Usado por**: Seu sistema (consolidação)  
**Endpoint G1**: http://g1-servidor:8000/soap  
**Frequência**: Diária (ou sob demanda)

#### Request (você envia)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>HASH_SHA256_ASSINADO</tns:hash>
      <tns:timestamp>2026-06-09T23:59:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_3</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:gerarRelatorioConsumo>
      <tns:data_inicio>2026-06-01</tns:inicio>
      <tns:data_fim>2026-06-09</tns:data_fim>
    </tns:gerarRelatorioConsumo>
  </soap:Body>
</soap:Envelope>
```

#### Response (G1 retorna)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:gerarRelatorioConsumoResponse>
      <tns:resultado>
        <tns:success>true</tns:success>
        <tns:mensagem>Relatório recebido e processado</tns:mensagem>
      </tns:resultado>
    </tns:gerarRelatorioConsumoResponse>
  </soap:Body>
</soap:Envelope>
```

#### Implementar Chamada Automática
```python
# Adicionar em seu scheduler (APScheduler ou Celery)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=23, minute=59)  # Diária às 23:59
def enviar_relatorio_diario():
    """Enviar consolidação para G1 diariamente"""
    from datetime import date, timedelta
    from src.soap.services.service_integracao import ServiceIntegracao
    
    service = ServiceIntegracao()
    ontem = date.today() - timedelta(days=1)
    
    xml_relatorio, resultado = service.gerar_relatorio_consumo(ontem, date.today())
    
    if resultado.success:
        # Enviar para G1
        response = requests.post(
            'http://g1-servidor:8000/soap',
            data=xml_relatorio,
            headers={'Content-Type': 'text/xml'}
        )
        print(f"✅ Relatório enviado a G1: {response.status_code}")
    else:
        print(f"❌ Erro ao gerar relatório: {resultado.mensagem}")

scheduler.start()
```

---

## 📥 G1 → G3 (Grupo 1 envia para você)

### Operação: sincronizarStatusFinanceiro
**Usado por**: Grupo 1 (atualiza status pacientes)  
**Endpoint**: POST /soap  
**Frequência**: On-demand (atualização de status)

#### Request (G1 envia)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>HASH_ASSINADO_G1</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_1</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:sincronizarStatusFinanceiro>
      <tns:arquivo_xml>
        <status_financeiro>
          <paciente>
            <cpf>12345678901</cpf>
            <status>autorizado</status>
            <permite_atendimento>1</permite_atendimento>
            <observacao>Credenciamento ativo</observacao>
          </paciente>
          <assinatura>
            <hash>HASH_VALIDADO_G1</hash>
            <timestamp>2026-06-09T09:59:00Z</timestamp>
            <grupo_origem>GRUPO_1</grupo_origem>
            <algoritmo>HMAC-SHA256</algoritmo>
          </assinatura>
        </status_financeiro>
      </tns:arquivo_xml>
      <tns:grupo_origem>GRUPO_1</tns:grupo_origem>
    </tns:sincronizarStatusFinanceiro>
  </soap:Body>
</soap:Envelope>
```

#### Response (você retorna)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <tns:sincronizarStatusFinanceiroResponse>
      <tns:resultado>
        <tns:success>true</tns:success>
        <tns:mensagem>Status de 1 pacientes sincronizados</tns:mensagem>
        <tns:timestamp>2026-06-09T10:00:02Z</tns:timestamp>
      </tns:resultado>
    </tns:sincronizarStatusFinanceiroResponse>
  </soap:Body>
</soap:Envelope>
```

---

## 🔑 Como Comunicar com G1 e G2

### Para G2 (pode chamar você)
**Compartilhar com G2:**
```
URL WSDL:     http://SEU_IP:8000/soap?wsdl
URL SOAP:     http://SEU_IP:8000/soap
Operação:     consultarDisponibilidade
Autenticação: HMAC-SHA256 no header
```

**Arquivo para compartilhar:**
```bash
cat exemplos_curl.sh | grep -A 20 "consultarDisponibilidade"
```

### Para G1 (você chama G1)
**Pedir a G1:**
```
URL WSDL:     http://g1-ip:PORTA/soap?wsdl
URL SOAP:     http://g1-ip:PORTA/soap
Operação:     sincronizarStatusFinanceiro
Autenticação: HMAC-SHA256 (você assina)
```

---

## 🧪 Teste de Integração (Mock Servers)

Para testar sem os servidores reais de G1/G2:

```python
# Criar mock_g1.py
from unittest.mock import patch
import requests

# Simular resposta de G1
with patch('requests.post') as mock_post:
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = """
    <soap:Envelope>
      <soap:Body>
        <sincronizarStatusFinanceiroResponse>
          <resultado>
            <success>true</success>
          </resultado>
        </sincronizarStatusFinanceiroResponse>
      </soap:Body>
    </soap:Envelope>
    """
    
    # Chamar seu código
    from src.soap.services.service_integracao import ServiceIntegracao
    service = ServiceIntegracao()
    # ... teste aqui
```

---

## 📞 Informações de Contato (Modelo)

| Grupo | URL | Contato | Status |
|-------|-----|---------|--------|
| G1 | http://g1-ip:8000 | email@g1 | ⏳ Aguardando |
| G2 | http://g2-ip:8000 | email@g2 | ⏳ Aguardando |
| G3 (Você) | http://localhost:8000 | seu-email | ✅ Online |

---

## ⚠️ Troubleshooting

**❌ Erro: ASSINATURA_INVALIDA**
→ Verificar HMAC: `calcular_hmac(body)` deve bater com header

**❌ Erro: OPERACAO_NAO_ENCONTRADA**
→ Verificar nome da operação em OPERACOES_MAP

**❌ Timeout**
→ Aumentar timeout em requests: `requests.post(..., timeout=30)`

**❌ CPF_INVALIDO**
→ CPF deve ter exatamente 11 dígitos

---

## ✅ Checklist para Go-Live

- [ ] Confirmou IP/URL de G1
- [ ] Confirmou IP/URL de G2
- [ ] Testou consultarDisponibilidade com G2 (mock ou real)
- [ ] Testou gerarRelatorioConsumo com G1
- [ ] Testou sincronizarStatusFinanceiro com G1
- [ ] HMAC validado em ambas direções
- [ ] Scheduler configurado para enviar relatório diário
- [ ] Monitoramento em produção (logs de integração)
