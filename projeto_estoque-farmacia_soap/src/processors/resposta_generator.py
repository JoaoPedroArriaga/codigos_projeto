"""
Gerador de arquivos XML de resposta com assinatura (G3 → G2)
CORRIGIDO para seguir formato do XSD resposta.xsd
"""
import os
from src.utils.xml_utils import gerar_nome_arquivo_xml, escrever_xml
from src.utils.hash_utils import adicionar_assinatura
from src.utils.xml_normalizer import XMLBuilder
from dotenv import load_dotenv

load_dotenv()


class RespostaGenerator:
    
    @staticmethod
    def gerar(respostas, id_prescricao):
        """
        Gera um arquivo XML de resposta com assinatura (G3 -> G2)
        
        Args:
            respostas: Lista de dicionários com campos:
                       - codigo_medicamento: int
                       - disponivel: 0 ou 1
                       - observacao: str (opcional)
            id_prescricao: ID da prescrição para nome do arquivo
        """
        # Construir XML usando o builder
        root = XMLBuilder.construir_resposta(respostas)
        
        # Adicionar assinatura como último elemento
        adicionar_assinatura(root, 'GRUPO_3')
        
        # Gerar nome do arquivo
        nome_arquivo = gerar_nome_arquivo_xml('RESPOSTA', str(id_prescricao))
        
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_respostas = os.getenv('PASTA_RESPOSTAS', 'saida/respostas')
        caminho = os.path.join(data_dir, pasta_respostas, nome_arquivo)
        
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        
        # Salvar XML
        escrever_xml(caminho, root)
        
        print(f"   ✅ Resposta gerada com assinatura: {caminho}")
        return caminho