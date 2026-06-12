# Projeto de Interoperabilidade — Estoque Farmácia

Sistema distribuído entre **G1 (Financeiro)**, **G2 (Prescrição)** e **G3 (Estoque)**.

## Projetos

| Pasta | Protocolo | Porta |
|-------|-----------|-------|
| [`projeto_estoque-farmacia_soap`](projeto_estoque-farmacia_soap/) | SOAP/XML | 8000 |
| [`projeto_estoque-farmacia_xml_rest`](projeto_estoque-farmacia_xml_rest/) | REST/JSON | 8001 |
| [`benchmarks`](benchmarks/) | Comparação REST vs SOAP | — |

## Início rápido

```powershell
# Subir SOAP + REST
.\iniciar_sistema.ps1

# Ou manualmente em dois terminais:
cd projeto_estoque-farmacia_soap && python run_api.py
cd projeto_estoque-farmacia_xml_rest && python run_api.py
```

## Documentação

- **[INTEROPERABILIDADE.md](INTEROPERABILIDADE.md)** — arquitetura conectada G1/G2/G3
- [DOCUMENTACAO.md (SOAP)](projeto_estoque-farmacia_soap/DOCUMENTACAO.md)
- [DOCUMENTACAO.md (REST)](projeto_estoque-farmacia_xml_rest/DOCUMENTACAO.md)
