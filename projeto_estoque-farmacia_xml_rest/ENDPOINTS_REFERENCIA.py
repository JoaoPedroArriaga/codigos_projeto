#!/usr/bin/env python
"""
REFERÊNCIA RÁPIDA DE ENDPOINTS
Sistema de Estoque e Farmácia v2.0.0
"""

# ============================================
# API REST - ENDPOINTS COMPLETOS
# ============================================

"""
Todos os endpoints abaixo estão funcionais e documentados em:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

# ============================================
# 🔍 MEDICAMENTOS (Read-only)
# ============================================

GET_MEDICAMENTOS = {
    "método": "GET",
    "rota": "/api/medicamentos",
    "descrição": "Lista todos os medicamentos cadastrados",
    "parâmetros": "Nenhum",
    "resposta": [
        {
            "id": 1,
            "codigo": 789123,
            "nome": "Paracetamol 500mg"
        }
    ],
    "status": 200,
    "exemplo": "curl http://localhost:8000/api/medicamentos"
}

GET_MEDICAMENTO_CODIGO = {
    "método": "GET",
    "rota": "/api/medicamentos/{codigo}",
    "descrição": "Obtém um medicamento específico por código",
    "parâmetros": {
        "codigo": "int (obrigatório)"
    },
    "resposta": {
        "id": 1,
        "codigo": 789123,
        "nome": "Paracetamol 500mg"
    },
    "status": 200,
    "erros": [404],
    "exemplo": "curl http://localhost:8000/api/medicamentos/789123"
}

# ============================================
# 📦 ESTOQUE
# ============================================

GET_ESTOQUE = {
    "método": "GET",
    "rota": "/api/estoque/{codigo_medicamento}",
    "descrição": "Obtém informações de estoque de um medicamento",
    "parâmetros": {
        "codigo_medicamento": "int (obrigatório)"
    },
    "resposta": {
        "codigo_medicamento": 789123,
        "nome_medicamento": "Paracetamol",
        "quantidade_total": 150,
        "lotes": [
            {
                "id_lote": 1,
                "numero_lote": "LOTE123",
                "quantidade_atual": 50,
                "data_validade": "2026-12-31",
                "preco_venda": 5.50
            }
        ]
    },
    "status": 200,
    "erros": [404, 500],
    "exemplo": "curl http://localhost:8000/api/estoque/789123"
}

POST_CONSULTAR_DISPONIBILIDADE = {
    "método": "POST",
    "rota": "/api/estoque/consultar",
    "descrição": "Consulta disponibilidade de um medicamento (FEFO)",
    "parâmetros": {
        "corpo": {
            "codigo_medicamento": "int (obrigatório)",
            "quantidade": "int > 0 (obrigatório)",
            "cpf_paciente": "str com 11 dígitos (obrigatório)"
        }
    },
    "requisição": {
        "codigo_medicamento": 789123,
        "quantidade": 5,
        "cpf_paciente": "12345678901"
    },
    "resposta_sucesso": {
        "success": True,
        "disponivel": True,
        "lote": "LOTE123",
        "validade": "2026-12-31",
        "preco": 5.50,
        "mensagem": "Disponível: 50 unidades"
    },
    "resposta_indisponivel": {
        "success": True,
        "disponivel": False,
        "lote": None,
        "validade": None,
        "preco": None,
        "mensagem": "Medicamento indisponível na quantidade solicitada (5)"
    },
    "status": 200,
    "erros": [400, 500],
    "exemplo": """curl -X POST http://localhost:8000/api/estoque/consultar \\
  -H "Content-Type: application/json" \\
  -d '{
    "codigo_medicamento": 789123,
    "quantidade": 5,
    "cpf_paciente": "12345678901"
  }'"""
}

GET_LOTES = {
    "método": "GET",
    "rota": "/api/estoque/lotes/{codigo_medicamento}",
    "descrição": "Lista todos os lotes de um medicamento",
    "parâmetros": {
        "codigo_medicamento": "int (obrigatório)"
    },
    "resposta": {
        "codigo_medicamento": 789123,
        "total_lotes": 3,
        "lotes": [
            {
                "id_lote": 1,
                "numero_lote": "LOTE123",
                "quantidade_atual": 50,
                "quantidade_inicial": 100,
                "data_validade": "2026-12-31",
                "preco_venda": 5.50
            }
        ]
    },
    "status": 200,
    "erros": [404, 500],
    "exemplo": "curl http://localhost:8000/api/estoque/lotes/789123"
}

# ============================================
# 🎫 RESERVAS
# ============================================

POST_CRIAR_RESERVA = {
    "método": "POST",
    "rota": "/api/reservas",
    "descrição": "Cria uma nova reserva de medicamento",
    "parâmetros": {
        "corpo": {
            "codigo_medicamento": "int > 0 (obrigatório)",
            "quantidade": "int > 0 (obrigatório)",
            "lote": "str (obrigatório)",
            "cpf_paciente": "str com 11 dígitos (obrigatório)"
        }
    },
    "requisição": {
        "codigo_medicamento": 789123,
        "quantidade": 5,
        "lote": "LOTE123",
        "cpf_paciente": "12345678901"
    },
    "resposta": {
        "success": True,
        "id_reserva": "12345",
        "mensagem": "Reserva criada com sucesso",
        "timestamp": "2026-05-13T10:30:00"
    },
    "status": 200,
    "erros": [400, 500],
    "exemplo": """curl -X POST http://localhost:8000/api/reservas \\
  -H "Content-Type: application/json" \\
  -d '{
    "codigo_medicamento": 789123,
    "quantidade": 5,
    "lote": "LOTE123",
    "cpf_paciente": "12345678901"
  }'"""
}

GET_RESERVAS_ATIVAS = {
    "método": "GET",
    "rota": "/api/reservas",
    "descrição": "Lista todas as reservas ativas",
    "parâmetros": "Nenhum",
    "resposta": {
        "total": 2,
        "reservas": [
            {
                "id_reserva": 1,
                "codigo_medicamento": 789123,
                "quantidade": 5,
                "numero_lote": "LOTE123",
                "cpf_paciente": "12345678901",
                "status": "ativa",
                "data_criacao": "2026-05-13T10:30:00"
            }
        ]
    },
    "status": 200,
    "erros": [500],
    "exemplo": "curl http://localhost:8000/api/reservas"
}

GET_RESERVA_ID = {
    "método": "GET",
    "rota": "/api/reservas/{id_reserva}",
    "descrição": "Obtém detalhes de uma reserva específica",
    "parâmetros": {
        "id_reserva": "int (obrigatório)"
    },
    "resposta": {
        "id_reserva": 1,
        "codigo_medicamento": 789123,
        "quantidade": 5,
        "numero_lote": "LOTE123",
        "cpf_paciente": "12345678901",
        "status": "ativa",
        "data_criacao": "2026-05-13T10:30:00"
    },
    "status": 200,
    "erros": [404, 500],
    "exemplo": "curl http://localhost:8000/api/reservas/1"
}

DELETE_CANCELAR_RESERVA = {
    "método": "DELETE",
    "rota": "/api/reservas/{id_reserva}",
    "descrição": "Cancela uma reserva",
    "parâmetros": {
        "id_reserva": "int (obrigatório)"
    },
    "resposta": {
        "success": True,
        "mensagem": "Reserva cancelada com sucesso"
    },
    "status": 200,
    "erros": [400, 404, 500],
    "exemplo": "curl -X DELETE http://localhost:8000/api/reservas/1"
}

# ============================================
# 📉 BAIXAS
# ============================================

POST_REGISTRAR_BAIXA = {
    "método": "POST",
    "rota": "/api/baixas",
    "descrição": "Registra uma baixa de estoque (reduz quantidade)",
    "parâmetros": {
        "corpo": {
            "codigo_medicamento": "int > 0 (obrigatório)",
            "quantidade": "int > 0 (obrigatório)",
            "lote": "str (obrigatório)",
            "motivo": "str (opcional)"
        }
    },
    "requisição": {
        "codigo_medicamento": 789123,
        "quantidade": 5,
        "lote": "LOTE123",
        "motivo": "Dispensado ao paciente"
    },
    "resposta": {
        "success": True,
        "id_baixa": "1",
        "quantidade_restante": 45,
        "mensagem": "Baixa de 5 unidades realizada com sucesso",
        "timestamp": "2026-05-13T11:00:00"
    },
    "status": 200,
    "erros": [400, 500],
    "exemplo": """curl -X POST http://localhost:8000/api/baixas \\
  -H "Content-Type: application/json" \\
  -d '{
    "codigo_medicamento": 789123,
    "quantidade": 5,
    "lote": "LOTE123",
    "motivo": "Dispensado"
  }'"""
}

# ============================================
# ℹ️ SISTEMA
# ============================================

GET_ROOT = {
    "método": "GET",
    "rota": "/",
    "descrição": "Página raiz - redireciona para docs",
    "resposta": {
        "message": "API de Estoque e Farmácia",
        "docs_url": "/docs"
    },
    "status": 200
}

GET_HEALTH = {
    "método": "GET",
    "rota": "/health",
    "descrição": "Verificação de saúde da API",
    "resposta": {
        "status": "healthy",
        "version": "2.0.0"
    },
    "status": 200,
    "exemplo": "curl http://localhost:8000/health"
}

GET_API_INFO = {
    "método": "GET",
    "rota": "/api",
    "descrição": "Informações sobre a API",
    "resposta": {
        "nome": "Sistema de Estoque e Farmácia",
        "versao": "2.0.0",
        "endpoints": ["..."],
        "documentacao": "/docs"
    },
    "status": 200,
    "exemplo": "curl http://localhost:8000/api"
}

# ============================================
# 📚 DOCUMENTAÇÃO
# ============================================

SWAGGER_UI = {
    "url": "http://localhost:8000/docs",
    "descrição": "Documentação interativa com Swagger UI",
    "funcionalidades": [
        "Testar endpoints diretamente",
        "Ver schemas de requisição/resposta",
        "Visualizar códigos de status",
        "Exemplos automáticos"
    ]
}

REDOC = {
    "url": "http://localhost:8000/redoc",
    "descrição": "Documentação em formato ReDoc",
    "funcionalidades": [
        "Layout mais legível",
        "Melhor para leitura offline",
        "Busca global"
    ]
}

# ============================================
# 📊 RESUMO
# ============================================

RESUMO_ENDPOINTS = """
✅ MEDICAMENTOS (2 endpoints)
   GET  /api/medicamentos
   GET  /api/medicamentos/{codigo}

✅ ESTOQUE (3 endpoints)
   GET  /api/estoque/{codigo_medicamento}
   POST /api/estoque/consultar
   GET  /api/estoque/lotes/{codigo_medicamento}

✅ RESERVAS (4 endpoints)
   POST   /api/reservas
   GET    /api/reservas
   GET    /api/reservas/{id_reserva}
   DELETE /api/reservas/{id_reserva}

✅ BAIXAS (1 endpoint)
   POST /api/baixas

✅ SISTEMA (3 endpoints)
   GET /
   GET /health
   GET /api

Total: 13 endpoints + Documentação automática
"""

# ============================================
# 🧪 EXEMPLOS DE USO
# ============================================

if __name__ == "__main__":
    print(RESUMO_ENDPOINTS)
    print("\n📚 Documentação em: http://localhost:8000/docs")
    print("🧪 Teste com: python testar_api.py")
