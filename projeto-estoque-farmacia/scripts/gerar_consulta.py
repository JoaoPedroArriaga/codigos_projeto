#!/usr/bin/env python
"""
Script para gerar arquivos CONSULTA com dados variados
Formato: CONSULTA_YYMMDD_HHMMSS_ID.csv
"""
import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.csv_utils import escrever_csv, gerar_nome_arquivo
from src.config.database import db

def buscar_medicamentos():
    """Busca medicamentos disponíveis no banco"""
    db.connect()
    medicamentos = db.execute(
        "SELECT codigo, nome FROM medicamentos ORDER BY codigo",
        fetch_all=True
    )
    db.close()
    return medicamentos

def gerar_consulta(codigo_medicamento=789123, quantidade=2, id_prescricao=None, cpf_paciente=12345678901):
    """Gera um arquivo de consulta"""
    if id_prescricao is None:
        id_prescricao = datetime.now().strftime('%H%M%S')
    
    dados = [{
        'id_prescricao': str(id_prescricao),
        'cpf_paciente': str(cpf_paciente),
        'codigo_medicamento': str(codigo_medicamento),
        'quantidade': str(quantidade)
    }]
    
    nome_arquivo = gerar_nome_arquivo('CONSULTA', id_prescricao)
    caminho = os.path.join('data', 'entrada', 'consultas', nome_arquivo)
    
    campos = ['id_prescricao', 'cpf_paciente', 'codigo_medicamento', 'quantidade']
    escrever_csv(caminho, campos, dados)
    print(f"✅ CONSULTA gerada: {caminho}")
    return caminho

def gerar_multiplas_consultas(quantidade=5):
    """Gera múltiplos arquivos de consulta com dados variados"""
    print(f"\n📦 Gerando {quantidade} consultas...")
    print("=" * 50)
    
    medicamentos = buscar_medicamentos()
    
    if not medicamentos:
        print("❌ Nenhum medicamento encontrado no banco!")
        return []
    
    cpfs = [
        '12345678901', '98765432100', '11122233344', 
        '55566677788', '99988877766', '44455566677'
    ]
    
    arquivos = []
    
    for i in range(quantidade):
        # Selecionar medicamento aleatório
        med = random.choice(medicamentos)
        codigo = med['codigo']
        
        # Quantidade variada (1 a 5)
        quantidade = random.randint(1, 5)
        
        # CPF aleatório
        cpf = random.choice(cpfs)
        
        # ID da prescrição (baseado no timestamp + índice)
        id_prescricao = int(f"{datetime.now().strftime('%H%M%S')}{i+1:03d}")
        
        print(f"   [{i+1}] Medicamento: {codigo} | Qtd: {quantidade} | CPF: {cpf}")
        
        arquivo = gerar_consulta(
            codigo_medicamento=codigo,
            quantidade=quantidade,
            id_prescricao=id_prescricao,
            cpf_paciente=cpf
        )
        arquivos.append(arquivo)
    
    print(f"\n✅ Geradas {len(arquivos)} consultas!")
    return arquivos

if __name__ == "__main__":
    # Gerar 5 consultas aleatórias
    gerar_multiplas_consultas(5)