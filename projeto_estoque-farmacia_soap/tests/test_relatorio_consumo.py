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


def test_gerar_e_salvar_arquivo_sem_itens_levanta_erro():
    servico = RelatorioConsumoService()
    try:
        servico.gerar_e_salvar_arquivo(date(1999, 1, 1), date(1999, 1, 1))
        assert False, "esperava ValueError"
    except ValueError as exc:
        assert "Nenhum item de consumo" in str(exc)
