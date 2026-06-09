#!/usr/bin/env python
"""
Script para mostrar combinações válidas de medicamentos e lotes
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import db

def mostrar_combinacoes():
    """Mostra combinações válidas de medicamentos e lotes"""
    db.connect()
    
    print("=" * 60)
    print("📦 COMBINAÇÕES VÁLIDAS DE MEDICAMENTOS E LOTES")
    print("=" * 60)
    
    combinacoes = db.execute(
        """SELECT m.codigo, m.nome as medicamento, 
                  l.numero_lote, l.quantidade_atual, l.data_validade
           FROM lotes l
           JOIN medicamentos m ON m.codigo = l.codigo_medicamento
           WHERE l.quantidade_atual > 0
           ORDER BY m.nome""",
        fetch_all=True
    )
    
    print(f"\n{'Código':<10} {'Medicamento':<25} {'Lote':<12} {'Estoque':<10} {'Validade'}")
    print("-" * 70)
    
    for c in combinacoes:
        print(f"{c['codigo']:<10} {c['medicamento']:<25} {c['numero_lote']:<12} {c['quantidade_atual']:<10.0f} {c['data_validade']}")
    
    print("\n" + "=" * 60)
    print("✅ Combinações válidas para os testes:")
    
    for c in combinacoes:
        print(f"   - {c['medicamento']} (código {c['codigo']}) → lote {c['numero_lote']}")
    
    db.close()

if __name__ == "__main__":
    mostrar_combinacoes()