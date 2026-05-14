#!/usr/bin/env python
"""
Script para verificar o estado atual do banco
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import db

def verificar_banco():
    print("=" * 70)
    print("🔍 VERIFICANDO ESTADO DO BANCO")
    print("=" * 70)
    
    db.connect()
    
    # 1. Medicamentos
    print("\n1. MEDICAMENTOS:")
    medicamentos = db.execute("SELECT * FROM medicamentos ORDER BY codigo", fetch_all=True)
    
    if not medicamentos:
        print("   ❌ Nenhum medicamento encontrado!")
    else:
        print(f"   ✅ {len(medicamentos)} medicamentos:")
        for m in medicamentos:
            unidade = m.get('unidade', 'NÃO DEFINIDA')
            print(f"      - {m['codigo']}: {m['nome']} ({unidade})")
    
    # 2. Lotes
    print("\n2. LOTES:")
    lotes = db.execute("""
        SELECT l.*, m.nome as medicamento_nome, m.unidade 
        FROM lotes l 
        JOIN medicamentos m ON m.codigo = l.codigo_medicamento 
        ORDER BY l.numero_lote
    """, fetch_all=True)
    
    if not lotes:
        print("   ❌ Nenhum lote encontrado!")
    else:
        print(f"   ✅ {len(lotes)} lotes:")
        for lote in lotes:
            unidade = lote.get('unidade', 'UN')
            print(f"      - {lote['numero_lote']}: {lote['medicamento_nome']} | Estoque: {lote['quantidade_atual']} {unidade} | Validade: {lote['data_validade']}")
    
    # 3. Estrutura da tabela medicamentos
    print("\n3. ESTRUTURA DA TABELA MEDICAMENTOS:")
    colunas = db.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'projeto' AND table_name = 'medicamentos'
        ORDER BY ordinal_position
    """, fetch_all=True)
    
    for col in colunas:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    # 4. Estrutura da tabela itens_consumo
    print("\n4. ESTRUTURA DA TABELA ITENS_CONSUMO:")
    colunas = db.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'projeto' AND table_name = 'itens_consumo'
        ORDER BY ordinal_position
    """, fetch_all=True)
    
    for col in colunas:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("=" * 70)

if __name__ == "__main__":
    verificar_banco()