"""
ServiceEstoque - Operações de gerenciamento de estoque
5 operações: obterEstoque, listarLotes, consultarDisponibilidade, verificarReservas, gerarAlerta
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.soap.types import (
    EstoqueType, LoteType, RespostaItemType, RespostaType, 
    ReservaType, ResultadoType
)
from src.repositorios import (
    RepositorioMedicamento, RepositorioLote, RepositorioReserva
)
from src.casos_de_uso import CasoDeUsoEstoque, CasoDeUsoConsulta
from src.config.database import db


class ServiceEstoque:
    """Serviço de estoque (SOAP)"""
    
    def __init__(self):
        self.repo_medicamento = RepositorioMedicamento(db)
        self.repo_lote = RepositorioLote(db)
        self.repo_reserva = RepositorioReserva(db)
        self.caso_estoque = CasoDeUsoEstoque(self.repo_lote, self.repo_medicamento)
        self.caso_consulta = CasoDeUsoConsulta(self.repo_lote, self.repo_medicamento)
    
    # ===== OPERAÇÃO 1: obterEstoque =====
    def obter_estoque(self, codigo_medicamento: int) -> EstoqueType:
        """
        Retorna estoque completo (total + lotes) de um medicamento
        
        Args:
            codigo_medicamento: Código do medicamento
            
        Returns:
            EstoqueType com quantidade total e lista de lotes
            
        Raises:
            Exception: Se medicamento não encontrado ou erro BD
        """
        try:
            medicamento = self.repo_medicamento.buscar_por_codigo(codigo_medicamento)
            
            if not medicamento:
                raise Exception(f"MEDICAMENTO_NAO_ENCONTRADO: Código {codigo_medicamento}")
            
            # Usar caso de uso para agregar lotes
            estoque_dict = self.caso_estoque.obter_estoque_total(codigo_medicamento)
            
            # Converter lotes para tipos SOAP
            lotes = [
                LoteType(
                    numero_lote=lote['numero_lote'],
                    codigo_medicamento=lote['codigo_medicamento'],
                    quantidade_atual=lote['quantidade_atual'],
                    data_validade=lote['data_validade'],
                    preco_venda=float(lote['preco_venda']),
                    id_lote=lote.get('id_lote'),
                    quantidade_inicial=lote.get('quantidade_inicial')
                )
                for lote in estoque_dict['lotes']
            ]
            
            return EstoqueType(
                codigo_medicamento=codigo_medicamento,
                quantidade_total=estoque_dict['quantidade_total'],
                lotes=lotes,
                nome_medicamento=medicamento['nome']
            )
        
        except Exception as e:
            if "MEDICAMENTO_NAO_ENCONTRADO" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 2: listarLotes =====
    def listar_lotes(self, codigo_medicamento: int) -> List[LoteType]:
        """
        Lista todos os lotes de um medicamento (ordenado por FEFO - validade crescente)
        
        Args:
            codigo_medicamento: Código do medicamento
            
        Returns:
            Lista de LoteType ordenada por validade (FEFO)
            
        Raises:
            Exception: Se medicamento não encontrado ou erro BD
        """
        try:
            # Verificar se medicamento existe
            medicamento = self.repo_medicamento.buscar_por_codigo(codigo_medicamento)
            if not medicamento:
                raise Exception(f"MEDICAMENTO_NAO_ENCONTRADO: Código {codigo_medicamento}")
            
            # Listar lotes (repo_lote.listar_por_medicamento retorna ordenado por FEFO)
            lotes_dict = self.repo_lote.listar_por_medicamento(codigo_medicamento)
            
            return [
                LoteType(
                    numero_lote=lote['numero_lote'],
                    codigo_medicamento=lote['codigo_medicamento'],
                    quantidade_atual=lote['quantidade_atual'],
                    data_validade=lote['data_validade'],
                    preco_venda=float(lote['preco_venda']),
                    id_lote=lote.get('id_lote'),
                    quantidade_inicial=lote.get('quantidade_inicial')
                )
                for lote in lotes_dict
            ]
        
        except Exception as e:
            if "MEDICAMENTO_NAO_ENCONTRADO" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 3: consultarDisponibilidade (⭐ CRÍTICA) =====
    def consultar_disponibilidade(
        self, 
        codigo_medicamento: int, 
        quantidade: int, 
        cpf_paciente: str
    ) -> RespostaType:
        """
        Consulta disponibilidade de medicamento (baseado em resposta.xsd)
        Operação crítica usada pelo Grupo 2
        
        Args:
            codigo_medicamento: Código do medicamento
            quantidade: Quantidade solicitada
            cpf_paciente: CPF do paciente (informativo)
            
        Returns:
            RespostaType com disponibilidade e observação
            
        Raises:
            Exception: Se código inválido ou erro BD
        """
        try:
            # Validar CPF (11 dígitos)
            if len(cpf_paciente.replace('.', '').replace('-', '')) != 11:
                raise Exception(f"CPF_INVALIDO: CPF deve ter 11 dígitos")
            
            # Usar caso de uso para processar consulta
            resultado = self.caso_consulta.processar_consulta(
                codigo_medicamento, 
                quantidade, 
                cpf_paciente
            )
            
            # Converter para tipo SOAP
            respostas = [
                RespostaItemType(
                    codigo_medicamento=r['codigo_medicamento'],
                    disponivel=r['disponivel'],
                    observacao=r.get('observacao')
                )
                for r in resultado['respostas']
            ]
            
            return RespostaType(respostas=respostas)
        
        except Exception as e:
            if "CPF_INVALIDO" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 4: verificarReservas =====
    def verificar_reservas(self, codigo_medicamento: int) -> List[ReservaType]:
        """
        Lista todas as reservas ativas para um medicamento
        
        Args:
            codigo_medicamento: Código do medicamento
            
        Returns:
            Lista de ReservaType (apenas ativas)
            
        Raises:
            Exception: Se erro BD
        """
        try:
            # Listar reservas ativas para medicamento
            reservas_dict = self.repo_reserva.listar_por_medicamento_ativas(codigo_medicamento)
            
            return [
                ReservaType(
                    id_reserva=r.get('id_reserva'),
                    id_prescricao=r['id_prescricao'],
                    cpf_paciente=r['cpf_paciente'],
                    codigo_medicamento=r['codigo_medicamento'],
                    quantidade=r['quantidade'],
                    numero_lote=r['numero_lote'],
                    data_validade=r.get('data_validade'),
                    preco=float(r['preco']) if r.get('preco') else None,
                    status=r.get('status'),
                    data_criacao=r.get('data_criacao')
                )
                for r in reservas_dict
            ]
        
        except Exception as e:
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 5: gerarAlerta =====
    def gerar_alerta(self, codigo_medicamento: int, quantidade_minima: int) -> ResultadoType:
        """
        Gera alerta se estoque do medicamento está abaixo do mínimo
        
        Args:
            codigo_medicamento: Código do medicamento
            quantidade_minima: Limite mínimo de estoque
            
        Returns:
            ResultadoType com sucesso
            
        Raises:
            Exception: Se erro BD
        """
        try:
            medicamento = self.repo_medicamento.buscar_por_codigo(codigo_medicamento)
            if not medicamento:
                raise Exception(f"MEDICAMENTO_NAO_ENCONTRADO: Código {codigo_medicamento}")
            
            # Obter estoque total
            estoque_dict = self.caso_estoque.obter_estoque_total(codigo_medicamento)
            quantidade_total = estoque_dict['quantidade_total']
            
            # Verificar se está abaixo do mínimo
            alerta_necessario = quantidade_total < quantidade_minima
            
            mensagem = f"Estoque de '{medicamento['nome']}': {quantidade_total} un. "
            if alerta_necessario:
                mensagem += f"(ALERTA: abaixo do mínimo {quantidade_minima})"
            else:
                mensagem += f"(OK - acima do mínimo {quantidade_minima})"
            
            return ResultadoType(
                success=True,
                timestamp=datetime.now(),
                mensagem=mensagem
            )
        
        except Exception as e:
            if "MEDICAMENTO_NAO_ENCONTRADO" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
