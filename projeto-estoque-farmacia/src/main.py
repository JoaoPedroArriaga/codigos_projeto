import os
import time
import schedule
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.config.database import db
from src.processors.consulta_processor import ConsultaProcessor
from src.processors.reserva_processor import ReservaProcessor
from src.processors.baixa_processor import BaixaProcessor
from src.processors.consumo_generator import ConsumoGenerator
from src.utils.csv_utils import listar_arquivos_entrada

def processar_tudo():
    """Processa todos os arquivos pendentes"""
    logger.info("🔍 Verificando arquivos...")
    
    # Processar consultas
    arquivos = listar_arquivos_entrada('consulta')
    for arquivo in arquivos:
        ConsultaProcessor.processar(arquivo)
    
    # Processar reservas
    arquivos = listar_arquivos_entrada('reserva')
    for arquivo in arquivos:
        ReservaProcessor.processar(arquivo)
    
    # Processar baixas
    arquivos = listar_arquivos_entrada('baixa')
    for arquivo in arquivos:
        BaixaProcessor.processar(arquivo)

def gerar_consumo():
    """Gera relatório de consumo"""
    from datetime import date
    logger.info("📊 Gerando relatório de consumo...")
    ConsumoGenerator.gerar(date.today())

def main():
    logger.info("🚀 Iniciando Sistema de Estoque e Farmácia - Grupo 3")
    
    try:
        db.connect()
        logger.info("✅ Conectado ao banco")
    except Exception as e:
        logger.error(f"❌ Erro no banco: {e}")
        return
    
    intervalo = int(os.getenv('PROCESSAMENTO_INTERVALO', 10))
    schedule.every(intervalo).seconds.do(processar_tudo)
    
    hora = int(os.getenv('CONSUMO_HORA_GERACAO', 23))
    schedule.every().day.at(f"{hora}:00").do(gerar_consumo)
    
    logger.info(f"⏰ Processamento a cada {intervalo} segundos")
    logger.info(f"📅 Geração de consumo às {hora}:00")
    
    # Executa uma vez ao iniciar
    processar_tudo()
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Sistema encerrado")
        db.close()