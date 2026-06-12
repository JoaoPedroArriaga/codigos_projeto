"""
ServiceTransacoes - Operações de transações críticas (Reservas e Baixas)
5 operações: criarReserva, obterReserva, cancelarReserva, registrarBaixa, listarBaixas
"""
from typing import List, Optional
from datetime import datetime, date

from src.soap.types import ReservaType, BaixaType, ResultadoType
from src.repositorios import (
    RepositorioReserva, RepositorioBaixa, RepositorioLote, RepositorioMedicamento
)
from src.casos_de_uso import CasoDeUsoReserva, CasoDeUsoBaixa
from src.config.database import db


def _mapear_erro_reserva(mensagem: str) -> str:
    """Converte mensagem de falha em código de erro SOAP"""
    msg = mensagem.lower()
    if 'não encontrado' in msg or 'nao encontrado' in msg:
        return 'MEDICAMENTO_NAO_ENCONTRADO'
    if 'insuficiente' in msg or 'nenhum lote' in msg:
        return 'ESTOQUE_INSUFICIENTE'
    if 'vencido' in msg:
        return 'LOTE_VENCIDO'
    return 'OPERACAO_NAO_AUTORIZADA'


def _mapear_erro_baixa(mensagem: str) -> str:
    """Converte mensagem de falha em código de erro SOAP"""
    msg = mensagem.lower()
    if 'medicamento' in msg and 'não encontrado' in msg:
        return 'MEDICAMENTO_NAO_ENCONTRADO'
    if 'lote' in msg and 'não encontrado' in msg:
        return 'LOTE_NAO_ENCONTRADO'
    if 'insuficiente' in msg:
        return 'ESTOQUE_INSUFICIENTE'
    if 'vencido' in msg:
        return 'LOTE_VENCIDO'
    return 'OPERACAO_NAO_AUTORIZADA'


class ServiceTransacoes:
    """Serviço de transações críticas (SOAP)"""

    def __init__(self):
        self.repo_reserva = RepositorioReserva(db)
        self.repo_baixa = RepositorioBaixa(db)
        self.repo_lote = RepositorioLote(db)
        self.repo_medicamento = RepositorioMedicamento(db)
        self.caso_reserva = CasoDeUsoReserva(
            self.repo_reserva, self.repo_lote, self.repo_medicamento
        )
        self.caso_baixa = CasoDeUsoBaixa(self.repo_lote, self.repo_medicamento)

    def criar_reserva(
        self,
        codigo_medicamento: int,
        quantidade: int,
        cpf_paciente: str
    ) -> ReservaType:
        """Cria uma reserva com seleção automática de lote FEFO"""
        cpf_limpo = cpf_paciente.replace('.', '').replace('-', '')
        if len(cpf_limpo) != 11:
            raise Exception("CPF_INVALIDO: CPF deve ter 11 dígitos")

        try:
            db.begin()
            try:
                resultado = self.caso_reserva.criar_reserva_com_fefo(
                    codigo_medicamento,
                    quantidade,
                    cpf_paciente
                )

                if not resultado['success']:
                    db.rollback()
                    codigo = _mapear_erro_reserva(resultado['mensagem'])
                    raise Exception(f"{codigo}: {resultado['mensagem']}")

                db.commit()

                return ReservaType(
                    id_reserva=str(resultado['id_reserva']),
                    id_prescricao=0,
                    cpf_paciente=cpf_paciente,
                    codigo_medicamento=codigo_medicamento,
                    quantidade=quantidade,
                    numero_lote=resultado['lote_selecionado'],
                    data_validade=resultado.get('data_validade'),
                    preco=float(resultado['preco']) if resultado.get('preco') else None,
                    status='RESERVADO',
                    data_criacao=datetime.now()
                )
            except Exception:
                db.rollback()
                raise
        except Exception as e:
            if any(err in str(e) for err in [
                "MEDICAMENTO_NAO_ENCONTRADO", "ESTOQUE_INSUFICIENTE",
                "CPF_INVALIDO", "LOTE_VENCIDO"
            ]):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")

    def obter_reserva(self, id_reserva: str) -> ReservaType:
        """Busca uma reserva específica por ID"""
        try:
            reserva_dict = self.repo_reserva.buscar_por_id(self._parse_id_reserva(id_reserva))

            if not reserva_dict:
                raise Exception(f"RESERVA_NAO_ENCONTRADA: ID {id_reserva}")

            lote_info = self.repo_lote.buscar_por_id(reserva_dict['id_lote'])

            return ReservaType(
                id_reserva=str(reserva_dict['id_reserva']),
                id_prescricao=int(reserva_dict.get('id_prescricao', 0)),
                cpf_paciente=str(reserva_dict['cpf_paciente']),
                codigo_medicamento=int(reserva_dict['codigo_medicamento']),
                quantidade=int(reserva_dict['quantidade']),
                numero_lote=reserva_dict['lote'],
                data_validade=lote_info['data_validade'] if lote_info else None,
                preco=float(lote_info['preco_venda']) if lote_info else None,
                status=reserva_dict.get('status'),
                data_criacao=reserva_dict.get('data_reserva')
            )
        except Exception as e:
            if "RESERVA_NAO_ENCONTRADA" in str(e):
                raise
            if "invalid literal" in str(e).lower():
                raise Exception(f"RESERVA_NAO_ENCONTRADA: ID {id_reserva} inválido")
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")

    def _parse_id_reserva(self, id_reserva: str) -> int:
        try:
            return int(id_reserva)
        except ValueError:
            raise Exception(f"RESERVA_NAO_ENCONTRADA: ID {id_reserva} inválido")

    def cancelar_reserva(self, id_reserva: str) -> ResultadoType:
        """Cancela uma reserva ativa"""
        try:
            reserva_id = self._parse_id_reserva(id_reserva)
            db.begin()
            try:
                reserva_dict = self.repo_reserva.buscar_por_id(reserva_id)

                if not reserva_dict:
                    raise Exception(f"RESERVA_NAO_ENCONTRADA: ID {id_reserva}")

                if reserva_dict.get('status') == 'CANCELADO':
                    raise Exception(f"RESERVA_JA_CANCELADA: ID {id_reserva}")

                self.repo_reserva.atualizar(
                    reserva_dict['id_reserva'],
                    {'status': 'CANCELADO'}
                )

                db.commit()

                return ResultadoType(
                    success=True,
                    timestamp=datetime.now(),
                    mensagem=f"Reserva {id_reserva} cancelada com sucesso"
                )
            except Exception:
                db.rollback()
                raise
        except Exception as e:
            if any(err in str(e) for err in ["RESERVA_NAO_ENCONTRADA", "RESERVA_JA_CANCELADA"]):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")

    def registrar_baixa(
        self,
        codigo_medicamento: int,
        quantidade: int,
        numero_lote: str,
        cpf_paciente: str,
        motivo: Optional[str] = None
    ) -> BaixaType:
        """Registra uma baixa de medicamento do estoque"""
        try:
            lote = self.repo_lote.buscar_por_numero(codigo_medicamento, numero_lote)
            quantidade_anterior = lote['quantidade_atual'] if lote else 0

            db.begin()
            try:
                resultado = self.caso_baixa.dar_baixa(
                    codigo_medicamento,
                    quantidade,
                    numero_lote,
                    motivo or ""
                )

                if not resultado['success']:
                    db.rollback()
                    codigo = _mapear_erro_baixa(resultado['mensagem'])
                    raise Exception(f"{codigo}: {resultado['mensagem']}")

                registro = self.repo_baixa.registrar(
                    codigo_medicamento=codigo_medicamento,
                    quantidade=quantidade,
                    numero_lote=numero_lote,
                    cpf_paciente=cpf_paciente,
                    id_lote=lote['id_lote'],
                    quantidade_anterior=quantidade_anterior,
                    quantidade_nova=resultado['quantidade_restante'],
                    motivo=motivo
                )

                db.commit()

                return BaixaType(
                    id_baixa=registro['id_baixa'],
                    id_prescricao=registro['id_prescricao'],
                    cpf_paciente=registro['cpf_paciente'],
                    codigo_medicamento=registro['codigo_medicamento'],
                    quantidade=registro['quantidade'],
                    numero_lote=registro['numero_lote'],
                    motivo=registro['motivo'],
                    data_uso=registro['data_uso'],
                    quantidade_restante=registro['quantidade_restante'],
                    timestamp=datetime.now()
                )
            except Exception:
                db.rollback()
                raise
        except Exception as e:
            if any(err in str(e) for err in [
                "LOTE_NAO_ENCONTRADO", "ESTOQUE_INSUFICIENTE",
                "MEDICAMENTO_NAO_ENCONTRADO", "LOTE_VENCIDO"
            ]):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")

    def listar_baixas(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> List[BaixaType]:
        """Lista histórico de baixas em período"""
        try:
            if data_fim is None:
                data_fim = datetime.now().date()
            if data_inicio is None:
                from datetime import timedelta
                data_inicio = data_fim - timedelta(days=7)

            baixas_dict = self.repo_baixa.listar_por_periodo(data_inicio, data_fim)

            return [
                BaixaType(
                    id_baixa=str(b['id_log']),
                    id_prescricao=int(b.get('id_prescricao', 0)),
                    cpf_paciente=str(b['cpf_paciente']),
                    codigo_medicamento=int(b['codigo_medicamento']),
                    quantidade=int(b['quantidade']),
                    numero_lote=b['numero_lote'],
                    motivo=b.get('motivo'),
                    data_uso=int(b['data_uso']) if b.get('data_uso') else None,
                    quantidade_restante=None,
                    timestamp=b.get('timestamp')
                )
                for b in baixas_dict
            ]
        except Exception as e:
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")

    def listar_reservas(self) -> List[ReservaType]:
        """Lista todas as reservas ativas"""
        try:
            reservas_dict = self.repo_reserva.listar_ativas()
            resultado = []
            for r in reservas_dict:
                lote_info = self.repo_lote.buscar_por_id(r['id_lote']) if r.get('id_lote') else None
                resultado.append(ReservaType(
                    id_reserva=str(r.get('id_reserva')),
                    id_prescricao=int(r.get('id_prescricao', 0)),
                    cpf_paciente=str(r['cpf_paciente']),
                    codigo_medicamento=int(r['codigo_medicamento']),
                    quantidade=int(r['quantidade']),
                    numero_lote=r['lote'],
                    data_validade=lote_info['data_validade'] if lote_info else None,
                    preco=float(lote_info['preco_venda']) if lote_info else None,
                    status=r.get('status'),
                    data_criacao=r.get('data_reserva')
                ))
            return resultado
        except Exception as e:
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
