#!/usr/bin/env python
"""
Script para gerar arquivos BAIXA com dados variados
Formato: BAIXA_YYMMDD_HHMMSS_ID.csv
"""
import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.csv_utils import escrever_csv, gerar_nome_arquivo
from src.config.database import db

def buscar_lote_reservado(id_prescricao):
    """Busca o lote que foi reservado para esta prescrição"""
    try:
        db.connect()
        result = db.execute(
            "SELECT lote FROM reservas_ativas WHERE id_prescricao = %s AND status = 'RESERVADO'",
            (id_prescricao,),
            fetch_one=True
        )
        db.close()
        return result['lote'] if result else None
    except Exception as e:
        print(f"   ⚠️ Erro ao buscar lote reservado: {e}")
        return None

def buscar_lotes():
    """Busca lotes disponíveis no banco"""
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

def gerar_baixa(codigo_medicamento=789123, quantidade=2, lote=None, id_prescricao=None, cpf_paciente=12345678901):
    """Gera um arquivo de baixa"""
    if id_prescricao is None:
        id_prescricao = datetime.now().strftime('%H%M%S')
    
    # Buscar lote reservado se não foi fornecido
    if lote is None:
        lote = buscar_lote_reservado(id_prescricao)
        if lote is None:
            lote = 'LOTE002'  # fallback padrão
    
    data_uso = datetime.now().strftime('%y%m%d')  # YYMMDD
    
    dados = [{
        'id_prescricao': str(id_prescricao),
        'cpf_paciente': str(cpf_paciente),
        'codigo_medicamento': str(codigo_medicamento),
        'quantidade': str(quantidade),
        'lote': lote,
        'data_uso': data_uso
    }]
    
    nome_arquivo = gerar_nome_arquivo('BAIXA', id_prescricao)
    caminho = os.path.join('data', 'entrada', 'baixas', nome_arquivo)
    
    campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade', 'lote', 'data_uso']
    escrever_csv(caminho, campos, dados)
    print(f"✅ BAIXA gerada: {caminho}")
    return caminho

def gerar_multiplas_baixas(quantidade=5):
    """Gera múltiplos arquivos de baixa com dados variados"""
    print(f"\n✅ Gerando {quantidade} baixas...")
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
        # Selecionar lote aleatório
        lote_sel = random.choice(lotes)
        codigo = lote_sel['codigo_medicamento']
        lote_numero = lote_sel['numero_lote']
        
        # Quantidade variada
        max_qtd = min(3, int(lote_sel['quantidade_atual']))
        quantidade = random.randint(1, max(1, max_qtd))
        
        # CPF aleatório
        cpf = random.choice(cpfs)
        
        # ID da prescrição
        id_prescricao = int(f"{datetime.now().strftime('%H%M%S')}{i+1:03d}")
        
        print(f"   [{i+1}] Lote: {lote_numero} | Medicamento: {codigo} | Qtd: {quantidade} | CPF: {cpf}")
        
        arquivo = gerar_baixa(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            lote=lote_numero,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        arquivos.append(arquivo)
    
    print(f"\n✅ Geradas {len(arquivos)} baixas!")
    return arquivos

if __name__ == "__main__":
    # Gerar 5 baixas aleatórias
    gerar_multiplas_baixas(5)