import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = None
            cls._instance.schema = os.getenv('DB_SCHEMA', 'projeto')
            cls._instance.in_transaction = False
        return cls._instance
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'estoque_farmacia'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres')
            )
            # Desabilitar autocommit para controle manual de transações
            self.conn.autocommit = False
            with self.conn.cursor() as cur:
                cur.execute(f"SET search_path TO {self.schema}")
            print(f"Conectado ao PostgreSQL (schema: {self.schema})")
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            raise
    
    def execute(self, query, params=None, fetch_one=False, fetch_all=False):
        if not self.conn:
            self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Garantir que search_path seja definido para cada cursor
                cur.execute(f"SET search_path TO {self.schema}")
                cur.execute(query, params or ())
                
                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
                
                # Só fazer commit se não estamos em uma transação explícita
                if not self.in_transaction:
                    self.conn.commit()
                
                return cur.rowcount
        except psycopg2.DatabaseError as e:
            # Se houver erro, fazer rollback se estamos em transação explícita
            if self.in_transaction:
                try:
                    self.conn.rollback()
                except:
                    pass
            raise
    
    def begin(self):
        """Inicia uma transação explícita"""
        if not self.conn:
            self.connect()
        self.in_transaction = True
        # No psycopg2 com autocommit=False, já estamos em uma transação
        # Marcar flag para controle adequado de commit/rollback
    
    def commit(self):
        """Confirma a transação"""
        if self.conn and self.in_transaction:
            try:
                self.conn.commit()
            finally:
                self.in_transaction = False
    
    def rollback(self):
        """Desfaz a transação"""
        if self.conn and self.in_transaction:
            try:
                self.conn.rollback()
            finally:
                self.in_transaction = False
    
    def close(self):
        if self.conn:
            if self.in_transaction:
                try:
                    self.conn.rollback()
                except:
                    pass
            self.conn.close()
            self.in_transaction = False
            print("Conexão fechada")

db = Database()