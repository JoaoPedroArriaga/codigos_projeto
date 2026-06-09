"""
Processador de arquivos de finalização de atendimento (G2 → G1)
G3 apenas valida a estrutura e registra
CORRIGIDO para seguir XSD finalizacao.xsd
"""
import os
import re
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.config.database import db


class FinalizacaoProcessor:
    
    XSD = 'finalizacao.xsd'
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF (11 dígitos)"""
        cpf_limpo = re.sub(r'[^0-9]', '', str(cpf))
        return len(cpf_limpo) == 11 and cpf_limpo.isdigit()
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo XML de finalização de atendimento"""
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
        
        # Extrair dados principais (o elemento raiz é finalizacaoAtendimento)
        id_atendimento = root.find('id_atendimento')
        cpf_paciente = root.find('cpf_paciente')
        data_atendimento = root.find('data_atendimento')
        tipo_atendimento = root.find('tipo_atendimento')
        cid = root.find('cid')
        valor_total = root.find('valor_total')
        
        id_val = id_atendimento.text if id_atendimento is not None else 'N/A'
        cpf_val = cpf_paciente.text if cpf_paciente is not None else 'N/A'
        data_val = data_atendimento.text if data_atendimento is not None else 'N/A'
        tipo_val = tipo_atendimento.text if tipo_atendimento is not None else 'N/A'
        cid_val = cid.text if cid is not None else 'N/A'
        valor_val = valor_total.text if valor_total is not None else '0'
        
        # Validar CPF
        if cpf_val != 'N/A' and not FinalizacaoProcessor.validar_cpf(cpf_val):
            print(f"   ⚠️ CPF possivelmente inválido: {cpf_val}")
        
        print(f"   📊 Dados: ID={id_val}, CPF={cpf_val}, Data={data_val}, Tipo={tipo_val}, CID={cid_val}, Valor=R${valor_val}")
        
        # Validar campos obrigatórios
        missing_fields = []
        if id_atendimento is None:
            missing_fields.append('id_atendimento')
        if cpf_paciente is None:
            missing_fields.append('cpf_paciente')
        if data_atendimento is None:
            missing_fields.append('data_atendimento')
        if tipo_atendimento is None:
            missing_fields.append('tipo_atendimento')
        if cid is None:
            missing_fields.append('cid')
        if valor_total is None:
            missing_fields.append('valor_total')
        
        if missing_fields:
            print(f"   ⚠️ Campos faltando: {missing_fields}")
        
        # Registrar no log
        db.execute(
            """INSERT INTO logs_arquivos_externos 
               (arquivo_nome, tipo, data_recebimento, status, observacao)
               VALUES (%s, %s, %s, %s, %s)""",
            (os.path.basename(caminho_arquivo), 'FINALIZACAO',
             data_val, 'VALIDADO',
             f'Atendimento: {id_val}, Paciente: {cpf_val}, Valor: R$ {valor_val}')
        )
        
        # Registrar finalização em tabela específica (opcional)
        db.execute(
            """INSERT INTO atendimentos_finalizados 
               (id_atendimento, cpf_paciente, data_atendimento, tipo_atendimento, cid, valor_total, arquivo_origem)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (id_val, cpf_val, data_val, tipo_val, cid_val, float(valor_val), os.path.basename(caminho_arquivo))
        )
        
        # Mover para processados
        mover_para_processados(caminho_arquivo, 'finalizacao')
        
        print(f"✅ Finalização {os.path.basename(caminho_arquivo)} processada")
        return True