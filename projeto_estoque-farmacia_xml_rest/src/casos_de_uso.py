"""
Casos de uso (Use Cases) - Lógica de negócio.
Implementa o Single Responsibility Principle e FEFO.
"""
from datetime import date, datetime
from typing import Dict, Any, Optional, List


class CasoDeUsoEstoque:
    """Lógica de negócio para operações de estoque"""
    
    def __init__(self, repo_lote, repo_medicamento):
        self.repo_lote = repo_lote
        self.repo_medicamento = repo_medicamento
    
    def verificar_disponibilidade(self, codigo_medicamento: int, quantidade: int) -> Dict[str, Any]:
        """Verifica disponibilidade de medicamento usando FEFO"""
        lote = self.repo_lote.buscar_disponivel_fefo(codigo_medicamento, quantidade)
        
        if lote:
            return {
                'disponivel': True,
                'lote': lote['numero_lote'],
                'validade': lote['data_validade'],
                'preco': float(lote['preco_venda']),
                'quantidade_disponivel': lote['quantidade_atual']
            }
        
        return {
            'disponivel': False,
            'lote': None,
            'validade': None,
            'preco': None,
            'quantidade_disponivel': 0
        }
    
    def obter_estoque_total(self, codigo_medicamento: int) -> Dict[str, Any]:
        """Obtém estoque total de um medicamento"""
        lotes = self.repo_lote.listar_por_medicamento(codigo_medicamento)
        
        if not lotes:
            return {
                'codigo_medicamento': codigo_medicamento,
                'quantidade_total': 0,
                'lotes': []
            }
        
        quantidade_total = sum(lote['quantidade_atual'] for lote in lotes)
        
        return {
            'codigo_medicamento': codigo_medicamento,
            'quantidade_total': quantidade_total,
            'lotes': lotes,
            'data_primeiro_vencimento': min(lote['data_validade'] for lote in lotes)
        }


class CasoDeUsoConsulta:
    """Lógica de negócio para consultas"""
    
    def __init__(self, repo_lote, repo_medicamento):
        self.repo_lote = repo_lote
        self.repo_medicamento = repo_medicamento
    
    def processar_consulta(self, codigo_medicamento: int, quantidade: int, cpf_paciente: str) -> Dict[str, Any]:
        """Processa uma consulta de disponibilidade usando FEFO"""
        medicamento = self.repo_medicamento.buscar_por_codigo(codigo_medicamento)
        
        if not medicamento:
            return {
                'success': True,
                'disponivel': False,
                'lote': None,
                'validade': None,
                'preco': None,
                'quantidade_disponivel': 0,
                'mensagem': f'Medicamento {codigo_medicamento} não encontrado'
            }
        
        lote = self.repo_lote.buscar_disponivel_fefo(codigo_medicamento, quantidade)
        
        if lote:
            return {
                'success': True,
                'disponivel': True,
                'lote': lote['numero_lote'],
                'validade': lote['data_validade'],
                'preco': float(lote['preco_venda']),
                'quantidade_disponivel': lote['quantidade_atual'],
                'mensagem': f'Disponível: {lote["quantidade_atual"]} unidades no lote {lote["numero_lote"]}'
            }
        
        return {
            'success': True,
            'disponivel': False,
            'lote': None,
            'validade': None,
            'preco': None,
            'quantidade_disponivel': 0,
            'mensagem': f'Medicamento indisponível na quantidade solicitada ({quantidade})'
        }


class CasoDeUsoReserva:
    """Lógica de negócio para reservas usando FEFO (First Expiry First Out)"""
    
    def __init__(self, repo_reserva, repo_lote, repo_medicamento):
        self.repo_reserva = repo_reserva
        self.repo_lote = repo_lote
        self.repo_medicamento = repo_medicamento
    
    def criar_reserva_com_fefo(self, codigo_medicamento: int, quantidade: int, cpf_paciente: str) -> Dict[str, Any]:
        """
        Cria uma reserva usando FEFO (First Expiry First Out)
        O lote é automaticamente selecionado - o que vence primeiro
        """
        # Validar medicamento
        medicamento = self.repo_medicamento.buscar_por_codigo(codigo_medicamento)
        if not medicamento:
            return {
                'success': False,
                'id_reserva': None,
                'lote_selecionado': None,
                'data_validade': None,
                'preco': None,
                'mensagem': f'Medicamento {codigo_medicamento} não encontrado',
                'timestamp': datetime.now().isoformat()
            }
        
        # Buscar lote disponível com FEFO (menor data de validade)
        lote = self.repo_lote.buscar_disponivel_fefo(codigo_medicamento, quantidade)
        
        if not lote:
            # Verificar se há lotes mas com quantidade insuficiente
            lotes_disponiveis = self.repo_lote.listar_disponiveis_fefo(codigo_medicamento)
            if lotes_disponiveis:
                total_disponivel = sum(l['quantidade_atual'] for l in lotes_disponiveis)
                return {
                    'success': False,
                    'id_reserva': None,
                    'lote_selecionado': None,
                    'data_validade': None,
                    'preco': None,
                    'mensagem': f'Estoque insuficiente. Disponível: {total_disponivel} unidades. Solicitado: {quantidade}',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'id_reserva': None,
                    'lote_selecionado': None,
                    'data_validade': None,
                    'preco': None,
                    'mensagem': f'Nenhum lote disponível para o medicamento {codigo_medicamento}',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Verificar validade
        if lote['data_validade'] < date.today():
            return {
                'success': False,
                'id_reserva': None,
                'lote_selecionado': lote['numero_lote'],
                'data_validade': lote['data_validade'],
                'preco': float(lote['preco_venda']),
                'mensagem': f'Lote {lote["numero_lote"]} está vencido desde {lote["data_validade"]}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Criar reserva com o lote selecionado pelo FEFO
        try:
            id_reserva = self.repo_reserva.criar({
                'codigo_medicamento': codigo_medicamento,
                'quantidade': quantidade,
                'numero_lote': lote['numero_lote'],
                'id_lote': lote['id_lote'],
                'cpf_paciente': cpf_paciente,
                'id_prescricao': 0,
                'status': 'ativa'
            })
            
            return {
                'success': True,
                'id_reserva': str(id_reserva),
                'lote_selecionado': lote['numero_lote'],
                'data_validade': lote['data_validade'],
                'preco': float(lote['preco_venda']),
                'mensagem': f'Reserva criada com sucesso! Lote {lote["numero_lote"]} selecionado (FEFO - vence em {lote["data_validade"].strftime("%d/%m/%Y")})',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'id_reserva': None,
                'lote_selecionado': lote['numero_lote'],
                'data_validade': lote['data_validade'],
                'preco': float(lote['preco_venda']),
                'mensagem': f'Erro ao criar reserva: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def listar_lotes_disponiveis_fefo(self, codigo_medicamento: int) -> List[Dict[str, Any]]:
        """Lista lotes disponíveis ordenados por FEFO"""
        return self.repo_lote.listar_disponiveis_fefo(codigo_medicamento)
    
    def cancelar_reserva(self, id_reserva: int) -> Dict[str, Any]:
        """Cancela uma reserva"""
        reserva = self.repo_reserva.buscar_por_id(id_reserva)
        
        if not reserva:
            return {
                'success': False,
                'mensagem': f'Reserva {id_reserva} não encontrada'
            }
        
        if reserva['status'] != 'ativa':
            return {
                'success': False,
                'mensagem': f'Reserva {id_reserva} já está {reserva["status"]}'
            }
        
        sucesso = self.repo_reserva.atualizar(id_reserva, {'status': 'cancelada'})
        
        return {
            'success': sucesso,
            'mensagem': 'Reserva cancelada com sucesso' if sucesso else 'Erro ao cancelar reserva'
        }
    
    def buscar_reserva_por_id(self, id_reserva: int) -> Optional[Dict[str, Any]]:
        """Busca uma reserva por ID"""
        return self.repo_reserva.buscar_por_id(id_reserva)
    
    def listar_reservas_ativas(self) -> List[Dict[str, Any]]:
        """Lista todas as reservas ativas"""
        return self.repo_reserva.listar_ativas()


class CasoDeUsoBaixa:
    """Lógica de negócio para baixas de estoque"""
    
    def __init__(self, repo_lote, repo_medicamento):
        self.repo_lote = repo_lote
        self.repo_medicamento = repo_medicamento
    
    def dar_baixa(self, codigo_medicamento: int, quantidade: int, 
                  numero_lote: str, motivo: str = "") -> Dict[str, Any]:
        """Processa baixa de estoque"""
        
        # Validar medicamento
        medicamento = self.repo_medicamento.buscar_por_codigo(codigo_medicamento)
        if not medicamento:
            return {
                'success': False,
                'id_baixa': None,
                'quantidade_restante': None,
                'mensagem': f'Medicamento {codigo_medicamento} não encontrado',
                'timestamp': datetime.now().isoformat()
            }
        
        # Validar lote
        lote = self.repo_lote.buscar_por_numero(codigo_medicamento, numero_lote)
        if not lote:
            return {
                'success': False,
                'id_baixa': None,
                'quantidade_restante': None,
                'mensagem': f'Lote {numero_lote} não encontrado',
                'timestamp': datetime.now().isoformat()
            }
        
        # Verificar estoque
        if lote['quantidade_atual'] < quantidade:
            return {
                'success': False,
                'id_baixa': None,
                'quantidade_restante': lote['quantidade_atual'],
                'mensagem': f'Estoque insuficiente. Disponível: {lote["quantidade_atual"]}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Verificar validade
        if lote['data_validade'] < date.today():
            return {
                'success': False,
                'id_baixa': None,
                'quantidade_restante': lote['quantidade_atual'],
                'mensagem': f'Não é possível dar baixa em lote vencido: {numero_lote}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Calcular nova quantidade
        nova_quantidade = lote['quantidade_atual'] - quantidade
        
        # Atualizar lote
        sucesso = self.repo_lote.atualizar(lote['id_lote'], {
            'quantidade_atual': nova_quantidade
        })
        
        if sucesso:
            return {
                'success': True,
                'id_baixa': str(lote['id_lote']),
                'quantidade_restante': nova_quantidade,
                'mensagem': f'Baixa de {quantidade} unidades realizada com sucesso',
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'success': False,
            'id_baixa': None,
            'quantidade_restante': lote['quantidade_atual'],
            'mensagem': 'Erro ao processar baixa',
            'timestamp': datetime.now().isoformat()
        }