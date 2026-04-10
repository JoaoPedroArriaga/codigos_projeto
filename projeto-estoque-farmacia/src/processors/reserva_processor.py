import os
from src.utils.csv_utils import ler_csv, mover_para_processados
from src.models.logs import LogReserva
from src.models.lote import Lote
from src.models.reserva_ativa import ReservaAtiva

class ReservaProcessor:
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo de reserva (sem lote - G3 aplica FEFO)"""
        print(f"📄 Processando reserva: {caminho_arquivo}")
        
        # 1. Ler CSV
        dados = ler_csv(caminho_arquivo)
        if not dados:
            return False
        
        # 2. Processar cada linha
        for row in dados:
            id_prescricao = int(row['id_prescricao'])
            cpf_paciente = int(row['cpf_paciente'])
            codigo_medicamento = int(row['codigo_medicamento'])
            quantidade = float(row['quantidade'])
            
            # Buscar o melhor lote disponível (FEFO - menor validade)
            lote_disponivel = Lote.buscar_disponivel(codigo_medicamento, quantidade)
            
            if not lote_disponivel:
                print(f"   ❌ [DEBUG] Nenhum lote disponível para medicamento {codigo_medicamento}")
                LogReserva.registrar(
                    os.path.basename(caminho_arquivo),
                    id_prescricao, cpf_paciente, codigo_medicamento,
                    quantidade, None, None,
                    'ERRO', 'Nenhum lote disponível'
                )
                continue
            
            lote_numero = lote_disponivel['numero_lote']
            id_lote = lote_disponivel['id_lote']
            
            # Criar reserva ativa com o lote escolhido pelo FEFO
            ReservaAtiva.criar(
                id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote_numero, id_lote
            )
            
            LogReserva.registrar(
                os.path.basename(caminho_arquivo),
                id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote_numero, id_lote,
                'PROCESSADO', f'Reserva realizada com lote {lote_numero} (FEFO)'
            )
            print(f"   ✅ [DEBUG] Reserva ativa criada para lote {lote_numero} (FEFO)")
        
        # 3. Mover arquivo original para processados
        mover_para_processados(caminho_arquivo, 'reservas')
        
        print(f"✅ Reserva {os.path.basename(caminho_arquivo)} processada")
        return True