"""
Processador de arquivos de status financeiro (G1 → G2)
G3 apenas valida a estrutura e registra
CORRIGIDO para seguir XSD status_financeiro.xsd
"""
import os
import hashlib
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.config.database import db


class StatusFinanceiroProcessor:
    
    XSD = 'status_financeiro.xsd'
    
    @staticmethod
    def validar_hash_controle(root, hash_recebido):
        """Valida o hash_controle do trailer"""
        # Extrair dados para cálculo do hash
        header = root.find('header')
        detalhes = root.find('detalhes')
        
        if header is None or detalhes is None:
            return False
        
        # Construir string para hash (exemplo simplificado)
        data_geracao = header.find('data_geracao').text if header.find('data_geracao') is not None else ''
        total_detalhes = len(detalhes.findall('detalhe'))
        
        conteudo = f"{data_geracao}{total_detalhes}"
        hash_calculado = hashlib.md5(conteudo.encode()).hexdigest()
        
        return hash_calculado == hash_recebido
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo XML de status financeiro"""
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
        
        if header is None or trailer is None:
            print("   ❌ Estrutura inválida: header ou trailer não encontrados")
            mover_para_processados(caminho_arquivo, 'status_financeiro_erro')
            return False
        
        data_geracao = header.find('data_geracao').text if header.find('data_geracao') is not None else 'N/A'
        total_detalhes = trailer.find('total_detalhes').text if trailer.find('total_detalhes') is not None else '0'
        hash_controle = trailer.find('hash_controle').text if trailer.find('hash_controle') is not None else ''
        
        # Validar hash_controle
        if hash_controle:
            if not StatusFinanceiroProcessor.validar_hash_controle(root, hash_controle):
                print(f"   ⚠️ Hash de controle não confere")
        
        print(f"   📊 Dados: Data={data_geracao}, Total registros={total_detalhes}")
        
        # Processar cada detalhe
        detalhes = root.find('detalhes')
        if detalhes is not None:
            for idx, detalhe in enumerate(detalhes.findall('detalhe')):
                cpf = detalhe.find('cpf_paciente')
                status = detalhe.find('status_financeiro')
                permite = detalhe.find('permite_atendimento')
                
                if cpf is not None and status is not None:
                    print(f"   📋 Paciente {cpf.text}: status={status.text}, permite={permite.text if permite is not None else 'N/A'}")
                    
                    # Registrar no banco (opcional)
                    db.execute(
                        """INSERT INTO logs_status_financeiro 
                           (arquivo_nome, cpf_paciente, status_financeiro, permite_atendimento, data_recebimento)
                           VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                        (os.path.basename(caminho_arquivo), cpf.text, status.text, 
                         permite.text if permite is not None else 'N')
                    )
        
        # Registrar log principal
        db.execute(
            """INSERT INTO logs_arquivos_externos 
               (arquivo_nome, tipo, data_recebimento, status, observacao)
               VALUES (%s, %s, %s, %s, %s)""",
            (os.path.basename(caminho_arquivo), 'STATUS_FINANCEIRO',
             data_geracao, 'VALIDADO',
             f'Total de registros: {total_detalhes}')
        )
        
        # Mover para processados
        mover_para_processados(caminho_arquivo, 'status_financeiro')
        
        print(f"✅ Status financeiro {os.path.basename(caminho_arquivo)} processado")
        return True