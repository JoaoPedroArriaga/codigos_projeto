"""
Relatório de consumo para o G1 puxar via REST (pull no começo do dia).
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Response

from src.servicos.relatorio_consumo import RelatorioConsumoService
from src.utils.hash_utils import calcular_hmac

router = APIRouter(prefix="/api/relatorios", tags=["Relatórios G1"])

GRUPOS_AUTORIZADOS = {"GRUPO_1"}


def _canonical_query(data_inicio: Optional[date], data_fim: Optional[date]) -> str:
    partes = []
    if data_inicio:
        partes.append(f"data_inicio={data_inicio.isoformat()}")
    if data_fim:
        partes.append(f"data_fim={data_fim.isoformat()}")
    return "&".join(partes)


def _validar_hmac_pull(
    data_inicio: Optional[date],
    data_fim: Optional[date],
    grupo_origem: str,
    hash_recebido: str,
) -> None:
    if grupo_origem not in GRUPOS_AUTORIZADOS:
        raise HTTPException(status_code=403, detail="Grupo não autorizado para este relatório")

    canonical = _canonical_query(data_inicio, data_fim)
    hash_esperado = calcular_hmac(canonical)
    if hash_recebido != hash_esperado:
        raise HTTPException(status_code=401, detail="ASSINATURA_INVALIDA")


@router.get("/consumo")
async def puxar_relatorio_consumo(
    data_inicio: Optional[date] = Query(None, description="Data inicial (padrão: ontem)"),
    data_fim: Optional[date] = Query(None, description="Data final (padrão: ontem)"),
    x_grupo_origem: str = Header(..., alias="X-Grupo-Origem"),
    x_hash: str = Header(..., alias="X-Hash"),
):
    """
    G1 puxa o relatório de consumo em XML (consumo.xsd + HMAC).

    Headers obrigatórios:
      X-Grupo-Origem: GRUPO_1
      X-Hash: HMAC-SHA256 da query (ex: data_inicio=2026-06-11&data_fim=2026-06-11)
    """
    _validar_hmac_pull(data_inicio, data_fim, x_grupo_origem, x_hash)

    servico = RelatorioConsumoService()
    xml_assinado, total, inicio, fim = servico.gerar_xml(data_inicio, data_fim)
    servico.marcar_como_enviado(inicio, fim)

    return Response(
        content=xml_assinado,
        media_type="application/xml; charset=utf-8",
        headers={
            "X-Total-Itens": str(total),
            "X-Data-Inicio": inicio.isoformat(),
            "X-Data-Fim": fim.isoformat(),
        },
    )
