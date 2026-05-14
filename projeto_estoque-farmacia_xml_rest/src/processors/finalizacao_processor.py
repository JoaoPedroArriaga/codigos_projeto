"""
Processador de arquivos de finalização de atendimento (G2 → G1)
G3 apenas valida a estrutura e registra
"""
import os
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.config.database import db

class FinalizacaoProcessor:
    
    XSD = 'finalizacao.xsd'
    
    @staticmethod
    def processar(caminho_arquivo):
        print(f"📄 Processando finalizacao: {caminho_arquivo}")
        
        # 1. Validar contra XSD (estrutura)
        valido, erro = validador.validar(caminho_arquivo, FinalizacaoProcessor.XSD)
        if not valido:
            print(f"   ❌ XML inválido: {erro}")
            mover_para_processados(caminho_arquivo, 'finalizacao_erro')
            return False
        
        print("   ✅ XML válido")
        
        # 2. Extrair informações básicas para o log
        root = ler_xml(caminho_arquivo)
        if root is None:
            mover_para_processados(caminho_arquivo, 'finalizacao_erro')
            return False
        
        # Extrair dados principais
        id_atendimento = root.find('id_atendimento').text if root.find('id_atendimento') is not None else 'N/A'
        cpf_paciente = root.find('cpf_paciente').text if root.find('cpf_paciente') is not None else 'N/A'
        valor_total = root.find('valor_total').text if root.find('valor_total') is not None else '0'
        
        print(f"   📊 Dados: ID={id_atendimento}, CPF={cpf_paciente}, Valor=R${valor_total}")
        
        # 3. Registrar no log
        db.execute(
            """INSERT INTO logs_arquivos_externos 
               (arquivo_nome, tipo, data_recebimento, status, observacao)
               VALUES (%s, %s, %s, %s, %s)""",
            (os.path.basename(caminho_arquivo), 'FINALIZACAO',
             id_atendimento, 'VALIDADO',
             f'Paciente: {cpf_paciente}, Valor: R$ {valor_total}')
        )
        
        # 4. Mover para processados
        mover_para_processados(caminho_arquivo, 'finalizacao')
        
        print(f"✅ Finalização {os.path.basename(caminho_arquivo)} processada")
        return True