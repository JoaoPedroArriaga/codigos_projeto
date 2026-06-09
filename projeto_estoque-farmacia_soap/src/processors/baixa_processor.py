"""
Processador de arquivos XML de baixa com validação de assinatura
CORRIGIDO para seguir XSD e validar campos obrigatórios
"""
import os
import re
from datetime import datetime
from src.utils.xml_utils import mover_para_processados, ler_xml
from src.utils.xml_validator import validador
from src.utils.xml_normalizer import XMLNormalizer
from src.utils.hash_utils import validar_assinatura
from src.models.logs import LogBaixa
from src.models.lote import Lote
from src.models.reserva_ativa import ReservaAtiva
from src.config.database import db


class BaixaProcessor:
    
    XSD = 'baixa.xsd'
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF (11 dígitos)"""
        cpf_limpo = re.sub(r'[^0-9]', '', str(cpf))
        return len(cpf_limpo) == 11 and cpf_limpo.isdigit()
    
    @staticmethod
    def validar_data_uso(data_uso: int) -> bool:
        """Valida data_uso no formato DDMMYY (6 dígitos)"""
        return 1 <= data_uso <= 311299  # Validação básica
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo XML de baixa com validação de assinatura"""
        print(f"📄 Processando baixa XML: {caminho_arquivo}")
        
        # 1. Validar assinatura
        valido, msg, dados_assinatura = validar_assinatura(caminho_arquivo)
        if not valido:
            print(f"   ❌ Assinatura inválida: {msg}")
            mover_para_processados(caminho_arquivo, 'baixas_erro')
            return False
        
        print(f"   ✅ Assinatura válida - Origem: {dados_assinatura['grupo_origem']}")
        
        # 2. Validar contra XSD
        valido, erro = validador.validar(caminho_arquivo, BaixaProcessor.XSD)
        if not valido:
            print(f"   ❌ XML inválido: {erro}")
            mover_para_processados(caminho_arquivo, 'baixas_erro')
            return False
        
        print("   ✅ XML válido")
        
        # 3. Ler XML
        root = ler_xml(caminho_arquivo)
        if root is None:
            mover_para_processados(caminho_arquivo, 'baixas_erro')
            return False
        
        # 4. Extrair dados normalizados
        dados = XMLNormalizer.extrair_dados_baixa(root)
        
        if not dados:
            print("   ❌ Nenhum dado encontrado no XML")
            mover_para_processados(caminho_arquivo, 'baixas_erro')
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
            if 'lote' not in item:
                missing_fields.append('lote')
            if 'quantidade' not in item:
                missing_fields.append('quantidade')
            if 'data_uso' not in item:
                missing_fields.append('data_uso')
            
            if missing_fields:
                print(f"   ❌ Item {idx+1} faltando campos: {missing_fields}")
                mover_para_processados(caminho_arquivo, 'baixas_erro')
                return False
            
            # Validar CPF
            if not BaixaProcessor.validar_cpf(item['cpf_paciente']):
                print(f"   ❌ CPF inválido: {item['cpf_paciente']}")
                mover_para_processados(caminho_arquivo, 'baixas_erro')
                return False
            
            # Validar quantidade > 0
            if item['quantidade'] <= 0:
                print(f"   ❌ Quantidade inválida: {item['quantidade']}")
                mover_para_processados(caminho_arquivo, 'baixas_erro')
                return False
            
            # Validar data_uso
            if not BaixaProcessor.validar_data_uso(item['data_uso']):
                print(f"   ⚠️ Data de uso possivelmente inválida: {item['data_uso']}")
        
        # 6. Processar cada baixa
        db.begin()
        
        try:
            for item in dados:
                id_prescricao = item['id_prescricao']
                cpf_paciente = item['cpf_paciente']
                codigo_medicamento = item['codigo_medicamento']
                quantidade = item['quantidade']
                lote_numero = item['lote']
                data_uso = item['data_uso']
                
                # Buscar reserva ativa
                reserva = ReservaAtiva.buscar_reserva_ativa(id_prescricao, lote_numero)
                
                if not reserva:
                    print(f"   ❌ Reserva não encontrada para lote {lote_numero}")
                    LogBaixa.registrar(
                        os.path.basename(caminho_arquivo),
                        id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, lote_numero, data_uso, None,
                        'ERRO', 'Reserva não encontrada'
                    )
                    continue
                
                # Buscar lote
                lote = Lote.buscar_por_lote(codigo_medicamento, lote_numero)
                
                if not lote:
                    print(f"   ❌ Lote não encontrado: {lote_numero}")
                    LogBaixa.registrar(
                        os.path.basename(caminho_arquivo),
                        id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, lote_numero, data_uso, None,
                        'ERRO', 'Lote não encontrado'
                    )
                    continue
                
                # Atualizar estoque
                quantidade_atual = float(lote['quantidade_atual'])
                
                if quantidade_atual < quantidade:
                    print(f"   ❌ Estoque insuficiente: {quantidade_atual} < {quantidade}")
                    LogBaixa.registrar(
                        os.path.basename(caminho_arquivo),
                        id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, lote_numero, data_uso, lote['id_lote'],
                        'ERRO', 'Estoque insuficiente'
                    )
                    continue
                
                nova_quantidade = quantidade_atual - quantidade
                Lote.atualizar_estoque(lote['id_lote'], nova_quantidade)
                
                # Marcar reserva como utilizada
                ReservaAtiva.marcar_utilizado(id_prescricao, lote_numero)
                
                # Registrar log
                log = LogBaixa.registrar(
                    os.path.basename(caminho_arquivo),
                    id_prescricao, cpf_paciente, codigo_medicamento,
                    quantidade, lote_numero, data_uso, lote['id_lote'],
                    'PROCESSADO', 'Baixa realizada'
                )
                
                # Registrar movimentação
                db.execute(
                    """INSERT INTO movimentacoes 
                       (id_lote, tipo, quantidade, quantidade_anterior, 
                        quantidade_nova, referencia_id, referencia_tabela)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (lote['id_lote'], 'BAIXA', quantidade,
                     quantidade_atual, nova_quantidade,
                     log['id_log'], 'logs_baixas')
                )
                
                # Buscar unidade
                unidade = db.execute(
                    "SELECT unidade FROM medicamentos WHERE codigo = %s",
                    (codigo_medicamento,),
                    fetch_one=True
                )
                
                # Registrar item de consumo
                db.execute(
                    """INSERT INTO itens_consumo 
                    (id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, preco_total, data_uso, lote, id_lote, id_baixa_log, unidade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_prescricao, cpf_paciente, codigo_medicamento,
                     quantidade, quantidade * float(lote['preco_venda']), data_uso,
                     lote_numero, lote['id_lote'], log['id_log'], unidade['unidade'] if unidade else 'CAIXA')
                )
                
                print(f"   ✅ Baixa realizada: lote {lote_numero} - {quantidade} unidades")
            
            db.commit()
            mover_para_processados(caminho_arquivo, 'baixas')
            print(f"✅ Baixa {os.path.basename(caminho_arquivo)} processada")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Erro ao processar baixa: {e}")
            return False