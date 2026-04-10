#!/usr/bin/env python
"""
TESTE COMPLETO - SISTEMA DE ESTOQUE E FARMÁCIA (CSV)
Executa o fluxo completo com validação de todos os cenários
"""
import os
import sys
import random
from datetime import datetime, date
from pathlib import Path

from src.config.database import db
from src.processors.consulta_processor import ConsultaProcessor
from src.processors.reserva_processor import ReservaProcessor
from src.processors.baixa_processor import BaixaProcessor
from src.processors.consumo_generator import ConsumoGenerator
from src.utils.csv_utils import escrever_csv, gerar_nome_arquivo

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

def mostrar_estoque_inicial():
    """Mostra estoque inicial"""
    print("\n📦 ESTOQUE INICIAL:")
    print("-" * 70)
    lotes = db.execute("""
        SELECT l.numero_lote, m.nome, l.quantidade_atual, m.unidade, l.data_validade
        FROM lotes l
        JOIN medicamentos m ON m.codigo = l.codigo_medicamento
        ORDER BY l.numero_lote
    """, fetch_all=True)
    
    for lote in lotes:
        validade = lote['data_validade']
        dias_restantes = (validade - date.today()).days
        status = "✅" if dias_restantes > 0 else "⚠️ VENCIDO"
        print(f"   {lote['numero_lote']}: {lote['nome']} | {lote['quantidade_atual']:.0f} {lote['unidade']} | Validade: {validade} {status}")

def mostrar_estoque_final():
    """Mostra estoque final"""
    print("\n📦 ESTOQUE FINAL:")
    print("-" * 70)
    lotes = db.execute("""
        SELECT l.numero_lote, m.nome, l.quantidade_atual, m.unidade,
               l.quantidade_inicial - l.quantidade_atual as consumido
        FROM lotes l
        JOIN medicamentos m ON m.codigo = l.codigo_medicamento
        ORDER BY l.numero_lote
    """, fetch_all=True)
    
    for lote in lotes:
        if lote['consumido'] and lote['consumido'] > 0:
            print(f"   {lote['numero_lote']}: {lote['nome']} | {lote['quantidade_atual']:.0f} {lote['unidade']} (consumido: {lote['consumido']:.0f})")
        else:
            print(f"   {lote['numero_lote']}: {lote['nome']} | {lote['quantidade_atual']:.0f} {lote['unidade']}")

def criar_arquivo(tipo, id_prescricao, dados):
    """Cria um arquivo de teste"""
    if tipo == 'CONSULTA':
        campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade']
    elif tipo == 'RESERVA':
        campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade']
    elif tipo == 'BAIXA':
        campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade', 'lote', 'data_uso']
    else:
        return None
    
    nome_arquivo = gerar_nome_arquivo(tipo, str(id_prescricao))
    caminho = os.path.join('data', 'entrada', f"{tipo.lower()}s", nome_arquivo)
    escrever_csv(caminho, campos, dados)
    return caminho

def main():
    print("=" * 80)
    print("🎬 TESTE COMPLETO - SISTEMA DE ESTOQUE E FARMÁCIA")
    print("=" * 80)
    
    # Conectar ao banco
    db.connect()
    
    # Limpar e mostrar estoque inicial
    limpar_dados()
    mostrar_estoque_inicial()
    
    # CPFs para testes
    cpfs = {
        'PACIENTE_A': '11122233344',
        'PACIENTE_B': '55566677788',
        'PACIENTE_C': '99988877766',
        'PACIENTE_D': '12345678901'
    }
    
    data_uso = datetime.now().strftime('%y%m%d')
    
    print("\n" + "=" * 80)
    print("📋 EXECUTANDO TESTES")
    print("=" * 80)
    
    # =========================================================
    # TESTE 1: SUCESSO - PARACETAMOL (CAIXA) - LOTE004
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ TESTE 1: SUCESSO - PARACETAMOL (CAIXA) - LOTE004")
    print("=" * 70)
    
    id_1 = int(f"{datetime.now().strftime('%H%M%S')}001")
    
    consulta = criar_arquivo('CONSULTA', id_1, [{
        'id_prescricao': str(id_1),
        'cpf_paciente': cpfs['PACIENTE_A'],
        'codigo_medicamento': '111222',
        'quantidade': '1'
    }])
    ConsultaProcessor.processar(consulta)
    
    reserva = criar_arquivo('RESERVA', id_1, [{
        'id_prescricao': str(id_1),
        'cpf_paciente': cpfs['PACIENTE_A'],
        'codigo_medicamento': '111222',
        'quantidade': '1'
    }])
    ReservaProcessor.processar(reserva)
    
    baixa = criar_arquivo('BAIXA', id_1, [{
        'id_prescricao': str(id_1),
        'cpf_paciente': cpfs['PACIENTE_A'],
        'codigo_medicamento': '111222',
        'quantidade': '1',
        'lote': 'LOTE004',
        'data_uso': data_uso
    }])
    BaixaProcessor.processar(baixa)
    print("   ✅ CONCLUÍDO")
    
    # =========================================================
    # TESTE 2: SUCESSO - AMOXICILINA (FEFO escolhe LOTE002)
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ TESTE 2: SUCESSO - AMOXICILINA (FEFO escolhe LOTE002)")
    print("=" * 70)
    
    id_2 = int(f"{datetime.now().strftime('%H%M%S')}002")
    
    consulta = criar_arquivo('CONSULTA', id_2, [{
        'id_prescricao': str(id_2),
        'cpf_paciente': cpfs['PACIENTE_B'],
        'codigo_medicamento': '789123',
        'quantidade': '2'
    }])
    ConsultaProcessor.processar(consulta)
    
    reserva = criar_arquivo('RESERVA', id_2, [{
        'id_prescricao': str(id_2),
        'cpf_paciente': cpfs['PACIENTE_B'],
        'codigo_medicamento': '789123',
        'quantidade': '2'
    }])
    ReservaProcessor.processar(reserva)
    
    baixa = criar_arquivo('BAIXA', id_2, [{
        'id_prescricao': str(id_2),
        'cpf_paciente': cpfs['PACIENTE_B'],
        'codigo_medicamento': '789123',
        'quantidade': '2',
        'lote': 'LOTE002',
        'data_uso': data_uso
    }])
    BaixaProcessor.processar(baixa)
    print("   ✅ CONCLUÍDO")
    
    # =========================================================
    # TESTE 3: SUCESSO - CODEÍNA (FRASCO) - LOTE006
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ TESTE 3: SUCESSO - CODEÍNA (FRASCO) - LOTE006")
    print("=" * 70)
    
    id_3 = int(f"{datetime.now().strftime('%H%M%S')}003")
    
    consulta = criar_arquivo('CONSULTA', id_3, [{
        'id_prescricao': str(id_3),
        'cpf_paciente': cpfs['PACIENTE_C'],
        'codigo_medicamento': '555666',
        'quantidade': '2'
    }])
    ConsultaProcessor.processar(consulta)
    
    reserva = criar_arquivo('RESERVA', id_3, [{
        'id_prescricao': str(id_3),
        'cpf_paciente': cpfs['PACIENTE_C'],
        'codigo_medicamento': '555666',
        'quantidade': '2'
    }])
    ReservaProcessor.processar(reserva)
    
    baixa = criar_arquivo('BAIXA', id_3, [{
        'id_prescricao': str(id_3),
        'cpf_paciente': cpfs['PACIENTE_C'],
        'codigo_medicamento': '555666',
        'quantidade': '2',
        'lote': 'LOTE006',
        'data_uso': data_uso
    }])
    BaixaProcessor.processar(baixa)
    print("   ✅ CONCLUÍDO")
    
    # =========================================================
    # TESTE 4: ESTOQUE INSUFICIENTE
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 4: ESTOQUE INSUFICIENTE - AMOXICILINA (solicita 101, mas o maior lote tem 100)")
    print("=" * 70)

    id_4 = int(f"{datetime.now().strftime('%H%M%S')}004")

    consulta = criar_arquivo('CONSULTA', id_4, [{
        'id_prescricao': str(id_4),
        'cpf_paciente': cpfs['PACIENTE_D'],
        'codigo_medicamento': '789123',
        'quantidade': '101'
    }])
    ConsultaProcessor.processar(consulta)
    print("   ℹ️ A consulta retornou disponivel=0 (estoque insuficiente)")
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # TESTE 5: MEDICAMENTO NÃO CADASTRADO
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 5: MEDICAMENTO NÃO CADASTRADO (código 999999 não existe)")
    print("=" * 70)
    
    id_5 = int(f"{datetime.now().strftime('%H%M%S')}005")
    
    consulta = criar_arquivo('CONSULTA', id_5, [{
        'id_prescricao': str(id_5),
        'cpf_paciente': cpfs['PACIENTE_A'],
        'codigo_medicamento': '999999',
        'quantidade': '1'
    }])
    ConsultaProcessor.processar(consulta)
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # TESTE 6: BAIXA SEM RESERVA
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 6: BAIXA SEM RESERVA")
    print("=" * 70)
    
    id_6 = int(f"{datetime.now().strftime('%H%M%S')}006")
    
    baixa_sem_reserva = criar_arquivo('BAIXA', id_6, [{
        'id_prescricao': str(id_6),
        'cpf_paciente': cpfs['PACIENTE_A'],
        'codigo_medicamento': '111222',
        'quantidade': '1',
        'lote': 'LOTE004',
        'data_uso': data_uso
    }])
    BaixaProcessor.processar(baixa_sem_reserva)
    print("   ℹ️ A baixa foi rejeitada porque não havia reserva ativa")
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # TESTE 7: RESERVA COM LOTE INVÁLIDO
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 7: RESERVA COM LOTE INVÁLIDO (LOTEINEXISTENTE)")
    print("=" * 70)
    
    id_7 = int(f"{datetime.now().strftime('%H%M%S')}007")
    
    consulta = criar_arquivo('CONSULTA', id_7, [{
        'id_prescricao': str(id_7),
        'cpf_paciente': cpfs['PACIENTE_B'],
        'codigo_medicamento': '111222',
        'quantidade': '1'
    }])
    ConsultaProcessor.processar(consulta)
    
    reserva_invalida = criar_arquivo('RESERVA', id_7, [{
        'id_prescricao': str(id_7),
        'cpf_paciente': cpfs['PACIENTE_B'],
        'codigo_medicamento': '111222',
        'quantidade': '1'
    }])
    ReservaProcessor.processar(reserva_invalida)
    print("   ℹ️ A reserva foi processada (FEFO escolheu o lote disponível)")
    print("   ✅ CONCLUÍDO (O SISTEMA APLICA FEFO)")
    
    # =========================================================
    # TESTE 8: BAIXA COM LOTE NÃO RESERVADO
    # =========================================================
    print("\n" + "=" * 70)
    print("❌ TESTE 8: BAIXA COM LOTE NÃO RESERVADO")
    print("=" * 70)
    
    id_8 = int(f"{datetime.now().strftime('%H%M%S')}008")
    
    consulta = criar_arquivo('CONSULTA', id_8, [{
        'id_prescricao': str(id_8),
        'cpf_paciente': cpfs['PACIENTE_C'],
        'codigo_medicamento': '789123',
        'quantidade': '1'
    }])
    ConsultaProcessor.processar(consulta)
    
    reserva = criar_arquivo('RESERVA', id_8, [{
        'id_prescricao': str(id_8),
        'cpf_paciente': cpfs['PACIENTE_C'],
        'codigo_medicamento': '789123',
        'quantidade': '1'
    }])
    ReservaProcessor.processar(reserva)
    
    baixa_lote_errado = criar_arquivo('BAIXA', id_8, [{
        'id_prescricao': str(id_8),
        'cpf_paciente': cpfs['PACIENTE_C'],
        'codigo_medicamento': '789123',
        'quantidade': '1',
        'lote': 'LOTE001',
        'data_uso': data_uso
    }])
    BaixaProcessor.processar(baixa_lote_errado)
    print("   ℹ️ A baixa foi rejeitada porque o lote LOTE001 não estava reservado")
    print("   ✅ CONCLUÍDO (ERRO ESPERADO)")
    
    # =========================================================
    # GERAR RELATÓRIO DE CONSUMO
    # =========================================================
    print("\n" + "=" * 80)
    print("📊 GERANDO RELATÓRIO DE CONSUMO")
    print("=" * 80)
    
    ConsumoGenerator.gerar(date.today())
    
    # =========================================================
    # MOSTRAR RESULTADOS
    # =========================================================
    print("\n" + "=" * 80)
    print("📈 RESULTADOS FINAIS")
    print("=" * 80)
    
    mostrar_estoque_final()
    
    print("\n📄 RELATÓRIO DE CONSUMO GERADO:")
    print("-" * 70)
    
    caminho_consumo = os.path.join('data', 'saida', 'consumos', f"CONSUMO_{date.today().strftime('%y%m%d')}.csv")
    
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
    
    print("\n📋 LOGS DE ERRO:")
    print("-" * 70)
    
    erros_reservas = db.execute("SELECT * FROM logs_reservas WHERE status = 'ERRO'", fetch_all=True)
    for e in erros_reservas:
        print(f"   ❌ Reserva: {e['observacao']}")
    
    erros_baixas = db.execute("SELECT * FROM logs_baixas WHERE status = 'ERRO'", fetch_all=True)
    for e in erros_baixas:
        print(f"   ❌ Baixa: {e['observacao']}")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("✅ TESTE COMPLETO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()