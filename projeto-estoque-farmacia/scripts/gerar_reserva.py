#!/usr/bin/env python
"""
Script para gerar arquivos RESERVA com dados variados
Formato: RESERVA_YYMMDD_HHMMSS_ID.csv
"""
import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.csv_utils import escrever_csv, gerar_nome_arquivo
from src.config.database import db

def buscar_lotes():
    """Busca lotes disponíveis no banco (apenas para referência de combinações válidas)"""
    db.connect()
    lotes = db.execute(
        """SELECT l.id_lote, l.numero_lote, l.codigo_medicamento, l.quantidade_atual 
           FROM lotes l
           WHERE l.quantidade_atual > 0 
           ORDER BY l.codigo_medicamento""",
        fetch_all=True
    )
    db.close()
    return lotes

def gerar_reserva(codigo_medicamento=789123, quantidade=2, id_prescricao=None, cpf_paciente=12345678901):
    """Gera um arquivo de reserva (sem lote)"""
    if id_prescricao is None:
        id_prescricao = datetime.now().strftime('%H%M%S')
    
    dados = [{
        'id_prescricao': str(id_prescricao),
        'cpf_paciente': str(cpf_paciente),
        'codigo_medicamento': str(codigo_medicamento),
        'quantidade': str(quantidade)
    }]
    
    nome_arquivo = gerar_nome_arquivo('RESERVA', id_prescricao)
    caminho = os.path.join('data', 'entrada', 'reservas', nome_arquivo)
    
    campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade']
    escrever_csv(caminho, campos, dados)
    print(f"✅ RESERVA gerada: {caminho}")
    return caminho

def gerar_multiplas_reservas(quantidade=5):
    """Gera múltiplos arquivos de reserva com dados variados"""
    print(f"\n🔒 Gerando {quantidade} reservas...")
    print("=" * 50)
    
    lotes = buscar_lotes()
    
    if not lotes:
        print("❌ Nenhum lote encontrado no banco!")
        return []
    
    cpfs = [
        '12345678901', '98765432100', '11122233344', 
        '55566677788', '99988877766', '44455566677'
    ]
    
    arquivos = []
    
    for i in range(quantidade):
        # Selecionar lote aleatório (apenas para escolher um medicamento válido)
        lote_sel = random.choice(lotes)
        codigo = lote_sel['codigo_medicamento']
        
        # Quantidade variada (até o estoque disponível)
        max_qtd = min(5, int(lote_sel['quantidade_atual']))
        quantidade = random.randint(1, max(1, max_qtd))
        
        # CPF aleatório
        cpf = random.choice(cpfs)
        
        # ID da prescrição
        id_prescricao = int(f"{datetime.now().strftime('%H%M%S')}{i+1:03d}")
        
        print(f"   [{i+1}] Medicamento: {codigo} | Qtd: {quantidade} | CPF: {cpf}")
        
        arquivo = gerar_reserva(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        arquivos.append(arquivo)
    
    print(f"\n✅ Geradas {len(arquivos)} reservas!")
    return arquivos

if __name__ == "__main__":
    gerar_multiplas_reservas(5)