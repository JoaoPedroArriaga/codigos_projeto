# Interoperabilidade — Sistema Conectado (G1 + G2 + G3)

Dois projetos G3, **mesma regra de negócio**, protocolos diferentes:

| Projeto | Protocolo | Porta | Papel |
|---------|-----------|-------|-------|
| `projeto_estoque-farmacia_soap` | **SOAP/XML** | **8000** | Integração formal (WSDL, G1/G2) + dashboard SOAP |
| `projeto_estoque-farmacia_xml_rest` | **REST/JSON** | **8001** | Mesma API em JSON + integração G1 REST |

Ambos usam o **mesmo PostgreSQL** e os mesmos XSDs (`consumo.xsd`, `status_financeiro.xsd`).

---

## Arquitetura conectada

```
                         ┌─────────────────────────────────────┐
                         │           G1 — Financeiro           │
                         └──────────────┬──────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │ manhã: PULL consumo     │ tarde: PUSH status      │
              ▼                         ▼                         │
   ┌──────────────────────┐   ┌──────────────────────┐            │
   │  G3 SOAP  :8000      │   │  G3 REST  :8001      │◄───────────┘
   │  gerarRelatorio...   │   │  GET /api/relatorios │   POST status
   │  sincronizarStatus.. │   │  POST /integracao    │
   └──────────┬───────────┘   └──────────┬───────────┘
              │                          │
              │    ┌─────────────────────┘
              │    │
              ▼    ▼
   ┌──────────────────────┐         ┌──────────────────────┐
   │     PostgreSQL       │         │   G2 — Prescrição    │
   │  estoque + consumo   │◄────────│  consulta / reserva  │
   └──────────────────────┘         └──────────────────────┘
              ▲                                │
              │                                │
              └──────── SOAP :8000 ────────────┘
                       ou REST :8001
```

---

## Matriz de integração (o que cada grupo usa)

### G1 ↔ G3 (Financeiro)

| Fluxo | Direção | SOAP (:8000) | REST (:8001) |
|-------|---------|--------------|--------------|
| Relatório de consumo | G1 **puxa** de manhã | `gerarRelatorioConsumo` | `GET /api/relatorios/consumo` |
| Status financeiro | G1 **envia** | `sincronizarStatusFinanceiro` | `POST /api/integracao/status-financeiro` |
| Consultar paciente | G3 interno / G2 | `consultarStatusPaciente` | `GET /api/integracao/status-paciente/{cpf}` |

### G2 ↔ G3 (Prescrição)

| Operação | SOAP (:8000) | REST (:8001) |
|----------|--------------|--------------|
| Consultar disponibilidade | `consultarDisponibilidade` | `POST /api/estoque/consultar` |
| Criar reserva | `criarReserva` | `POST /api/reservas` |
| Listar medicamentos | `listarMedicamentos` | `GET /api/medicamentos` |
| Obter estoque | `obterEstoque` | `GET /api/estoque/{codigo}` |

---

## Subir os dois servidores

**Terminal 1 — SOAP:**
```powershell
cd projeto_estoque-farmacia_soap
python run_api.py
```

**Terminal 2 — REST:**
```powershell
cd projeto_estoque-farmacia_xml_rest
python run_api.py
```

Ou use o script na raiz:
```powershell
.\iniciar_sistema.ps1
```

---

## Testar integração (simular grupos)

```powershell
# G1 puxa consumo
cd projeto_estoque-farmacia_soap && python exemplos_pull_g1.py
cd projeto_estoque-farmacia_xml_rest && python exemplos_pull_g1.py

# G2 consulta estoque (SOAP)
cd projeto_estoque-farmacia_soap && python exemplos_soap.py

# Benchmark REST vs SOAP
cd benchmarks && python benchmark_comparison.py
```

---

## Autenticação

| Protocolo | Mecanismo |
|-----------|-----------|
| SOAP | HMAC-SHA256 no `<soap:Header>` (`grupo_origem` + `hash`) |
| REST (relatório) | Headers `X-Grupo-Origem` + `X-Hash` (HMAC da query) |
| REST (status G1) | XML assinado internamente (`status_financeiro.xsd`) + header `X-Grupo-Origem: GRUPO_1` |

Chave compartilhada: `chave_secreta_compartilhada_entre_grupos_2026`

---

## Documentação por projeto

- SOAP: `projeto_estoque-farmacia_soap/DOCUMENTACAO.md`
- REST: `projeto_estoque-farmacia_xml_rest/DOCUMENTACAO.md`
- Conexão detalhada SOAP: `projeto_estoque-farmacia_soap/CONEXAO_GRUPOS.md`
