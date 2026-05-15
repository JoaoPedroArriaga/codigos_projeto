"""
Processador de arquivos XML de consulta com validação de assinatura
CORRIGIDO para seguir XSD e validar campos obrigatórios
"""
import os
import re
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.utils.xml_normalizer import XMLNormalizer
from src.utils.hash_utils import validar_assinatura
from src.models.logs import LogConsulta
from src.services.estoque_service import EstoqueService
from src.processors.resposta_generator import RespostaGenerator


class ConsultaProcessor:
    
    XSD = 'consulta.xsd'
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF (11 dígitos)"""
        cpf_limpo = re.sub(r'[^0-9]', '', str(cpf))
        return len(cpf_limpo) == 11 and cpf_limpo.isdigit()
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo XML de consulta com validação de assinatura"""
        print(f"📄 Processando consulta XML: {caminho_arquivo}")
        
        # 1. Validar assinatura
        valido, msg, dados_assinatura = validar_assinatura(caminho_arquivo)
        if not valido:
            print(f"   ❌ Assinatura inválida: {msg}")
            mover_para_processados(caminho_arquivo, 'consultas_erro')
            return False
        
        print(f"   ✅ Assinatura válida - Origem: {dados_assinatura['grupo_origem']}")
        
        # 2. Validar contra XSD
        valido, erro = validador.validar(caminho_arquivo, ConsultaProcessor.XSD)
        if not valido:
            print(f"   ❌ XML inválido: {erro}")
            mover_para_processados(caminho_arquivo, 'consultas_erro')
            return False
        
        print("   ✅ XML válido")
        
        # 3. Ler XML
        root = ler_xml(caminho_arquivo)
        if root is None:
            mover_para_processados(caminho_arquivo, 'consultas_erro')
            return False
        
        # 4. Extrair dados normalizados
        dados = XMLNormalizer.extrair_dados_consulta(root)
        
        if not dados:
            print("   ❌ Nenhum dado encontrado no XML")
            mover_para_processados(caminho_arquivo, 'consultas_erro')
            return False
        
        # 5. Validar campos obrigatórios
        for idx, item in enumerate(dados):
            missing_fields = []
            if 'id_prescricao' not in item:
                missing_fields.append('prescricao')
            if 'cpf_paciente' not in item:
                missing_fields.append('cpf')
            if 'codigo_medicamento' not in item:
                missing_fields.append('codigo_medicamento')
            if 'quantidade' not in item:
                missing_fields.append('quantidade')
            
            if missing_fields:
                print(f"   ❌ Item {idx+1} faltando campos: {missing_fields}")
                mover_para_processados(caminho_arquivo, 'consultas_erro')
                return False
            
            # Validar CPF
            if not ConsultaProcessor.validar_cpf(item['cpf_paciente']):
                print(f"   ❌ CPF inválido: {item['cpf_paciente']}")
                mover_para_processados(caminho_arquivo, 'consultas_erro')
                return False
            
            # Validar quantidade > 0
            if item['quantidade'] <= 0:
                print(f"   ❌ Quantidade inválida: {item['quantidade']}")
                mover_para_processados(caminho_arquivo, 'consultas_erro')
                return False
        
        # 6. Processar cada consulta
        respostas = []
        for item in dados:
            id_prescricao = item['id_prescricao']
            cpf_paciente = item['cpf_paciente']
            codigo_medicamento = item['codigo_medicamento']
            quantidade = item['quantidade']
            
            resultado = EstoqueService.verificar_disponibilidade(
                codigo_medicamento, quantidade
            )
            
            LogConsulta.registrar(
                os.path.basename(caminho_arquivo),
                id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, resultado['disponivel'],
                'Disponível' if resultado['disponivel'] else 'Estoque insuficiente'
            )
            
            respostas.append({
                'codigo_medicamento': codigo_medicamento,
                'disponivel': 1 if resultado['disponivel'] else 0,
                'observacao': '' if resultado['disponivel'] else 'Estoque insuficiente'
            })
            
            print(f"   📋 Medicamento {codigo_medicamento}: disponivel={1 if resultado['disponivel'] else 0}")
        
        # 7. Gerar arquivo de resposta
        id_prescricao_principal = dados[0]['id_prescricao']
        RespostaGenerator.gerar(respostas, id_prescricao_principal)
        
        # 8. Mover arquivo original para processados
        mover_para_processados(caminho_arquivo, 'consultas')
        
        print(f"✅ Consulta {os.path.basename(caminho_arquivo)} processada")
        return True