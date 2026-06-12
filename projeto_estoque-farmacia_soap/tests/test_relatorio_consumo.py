"""Testes do serviço de relatório de consumo (G1 pull)."""
from datetime import date, timedelta

from src.servicos.relatorio_consumo import RelatorioConsumoService


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
