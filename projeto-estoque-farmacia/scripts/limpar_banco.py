#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import db

def limpar_tudo():
    db.connect()
    
    # Limpar tabelas de dados
    db.execute("TRUNCATE TABLE itens_consumo CASCADE")
    db.execute("TRUNCATE TABLE movimentacoes CASCADE")
    db.execute("TRUNCATE TABLE logs_consultas CASCADE")
    db.execute("TRUNCATE TABLE logs_reservas CASCADE")
    db.execute("TRUNCATE TABLE logs_baixas CASCADE")
    db.execute("TRUNCATE TABLE logs_consumos CASCADE")
    db.execute("TRUNCATE TABLE reservas_ativas CASCADE")
    
    # Resetar estoque
    db.execute("UPDATE lotes SET quantidade_atual = quantidade_inicial")
    
    db.close()
    print("✅ Banco limpo e estoque resetado!")

if __name__ == "__main__":
    limpar_tudo()