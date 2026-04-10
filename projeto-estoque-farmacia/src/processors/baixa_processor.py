import os
from src.utils.csv_utils import ler_csv, mover_para_processados
from src.models.logs import LogBaixa
from src.models.lote import Lote
from src.models.reserva_ativa import ReservaAtiva
from src.config.database import db

class BaixaProcessor:
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo de baixa (com lote informado pelo G2)"""
        print(f"📄 Processando baixa: {caminho_arquivo}")
        
        # 1. Ler CSV
        dados = ler_csv(caminho_arquivo)
        if not dados:
            return False
        
        print(f"   📋 [DEBUG] Dados lidos: {len(dados)} linha(s)")
        
        # 2. Iniciar transação
        db.begin()
        
        try:
            for idx, row in enumerate(dados):
                print(f"   📋 [DEBUG] Processando linha {idx + 1}: {row}")
                
                id_prescricao = int(row['id_prescricao'])
                cpf_paciente = int(row['cpf_paciente'])
                codigo_medicamento = int(row['codigo_medicamento'])
                quantidade = float(row['quantidade'])
                lote_numero = row['lote']
                data_uso = int(row['data_uso'])
                
                # Buscar a reserva ativa para este lote
                reserva = ReservaAtiva.buscar_reserva_ativa(id_prescricao, lote_numero)
                
                if not reserva:
                    print(f"   ❌ [DEBUG] Reserva não encontrada para lote {lote_numero}")
                    LogBaixa.registrar(
                        os.path.basename(caminho_arquivo), 
                        id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, lote_numero, data_uso, None, 
                        'ERRO', 'Reserva não encontrada'
                    )
                    continue
                
                # Busca lote
                lote = Lote.buscar_por_lote(codigo_medicamento, lote_numero)
                
                if not lote:
                    print(f"   ❌ [DEBUG] Lote não encontrado: {lote_numero}")
                    LogBaixa.registrar(
                        os.path.basename(caminho_arquivo), 
                        id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, lote_numero, data_uso, None, 
                        'ERRO', 'Lote não encontrado'
                    )
                    continue
                
                # Converter para float
                quantidade_atual = float(lote['quantidade_atual'])
                print(f"   📦 [DEBUG] Lote encontrado: {lote_numero}, estoque: {quantidade_atual}")
                
                if quantidade_atual < quantidade:
                    print(f"   ❌ [DEBUG] Estoque insuficiente: {quantidade_atual} < {quantidade}")
                    LogBaixa.registrar(
                        os.path.basename(caminho_arquivo), 
                        id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, lote_numero, data_uso, lote['id_lote'],
                        'ERRO', 'Estoque insuficiente'
                    )
                    continue
                
                # Atualiza estoque
                nova_quantidade = quantidade_atual - quantidade
                Lote.atualizar_estoque(lote['id_lote'], nova_quantidade)
                print(f"   ✅ [DEBUG] Estoque atualizado: {quantidade_atual} -> {nova_quantidade}")
                
                # Marcar reserva como utilizada
                ReservaAtiva.marcar_utilizado(id_prescricao, lote_numero)
                print("   ✅ [DEBUG] Reserva marcada como UTILIZADA")
                
                # Registra log da baixa
                log = LogBaixa.registrar(
                    os.path.basename(caminho_arquivo), 
                    id_prescricao, cpf_paciente, codigo_medicamento,
                    quantidade, lote_numero, data_uso, lote['id_lote'],
                    'PROCESSADO', 'Baixa realizada'
                )
                print(f"   ✅ [DEBUG] Log registrado ID: {log['id_log']}")
                
                # Registra movimentação
                db.execute(
                    """INSERT INTO movimentacoes 
                       (id_lote, tipo, quantidade, quantidade_anterior, 
                        quantidade_nova, referencia_id, referencia_tabela)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (lote['id_lote'], 'BAIXA', quantidade,
                     quantidade_atual, nova_quantidade,
                     log['id_log'], 'logs_baixas')
                )
                print("   ✅ [DEBUG] Movimentação registrada")
                
                # Buscar unidade do medicamento
                unidade = db.execute(
                    "SELECT unidade FROM medicamentos WHERE codigo = %s",
                    (codigo_medicamento,),
                    fetch_one=True
                )

                # Registra item de consumo (com unidade)
                db.execute(
                    """INSERT INTO itens_consumo 
                    (id_prescricao, cpf_paciente, codigo_medicamento,
                        quantidade, preco_total, data_uso, lote, id_lote, id_baixa_log, unidade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_prescricao, cpf_paciente, codigo_medicamento,
                    quantidade, quantidade * float(lote['preco_venda']), data_uso,
                    lote_numero, lote['id_lote'], log['id_log'], unidade['unidade'])
                )
                print(f"   ✅ [DEBUG] Item de consumo registrado: R$ {quantidade * float(lote['preco_venda']):.2f}")
            
            # Confirma transação
            db.commit()
            
            # Mover arquivo para processados
            mover_para_processados(caminho_arquivo, 'baixas')
            
            print(f"✅ Baixa {os.path.basename(caminho_arquivo)} processada")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Erro ao processar baixa: {e}")
            return False