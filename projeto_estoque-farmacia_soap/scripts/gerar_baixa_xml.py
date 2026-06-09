#!/usr/bin/env python
import os
import sys
from datetime import datetime
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.xml_utils import gerar_nome_arquivo_xml, escrever_xml
from src.utils.hash_utils import adicionar_assinatura
from src.config.database import db

def buscar_lote_reservado(id_prescricao):
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

def gerar_baixa_xml(codigo_medicamento=789123, quantidade=2, lote=None, id_prescricao=None, cpf_paciente=12345678901):
    if id_prescricao is None:
        id_prescricao = datetime.now().strftime('%H%M%S%f')
    
    if lote is None:
        lote = buscar_lote_reservado(id_prescricao)
        if lote is None:
            lote = 'LOTE002'
    
    data_uso = datetime.now().strftime('%y%m%d')
    
    root = etree.Element('baixas')
    baixa = etree.SubElement(root, 'baixa')
    etree.SubElement(baixa, 'prescricao').text = str(id_prescricao)
    etree.SubElement(baixa, 'cpf').text = str(cpf_paciente)
    etree.SubElement(baixa, 'codigo_medicamento').text = str(codigo_medicamento)
    etree.SubElement(baixa, 'lote').text = lote
    etree.SubElement(baixa, 'quantidade').text = str(quantidade)
    etree.SubElement(baixa, 'data_uso').text = data_uso
    
    adicionar_assinatura(root, 'GRUPO_2')
    
    nome_arquivo = gerar_nome_arquivo_xml('BAIXA', str(id_prescricao))
    caminho = os.path.join('data', 'entrada', 'baixas', nome_arquivo)
    
    escrever_xml(caminho, root)
    print(f"✅ BAIXA XML gerada: {caminho}")
    return caminho

if __name__ == "__main__":
    gerar_baixa_xml()