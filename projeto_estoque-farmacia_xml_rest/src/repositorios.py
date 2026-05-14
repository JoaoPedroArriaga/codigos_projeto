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
            "SELECT * FROM medicamentos ORDER BY nome",
            fetch_all=True
        )
    
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM medicamentos WHERE id = %s",
            (id,),
            fetch_one=True
        )
    
    def buscar_por_codigo(self, codigo: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM medicamentos WHERE codigo = %s",
            (codigo,),
            fetch_one=True
        )
    
    def criar(self, dados: Dict[str, Any]) -> int:
        resultado = self.db.execute(
            "INSERT INTO medicamentos (codigo, nome) VALUES (%s, %s) RETURNING id",
            (dados['codigo'], dados['nome']),
            fetch_one=True
        )
        return resultado['id'] if resultado else None
    
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        return self.db.execute(
            "UPDATE medicamentos SET nome = %s WHERE id = %s",
            (dados['nome'], id)
        ) > 0
    
    def deletar(self, id: int) -> bool:
        return self.db.execute(
            "DELETE FROM medicamentos WHERE id = %s",
            (id,)
        ) > 0


class RepositorioLote(RepositorioBase):
    """Repositório de lotes"""
    
    def __init__(self, db):
        self.db = db
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM lotes ORDER BY data_validade ASC",
            fetch_all=True
        )
    
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM lotes WHERE id_lote = %s",
            (id,),
            fetch_one=True
        )
    
    def listar_por_medicamento(self, codigo_medicamento: int) -> List[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM lotes 
               WHERE codigo_medicamento = %s 
               ORDER BY data_validade ASC""",
            (codigo_medicamento,),
            fetch_all=True
        )
    
    def buscar_disponivel(self, codigo_medicamento: int, quantidade: int) -> Optional[Dict[str, Any]]:
        """Busca lote disponível seguindo FEFO (First Expiry First Out)"""
        return self.db.execute(
            """SELECT * FROM lotes 
               WHERE codigo_medicamento = %s 
                 AND quantidade_atual >= %s 
                 AND data_validade >= CURRENT_DATE 
               ORDER BY data_validade ASC 
               LIMIT 1""",
            (codigo_medicamento, quantidade),
            fetch_one=True
        )
    
    def buscar_por_numero(self, codigo_medicamento: int, numero_lote: str) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM lotes 
               WHERE codigo_medicamento = %s 
                 AND numero_lote = %s""",
            (codigo_medicamento, numero_lote),
            fetch_one=True
        )
    
    def criar(self, dados: Dict[str, Any]) -> int:
        resultado = self.db.execute(
            """INSERT INTO lotes 
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
            "UPDATE lotes SET quantidade_atual = %s WHERE id_lote = %s",
            (dados['quantidade_atual'], id)
        ) > 0
    
    def deletar(self, id: int) -> bool:
        return self.db.execute(
            "DELETE FROM lotes WHERE id_lote = %s",
            (id,)
        ) > 0


class RepositorioReserva(RepositorioBase):
    """Repositório de reservas"""
    
    def __init__(self, db):
        self.db = db
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM reservas_ativas ORDER BY data_criacao DESC",
            fetch_all=True
        )
    
    def buscar_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.db.execute(
            "SELECT * FROM reservas_ativas WHERE id_reserva = %s",
            (id,),
            fetch_one=True
        )
    
    def listar_ativas(self) -> List[Dict[str, Any]]:
        return self.db.execute(
            """SELECT * FROM reservas_ativas 
               WHERE status = 'ativa' 
               ORDER BY data_criacao DESC""",
            fetch_all=True
        )
    
    def criar(self, dados: Dict[str, Any]) -> int:
        resultado = self.db.execute(
            """INSERT INTO reservas_ativas 
               (codigo_medicamento, quantidade, numero_lote, cpf_paciente, status) 
               VALUES (%s, %s, %s, %s, %s) 
               RETURNING id_reserva""",
            (dados['codigo_medicamento'], dados['quantidade'],
             dados['numero_lote'], dados['cpf_paciente'], 'ativa'),
            fetch_one=True
        )
        return resultado['id_reserva'] if resultado else None
    
    def atualizar(self, id: int, dados: Dict[str, Any]) -> bool:
        return self.db.execute(
            "UPDATE reservas_ativas SET status = %s WHERE id_reserva = %s",
            (dados['status'], id)
        ) > 0
    
    def deletar(self, id: int) -> bool:
        return self.db.execute(
            "DELETE FROM reservas_ativas WHERE id_reserva = %s",
            (id,)
        ) > 0
