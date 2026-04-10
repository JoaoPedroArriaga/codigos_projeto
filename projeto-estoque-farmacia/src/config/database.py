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
            print(f"✅ Conectado ao PostgreSQL (schema: {self.schema})")
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            raise
    
    def execute(self, query, params=None, fetch_one=False, fetch_all=False):
        if not self.conn:
            self.connect()
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            
            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            
            self.conn.commit()
            return cur.rowcount
    
    def begin(self):
        """Inicia uma transação (já está em modo não-autocommit)"""
        # No psycopg2 com autocommit=False, já estamos em uma transação
        # Não precisa fazer nada
        pass
    
    def commit(self):
        """Confirma a transação"""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """Desfaz a transação"""
        if self.conn:
            self.conn.rollback()
    
    def close(self):
        if self.conn:
            self.conn.close()
            print("🔒 Conexão fechada")

db = Database()