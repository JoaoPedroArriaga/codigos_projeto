"""
Processador de arquivos XML de reserva com validação de assinatura
"""
import os
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.utils.xml_normalizer import XMLNormalizer
from src.utils.hash_utils import validar_assinatura
from src.models.logs import LogReserva
from src.models.lote import Lote
from src.models.reserva_ativa import ReservaAtiva

class ReservaProcessor:
    
    XSD = 'reserva.xsd'
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo XML de reserva com validação de assinatura"""
        print(f"📄 Processando reserva XML: {caminho_arquivo}")
        
        # 1. Validar assinatura
        valido, msg, dados_assinatura = validar_assinatura(caminho_arquivo)
        if not valido:
            print(f"   ❌ Assinatura inválida: {msg}")
            mover_para_processados(caminho_arquivo, 'reservas_erro')
            return False
        
        print(f"   ✅ Assinatura válida - Origem: {dados_assinatura['grupo_origem']}")
        
        # 2. Validar contra XSD
        valido, erro = validador.validar(caminho_arquivo, ReservaProcessor.XSD)
        if not valido:
            print(f"   ❌ XML inválido: {erro}")
            mover_para_processados(caminho_arquivo, 'reservas_erro')
            return False
        
        print("   ✅ XML válido")
        
        # 3. Ler XML
        root = ler_xml(caminho_arquivo)
        if root is None:
            mover_para_processados(caminho_arquivo, 'reservas_erro')
            return False
        
        # 4. Extrair dados normalizados
        dados = XMLNormalizer.extrair_dados_reserva(root)
        
        if not dados:
            print("   ❌ Nenhum dado encontrado no XML")
            mover_para_processados(caminho_arquivo, 'reservas_erro')
            return False
        
        # 5. Processar cada reserva
        for item in dados:
            id_prescricao = int(item['id_prescricao'])
            cpf_paciente = int(item['cpf_paciente'])
            codigo_medicamento = int(item['codigo_medicamento'])
            quantidade = float(item['quantidade'])
            
            # Buscar lote disponível (FEFO)
            lote_disponivel = Lote.buscar_disponivel(codigo_medicamento, quantidade)
            
            if not lote_disponivel:
                print(f"   ❌ Nenhum lote disponível para medicamento {codigo_medicamento}")
                LogReserva.registrar(
                    os.path.basename(caminho_arquivo),
                    id_prescricao, cpf_paciente, codigo_medicamento,
                    quantidade, None, None, 'ERRO', 'Nenhum lote disponível'
                )
                continue
            
            # Criar reserva ativa
            ReservaAtiva.criar(
                id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote_disponivel['numero_lote'], lote_disponivel['id_lote']
            )
            
            LogReserva.registrar(
                os.path.basename(caminho_arquivo),
                id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote_disponivel['numero_lote'], lote_disponivel['id_lote'],
                'PROCESSADO', f'Reserva realizada com lote {lote_disponivel["numero_lote"]} (FEFO)'
            )
            
            print(f"   ✅ Reserva criada para lote {lote_disponivel['numero_lote']}")
        
        # 6. Mover arquivo original para processados
        mover_para_processados(caminho_arquivo, 'reservas')
        
        print(f"✅ Reserva {os.path.basename(caminho_arquivo)} processada")
        return True