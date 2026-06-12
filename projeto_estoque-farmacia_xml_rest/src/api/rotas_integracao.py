"""
Integração G1 ↔ G3 via REST/JSON (status financeiro e consulta de paciente).
"""
from fastapi import APIRouter, HTTPException

from src.schemas import StatusFinanceiroRequestSchema, StatusFinanceiroResponseSchema
from src.servicos.status_financeiro import StatusFinanceiroService

router = APIRouter(prefix="/api/integracao", tags=["Integração G1"])
_servico = StatusFinanceiroService()
GRUPO_G1 = "GRUPO_1"


@router.post("/status-financeiro", response_model=StatusFinanceiroResponseSchema)
async def sincronizar_status_financeiro(payload: StatusFinanceiroRequestSchema):
    """
    G1 envia status financeiro em JSON.
    Equivalente SOAP: sincronizarStatusFinanceiro (XML)
    """
    try:
        pacientes = [p.model_dump() for p in payload.pacientes]
        total, mensagem = _servico.sincronizar(pacientes, GRUPO_G1)
        return StatusFinanceiroResponseSchema(
            success=True,
            total_sincronizados=total,
            mensagem=mensagem,
        )
    except ValueError as e:
        erro = str(e)
        if "CPF_INVALIDO" in erro or "DADOS_INVALIDOS" in erro or "LISTA_VAZIA" in erro:
            raise HTTPException(status_code=400, detail=erro)
        raise HTTPException(status_code=500, detail=erro)


@router.get("/status-paciente/{cpf}")
async def consultar_status_paciente(cpf: str):
    """Consulta status financeiro sincronizado do G1. Equivalente SOAP: consultarStatusPaciente"""
    try:
        return _servico.consultar(cpf)
    except ValueError as e:
        erro = str(e)
        if "CPF_INVALIDO" in erro or "PACIENTE_NAO_ENCONTRADO" in erro:
            raise HTTPException(status_code=404, detail=erro)
        raise HTTPException(status_code=500, detail=erro)
