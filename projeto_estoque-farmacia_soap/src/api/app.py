"""
Aplicação FastAPI - Servidor SOAP + Dashboard
"""
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os

from src.soap.middleware.request_logging import SoapRequestLoggingMiddleware
from src.soap.routes import registrar_rotas_soap
from src.servicos.relatorio_consumo import RelatorioConsumoService

app = FastAPI(
    title="Sistema de Estoque e Farmácia - SOAP",
    description="Integração via POST /soap. Dashboard em /.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SoapRequestLoggingMiddleware)

registrar_rotas_soap(app)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
frontend_dir = os.path.join(project_root, "frontend")
static_dir = os.path.join(frontend_dir, "static")
templates_dir = os.path.join(frontend_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve o dashboard HTML"""
    dashboard_path = os.path.join(templates_dir, "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return {
        "message": "Sistema de Estoque e Farmácia",
        "protocolo": "SOAP",
        "wsdl": "/soap?wsdl",
        "endpoint": "/soap",
    }


@app.get("/health")
async def health_check():
    """Verificação de saúde do servidor"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "protocolo": "SOAP"
    }


@app.get("/api/dashboard/consumo")
async def dashboard_consumo(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
):
    """Relatório de consumo em JSON para o dashboard (sem autenticação G1)."""
    servico = RelatorioConsumoService()
    relatorio, _, _ = servico.gerar_json(data_inicio, data_fim)
    return relatorio


@app.get("/api/dashboard/consumo/xml")
async def dashboard_consumo_xml(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
):
    """Gera XML de consumo (consumo.xsd), salva em data/saida/consumos/ e devolve download."""
    servico = RelatorioConsumoService()
    try:
        _, nome_arquivo, xml_assinado, _, inicio, fim = servico.gerar_e_salvar_arquivo(
            data_inicio, data_fim
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=xml_assinado,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
            "X-Periodo-Inicio": inicio.isoformat(),
            "X-Periodo-Fim": fim.isoformat(),
        },
    )


@app.get("/api")
async def api_info():
    """Informações sobre o protocolo de integração"""
    return {
        "nome": "Sistema de Estoque e Farmácia",
        "versao": "2.0.0",
        "protocolo": "SOAP",
        "wsdl": "/soap?wsdl",
        "endpoint": "/soap",
        "health": "/soap/health",
        "dashboard": "/"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
