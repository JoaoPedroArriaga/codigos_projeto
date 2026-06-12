"""Testes da integração G1 via REST/JSON."""
from datetime import date, timedelta

import pytest

from src.servicos.relatorio_consumo import RelatorioConsumoService
from src.servicos.status_financeiro import StatusFinanceiroService


def test_resolver_periodo_padrao_ontem():
    servico = RelatorioConsumoService()
    inicio, fim = servico.resolver_periodo()
    ontem = date.today() - timedelta(days=1)
    assert inicio == ontem
    assert fim == ontem


def test_resolver_periodo_explicito():
    servico = RelatorioConsumoService()
    inicio, fim = servico.resolver_periodo(date(2026, 6, 1), date(2026, 6, 10))
    assert inicio == date(2026, 6, 1)
    assert fim == date(2026, 6, 10)


def test_gerar_json_estrutura():
    servico = RelatorioConsumoService()
    relatorio, inicio, fim = servico.gerar_json(date(2026, 4, 10), date(2026, 4, 10))
    assert relatorio["data_inicio"] == inicio.isoformat()
    assert relatorio["data_fim"] == fim.isoformat()
    assert relatorio["total_itens"] == len(relatorio["itens"])


def test_status_financeiro_sincronizar_e_consultar():
    servico = StatusFinanceiroService()
    pacientes = [
        {"cpf": "12345678901", "status": "ADIMPLENTE", "permite_atendimento": 1},
    ]
    total, msg = servico.sincronizar(pacientes, "GRUPO_1")
    assert total == 1
    assert "Sincronizados" in msg

    dados = servico.consultar("12345678901")
    assert dados["status"] == "ADIMPLENTE"
    assert dados["permite_atendimento"] == 1


def test_status_financeiro_cpf_invalido():
    servico = StatusFinanceiroService()
    with pytest.raises(ValueError, match="CPF_INVALIDO"):
        servico.sincronizar([{"cpf": "123", "status": "ADIMPLENTE"}], "GRUPO_1")


def test_status_financeiro_lista_vazia():
    servico = StatusFinanceiroService()
    with pytest.raises(ValueError, match="LISTA_VAZIA"):
        servico.sincronizar([], "GRUPO_1")
