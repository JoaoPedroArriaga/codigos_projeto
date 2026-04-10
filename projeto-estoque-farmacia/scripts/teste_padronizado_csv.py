#!/usr/bin/env python
"""
TESTE PADRONIZADO CSV
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
from src.utils.csv_utils import escrever_csv, gerar_nome_arquivo

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

def criar_consulta(id_presc, codigo, qtd):
    nome = gerar_nome_arquivo('CONSULTA', str(id_presc))
    caminho = BASE_DIR / 'data' / 'entrada' / 'consultas' / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = [{
        'id_prescricao': str(id_presc),
        'cpf_paciente': CPF_PADRAO,
        'codigo_medicamento': str(codigo),
        'quantidade': str(qtd)
    }]
    escrever_csv(str(caminho), ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade'], dados)
    return caminho

def criar_reserva(id_presc, codigo, qtd):
    nome = gerar_nome_arquivo('RESERVA', str(id_presc))
    caminho = BASE_DIR / 'data' / 'entrada' / 'reservas' / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = [{
        'id_prescricao': str(id_presc),
        'cpf_paciente': CPF_PADRAO,
        'codigo_medicamento': str(codigo),
        'quantidade': str(qtd)
    }]
    escrever_csv(str(caminho), ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade'], dados)
    return caminho

def criar_baixa(id_presc, codigo, qtd, lote):
    nome = gerar_nome_arquivo('BAIXA', str(id_presc))
    caminho = BASE_DIR / 'data' / 'entrada' / 'baixas' / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = [{
        'id_prescricao': str(id_presc),
        'cpf_paciente': CPF_PADRAO,
        'codigo_medicamento': str(codigo),
        'quantidade': str(qtd),
        'lote': lote,
        'data_uso': datetime.now().strftime('%y%m%d')
    }]
    escrever_csv(str(caminho), ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade', 'lote', 'data_uso'], dados)
    return caminho

def main():
    print("=" * 70)
    print("TESTE PADRONIZADO CSV")
    print("=" * 70)
    
    db.connect()
    limpar_tudo()
    
    # Criar pastas
    for pasta in ['consultas', 'reservas', 'baixas']:
        (BASE_DIR / 'data' / 'entrada' / pasta).mkdir(parents=True, exist_ok=True)
    for pasta in ['respostas', 'consumos']:
        (BASE_DIR / 'data' / 'saida' / pasta).mkdir(parents=True, exist_ok=True)
    for pasta in ['consultas', 'reservas', 'baixas']:
        (BASE_DIR / 'data' / 'processados' / pasta).mkdir(parents=True, exist_ok=True)
    
    # 1. GERACAO
    print("\n[1] GERANDO ARQUIVOS...")
    start_geracao = time.perf_counter()
    
    consultas = []
    reservas = []
    
    for i in range(NUM_CONSULTAS):
        idx = i % len(MEDICAMENTOS)
        codigo = MEDICAMENTOS[idx]
        qtd = QUANTIDADES[idx]
        id_presc = int(f"{datetime.now().strftime('%H%M%S')}{i:03d}")
        
        consulta = criar_consulta(id_presc, codigo, qtd)
        consultas.append((consulta, id_presc, codigo, qtd))
        
        reserva = criar_reserva(id_presc, codigo, qtd)
        reservas.append((reserva, id_presc, codigo, qtd))
        
        print(f"   [{i+1}] Gerado: Prescricao {id_presc}, Medicamento {codigo}, Qtd {qtd}")
    
    end_geracao = time.perf_counter()
    tempo_geracao = end_geracao - start_geracao
    print(f"\n   [OK] Geracao concluida em {tempo_geracao:.4f}s")
    
    # 2. PROCESSAMENTO
    print("\n[2] PROCESSANDO CONSULTAS...")
    start_process = time.perf_counter()
    
    for consulta, id_presc, codigo, qtd in consultas:
        ConsultaProcessor.processar(str(consulta))
        print(f"   Consulta {id_presc}: OK")
    
    print("\n[3] PROCESSANDO RESERVAS...")
    
    for reserva, id_presc, codigo, qtd in reservas:
        ReservaProcessor.processar(str(reserva))
        print(f"   Reserva {id_presc}: OK")
    
    print("\n[4] BUSCANDO LOTES PARA BAIXAS...")
    
    baixas = []
    for i, (_, id_presc, codigo, qtd) in enumerate(reservas):
        lote = db.execute(
            "SELECT lote FROM reservas_ativas WHERE id_prescricao = %s AND status = 'RESERVADO'",
            (id_presc,), fetch_one=True
        )
        if lote:
            baixa = criar_baixa(id_presc, codigo, qtd, lote['lote'])
            baixas.append(baixa)
            print(f"   Baixa {id_presc}: lote {lote['lote']}")
    
    print("\n[5] PROCESSANDO BAIXAS...")
    
    for baixa in baixas:
        BaixaProcessor.processar(str(baixa))
        print(f"   Baixa processada")
    
    end_process = time.perf_counter()
    tempo_processamento = end_process - start_process
    print(f"\n   [OK] Processamento concluido em {tempo_processamento:.4f}s")
    
    # 3. CONSUMO
    print("\n[6] GERANDO RELATORIO DE CONSUMO...")
    start_consumo = time.perf_counter()
    ConsumoGenerator.gerar(date.today())
    end_consumo = time.perf_counter()
    tempo_consumo = end_consumo - start_consumo
    print(f"   [OK] Consumo gerado em {tempo_consumo:.4f}s")
    
    tempo_total = tempo_geracao + tempo_processamento + tempo_consumo
    
    print("\n" + "=" * 70)
    print("RESULTADOS DO TESTE PADRONIZADO CSV")
    print("=" * 70)
    print(f"\n   Geracao de arquivos:  {tempo_geracao:.4f}s")
    print(f"   Processamento:        {tempo_processamento:.4f}s")
    print(f"   Geracao de consumo:   {tempo_consumo:.4f}s")
    print(f"   {'-' * 35}")
    print(f"   TOTAL:                {tempo_total:.4f}s")
    
    print(f"\nESTATISTICAS:")
    print(f"   Consultas: {NUM_CONSULTAS}")
    print(f"   Reservas: {NUM_CONSULTAS}")
    print(f"   Baixas: {len(baixas)}")
    
    db.close()
    print("\n[OK] Teste CSV concluido!")

if __name__ == "__main__":
    main()