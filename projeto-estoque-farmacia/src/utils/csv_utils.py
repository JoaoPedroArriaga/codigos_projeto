import csv
import os
import shutil
from datetime import datetime

def ler_csv(caminho):
    """Lê um arquivo CSV e retorna lista de dicionários"""
    dados = []
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dados.append(row)
        return dados
    except Exception as e:
        print(f"Erro ao ler CSV {caminho}: {e}")
        return None

def escrever_csv(caminho, campos, dados):
    """Escreve um arquivo CSV"""
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        
        with open(caminho, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(dados)
        return True
    except Exception as e:
        print(f"Erro ao escrever CSV {caminho}: {e}")
        return False

def gerar_nome_arquivo(tipo, id_consulta=None):
    """
    Gera nome do arquivo conforme padrão: TIPO_YYMMDD_HHMMSS_ID.csv
    Exemplo: CONSULTA_250327_143022_123456.csv
    """
    agora = datetime.now()
    data = agora.strftime('%y%m%d')
    hora = agora.strftime('%H%M%S')
    
    if id_consulta is None:
        id_consulta = agora.strftime('%H%M%S')
    
    if tipo == 'CONSULTA':
        return f"CONSULTA_{data}_{hora}_{id_consulta}.csv"
    elif tipo == 'RESPOSTA':
        return f"RESPOSTA_{data}_{hora}_{id_consulta}.csv"
    elif tipo == 'RESERVA':
        return f"RESERVA_{data}_{hora}_{id_consulta}.csv"
    elif tipo == 'BAIXA':
        return f"BAIXA_{data}_{hora}_{id_consulta}.csv"
    elif tipo == 'CONSUMO':
        return f"CONSUMO_{data}.csv"
    else:
        return f"{tipo}_{data}_{hora}_{id_consulta}.csv"

def mover_para_processados(caminho_arquivo, tipo):
    """Move um arquivo para a pasta de processados"""
    try:
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_processados = os.getenv('PASTA_PROCESSADOS', 'processados')
        
        destino_dir = os.path.join(data_dir, pasta_processados, tipo)
        os.makedirs(destino_dir, exist_ok=True)
        
        nome_arquivo = os.path.basename(caminho_arquivo)
        destino = os.path.join(destino_dir, nome_arquivo)
        
        print(f"   📁 Movendo para processados: {destino}")
        shutil.move(caminho_arquivo, destino)
        return True
    except Exception as e:
        print(f"Erro ao mover arquivo: {e}")
        return False

def listar_arquivos_entrada(tipo):
    """Lista arquivos pendentes na pasta de entrada"""
    data_dir = os.getenv('DATA_DIR', 'data')
    
    pastas = {
        'consulta': os.getenv('PASTA_CONSULTAS', 'entrada/consultas'),
        'reserva': os.getenv('PASTA_RESERVAS', 'entrada/reservas'),
        'baixa': os.getenv('PASTA_BAIXAS', 'entrada/baixas')
    }
    
    pasta = pastas.get(tipo)
    if not pasta:
        return []
    
    caminho = os.path.join(data_dir, pasta)
    if not os.path.exists(caminho):
        os.makedirs(caminho, exist_ok=True)
        return []
    
    arquivos = [f for f in os.listdir(caminho) if f.endswith('.csv')]
    return [os.path.join(caminho, f) for f in arquivos]