"""
Relatório de consumo para o G1 puxar via REST/JSON (pull no começo do dia).
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from src.schemas import RelatorioConsumoResponseSchema
from src.servicos.relatorio_consumo import RelatorioConsumoService

router = APIRouter(prefix="/api/relatorios", tags=["Relatórios G1"])


@router.get("/consumo", response_model=RelatorioConsumoResponseSchema)
async def puxar_relatorio_consumo(
    data_inicio: Optional[date] = Query(None, description="Data inicial (padrão: ontem)"),
    data_fim: Optional[date] = Query(None, description="Data final (padrão: ontem)"),
):
    """G1 puxa o relatório de consumo em JSON."""
    servico = RelatorioConsumoService()
    relatorio, inicio, fim = servico.gerar_json(data_inicio, data_fim)
    servico.marcar_como_enviado(inicio, fim)

    return relatorio
