
"""
Servidor SOAP standalone - FastAPI endpoint para /soap
Para uso unificado, prefira: python run_api.py
"""
from fastapi import FastAPI

from src.soap.routes import registrar_rotas_soap


def criar_app():
    """Factory para criar aplicação FastAPI com rotas SOAP"""
    app = FastAPI(
        title="Estoque Farmácia - SOAP API v1",
        description="API SOAP para gerenciamento de estoque farmacêutico",
        version="1.0"
    )
    registrar_rotas_soap(app)
    return app


app = criar_app()


if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor SOAP na porta 8000")
    print("WSDL disponível em: http://localhost:8000/soap?wsdl")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
