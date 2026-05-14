#!/usr/bin/env python
"""
TESTE PADRONIZADO XML
"""
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

print(f"[DIR] Diretorio: {os.getcwd()}")

from src.config.database import db
from src.processors.consulta_processor import ConsultaProcessor
from src.processors.reserva_processor import ReservaProcessor
from src.processors.baixa_processor import BaixaProcessor
from src.processors.consumo_generator import ConsumoGenerator
from scripts.gerar_consulta_xml import gerar_consulta_xml
from scripts.gerar_reserva_xml import gerar_reserva_xml
from scripts.gerar_baixa_xml import gerar_baixa_xml

NUM_CONSULTAS = 5
CPF_PADRAO = "11122233344"
MEDICAMENTOS = [111222, 789123, 555666]
QUANTIDADES = [1, 2, 1]

def limpar_tudo():
    print("[LIMPEZA] Limpando banco...")
    db.execute("TRUNCATE TABLE itens_consumo CASCADE")
    db.execute("TRUNCATE TABLE logs_consultas CASCADE")
    db.execute("TRUNCATE TABLE logs_reservas CASCADE")
    db.execute("TRUNCATE TABLE logs_baixas CASCADE")
    db.execute("TRUNCATE TABLE logs_consumos CASCADE")
    db.execute("TRUNCATE TABLE reservas_ativas CASCADE")
    db.execute("UPDATE lotes SET quantidade_atual = quantidade_inicial")
    db.commit()

def criar_pastas():
    pastas = [
        "data/entrada/consultas",
        "data/entrada/reservas",
        "data/entrada/baixas",
        "data/saida/respostas",
        "data/saida/consumos",
        "data/processados/consultas",
        "data/processados/reservas",
        "data/processados/baixas",
    ]
    for pasta in pastas:
        caminho = BASE_DIR / pasta
        caminho.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 70)
    print("TESTE PADRONIZADO XML")
    print("=" * 70)
    
    criar_pastas()
    
    db.connect()
    limpar_tudo()
    
    # 1. GERACAO
    print("\n[1] GERANDO ARQUIVOS XML...")
    start_geracao = time.perf_counter()
    
    consultas = []
    reservas = []
    
    for i in range(NUM_CONSULTAS):
        idx = i % len(MEDICAMENTOS)
        codigo = MEDICAMENTOS[idx]
        qtd = QUANTIDADES[idx]
        id_presc = f"{datetime.now().strftime('%H%M%S')}{i:03d}"
        
        consulta = gerar_consulta_xml(codigo, qtd, id_presc, CPF_PADRAO)
        consultas.append((consulta, id_presc, codigo, qtd))
        
        reserva = gerar_reserva_xml(codigo, qtd, id_presc, CPF_PADRAO)
        reservas.append((reserva, id_presc, codigo, qtd))
        
        print(f"   [{i+1}] Gerado: Prescricao {id_presc}, Medicamento {codigo}, Qtd {qtd}")
    
    end_geracao = time.perf_counter()
    tempo_geracao = end_geracao - start_geracao
    print(f"\n   [OK] Geracao concluida em {tempo_geracao:.4f}s")
    
    # 2. PROCESSAMENTO
    print("\n[2] PROCESSANDO CONSULTAS XML...")
    start_process = time.perf_counter()
    
    for consulta, id_presc, codigo, qtd in consultas:
        ConsultaProcessor.processar(consulta)
        print(f"   Consulta {id_presc}: OK")
    
    print("\n[3] PROCESSANDO RESERVAS XML...")
    
    for reserva, id_presc, codigo, qtd in reservas:
        ReservaProcessor.processar(reserva)
        print(f"   Reserva {id_presc}: OK")
    
    print("\n[4] BUSCANDO LOTES PARA BAIXAS XML...")
    
    baixas = []
    for i, (_, id_presc, codigo, qtd) in enumerate(reservas):
        lote = db.execute(
            "SELECT lote FROM reservas_ativas WHERE id_prescricao = %s AND status = 'RESERVADO'",
            (id_presc,), fetch_one=True
        )
        if lote:
            baixa = gerar_baixa_xml(codigo, qtd, lote['lote'], id_presc, CPF_PADRAO)
            baixas.append(baixa)
            print(f"   Baixa {id_presc}: lote {lote['lote']}")
    
    print("\n[5] PROCESSANDO BAIXAS XML...")
    
    for baixa in baixas:
        BaixaProcessor.processar(baixa)
        print("   Baixa processada")
    
    end_process = time.perf_counter()
    tempo_processamento = end_process - start_process
    print(f"\n   [OK] Processamento concluido em {tempo_processamento:.4f}s")
    
    # 3. CONSUMO
    print("\n[6] GERANDO RELATORIO DE CONSUMO XML...")
    start_consumo = time.perf_counter()
    ConsumoGenerator.gerar(date.today())
    end_consumo = time.perf_counter()
    tempo_consumo = end_consumo - start_consumo
    print(f"   [OK] Consumo gerado em {tempo_consumo:.4f}s")
    
    tempo_total = tempo_geracao + tempo_processamento + tempo_consumo
    
    print("\n" + "=" * 70)
    print("RESULTADOS DO TESTE PADRONIZADO XML")
    print("=" * 70)
    print(f"\n   Geracao de arquivos:  {tempo_geracao:.4f}s")
    print(f"   Processamento:        {tempo_processamento:.4f}s")
    print(f"   Geracao de consumo:   {tempo_consumo:.4f}s")
    print(f"   {'-' * 35}")
    print(f"   TOTAL:                {tempo_total:.4f}s")
    
    print("\nESTATISTICAS:")
    print(f"   Consultas: {NUM_CONSULTAS}")
    print(f"   Reservas: {NUM_CONSULTAS}")
    print(f"   Baixas: {len(baixas)}")
    
    db.close()
    print("\n[OK] Teste XML concluido!")

if __name__ == "__main__":
    main()