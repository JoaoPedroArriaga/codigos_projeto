# Documentação — G3 REST (`projeto_estoque-farmacia_xml_rest`)

Implementação **REST/JSON** do sistema de estoque — par do projeto SOAP, mesma regra de negócio.

> Visão geral conectada (G1 + G2 + G3): [`../INTEROPERABILIDADE.md`](../INTEROPERABILIDADE.md)

---

## Papel no ecossistema

| Item | Valor |
|------|-------|
| Protocolo | REST/JSON |
| Porta | **8001** (`API_PORT` no `.env`) |
| G2 | `GET/POST /api/*` (medicamentos, estoque, reservas, baixas) |
| G1 | Pull consumo + push status financeiro (**JSON**) |

> Integração **XML/XSD** com o G1 fica no projeto **SOAP** (`:8000`).

---

## Executar

```bash
python run_api.py
# http://localhost:8001/docs
```

---

## Integração G1 (REST ↔ REST, JSON)

### Puxar consumo (manhã)

```
GET /api/relatorios/consumo?data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD
Accept: application/json
```

Resposta:

```json
{
  "data_inicio": "2026-04-10",
  "data_fim": "2026-04-10",
  "total_itens": 5,
  "itens": [
    {
      "prescricao": "195557000",
      "cpf": "11122233344",
      "codigo_medicamento": 111222,
      "quantidade": 1.0,
      "unidade": "CAIXA",
      "preco_total": 12.0,
      "data_uso": "2026-04-10"
    }
  ]
}
```

```bash
python exemplos_pull_g1.py --data 2026-04-10
```

Teste com curl:

```powershell
curl.exe "http://localhost:8001/api/relatorios/consumo?data_inicio=2026-04-10&data_fim=2026-04-10"
```

### Enviar status financeiro

```
POST /api/integracao/status-financeiro
Content-Type: application/json

{
  "pacientes": [
    {
      "cpf": "11122233344",
      "status": "ADIMPLENTE",
      "permite_atendimento": 1,
      "observacao": "OK"
    }
  ]
}
```

```bash
python exemplos_push_g1_status.py
```

### Consultar status de paciente

```
GET /api/integracao/status-paciente/{cpf}
```

---

## Integração G2

Equivalente REST das operações SOAP — ver Swagger em `/docs`:

- `POST /api/estoque/consultar`
- `POST /api/reservas`
- `GET /api/medicamentos`
- etc.

---

## Benchmark

Comparar com SOAP (porta 8000):

```bash
cd ../benchmarks && python benchmark_comparison.py
```
