"""
Aplicação FastAPI - Servidor SOAP + Dashboard
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.soap.routes import registrar_rotas_soap

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
