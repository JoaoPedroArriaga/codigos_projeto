"""
Gerador de arquivos XML de resposta com assinatura (G3 → G2)
"""
import os
from src.utils.xml_utils import gerar_nome_arquivo_xml, escrever_xml
from src.utils.hash_utils import adicionar_assinatura
from lxml import etree
from dotenv import load_dotenv

load_dotenv()

class RespostaGenerator:
    
    @staticmethod
    def gerar(respostas, id_prescricao):
        """Gera um arquivo XML de resposta com assinatura (G3 -> G2)"""
        
        # Criar elemento raiz
        root = etree.Element('respostas')
        
        for resp in respostas:
            resposta_elem = etree.SubElement(root, 'resposta')
            etree.SubElement(resposta_elem, 'codigo_medicamento').text = str(resp['codigo_medicamento'])
            etree.SubElement(resposta_elem, 'disponivel').text = str(resp['disponivel'])
            etree.SubElement(resposta_elem, 'observacao').text = resp.get('observacao', '')
        
        # Adicionar assinatura (grupo G3)
        adicionar_assinatura(root, 'GRUPO_3')
        
        # Gerar nome do arquivo
        nome_arquivo = gerar_nome_arquivo_xml('RESPOSTA', str(id_prescricao))
        
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_respostas = os.getenv('PASTA_RESPOSTAS', 'saida/respostas')
        caminho = os.path.join(data_dir, pasta_respostas, nome_arquivo)
        
        # Salvar XML
        escrever_xml(caminho, root)
        
        print(f"   ✅ Resposta gerada com assinatura: {caminho}")
        return caminho