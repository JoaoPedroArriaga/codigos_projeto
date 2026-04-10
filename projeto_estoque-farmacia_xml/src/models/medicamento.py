from src.config.database import db

class Medicamento:
    @staticmethod
    def listar_todos():
        return db.execute(
            "SELECT * FROM medicamentos ORDER BY nome",
            fetch_all=True
        )
    
    @staticmethod
    def buscar_por_codigo(codigo):
        return db.execute(
            "SELECT * FROM medicamentos WHERE codigo = %s",
            (codigo,),
            fetch_one=True
        )
    
    @staticmethod
    def criar(codigo, nome):
        return db.execute(
            "INSERT INTO medicamentos (codigo, nome) VALUES (%s, %s)",
            (codigo, nome)
        )