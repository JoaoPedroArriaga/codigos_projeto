"""
Exemplos de curl para testar SOAP API
Execute estes comandos no terminal para testar a API

IMPORTANTE: Os hashes HMAC nos exemplos abaixo são placeholders.
Para requisições autenticadas, gere o hash real com:
  python exemplos_soap.py --hash-only listarMedicamentos

Ou use o cliente Python completo (recomendado):
  python exemplos_soap.py
  python exemplos_soap.py consultarDisponibilidade
"""

# ===== 1. Verificar WSDL =====
# GET /soap?wsdl
curl -i http://localhost:8000/soap?wsdl

# ===== 2. Health check =====
# GET /soap/health
curl http://localhost:8000/soap/health | jq

# ===== 3. listarMedicamentos (sem parâmetros) =====
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: listarMedicamentos" \
  -d @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:listarMedicamentos/>
  </soap:Body>
</soap:Envelope>
EOF

# ===== 4. obterMedicamento (com parâmetro) =====
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: obterMedicamento" \
  -d @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:obterMedicamento>
      <tns:codigo>789123</tns:codigo>
    </tns:obterMedicamento>
  </soap:Body>
</soap:Envelope>
EOF

# ===== 5. consultarDisponibilidade (⭐ CRÍTICA) =====
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: consultarDisponibilidade" \
  -d @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
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
EOF

# ===== 6. criarReserva (FEFO automático) =====
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: criarReserva" \
  -d @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:criarReserva>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>5</tns:quantidade>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
    </tns:criarReserva>
  </soap:Body>
</soap:Envelope>
EOF

# ===== 7. registrarBaixa (reduz estoque) =====
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: registrarBaixa" \
  -d @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:registrarBaixa>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>2</tns:quantidade>
      <tns:numero_lote>LOTE123</tns:numero_lote>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
      <tns:motivo>Dispensação ao paciente</tns:motivo>
    </tns:registrarBaixa>
  </soap:Body>
</soap:Envelope>
EOF

# ===== 8. TESTE ERRO: CPF inválido =====
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: consultarDisponibilidade" \
  -d @- << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Body>
    <tns:consultarDisponibilidade>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>5</tns:quantidade>
      <tns:cpf_paciente>123</tns:cpf_paciente>
    </tns:consultarDisponibilidade>
  </soap:Body>
</soap:Envelope>
EOF

# ===== 9. Pretty print response =====
# Adicione ao final do curl: | xmllint --format -
curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: listarMedicamentos" \
  -d @- << 'EOF' | xmllint --format -
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Body>
    <tns:listarMedicamentos/>
  </soap:Body>
</soap:Envelope>
EOF
