"""
Repositórios abstratos seguindo Dependency Inversion Principle.
Desacopla a lógica de negócio do banco de dados.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class RepositorioBase(ABC):
    """Interface base para repositórios"""
    
    @abstractmethod
    def listar_todos(self) -> List[Dict[str, Any]]:
        """Lista todos os registros"""
        pass
    
    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Busca um registro por ID"""
        pass
    
    @abstractmethod
    def criar(self, dados: Dict[str, Any]) -> int:
        """Cria um novo registro, retorna ID"""
        pass
    
    @abstractmethod
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        """Atualiza um registro"""
        pass
    
    @abstractmethod
    def deletar(self, id: int) -> bool:
        """Deleta um registro"""
        pass


class RepositorioMedicamento(RepositorioBase):
    """Repositório de medicamentos"""
    
    def __init__(self, db):
        self.db = db
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM projeto.medicamentos ORDER BY nome",
            fetch_all=True
        )
    
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.buscar_por_codigo(id)
    
    def buscar_por_codigo(self, codigo: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM projeto.medicamentos WHERE codigo = %s",
            (codigo,),
            fetch_one=True
        )
    
    def criar(self, dados: Dict[str, Any]) -> int:
        resultado = self.db.execute(
            """INSERT INTO projeto.medicamentos (codigo, nome)
               VALUES (%s, %s)
               ON CONFLICT (codigo) DO UPDATE SET nome = EXCLUDED.nome
               RETURNING codigo""",
            (dados['codigo'], dados['nome']),
            fetch_one=True
        )
        return int(resultado['codigo']) if resultado else None
    
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        return self.db.execute(
            "UPDATE projeto.medicamentos SET nome = %s WHERE codigo = %s",
            (dados['nome'], id)
        ) > 0
    
    def deletar(self, id: int) -> bool:
        return self.db.execute(
            "DELETE FROM projeto.medicamentos WHERE codigo = %s",
            (id,)
        ) > 0


class RepositorioLote(RepositorioBase):
    """Repositório de lotes"""
    
    def __init__(self, db):
        self.db = db
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM projeto.lotes ORDER BY data_validade ASC",
            fetch_all=True
        )
    
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM projeto.lotes WHERE id_lote = %s",
            (id,),
            fetch_one=True
        )
    
    def listar_por_medicamento(self, codigo_medicamento: int) -> List[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM projeto.lotes 
               WHERE codigo_medicamento = %s 
               ORDER BY data_validade ASC""",
            (codigo_medicamento,),
            fetch_all=True
        )
    
    def buscar_disponivel(self, codigo_medicamento: int, quantidade: int) -> Optional[Dict[str, Any]]:
        """Busca lote disponível seguindo FEFO (First Expiry First Out)"""
        return self.db.execute(
            """SELECT * FROM projeto.lotes 
               WHERE codigo_medicamento = %s 
                 AND quantidade_atual >= %s 
                 AND data_validade >= CURRENT_DATE 
               ORDER BY data_validade ASC 
               LIMIT 1""",
            (codigo_medicamento, quantidade),
            fetch_one=True
        )
    
    def buscar_disponivel_fefo(self, codigo_medicamento: int, quantidade: int) -> Optional[Dict[str, Any]]:
        """
        Busca lote disponível seguindo FEFO (First Expiry First Out)
        Retorna o lote com menor data de validade que atende a quantidade
        """
        return self.db.execute(
            """SELECT * FROM projeto.lotes 
               WHERE codigo_medicamento = %s 
                 AND quantidade_atual >= %s 
                 AND data_validade >= CURRENT_DATE 
               ORDER BY data_validade ASC 
               LIMIT 1""",
            (codigo_medicamento, quantidade),
            fetch_one=True
        )
    
    def listar_disponiveis_fefo(self, codigo_medicamento: int) -> List[Dict[str, Any]]:
        """
        Lista todos os lotes disponíveis ordenados por FEFO
        """
        return self.db.execute(
            """SELECT * FROM projeto.lotes 
               WHERE codigo_medicamento = %s 
                 AND quantidade_atual > 0 
                 AND data_validade >= CURRENT_DATE 
               ORDER BY data_validade ASC""",
            (codigo_medicamento,),
            fetch_all=True
        )
    
    def buscar_por_numero(self, codigo_medicamento: int, numero_lote: str) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM projeto.lotes 
               WHERE codigo_medicamento = %s 
                 AND numero_lote = %s""",
            (codigo_medicamento, numero_lote),
            fetch_one=True
        )
    
    def criar(self, dados: Dict[str, Any]) -> int:
        resultado = self.db.execute(
            """INSERT INTO projeto.lotes 
               (numero_lote, codigo_medicamento, quantidade_inicial, 
                quantidade_atual, data_validade, preco_venda) 
               VALUES (%s, %s, %s, %s, %s, %s) 
               RETURNING id_lote""",
            (dados['numero_lote'], dados['codigo_medicamento'],
             dados['quantidade_inicial'], dados['quantidade_atual'],
             dados['data_validade'], dados['preco_venda']),
            fetch_one=True
        )
        return resultado['id_lote'] if resultado else None
    
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        return self.db.execute(
            "UPDATE projeto.lotes SET quantidade_atual = %s WHERE id_lote = %s",
            (dados['quantidade_atual'], id)
        ) > 0
    
    def deletar(self, id: int) -> bool:
        return self.db.execute(
            "DELETE FROM projeto.lotes WHERE id_lote = %s",
            (id,)
        ) > 0


class RepositorioReserva(RepositorioBase):
    """Repositório de reservas"""
    
    def __init__(self, db):
        self.db = db
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM projeto.reservas_ativas ORDER BY data_reserva DESC",
            fetch_all=True
        )
    
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM projeto.reservas_ativas WHERE id_reserva = %s",
            (id,),
            fetch_one=True
        )
    
    def listar_ativas(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM projeto.reservas_ativas 
               WHERE status = 'RESERVADO'
               ORDER BY data_reserva DESC""",
            fetch_all=True
        )

    def listar_por_medicamento_ativas(self, codigo_medicamento: int) -> List[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM projeto.reservas_ativas
               WHERE codigo_medicamento = %s AND status = 'RESERVADO'
               ORDER BY data_reserva DESC""",
            (codigo_medicamento,),
            fetch_all=True
        ) or []
    
    def criar(self, dados: Dict[str, Any]) -> int:
        resultado = self.db.execute(
            """INSERT INTO projeto.reservas_ativas 
               (codigo_medicamento, quantidade, lote, id_lote, cpf_paciente, id_prescricao, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) 
               RETURNING id_reserva""",
            (dados['codigo_medicamento'], dados['quantidade'],
             dados['numero_lote'], dados.get('id_lote', 0), dados['cpf_paciente'], 
             dados.get('id_prescricao', 0), dados.get('status', 'RESERVADO')),
            fetch_one=True
        )
        return resultado['id_reserva'] if resultado else None
    
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        return self.db.execute(
            "UPDATE projeto.reservas_ativas SET status = %s WHERE id_reserva = %s",
            (dados['status'], id)
        ) > 0
    
    def deletar(self, id: int) -> bool:
        return self.db.execute(
            "DELETE FROM projeto.reservas_ativas WHERE id_reserva = %s",
            (id,)
        ) > 0


class RepositorioBaixa:
    """Repositório de baixas de estoque (logs + movimentações)"""

    def __init__(self, db):
        self.db = db

    def listar_por_periodo(
        self,
        data_inicio,
        data_fim
    ) -> List[Dict[str, Any]]:
        """Lista baixas processadas em um período"""
        return self.db.execute(
            """SELECT lb.id_log, lb.id_prescricao, lb.cpf_paciente,
                      lb.codigo_medicamento, lb.quantidade,
                      lb.lote AS numero_lote, lb.data_uso, lb.observacao AS motivo,
                      lb.data_recebimento AS timestamp, lb.id_lote
               FROM logs_baixas lb
               WHERE lb.status = 'PROCESSADO'
                 AND lb.data_recebimento::date BETWEEN %s AND %s
               ORDER BY lb.data_recebimento DESC""",
            (data_inicio, data_fim),
            fetch_all=True
        ) or []

    def registrar(
        self,
        codigo_medicamento: int,
        quantidade: int,
        numero_lote: str,
        cpf_paciente: str,
        id_lote: int,
        quantidade_anterior: int,
        quantidade_nova: int,
        motivo: str = "",
        id_prescricao: int = 0,
        data_uso: int = None
    ) -> Dict[str, Any]:
        """Registra baixa em logs_baixas e movimentacoes"""
        if data_uso is None:
            from datetime import datetime
            data_uso = int(datetime.now().strftime('%y%m%d'))

        log = self.db.execute(
            """INSERT INTO logs_baixas
               (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote, data_uso, id_lote, status, observacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id_log""",
            (
                'SOAP_API',
                id_prescricao,
                cpf_paciente,
                codigo_medicamento,
                quantidade,
                numero_lote,
                data_uso,
                id_lote,
                'PROCESSADO',
                motivo or 'Baixa via SOAP'
            ),
            fetch_one=True
        )

        if not log:
            return None

        self.db.execute(
            """INSERT INTO movimentacoes
               (id_lote, tipo, quantidade, quantidade_anterior,
                quantidade_nova, referencia_id, referencia_tabela)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                id_lote,
                'BAIXA',
                quantidade,
                quantidade_anterior,
                quantidade_nova,
                log['id_log'],
                'logs_baixas'
            )
        )

        return {
            'id_baixa': str(log['id_log']),
            'id_prescricao': id_prescricao,
            'cpf_paciente': str(cpf_paciente),
            'codigo_medicamento': codigo_medicamento,
            'quantidade': quantidade,
            'numero_lote': numero_lote,
            'motivo': motivo,
            'data_uso': data_uso,
            'quantidade_restante': quantidade_nova,
            'timestamp': None
        }