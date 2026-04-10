import os
from ftplib import FTP, error_perm
from dotenv import load_dotenv

load_dotenv()

class FTPClient:
    def __init__(self):
        self.host = os.getenv('FTP_HOST')
        self.port = int(os.getenv('FTP_PORT', 21))
        self.user = os.getenv('FTP_USER')
        self.password = os.getenv('FTP_PASSWORD')
        self.root = os.getenv('FTP_ROOT', '/')
        self.ftp = None
    
    def connect(self):
        try:
            self.ftp = FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.user, self.password)
            try:
                self.ftp.cwd(self.root)
            except:
                pass
            print(f"✅ Conectado ao FTP: {self.host}")
            return True
        except Exception as e:
            print(f"❌ Erro FTP: {e}")
            return False
    
    def disconnect(self):
        if self.ftp:
            self.ftp.quit()
    
    def list_files(self, pasta):
        try:
            self.ftp.cwd(pasta)
            files = self.ftp.nlst()
            self.ftp.cwd('..')
            return files
        except error_perm:
            return []
    
    def download_file(self, pasta, nome_arquivo, destino):
        try:
            self.ftp.cwd(pasta)
            with open(destino, 'wb') as f:
                self.ftp.retrbinary(f'RETR {nome_arquivo}', f.write)
            self.ftp.cwd('..')
            return True
        except Exception as e:
            print(f"Erro ao baixar {nome_arquivo}: {e}")
            return False
    
    def upload_file(self, pasta, caminho_local, nome_arquivo):
        try:
            try:
                self.ftp.cwd(pasta)
            except error_perm:
                self.ftp.mkd(pasta)
                self.ftp.cwd(pasta)
            
            with open(caminho_local, 'rb') as f:
                self.ftp.storbinary(f'STOR {nome_arquivo}', f)
            self.ftp.cwd('..')
            return True
        except Exception as e:
            print(f"Erro ao enviar {nome_arquivo}: {e}")
            return False
    
    def move_file(self, pasta_origem, pasta_destino, nome_arquivo):
        try:
            self.ftp.cwd(pasta_origem)
            self.ftp.rename(nome_arquivo, f'../{pasta_destino}/{nome_arquivo}')
            self.ftp.cwd('..')
            return True
        except Exception as e:
            print(f"Erro ao mover {nome_arquivo}: {e}")
            return False

ftp_client = FTPClient()