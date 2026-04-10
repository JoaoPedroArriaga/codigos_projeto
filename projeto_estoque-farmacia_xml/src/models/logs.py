from src.config.database import db

class LogConsulta:
    @staticmethod
    def registrar(arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                  quantidade, disponivel, observacao):
        """Registra log de consulta (versão simplificada)"""
        return db.execute(
            """INSERT INTO logs_consultas 
               (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, disponivel, observacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
             quantidade, disponivel, observacao)
        )

class LogReserva:
    @staticmethod
    def registrar(arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                  quantidade, lote, id_lote, status, observacao):
        return db.execute(
            """INSERT INTO logs_reservas 
               (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote, id_lote, status, observacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id_log""",
            (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
             quantidade, lote, id_lote, status, observacao),
            fetch_one=True
        )

class LogBaixa:
    @staticmethod
    def registrar(arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                  quantidade, lote, data_uso, id_lote, status, observacao):
        return db.execute(
            """INSERT INTO logs_baixas 
               (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote, data_uso, id_lote, status, observacao)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id_log""",
            (arquivo_nome, id_prescricao, cpf_paciente, codigo_medicamento,
             quantidade, lote, data_uso, id_lote, status, observacao),
            fetch_one=True
        )