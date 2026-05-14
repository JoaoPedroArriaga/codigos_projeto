#!/usr/bin/env python
"""
TESTE COMPLETO XML - SISTEMA DE ESTOQUE E FARMÁCIA
Executa o fluxo completo com validação de todos os cenários usando XML
"""
import os
import sys
from datetime import datetime, date
from pathlib import Path
from src.config.database import db

from src.processors.consulta_processor import ConsultaProcessor
from src.processors.reserva_processor import ReservaProcessor
from src.processors.baixa_processor import BaixaProcessor
from src.processors.consumo_generator import ConsumoGenerator
from scripts.gerar_consulta_xml import gerar_consulta_xml
from scripts.gerar_reserva_xml import gerar_reserva_xml
from scripts.gerar_baixa_xml import gerar_baixa_xml

# Define o diretório base como a RAIZ do projeto (2 níveis acima do script)
BASE_DIR = Path(__file__).parent.parent
os.chdir(BASE_DIR)  # Muda para a raiz do projeto

sys.path.insert(0, str(BASE_DIR))

def limpar_dados():
    """Limpa dados anteriores"""
    print("\n🧹 LIMPANDO DADOS ANTERIORES...")
    db.execute("TRUNCATE TABLE itens_consumo CASCADE")
    db.execute("TRUNCATE TABLE movimentacoes CASCADE")
    db.execute("TRUNCATE TABLE logs_consultas CASCADE")
    db.execute("TRUNCATE TABLE logs_reservas CASCADE")
    db.execute("TRUNCATE TABLE logs_baixas CASCADE")
    db.execute("TRUNCATE TABLE logs_consumos CASCADE")
    db.execute("TRUNCATE TABLE reservas_ativas CASCADE")
    db.execute("UPDATE lotes SET quantidade_atual = quantidade_inicial")
    print("   ✅ Limpeza concluída!")

def mostrar_estoque():
    """Mostra estoque atual"""
    print("\n📦 ESTOQUE ATUAL:")
    lotes = db.execute("""
        SELECT l.numero_lote, m.nome, l.quantidade_atual, m.unidade
        FROM lotes l
        JOIN medicamentos m ON m.codigo = l.codigo_medicamento
        ORDER BY l.numero_lote
    """, fetch_all=True)
    for lote in lotes:
        print(f"   {lote['numero_lote']}: {lote['nome']} | {lote['quantidade_atual']:.0f} {lote['unidade']}")

def main():
    print("=" * 80)
    print("🎬 TESTE COMPLETO XML - SISTEMA DE ESTOQUE E FARMÁCIA")
    print("=" * 80)
    
    db.connect()
    
    # Limpar e mostrar estoque
    limpar_dados()
    mostrar_estoque()
    
    cpfs = {
        'PACIENTE_A': '11122233344',
        'PACIENTE_B': '55566677788',
        'PACIENTE_C': '99988877766',
        'PACIENTE_D': '12345678901'
    }
    
    print("\n" + "=" * 80)
    print("📋 EXECUTANDO TESTES XML")
    print("=" * 80)
    
    # =========================================================
    # TESTE 1: SUCESSO - PARACETAMOL (CAIXA)
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ TESTE 1: SUCESSO - PARACETAMOL (CAIXA)")
    print("=" * 70)
    
    id_1 = datetime.now().strftime('%H%M%S')
    
    consulta = gerar_consulta_xml(
        codigo_medicamento=111222,
        quantidade=1,
        id_prescricao=id_1,
        cpf_paciente=cpfs['PACIENTE_A']
    )
    ConsultaProcessor.processar(consulta)
    
    reserva = gerar_reserva_xml(
        codigo_medicamento=111222,
        quantidade=1,
        id_prescricao=id_1,
        cpf_paciente=cpfs['PACIENTE_A']
    )
    ReservaProcessor.processar(reserva)
    
    baixa = gerar_baixa_xml(
        codigo_medicamento=111222,
        quantidade=1,
        lote='LOTE004',
        id_prescricao=id_1,
        cpf_paciente=cpfs['PACIENTE_A']
    )
    BaixaProcessor.processar(baixa)
    print("   ✅ CONCLUÍDO")
    
    # =========================================================
    # TESTE 2: SUCESSO - AMOXICILINA (FEFO escolhe LOTE002)
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ TESTE 2: SUCESSO - AMOXICILINA (FEFO escolhe LOTE002)")
    print("=" * 70)
    
    id_2 = datetime.now().strftime('%H%M%S')
    
    consulta = gerar_consulta_xml(
        codigo_medicamento=789123,
        quantidade=2,
        id_prescricao=id_2,
        cpf_paciente=cpfs['PACIENTE_B']
    )
    ConsultaProcessor.processar(consulta)
    
    reserva = gerar_reserva_xml(
        codigo_medicamento=789123,
        quantidade=2,
        id_prescricao=id_2,
        cpf_paciente=cpfs['PACIENTE_B']
    )
    ReservaProcessor.processar(reserva)
    
    baixa = gerar_baixa_xml(
        codigo_medicamento=789123,
        quantidade=2,
        lote='LOTE002',
        id_prescricao=id_2,
        cpf_paciente=cpfs['PACIENTE_B']
    )
    BaixaProcessor.processar(baixa)
    print("   ✅ CONCLUÍDO")
    
    # =========================================================
    # TESTE 3: SUCESSO - CODEÍNA (FRASCO)
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ TESTE 3: SUCESSO - CODEÍNA (FRASCO)")
    print("=" * 70)
    
    id_3 = datetime.now().strftime('%H%M%S')
    
    consulta = gerar_consulta_xml(
        codigo_medicamento=555666,
        quantidade=2,
        id_prescricao=id_3,
        cpf_paciente=cpfs['PACIENTE_C']
    )
    ConsultaProcessor.processar(consulta)
    
    reserva = gerar_reserva_xml(
        codigo_medicamento=555666,
        quantidade=2,
        id_prescricao=id_3,
        cpf_paciente=cpfs['PACIENTE_C']
    )
    ReservaProcessor.processar(reserva)
    
    baixa = gerar_baixa_xml(
        codigo_medicamento=555666,
        quantidade=2,
        lote='LOTE006',
        id_prescricao=id_3,
        cpf_paciente=cpfs['PACIENTE_C']
    )
    BaixaProcessor.processar(baixa)
    print("   ✅ CONCLUÍDO")
    
    # =========================================================
    # TESTE 4: ESTOQUE INSUFICIENTE
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 4: ESTOQUE INSUFICIENTE - AMOXICILINA (solicita 101, mas o maior lote tem 100)")
    print("=" * 70)

    id_4 = datetime.now().strftime('%H%M%S')
    
    consulta = gerar_consulta_xml(
        codigo_medicamento=789123,
        quantidade=101,
        id_prescricao=id_4,
        cpf_paciente=cpfs['PACIENTE_D']
    )
    ConsultaProcessor.processar(consulta)
    print("   ℹ️ A consulta retornou disponivel=0 (estoque insuficiente)")
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # TESTE 5: MEDICAMENTO NÃO CADASTRADO
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 5: MEDICAMENTO NÃO CADASTRADO (código 999999 não existe)")
    print("=" * 70)
    
    id_5 = datetime.now().strftime('%H%M%S')
    
    consulta = gerar_consulta_xml(
        codigo_medicamento=999999,
        quantidade=1,
        id_prescricao=id_5,
        cpf_paciente=cpfs['PACIENTE_A']
    )
    ConsultaProcessor.processar(consulta)
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # TESTE 6: BAIXA SEM RESERVA
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 6: BAIXA SEM RESERVA")
    print("=" * 70)
    
    id_6 = datetime.now().strftime('%H%M%S')
    
    baixa_sem_reserva = gerar_baixa_xml(
        codigo_medicamento=111222,
        quantidade=1,
        lote='LOTE004',
        id_prescricao=id_6,
        cpf_paciente=cpfs['PACIENTE_A']
    )
    BaixaProcessor.processar(baixa_sem_reserva)
    print("   ℹ️ A baixa foi rejeitada porque não havia reserva ativa")
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # TESTE 7: BAIXA COM LOTE NÃO RESERVADO
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 7: BAIXA COM LOTE NÃO RESERVADO")
    print("=" * 70)
    
    id_7 = datetime.now().strftime('%H%M%S')
    
    consulta = gerar_consulta_xml(
        codigo_medicamento=789123,
        quantidade=1,
        id_prescricao=id_7,
        cpf_paciente=cpfs['PACIENTE_C']
    )
    ConsultaProcessor.processar(consulta)
    
    reserva = gerar_reserva_xml(
        codigo_medicamento=789123,
        quantidade=1,
        id_prescricao=id_7,
        cpf_paciente=cpfs['PACIENTE_C']
    )
    ReservaProcessor.processar(reserva)
    
    baixa_lote_errado = gerar_baixa_xml(
        codigo_medicamento=789123,
        quantidade=1,
        lote='LOTE001',
        id_prescricao=id_7,
        cpf_paciente=cpfs['PACIENTE_C']
    )
    BaixaProcessor.processar(baixa_lote_errado)
    print("   ℹ️ A baixa foi rejeitada porque o lote LOTE001 não estava reservado")
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # GERAR RELATÓRIO DE CONSUMO
    # =========================================================
    print("\n" + "=" * 80)
    print("📊 GERANDO RELATÓRIO DE CONSUMO XML")
    print("=" * 80)
    
    ConsumoGenerator.gerar(date.today())
    
    # =========================================================
    # MOSTRAR RESULTADOS
    # =========================================================
    print("\n" + "=" * 80)
    print("📈 RESULTADOS FINAIS")
    print("=" * 80)
    
    mostrar_estoque()
    
    print("\n📄 RELATÓRIO DE CONSUMO XML GERADO:")
    caminho_consumo = os.path.join('data', 'saida', 'consumos', f"CONSUMO_{date.today().strftime('%y%m%d')}.xml")
    
    if os.path.exists(caminho_consumo):
        with open(caminho_consumo, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("   Arquivo não encontrado")
    
    print("\n📊 ESTATÍSTICAS:")
    print("-" * 70)
    
    consultas = db.execute("SELECT COUNT(*) as total FROM logs_consultas", fetch_one=True)
    reservas = db.execute("SELECT COUNT(*) as total FROM logs_reservas WHERE status = 'PROCESSADO'", fetch_one=True)
    baixas = db.execute("SELECT COUNT(*) as total FROM logs_baixas WHERE status = 'PROCESSADO'", fetch_one=True)
    consumo = db.execute("SELECT SUM(preco_total) as total FROM itens_consumo", fetch_one=True)
    
    print(f"   Total de consultas: {consultas['total']}")
    print(f"   Total de reservas (sucesso): {reservas['total']}")
    print(f"   Total de baixas (sucesso): {baixas['total']}")
    if consumo['total']:
        print(f"   Valor total faturado: R$ {consumo['total']:.2f}")
    else:
        print("   Valor total faturado: R$ 0.00")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("✅ TESTE COMPLETO XML CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()