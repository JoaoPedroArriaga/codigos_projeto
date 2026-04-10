#!/usr/bin/env python
"""
Script para testar o fluxo completo do sistema com XML
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
from scripts.gerar_consulta_xml import gerar_consulta_xml
from scripts.gerar_reserva_xml import gerar_reserva_xml
from scripts.gerar_baixa_xml import gerar_baixa_xml

def buscar_medicamentos():
    """Busca medicamentos disponíveis no banco"""
    db.connect()
    medicamentos = db.execute("SELECT codigo FROM medicamentos ORDER BY codigo", fetch_all=True)
    db.close()
    return [m['codigo'] for m in medicamentos] if medicamentos else [789123]

def main():
    print("=" * 60)
    print("🧪 TESTE XML DO SISTEMA DE ESTOQUE E FARMÁCIA")
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
    print(f"\n📝 Gerando {quantidade_testes} fluxos de teste com XML...\n")
    
    consultas = []
    reservas = []
    
    for i in range(quantidade_testes):
        print(f"{'='*50}")
        print(f"🔹 TESTE {i+1}")
        print(f"{'='*50}")
        
        # Selecionar medicamento aleatório
        codigo = random.choice(medicamentos)
        quantidade = random.randint(1, 3)
        cpf = random.choice(cpfs)
        # ID ÚNICO para cada teste (timestamp + índice)
        id_prescricao = f"{datetime.now().strftime('%H%M%S')}{i+1:03d}"
        
        print(f"   📋 ID Prescrição: {id_prescricao}")
        print(f"   💊 Medicamento: {codigo}")
        print(f"   🔢 Quantidade: {quantidade}")
        print(f"   👤 CPF: {cpf}")
        print()
        
        # Criar consulta XML
        print("   [1/3] Criando CONSULTA XML...")
        consulta = gerar_consulta_xml(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        consultas.append(consulta)
        
        # Criar reserva XML (sem lote)
        print("   [2/3] Criando RESERVA XML...")
        reserva = gerar_reserva_xml(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        reservas.append(reserva)
        
        print()
    
    # Processar arquivos
    print("=" * 60)
    print("⚙️ PROCESSANDO ARQUIVOS XML")
    print("=" * 60)
    
    db.connect()
    
    print("\n📄 Processando consultas XML...")
    for arquivo in consultas:
        # Verificar se o arquivo ainda existe
        if os.path.exists(arquivo):
            ConsultaProcessor.processar(arquivo)
        else:
            print(f"   ⚠️ Arquivo não encontrado: {arquivo}")
    
    print("\n🔒 Processando reservas XML...")
    for arquivo in reservas:
        if os.path.exists(arquivo):
            ReservaProcessor.processar(arquivo)
        else:
            print(f"   ⚠️ Arquivo não encontrado: {arquivo}")
    
    # Buscar reservas ativas para criar baixas
    print("\n📦 Buscando reservas para criar baixas...")
    
    reservas_ativas = db.execute(
        "SELECT id_prescricao, cpf_paciente, codigo_medicamento, quantidade, lote FROM reservas_ativas WHERE status = 'RESERVADO'",
        fetch_all=True
    )
    
    baixas = []
    for reserva in reservas_ativas:
        print(f"   Criando BAIXA XML para prescrição {reserva['id_prescricao']} (lote {reserva['lote']})")
        baixa = gerar_baixa_xml(
            codigo_medicamento=reserva['codigo_medicamento'],
            quantidade=reserva['quantidade'],
            lote=reserva['lote'],
            id_prescricao=reserva['id_prescricao'],
            cpf_paciente=reserva['cpf_paciente']
        )
        baixas.append(baixa)
    
    print("\n✅ Processando baixas XML...")
    for arquivo in baixas:
        if os.path.exists(arquivo):
            BaixaProcessor.processar(arquivo)
        else:
            print(f"   ⚠️ Arquivo não encontrado: {arquivo}")
    
    # Gerar consumo
    print("\n📊 Gerando relatório de consumo XML...")
    from datetime import date
    ConsumoGenerator.gerar(date.today())
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("📈 RESULTADOS")
    print("=" * 60)

    # Buscar estoque uma única vez
    lotes_atual = db.execute("SELECT * FROM lotes ORDER BY numero_lote", fetch_all=True)

    print("\n📦 Estoque atual:")
    for lote in lotes_atual:
        print(f"   - {lote['numero_lote']}: {lote['quantidade_atual']} unidades")

    itens = db.execute("SELECT * FROM itens_consumo ORDER BY id_item DESC", fetch_all=True)
    print(f"\n📋 Itens de consumo: {len(itens)}")
    total_valor = sum(float(i['preco_total']) for i in itens)
    print(f"   Valor total faturado: R$ {total_valor:.2f}")

    print("\n📁 Arquivos XML gerados:")
    print(f"   Consultas: {len(consultas)}")
    print(f"   Reservas: {len(reservas)}")
    print(f"   Baixas: {len(baixas)}")

    print("\n✅ TESTE XML CONCLUÍDO!")
    db.close()

if __name__ == "__main__":
    main()