"""
Processador de arquivos XML de consulta com validação de assinatura
"""
import os
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
        
        # 5. Processar cada consulta
        respostas = []
        for item in dados:
            id_prescricao = int(item['id_prescricao'])
            cpf_paciente = int(item['cpf_paciente'])
            codigo_medicamento = int(item['codigo_medicamento'])
            quantidade = float(item['quantidade'])
            
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
        
        # 6. Gerar arquivo de resposta (já tem assinatura pelo RespostaGenerator)
        id_prescricao_principal = dados[0]['id_prescricao']
        RespostaGenerator.gerar(respostas, id_prescricao_principal)
        
        # 7. Mover arquivo original para processados
        mover_para_processados(caminho_arquivo, 'consultas')
        
        print(f"✅ Consulta {os.path.basename(caminho_arquivo)} processada")
        return True