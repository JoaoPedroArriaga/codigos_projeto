# Documentação — G3 REST (`projeto_estoque-farmacia_xml_rest`)

Implementação **REST/JSON** do sistema de estoque — par do projeto SOAP, mesma regra de negócio.

> Visão geral conectada (G1 + G2 + G3): [`../INTEROPERABILIDADE.md`](../INTEROPERABILIDADE.md)

---

## Papel no ecossistema

| Item | Valor |
|------|-------|
| Protocolo | REST JSON (+ XML na integração G1) |
| Porta | **8001** (`API_PORT` no `.env`) |
| G2 | `GET/POST /api/*` (medicamentos, estoque, reservas, baixas) |
| G1 | Pull consumo + push status financeiro |

---

## Executar

```bash
python run_api.py
# http://localhost:8001/docs
```

---

## Integração G1

### Puxar consumo (manhã)

```
GET /api/relatorios/consumo?data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD

Headers:
  X-Grupo-Origem: GRUPO_1
  X-Hash: HMAC-SHA256 de "data_inicio=...&data_fim=..."
```

Resposta: XML `consumo.xsd` assinado.

```bash
python exemplos_pull_g1.py
```

### Enviar status financeiro

```
POST /api/integracao/status-financeiro
Content-Type: application/xml
X-Grupo-Origem: GRUPO_1

Body: XML status_financeiro.xsd com <assinatura> HMAC
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
cd ../benchmarks
python benchmark_comparison.py
```
