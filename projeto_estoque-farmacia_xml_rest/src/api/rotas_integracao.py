"""
Integração G1 ↔ G3 via REST (status financeiro e consulta de paciente).
"""
from fastapi import APIRouter, Header, HTTPException, Request

from src.servicos.status_financeiro import StatusFinanceiroService

router = APIRouter(prefix="/api/integracao", tags=["Integração G1"])
_servico = StatusFinanceiroService()


@router.post("/status-financeiro")
async def sincronizar_status_financeiro(
    request: Request,
    x_grupo_origem: str = Header(..., alias="X-Grupo-Origem"),
):
    """
    G1 envia XML status_financeiro.xsd assinado com HMAC.
    Equivalente SOAP: sincronizarStatusFinanceiro
    """
    if x_grupo_origem != "GRUPO_1":
        raise HTTPException(status_code=403, detail="Apenas GRUPO_1 pode enviar status financeiro")

    xml_body = (await request.body()).decode('utf-8')
    if not xml_body.strip():
        raise HTTPException(status_code=400, detail="Body XML vazio")

    try:
        total, mensagem = _servico.sincronizar(xml_body, x_grupo_origem)
        return {"success": True, "total_sincronizados": total, "mensagem": mensagem}
    except Exception as e:
        erro = str(e)
        if "ASSINATURA" in erro:
            raise HTTPException(status_code=401, detail=erro)
        if "XML_INVALIDO" in erro:
            raise HTTPException(status_code=400, detail=erro)
        raise HTTPException(status_code=500, detail=erro)


@router.get("/status-paciente/{cpf}")
async def consultar_status_paciente(cpf: str):
    """Consulta status financeiro sincronizado do G1. Equivalente SOAP: consultarStatusPaciente"""
    try:
        return _servico.consultar(cpf)
    except Exception as e:
        erro = str(e)
        if "CPF_INVALIDO" in erro or "PACIENTE_NAO_ENCONTRADO" in erro:
            raise HTTPException(status_code=404, detail=erro)
        raise HTTPException(status_code=500, detail=erro)
