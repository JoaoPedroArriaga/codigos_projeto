"""
Utilitários para manipulação de XML
"""
import os
import shutil
from datetime import datetime
from lxml import etree

def gerar_nome_arquivo_xml(tipo, id_consulta=None):
    """
    Gera nome do arquivo XML conforme padrão: TIPO_YYMMDD_HHMMSS_ID.xml
    Exemplo: CONSULTA_260327_143022_001.xml
    """
    agora = datetime.now()
    data = agora.strftime('%y%m%d')
    hora = agora.strftime('%H%M%S')
    
    if id_consulta is None:
        id_consulta = agora.strftime('%H%M%S')
    
    if tipo == 'CONSULTA':
        return f"CONSULTA_{data}_{hora}_{id_consulta}.xml"
    elif tipo == 'RESPOSTA':
        return f"RESPOSTA_{data}_{hora}_{id_consulta}.xml"
    elif tipo == 'RESERVA':
        return f"RESERVA_{data}_{hora}_{id_consulta}.xml"
    elif tipo == 'BAIXA':
        return f"BAIXA_{data}_{hora}_{id_consulta}.xml"
    elif tipo == 'CONSUMO':
        return f"CONSUMO_{data}.xml"
    else:
        return f"{tipo}_{data}_{hora}_{id_consulta}.xml"

def mover_para_processados(caminho_arquivo, tipo):
    """Move um arquivo para a pasta de processados"""
    try:
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_processados = os.getenv('PASTA_PROCESSADOS', 'processados')
        
        destino_dir = os.path.join(data_dir, pasta_processados, tipo)
        os.makedirs(destino_dir, exist_ok=True)
        
        nome_arquivo = os.path.basename(caminho_arquivo)
        destino = os.path.join(destino_dir, nome_arquivo)
        
        print(f"   Movendo para processados: {destino}")
        shutil.move(caminho_arquivo, destino)
        return True
    except Exception as e:
        print(f"Erro ao mover arquivo: {e}")
        return False

def listar_arquivos_entrada(tipo):
    """Lista arquivos XML pendentes na pasta de entrada"""
    data_dir = os.getenv('DATA_DIR', 'data')
    
    pastas = {
        'consulta': os.getenv('PASTA_CONSULTAS', 'entrada/consultas'),
        'reserva': os.getenv('PASTA_RESERVAS', 'entrada/reservas'),
        'baixa': os.getenv('PASTA_BAIXAS', 'entrada/baixas'),
        'status_financeiro': os.getenv('PASTA_STATUS', 'entrada/status_financeiro'),
        'finalizacao': os.getenv('PASTA_FINALIZACAO', 'entrada/finalizacao'),
    }
    
    pasta = pastas.get(tipo)
    if not pasta:
        return []
    
    caminho = os.path.join(data_dir, pasta)
    if not os.path.exists(caminho):
        os.makedirs(caminho, exist_ok=True)
        return []
    
    arquivos = [f for f in os.listdir(caminho) if f.endswith('.xml')]
    return [os.path.join(caminho, f) for f in arquivos]

def ler_xml(caminho):
    """Lê um arquivo XML e retorna o elemento raiz"""
    try:
        tree = etree.parse(caminho)
        return tree.getroot()
    except Exception as e:
        print(f"Erro ao ler XML {caminho}: {e}")
        return None

def escrever_xml(caminho, root):
    """Escreve um arquivo XML sem formatação extra para hash consistente"""
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        # Usar pretty_print=False para hash consistente
        xml_string = etree.tostring(root, encoding='unicode', method='xml', pretty_print=False)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(xml_string)
        return True
    except Exception as e:
        print(f"Erro ao escrever XML {caminho}: {e}")
        return False