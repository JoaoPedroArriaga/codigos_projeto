"""
Processador de arquivos de status financeiro (G1 → G2)
G3 apenas valida a estrutura e registra
"""
import os
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.config.database import db

class StatusFinanceiroProcessor:
    
    XSD = 'status_financeiro.xsd'
    
    @staticmethod
    def processar(caminho_arquivo):
        print(f"📄 Processando status_financeiro: {caminho_arquivo}")
        
        # 1. Validar contra XSD (estrutura)
        valido, erro = validador.validar(caminho_arquivo, StatusFinanceiroProcessor.XSD)
        if not valido:
            print(f"   ❌ XML inválido: {erro}")
            mover_para_processados(caminho_arquivo, 'status_financeiro_erro')
            return False
        
        print("   ✅ XML válido")
        
        # 2. Extrair informações básicas para o log
        root = ler_xml(caminho_arquivo)
        if root is None:
            mover_para_processados(caminho_arquivo, 'status_financeiro_erro')
            return False
        
        # Extrair dados do header e trailer
        header = root.find('header')
        trailer = root.find('trailer')
        
        data_geracao = header.find('data_geracao').text if header is not None else 'N/A'
        total_detalhes = trailer.find('total_detalhes').text if trailer is not None else '0'
        
        print(f"   📊 Dados: Data={data_geracao}, Total registros={total_detalhes}")
        
        # 3. Registrar no log
        db.execute(
            """INSERT INTO logs_arquivos_externos 
               (arquivo_nome, tipo, data_recebimento, status, observacao)
               VALUES (%s, %s, %s, %s, %s)""",
            (os.path.basename(caminho_arquivo), 'STATUS_FINANCEIRO',
             data_geracao, 'VALIDADO',
             f'Total de registros: {total_detalhes}')
        )
        
        # 4. Mover para processados
        mover_para_processados(caminho_arquivo, 'status_financeiro')
        
        print(f"✅ Status financeiro {os.path.basename(caminho_arquivo)} processado")
        return True