"""
Aplicação FastAPI - API REST do Sistema de Estoque e Farmácia
"""
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os

from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.servicos.relatorio_consumo import RelatorioConsumoService

# Importar rotas
from src.api.rotas_medicamentos import router as router_medicamentos
from src.api.rotas_estoque import router as router_estoque
from src.api.rotas_reservas import router as router_reservas
from src.api.rotas_baixas import router as router_baixas
from src.api.rotas_relatorios import router as router_relatorios
from src.api.rotas_integracao import router as router_integracao

# Criar aplicação
app = FastAPI(
    title="API - Sistema de Estoque e Farmácia",
    description="API REST para gerenciamento de estoque e farmácia com processamento XML",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Registrar rotas
app.include_router(router_medicamentos)
app.include_router(router_estoque)
app.include_router(router_reservas)
app.include_router(router_baixas)
app.include_router(router_relatorios)
app.include_router(router_integracao)

# Servir arquivos estáticos (frontend)
# __file__ = src/api/app.py, então sobe 2 níveis chega em projeto root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
frontend_dir = os.path.join(project_root, "frontend")
static_dir = os.path.join(frontend_dir, "static")
templates_dir = os.path.join(frontend_dir, "templates")

# Servir arquivos CSS, JS, etc
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve o dashboard HTML"""
    dashboard_path = os.path.join(templates_dir, "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return {"message": "API de Estoque e Farmácia", "docs_url": "/docs"}


@app.get("/health")
async def health_check():
    """Verificação de saúde da API"""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }


@app.get("/api/dashboard/consumo")
async def dashboard_consumo(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
):
    """Alias do relatório de consumo para o dashboard."""
    servico = RelatorioConsumoService()
    relatorio, _, _ = servico.gerar_json(data_inicio, data_fim)
    return relatorio


@app.get("/api/dashboard/consumo/json")
async def dashboard_consumo_json(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
):
    """Gera JSON de consumo, salva em data/saida/consumos/ e devolve download."""
    servico = RelatorioConsumoService()
    try:
        _, nome_arquivo, conteudo, _, inicio, fim = servico.gerar_e_salvar_arquivo(
            data_inicio, data_fim
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=conteudo,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
            "X-Periodo-Inicio": inicio.isoformat(),
            "X-Periodo-Fim": fim.isoformat(),
        },
    )


@app.get("/api")
async def api_info():
    """Informações sobre a API"""
    return {
        "nome": "Sistema de Estoque e Farmácia",
        "versao": "2.0.0",
        "endpoints": [
            "GET /api/medicamentos - Listar medicamentos",
            "GET /api/medicamentos/{codigo} - Obter medicamento",
            "GET /api/estoque/{codigo_medicamento} - Obter estoque",
            "POST /api/estoque/consultar - Consultar disponibilidade",
            "GET /api/estoque/lotes/{codigo_medicamento} - Listar lotes",
            "POST /api/reservas - Criar reserva",
            "GET /api/reservas - Listar reservas ativas",
            "GET /api/reservas/{id} - Obter reserva",
            "DELETE /api/reservas/{id} - Cancelar reserva",
            "POST /api/baixas - Registrar baixa",
            "GET /api/relatorios/consumo - G1 puxa relatório de consumo (JSON)",
            "POST /api/integracao/status-financeiro - G1 envia status financeiro (JSON)",
            "GET /api/integracao/status-paciente/{cpf} - Consultar status do G1"
        ],
        "documentacao": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
