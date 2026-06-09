"""
ServiceMedicamentos - Operações de gerenciamento de medicamentos
3 operações: listarMedicamentos, obterMedicamento, sincronizarMedicamentos
"""
from typing import List, Optional
from lxml import etree

from src.soap.types import MedicamentoType, ResultadoType
from src.repositorios import RepositorioMedicamento
from src.config.database import db


class ServiceMedicamentos:
    """Serviço de medicamentos (SOAP)"""
    
    def __init__(self):
        self.repositorio = RepositorioMedicamento(db)
    
    # ===== OPERAÇÃO 1: listarMedicamentos =====
    def listar_medicamentos(self) -> List[MedicamentoType]:
        """
        Lista todos os medicamentos cadastrados
        
        Returns:
            Lista de MedicamentoType
            
        Raises:
            SOAPFault se erro de BD
        """
        try:
            medicamentos_dict = self.repositorio.listar_todos()
            
            return [
                MedicamentoType(
                    codigo=med['codigo'],
                    nome=med['nome'],
                    id=med.get('id')
                )
                for med in medicamentos_dict
            ]
        except Exception as e:
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 2: obterMedicamento =====
    def obter_medicamento(self, codigo: int) -> MedicamentoType:
        """
        Busca um medicamento específico por código
        
        Args:
            codigo: Código do medicamento
            
        Returns:
            MedicamentoType com dados completos
            
        Raises:
            Exception: Se medicamento não encontrado ou erro BD
        """
        try:
            medicamento_dict = self.repositorio.buscar_por_codigo(codigo)
            
            if not medicamento_dict:
                raise Exception(f"MEDICAMENTO_NAO_ENCONTRADO: Código {codigo} não existe")
            
            return MedicamentoType(
                codigo=medicamento_dict['codigo'],
                nome=medicamento_dict['nome'],
                id=medicamento_dict.get('id')
            )
        except Exception as e:
            if "MEDICAMENTO_NAO_ENCONTRADO" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
    
    # ===== OPERAÇÃO 3: sincronizarMedicamentos =====
    def sincronizar_medicamentos(self, arquivo_xml: str, grupo_origem: str) -> ResultadoType:
        """
        Sincroniza medicamentos a partir de um arquivo XML (recebido do Grupo 1)
        
        Formato esperado:
        ```xml
        <medicamentos>
          <medicamento>
            <codigo>123</codigo>
            <nome>Paracetamol 500mg</nome>
          </medicamento>
        </medicamentos>
        ```
        
        Args:
            arquivo_xml: String XML com medicamentos
            grupo_origem: Identificador do grupo (ex: GRUPO_1, GRUPO_2)
            
        Returns:
            ResultadoType com sucesso/falha
            
        Raises:
            Exception: Se XML inválido, XSD invalida, ou erro de processamento
        """
        try:
            # Parsear XML
            root = etree.fromstring(arquivo_xml.encode('utf-8'))
            medicamentos_list = root.findall('medicamento')
            
            if not medicamentos_list:
                raise Exception("XML_INVALIDO: Nenhum medicamento encontrado")
            
            # Sincronizar cada medicamento
            total_sincronizados = 0
            db.begin()
            
            try:
                for med_elem in medicamentos_list:
                    codigo_elem = med_elem.find('codigo')
                    nome_elem = med_elem.find('nome')
                    
                    if codigo_elem is None or nome_elem is None:
                        raise Exception("XML_INVALIDO: Faltam campos codigo ou nome")
                    
                    codigo = int(codigo_elem.text)
                    nome = nome_elem.text
                    
                    # Verificar se medicamento já existe
                    existente = self.repositorio.buscar_por_codigo(codigo)
                    
                    if existente:
                        # Atualizar
                        self.repositorio.atualizar(existente['id'], {'codigo': codigo, 'nome': nome})
                    else:
                        # Criar novo
                        self.repositorio.criar({'codigo': codigo, 'nome': nome})
                    
                    total_sincronizados += 1
                
                db.commit()
                
                from datetime import datetime
                return ResultadoType(
                    success=True,
                    timestamp=datetime.now(),
                    mensagem=f"Sincronizados {total_sincronizados} medicamentos de {grupo_origem}"
                )
            
            except Exception as e:
                db.rollback()
                raise Exception(f"ERRO_PROCESSAMENTO: {str(e)}")
        
        except etree.XMLSyntaxError as e:
            raise Exception(f"XML_INVALIDO: {str(e)}")
        except ValueError as e:
            raise Exception(f"XML_INVALIDO: Campo 'codigo' não é número - {str(e)}")
        except Exception as e:
            if "XML_INVALIDO" in str(e) or "ERRO_PROCESSAMENTO" in str(e):
                raise
            raise Exception(f"ERRO_BANCO_DADOS: {str(e)}")
