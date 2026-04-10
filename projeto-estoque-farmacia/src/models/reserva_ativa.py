from src.config.database import db

class ReservaAtiva:
    @staticmethod
    def criar(id_prescricao, cpf_paciente, codigo_medicamento, 
              quantidade, lote, id_lote):
        """Cria uma nova reserva ativa"""
        return db.execute(
            """INSERT INTO reservas_ativas 
               (id_prescricao, cpf_paciente, codigo_medicamento,
                quantidade, lote, id_lote, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'RESERVADO')""",
            (id_prescricao, cpf_paciente, codigo_medicamento,
             quantidade, lote, id_lote)
        )
    
    @staticmethod
    def marcar_utilizado(id_prescricao, lote):
        """Marca uma reserva como utilizada (após baixa)"""
        return db.execute(
            """UPDATE reservas_ativas 
               SET status = 'UTILIZADO', data_utilizacao = CURRENT_TIMESTAMP
               WHERE id_prescricao = %s AND lote = %s AND status = 'RESERVADO'""",
            (id_prescricao, lote)
        )
    
    @staticmethod
    def marcar_cancelado(id_prescricao, lote):
        """Marca uma reserva como cancelada"""
        return db.execute(
            """UPDATE reservas_ativas 
               SET status = 'CANCELADO', data_cancelamento = CURRENT_TIMESTAMP
               WHERE id_prescricao = %s AND lote = %s AND status = 'RESERVADO'""",
            (id_prescricao, lote)
        )
    
    @staticmethod
    def buscar_reserva_ativa(id_prescricao, lote):
        """Busca uma reserva ativa"""
        return db.execute(
            """SELECT * FROM reservas_ativas 
               WHERE id_prescricao = %s AND lote = %s AND status = 'RESERVADO'""",
            (id_prescricao, lote),
            fetch_one=True
        )
    
    @staticmethod
    def listar_reservas_ativas():
        """Lista todas as reservas ativas"""
        return db.execute(
            """SELECT r.*, m.nome as medicamento_nome, m.unidade
               FROM reservas_ativas r
               JOIN medicamentos m ON m.codigo = r.codigo_medicamento
               WHERE r.status = 'RESERVADO'
               ORDER BY r.data_reserva""",
            fetch_all=True
        )