"""
ServiceTransacoes - Operações de transações críticas (Reservas e Baixas)
5 operações: criarReserva, obterReserva, cancelarReserva, registrarBaixa, listarBaixas
⭐ OPERAÇÕES CRÍTICAS: criarReserva e registrarBaixa usam FEFO e transações BD
"""
from typing import List, Optional
from datetime import datetime, date

from src.soap.types import ReservaType, BaixaType, ResultadoType
from src.repositorios import (
    RepositorioReserva, RepositorioBaixa, RepositorioLote, RepositorioMedicamento
)
from src.casos_de_uso import CasoDeUsoReserva, CasoDeUsoBaixa
from src.config.database import db


class ServiceTransacoes:
    """Serviço de transações críticas (SOAP)"""
    
    def __init__(self):
        self.repo_reserva = RepositorioReserva(db)
        self.repo_baixa = RepositorioBaixa(db)
        self.repo_lote = RepositorioLote(db)
        self.repo_medicamento = RepositorioMedicamento(db)
        self.caso_reserva = CasoDeUsoReserva(
            self.repo_reserva, self.repo_lote, self.repo_medicamento, db
        )
        self.caso_baixa = CasoDeUsoBaixa(
            self.repo_baixa, self.repo_lote, self.repo_medicamento, db
        )
    
    # ===== OPERAÇÃO 1: criarReserva (⭐ CRÍTICA COM FEFO) =====
    def criar_reserva(
        self, 
        codigo_medicamento: int, 
        quantidade: int, 
        cpf_paciente: str
    ) -> ReservaType:
        """
        Cria uma reserva com seleção automática de lote FEFO
        
        Fluxo:
        1. Validar CPF
        2. Buscar medicamento
        3. FEFO: Selecionar lote com menor validade
        4. Criar reserva no BD (transação)
        5. Retornar ReservaType com lote + preço
        
        Args:
            codigo_medicamento: Código do medicamento
            quantidade: Quantidade a reservar
            cpf_paciente: CPF do paciente
            
        Returns:
            ReservaType com ID da reserva e lote selecionado
            
        Raises:
            Exception: Se medicamento não existe, estoque insuficiente, erro BD
        """
        try:
            # Validar CPF
            if len(cpf_paciente.replace('.', '').replace('-', '')) != 11:
                raise Exception("CPF_INVALIDO: CPF deve ter 11 dígitos")
            
            # Usar caso de uso (gerencia transação e FEFO)
            db.begin()
            try:
                resultado = self.caso_reserva.executar(
                    codigo_medicamento, 
                    quantidade, 
                    cpf_paciente
                )
                db.commit()
                
                # Converter resultado para tipo SOAP
                return ReservaType(
                    id_reserva=resultado['id_reserva'],
                    id_prescricao=resultado.get('id_prescricao'),
                    cpf_paciente=resultado['cpf_paciente'],
                    codigo_medicamento=resultado['codigo_medicamento'],
                    quantidade=resultado['quantidade'],
                    numero_lote=resultado['numero_lote'],
                    data_validade=resultado.get('data_validade'),
                    preco=float(resultado.get('preco', 0)) if resultado.get('preco') else None,
                    status=resultado.get('status', 'ativa'),
                    data_criacao=resultado.get('data_criacao', datetime.now())
                )
            
            except Exception as e:
                db.rollback()
                raise e
        
        except Exception as e:
            if any(err in str(e) for err in ["MEDICAMENTO_NAO_ENCONTRADO", "ESTOQUE_INSUFICIENTE", "CPF_INVALIDO"]):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 2: obterReserva =====
    def obter_reserva(self, id_reserva: str) -> ReservaType:
        """
        Busca uma reserva específica por ID
        
        Args:
            id_reserva: ID da reserva
            
        Returns:
            ReservaType com dados completos
            
        Raises:
            Exception: Se reserva não encontrada ou erro BD
        """
        try:
            reserva_dict = self.repo_reserva.buscar_por_id_reserva(id_reserva)
            
            if not reserva_dict:
                raise Exception(f"RESERVA_NAO_ENCONTRADA: ID {id_reserva}")
            
            return ReservaType(
                id_reserva=reserva_dict['id_reserva'],
                id_prescricao=reserva_dict.get('id_prescricao'),
                cpf_paciente=reserva_dict['cpf_paciente'],
                codigo_medicamento=reserva_dict['codigo_medicamento'],
                quantidade=reserva_dict['quantidade'],
                numero_lote=reserva_dict['numero_lote'],
                data_validade=reserva_dict.get('data_validade'),
                preco=float(reserva_dict.get('preco', 0)) if reserva_dict.get('preco') else None,
                status=reserva_dict.get('status'),
                data_criacao=reserva_dict.get('data_criacao')
            )
        
        except Exception as e:
            if "RESERVA_NAO_ENCONTRADA" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 3: cancelarReserva =====
    def cancelar_reserva(self, id_reserva: str) -> ResultadoType:
        """
        Cancela uma reserva ativa (libera lote)
        
        Args:
            id_reserva: ID da reserva
            
        Returns:
            ResultadoType com sucesso
            
        Raises:
            Exception: Se reserva não encontrada, já cancelada, ou erro BD
        """
        try:
            db.begin()
            try:
                reserva_dict = self.repo_reserva.buscar_por_id_reserva(id_reserva)
                
                if not reserva_dict:
                    raise Exception(f"RESERVA_NAO_ENCONTRADA: ID {id_reserva}")
                
                if reserva_dict.get('status') == 'cancelada':
                    raise Exception(f"RESERVA_JA_CANCELADA: ID {id_reserva}")
                
                # Cancelar (marcar como cancelada)
                self.repo_reserva.atualizar(
                    reserva_dict['id'],  # ID interno
                    {'status': 'cancelada'}
                )
                
                db.commit()
                
                return ResultadoType(
                    success=True,
                    timestamp=datetime.now(),
                    mensagem=f"Reserva {id_reserva} cancelada com sucesso"
                )
            
            except Exception as e:
                db.rollback()
                raise e
        
        except Exception as e:
            if any(err in str(e) for err in ["RESERVA_NAO_ENCONTRADA", "RESERVA_JA_CANCELADA"]):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 4: registrarBaixa (⭐ CRÍTICA COM TRANSAÇÃO) =====
    def registrar_baixa(
        self, 
        codigo_medicamento: int, 
        quantidade: int, 
        numero_lote: str, 
        cpf_paciente: str,
        motivo: Optional[str] = None
    ) -> BaixaType:
        """
        Registra uma baixa (saída) de medicamento do estoque
        
        Fluxo:
        1. Validar lote existe
        2. Validar quantidade suficiente no lote
        3. Reduzir quantidade_atual do lote (transação)
        4. Registrar baixa no histórico
        5. Retornar BaixaType com qtd restante
        
        Args:
            codigo_medicamento: Código do medicamento
            quantidade: Quantidade a dar baixa
            numero_lote: Número do lote
            cpf_paciente: CPF do paciente (informativo)
            motivo: Motivo da baixa (ex: "Dispensação ao paciente")
            
        Returns:
            BaixaType com ID, quantidade restante, etc
            
        Raises:
            Exception: Se lote não existe, quantidade insuficiente, erro BD
        """
        try:
            # Usar caso de uso (gerencia transação)
            db.begin()
            try:
                resultado = self.caso_baixa.executar(
                    codigo_medicamento,
                    quantidade,
                    numero_lote,
                    cpf_paciente,
                    motivo
                )
                db.commit()
                
                # Converter resultado para tipo SOAP
                return BaixaType(
                    id_baixa=resultado.get('id_baixa'),
                    id_prescricao=resultado.get('id_prescricao'),
                    cpf_paciente=resultado['cpf_paciente'],
                    codigo_medicamento=resultado['codigo_medicamento'],
                    quantidade=resultado['quantidade'],
                    numero_lote=resultado['numero_lote'],
                    motivo=resultado.get('motivo'),
                    data_uso=resultado.get('data_uso'),
                    quantidade_restante=resultado.get('quantidade_restante'),
                    timestamp=resultado.get('timestamp', datetime.now())
                )
            
            except Exception as e:
                db.rollback()
                raise e
        
        except Exception as e:
            if any(err in str(e) for err in ["LOTE_NAO_ENCONTRADO", "ESTOQUE_INSUFICIENTE"]):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 5: listarBaixas =====
    def listar_baixas(
        self, 
        data_inicio: Optional[date] = None, 
        data_fim: Optional[date] = None
    ) -> List[BaixaType]:
        """
        Lista histórico de baixas em período (relatório)
        
        Args:
            data_inicio: Data inicial (opt) - padrão: última semana
            data_fim: Data final (opt) - padrão: hoje
            
        Returns:
            Lista de BaixaType ordenada por data desc
            
        Raises:
            Exception: Se erro BD
        """
        try:
            # Padrões se não especificado
            if data_fim is None:
                data_fim = datetime.now().date()
            if data_inicio is None:
                from datetime import timedelta
                data_inicio = data_fim - timedelta(days=7)
            
            # Listar baixas no período
            baixas_dict = self.repo_baixa.listar_por_periodo(data_inicio, data_fim)
            
            return [
                BaixaType(
                    id_baixa=b.get('id_baixa'),
                    id_prescricao=b.get('id_prescricao'),
                    cpf_paciente=b['cpf_paciente'],
                    codigo_medicamento=b['codigo_medicamento'],
                    quantidade=b['quantidade'],
                    numero_lote=b['numero_lote'],
                    motivo=b.get('motivo'),
                    data_uso=b.get('data_uso'),
                    quantidade_restante=b.get('quantidade_restante'),
                    timestamp=b.get('timestamp')
                )
                for b in baixas_dict
            ]
        
        except Exception as e:
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
