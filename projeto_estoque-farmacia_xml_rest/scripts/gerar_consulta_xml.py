#!/usr/bin/env python
import os
import sys
from datetime import datetime
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.xml_utils import gerar_nome_arquivo_xml, escrever_xml
from src.utils.hash_utils import adicionar_assinatura

def gerar_consulta_xml(codigo_medicamento=789123, quantidade=2, id_prescricao=None, cpf_paciente=12345678901):
    if id_prescricao is None:
        id_prescricao = datetime.now().strftime('%H%M%S%f')
    
    root = etree.Element('consultas')
    consulta = etree.SubElement(root, 'consulta')
    etree.SubElement(consulta, 'prescricao').text = str(id_prescricao)
    etree.SubElement(consulta, 'cpf').text = str(cpf_paciente)
    etree.SubElement(consulta, 'codigo_medicamento').text = str(codigo_medicamento)
    etree.SubElement(consulta, 'quantidade').text = str(quantidade)
    
    adicionar_assinatura(root, 'GRUPO_2')
    
    nome_arquivo = gerar_nome_arquivo_xml('CONSULTA', str(id_prescricao))
    caminho = os.path.join('data', 'entrada', 'consultas', nome_arquivo)
    
    escrever_xml(caminho, root)
    print(f"✅ CONSULTA XML gerada: {caminho}")
    return caminho

if __name__ == "__main__":
    gerar_consulta_xml()