#!/usr/bin/env python
"""
Script para gerar todos os arquivos de uma vez (fluxo completo)
Usa combinações válidas do banco
"""
import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gerar_consulta import gerar_consulta
from scripts.gerar_reserva import gerar_reserva
from scripts.gerar_baixa import gerar_baixa

def buscar_combinacoes_validas():
    """Busca combinações válidas de medicamentos e lotes"""
    from src.config.database import db
    
    db.connect()
    combinacoes = db.execute(
        """SELECT l.codigo_medicamento, l.numero_lote, l.quantidade_atual,
                  m.nome as medicamento_nome
           FROM lotes l
           JOIN medicamentos m ON m.codigo = l.codigo_medicamento
           WHERE l.quantidade_atual > 0
           ORDER BY l.codigo_medicamento""",
        fetch_all=True
    )
    db.close()
    return combinacoes

def gerar_fluxo_completo(quantidade=3):
    """Gera múltiplos fluxos completos com combinações válidas"""
    print("=" * 60)
    print("📦 GERANDO FLUXO COMPLETO MÚLTIPLO")
    print("=" * 60)
    
    combinacoes = buscar_combinacoes_validas()
    
    if not combinacoes:
        print("❌ Nenhuma combinação válida encontrada!")
        return
    
    print(f"\n📋 Combinações disponíveis: {len(combinacoes)}")
    for c in combinacoes:
        print(f"   - {c['medicamento_nome']} → lote {c['numero_lote']} (estoque: {c['quantidade_atual']})")
    
    cpfs = [
        '12345678901', '98765432100', '11122233344', 
        '55566677788', '99988877766', '44455566677'
    ]
    
    todos_arquivos = {'consultas': [], 'reservas': [], 'baixas': []}
    
    print(f"\n📝 Gerando {quantidade} fluxos completos...\n")
    
    for i in range(min(quantidade, len(combinacoes))):
        print(f"{'='*50}")
        print(f"🔹 FLUXO {i+1}")
        print(f"{'='*50}")
        
        # Selecionar combinação
        combo = combinacoes[i]
        codigo = combo['codigo_medicamento']
        lote_numero = combo['numero_lote']
        medicamento_nome = combo['medicamento_nome']
        estoque = float(combo['quantidade_atual'])
        
        # Quantidade (máximo 3 ou o que tiver em estoque)
        quantidade = random.randint(1, min(3, int(estoque)))
        
        # CPF
        cpf = random.choice(cpfs)
        
        # ID da prescrição
        id_prescricao = int(f"{datetime.now().strftime('%H%M%S')}{i+1:03d}")
        
        print(f"   📋 ID: {id_prescricao}")
        print(f"   💊 Medicamento: {medicamento_nome} (código {codigo})")
        print(f"   🏷️  Lote (para baixa): {lote_numero}")
        print(f"   🔢 Quantidade: {quantidade}")
        print(f"   👤 CPF: {cpf}")
        print()
        
        # Gerar consulta
        print("   [1/3] Gerando CONSULTA...")
        consulta = gerar_consulta(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        todos_arquivos['consultas'].append(consulta)
        
        # Gerar reserva (sem lote)
        print("   [2/3] Gerando RESERVA...")
        reserva = gerar_reserva(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        todos_arquivos['reservas'].append(reserva)
        
        # Gerar baixa (com o lote que será reservado)
        print("   [3/3] Gerando BAIXA...")
        baixa = gerar_baixa(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            lote=lote_numero,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        todos_arquivos['baixas'].append(baixa)
        
        print()
    
    # Resumo final
    print("=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    print(f"   Consultas: {len(todos_arquivos['consultas'])} arquivos")
    print(f"   Reservas: {len(todos_arquivos['reservas'])} arquivos")
    print(f"   Baixas: {len(todos_arquivos['baixas'])} arquivos")
    print(f"   Total: {sum(len(v) for v in todos_arquivos.values())} arquivos")
    print("\n✅ TODOS OS ARQUIVOS GERADOS!")
    print("   Agora o sistema vai processar automaticamente")
    print("=" * 60)
    
    return todos_arquivos

if __name__ == "__main__":
    gerar_fluxo_completo(3)