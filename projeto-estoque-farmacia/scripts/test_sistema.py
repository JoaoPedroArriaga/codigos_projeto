#!/usr/bin/env python
"""
Script para testar o fluxo completo do sistema
"""
import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import db
from src.processors.consulta_processor import ConsultaProcessor
from src.processors.reserva_processor import ReservaProcessor
from src.processors.baixa_processor import BaixaProcessor
from src.processors.consumo_generator import ConsumoGenerator
from src.utils.csv_utils import escrever_csv, gerar_nome_arquivo

def buscar_medicamentos():
    """Busca medicamentos disponíveis no banco"""
    db.connect()
    medicamentos = db.execute(
        "SELECT codigo FROM medicamentos ORDER BY codigo",
        fetch_all=True
    )
    db.close()
    return [m['codigo'] for m in medicamentos] if medicamentos else [789123]

def criar_arquivo_consulta(id_prescricao, cpf, codigo, quantidade):
    """Cria um arquivo de consulta"""
    dados = [{
        'id_prescricao': str(id_prescricao),
        'cpf_paciente': str(cpf),
        'codigo_medicamento': str(codigo),
        'quantidade': str(quantidade)
    }]
    
    nome_arquivo = gerar_nome_arquivo('CONSULTA', str(id_prescricao))
    caminho = os.path.join('data', 'entrada', 'consultas', nome_arquivo)
    campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade']
    escrever_csv(caminho, campos, dados)
    return caminho

def criar_arquivo_reserva(id_prescricao, cpf, codigo, quantidade):
    """Cria um arquivo de reserva (sem lote)"""
    dados = [{
        'id_prescricao': str(id_prescricao),
        'cpf_paciente': str(cpf),
        'codigo_medicamento': str(codigo),
        'quantidade': str(quantidade)
    }]
    
    nome_arquivo = gerar_nome_arquivo('RESERVA', str(id_prescricao))
    caminho = os.path.join('data', 'entrada', 'reservas', nome_arquivo)
    campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade']
    escrever_csv(caminho, campos, dados)
    return caminho

def criar_arquivo_baixa(id_prescricao, cpf, codigo, quantidade, lote):
    """Cria um arquivo de baixa"""
    data_uso = datetime.now().strftime('%y%m%d')
    
    dados = [{
        'id_prescricao': str(id_prescricao),
        'cpf_paciente': str(cpf),
        'codigo_medicamento': str(codigo),
        'quantidade': str(quantidade),
        'lote': lote,
        'data_uso': data_uso
    }]
    
    nome_arquivo = gerar_nome_arquivo('BAIXA', str(id_prescricao))
    caminho = os.path.join('data', 'entrada', 'baixas', nome_arquivo)
    campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade', 'lote', 'data_uso']
    escrever_csv(caminho, campos, dados)
    return caminho

def main():
    print("=" * 60)
    print("🧪 TESTE DO SISTEMA DE ESTOQUE E FARMÁCIA")
    print("=" * 60)
    
    # Buscar medicamentos
    print("\n📊 Buscando medicamentos...")
    medicamentos = buscar_medicamentos()
    
    if not medicamentos:
        print("❌ Nenhum medicamento encontrado!")
        return
    
    print(f"   ✅ Encontrados {len(medicamentos)} medicamentos")
    
    # CPFs para teste
    cpfs = [
        '12345678901', '98765432100', '11122233344', 
        '55566677788', '99988877766', '44455566677'
    ]
    
    quantidade_testes = 3
    print(f"\n📝 Gerando {quantidade_testes} fluxos de teste...\n")
    
    arquivos = {'consultas': [], 'reservas': []}
    
    for i in range(quantidade_testes):
        print(f"{'='*50}")
        print(f"🔹 TESTE {i+1}")
        print(f"{'='*50}")
        
        # Selecionar medicamento aleatório
        codigo = random.choice(medicamentos)
        quantidade = random.randint(1, 3)
        cpf = random.choice(cpfs)
        id_prescricao = int(f"{datetime.now().strftime('%H%M%S')}{i+1:03d}")
        
        print(f"   📋 ID Prescrição: {id_prescricao}")
        print(f"   💊 Medicamento: {codigo}")
        print(f"   🔢 Quantidade: {quantidade}")
        print(f"   👤 CPF: {cpf}")
        print()
        
        # Criar consulta
        print("   [1/3] Criando CONSULTA...")
        consulta = criar_arquivo_consulta(id_prescricao, cpf, codigo, quantidade)
        arquivos['consultas'].append(consulta)
        
        # Criar reserva (sem lote - G3 vai aplicar FEFO)
        print("   [2/3] Criando RESERVA...")
        reserva = criar_arquivo_reserva(id_prescricao, cpf, codigo, quantidade)
        arquivos['reservas'].append(reserva)
        
        print()
    
    # Processar arquivos
    print("=" * 60)
    print("⚙️ PROCESSANDO ARQUIVOS")
    print("=" * 60)
    
    db.connect()
    
    print("\n📄 Processando consultas...")
    for arquivo in arquivos['consultas']:
        ConsultaProcessor.processar(arquivo)
    
    print("\n🔒 Processando reservas...")
    for arquivo in arquivos['reservas']:
        ReservaProcessor.processar(arquivo)
    
    # Agora criar as baixas (precisamos saber qual lote foi reservado)
    print("\n📦 Buscando reservas para criar baixas...")
    
    # Buscar as reservas ativas para obter os lotes
    reservas_ativas = db.execute(
        "SELECT id_prescricao, cpf_paciente, codigo_medicamento, quantidade, lote FROM reservas_ativas WHERE status = 'RESERVADO'",
        fetch_all=True
    )
    
    arquivos_baixa = []
    for reserva in reservas_ativas:
        print(f"   Criando BAIXA para prescrição {reserva['id_prescricao']} (lote {reserva['lote']})")
        baixa = criar_arquivo_baixa(
            reserva['id_prescricao'],
            reserva['cpf_paciente'],
            reserva['codigo_medicamento'],
            reserva['quantidade'],
            reserva['lote']
        )
        arquivos_baixa.append(baixa)
    
    print("\n✅ Processando baixas...")
    for arquivo in arquivos_baixa:
        BaixaProcessor.processar(arquivo)
    
    # Gerar consumo
    print("\n📊 Gerando relatório de consumo...")
    from datetime import date
    ConsumoGenerator.gerar(date.today())
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("📈 RESULTADOS")
    print("=" * 60)
    
    lotes_atual = db.execute("SELECT * FROM lotes ORDER BY numero_lote", fetch_all=True)
    print("\n📦 Estoque atual:")
    for lote in lotes_atual:
        print(f"   - {lote['numero_lote']}: {lote['quantidade_atual']} unidades")
    
    itens = db.execute("SELECT * FROM itens_consumo ORDER BY id_item DESC", fetch_all=True)
    print(f"\n📋 Itens de consumo: {len(itens)}")
    total_valor = sum(float(i['preco_total']) for i in itens)
    print(f"   Valor total faturado: R$ {total_valor:.2f}")
    
    print("\n✅ TESTE CONCLUÍDO!")
    db.close()

if __name__ == "__main__":
    main()