#!/usr/bin/env python
"""
Inicializador do Sistema de Estoque e Farmácia
Inicia a API REST e o processamento em background de forma sincronizada
"""
import sys
import os
import asyncio
import threading
import logging
from dotenv import load_dotenv

# Adicionar o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def iniciar_processamento_background():
    """Inicia o processamento de XML em thread separada"""
    logger.info("🚀 Iniciando processamento em background...")
    
    from src.main import main as main_processamento
    
    try:
        main_processamento()
    except KeyboardInterrupt:
        logger.info("👋 Processamento encerrado")
    except Exception as e:
        logger.error(f"❌ Erro no processamento: {e}")


def iniciar_api():
    """Inicia a API REST"""
    logger.info("🌐 Iniciando API REST...")
    
    import uvicorn
    from src.api.app import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


def main():
    """Inicia tanto a API quanto o processamento em background"""
    logger.info("=" * 60)
    logger.info("🏥 SISTEMA DE ESTOQUE E FARMÁCIA - v2.0.0")
    logger.info("=" * 60)
    
    # Iniciar processamento em thread separada
    thread_processamento = threading.Thread(
        target=iniciar_processamento_background,
        daemon=True
    )
    thread_processamento.start()
    logger.info("✅ Thread de processamento iniciada")
    
    # Dar um tempo para o processamento se conectar
    import time
    time.sleep(2)
    
    # Iniciar API na thread principal
    logger.info("=" * 60)
    logger.info("📡 API disponível em http://localhost:8000")
    logger.info("📚 Documentação em http://localhost:8000/docs")
    logger.info("=" * 60)
    
    iniciar_api()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Sistema encerrado pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)
