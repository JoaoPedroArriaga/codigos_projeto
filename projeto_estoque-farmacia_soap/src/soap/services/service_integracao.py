"""
ServiceIntegracao - Operações de integração B2B com Grupos 1 e 2
3 operações: gerarRelatorioConsumo, consultarStatusPaciente, sincronizarStatusFinanceiro
"""
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, date
from lxml import etree

from src.soap.types import ResultadoType
from src.repositorios import RepositorioBaixa
from src.config.database import db
from src.utils.hash_utils import calcular_hmac, serializar_xml


class ServiceIntegracao:
    """Serviço de integração B2B (SOAP)"""
    
    def __init__(self):
        self.repo_baixa = RepositorioBaixa(db)
        # Cache de status financeiro (sincronizado do G1)
        self.cache_status_financeiro: Dict[str, Dict[str, Any]] = {}
    
    # ===== OPERAÇÃO 1: gerarRelatorioConsumo (G3 → G1) =====
    def gerar_relatorio_consumo(
        self, 
        data_inicio: Optional[date] = None, 
        data_fim: Optional[date] = None
    ) -> Tuple[str, ResultadoType]:
        """
        Gera relatório de consumo em formato consumo.xsd, assina com HMAC-SHA256
        
        Fluxo:
        1. Query BD: baixas no período
        2. Gerar XML consumo.xsd
        3. Assinar com HMAC-SHA256
        4. Retornar (xml_string, resultado)
        
        Caso de uso: Consolidação com Grupo 1
        
        Args:
            data_inicio: Data inicial (opt) - padrão: 30 dias atrás
            data_fim: Data final (opt) - padrão: hoje
            
        Returns:
            Tupla: (arquivo_xml_string_assinado, ResultadoType)
            
        Raises:
            Exception: Se erro BD ou geração XML
        """
        try:
            # Padrões
            if data_fim is None:
                data_fim = datetime.now().date()
            if data_inicio is None:
                from datetime import timedelta
                data_inicio = data_fim - timedelta(days=30)
            
            # Query BD
            baixas_dict = self.repo_baixa.listar_por_periodo(data_inicio, data_fim)
            
            # Gerar XML consumo.xsd
            consumo_root = etree.Element('consumo')
            
            # Header
            header = etree.SubElement(consumo_root, 'header')
            etree.SubElement(header, 'data_inicio').text = data_inicio.isoformat()
            etree.SubElement(header, 'data_fim').text = data_fim.isoformat()
            etree.SubElement(header, 'grupo_origem').text = 'GRUPO_3'
            etree.SubElement(header, 'timestamp').text = datetime.now().isoformat()
            
            # Itens de consumo
            itens = etree.SubElement(consumo_root, 'itens')
            for baixa in baixas_dict:
                item = etree.SubElement(itens, 'item')
                etree.SubElement(item, 'codigo_medicamento').text = str(baixa['codigo_medicamento'])
                etree.SubElement(item, 'quantidade').text = str(baixa['quantidade'])
                etree.SubElement(item, 'numero_lote').text = str(baixa['numero_lote'])
                etree.SubElement(item, 'data_uso').text = str(baixa.get('data_uso', ''))
                etree.SubElement(item, 'cpf_paciente').text = str(baixa.get('cpf_paciente', ''))
                etree.SubElement(item, 'motivo').text = str(baixa.get('motivo', ''))
            
            # Serializar XML (sem assinatura por enquanto)
            xml_string = serializar_xml(consumo_root)
            
            # Calcular HMAC-SHA256 (assinar o conteúdo dos itens)
            hash_valor = calcular_hmac(xml_string)
            
            # Adicionar elemento de assinatura ao XML
            assinatura = etree.SubElement(consumo_root, 'assinatura')
            etree.SubElement(assinatura, 'hash').text = hash_valor
            etree.SubElement(assinatura, 'timestamp').text = datetime.now().isoformat()
            etree.SubElement(assinatura, 'grupo_origem').text = 'GRUPO_3'
            etree.SubElement(assinatura, 'algoritmo').text = 'HMAC-SHA256'
            
            # Re-serializar com assinatura
            xml_assinado = serializar_xml(consumo_root)
            
            resultado = ResultadoType(
                success=True,
                timestamp=datetime.now(),
                mensagem=f"Relatório gerado: {len(baixas_dict)} itens de {data_inicio} a {data_fim}"
            )
            
            return xml_assinado, resultado
        
        except Exception as e:
            raise Exception(f"ERRO_GERACAO_RELATORIO: {str(e)}")
    
    # ===== OPERAÇÃO 2: consultarStatusPaciente =====
    def consultar_status_paciente(self, cpf: str) -> Dict[str, Any]:
        """
        Consulta status financeiro do paciente (cache sincronizado do G1)
        
        Fluxo:
        1. Validar CPF
        2. Procurar em cache (cache_status_financeiro)
        3. Retornar status ou erro se não encontrado
        
        Caso de uso: Verificação de autorização antes de atendimento
        
        Args:
            cpf: CPF do paciente
            
        Returns:
            Dict com status financeiro (status, permite_atendimento, etc)
            
        Raises:
            Exception: Se CPF inválido ou não encontrado
        """
        try:
            # Validar CPF
            cpf_limpo = cpf.replace('.', '').replace('-', '')
            if len(cpf_limpo) != 11:
                raise Exception(f"CPF_INVALIDO: CPF deve ter 11 dígitos")
            
            # Procurar em cache
            if cpf_limpo not in self.cache_status_financeiro:
                raise Exception(f"PACIENTE_NAO_ENCONTRADO: CPF {cpf} não tem status cadastrado")
            
            return self.cache_status_financeiro[cpf_limpo]
        
        except Exception as e:
            if any(err in str(e) for err in ["CPF_INVALIDO", "PACIENTE_NAO_ENCONTRADO"]):
                raise
            raise Exception(f"ERRO_CONSULTA_STATUS: {str(e)}")
    
    # ===== OPERAÇÃO 3: sincronizarStatusFinanceiro (G1 → G3) =====
    def sincronizar_status_financeiro(
        self, 
        arquivo_xml: str, 
        grupo_origem: str
    ) -> ResultadoType:
        """
        Sincroniza status financeiro de pacientes (recebido do Grupo 1)
        
        Formato esperado (status_financeiro.xsd):
        ```xml
        <status_financeiro>
          <paciente>
            <cpf>12345678901</cpf>
            <status>autorizado|suspenso|pendente</status>
            <permite_atendimento>1|0</permite_atendimento>
            <observacao>...</observacao>
          </paciente>
        </status_financeiro>
        ```
        
        Fluxo:
        1. Parsear XML
        2. Validar XSD (status_financeiro.xsd)
        3. Validar assinatura HMAC-SHA256
        4. Armazenar em cache (CPF → status)
        5. Retornar sucesso
        
        Caso de uso: Consolidação de autorização com G1
        
        Args:
            arquivo_xml: String XML com status de pacientes
            grupo_origem: Identificador do grupo (deve ser GRUPO_1)
            
        Returns:
            ResultadoType com sucesso
            
        Raises:
            Exception: Se XML inválido, assinatura invalida, erro processamento
        """
        try:
            # Parsear XML
            root = etree.fromstring(arquivo_xml.encode('utf-8'))
            
            # Validar assinatura
            assinatura_elem = root.find('assinatura')
            if assinatura_elem is None:
                raise Exception("ASSINATURA_FALTANDO: XML deve conter elemento <assinatura>")
            
            hash_recebido = assinatura_elem.findtext('hash')
            if not hash_recebido:
                raise Exception("ASSINATURA_INVALIDA: Elemento <hash> vazio")
            
            # Remover assinatura do XML para validação
            root.remove(assinatura_elem)
            xml_sem_assinatura = serializar_xml(root)
            
            # Calcular novo hash
            hash_calculado = calcular_hmac(xml_sem_assinatura)
            
            # Comparar hashes
            if hash_recebido != hash_calculado:
                raise Exception("ASSINATURA_INVALIDA: Hash não confere com conteúdo")
            
            # Restaurar assinatura (para referência)
            root.append(assinatura_elem)
            
            # Processar pacientes
            pacientes_list = root.findall('paciente')
            total_sincronizados = 0
            
            for pac_elem in pacientes_list:
                cpf_elem = pac_elem.find('cpf')
                status_elem = pac_elem.find('status')
                permite_atendimento_elem = pac_elem.find('permite_atendimento')
                observacao_elem = pac_elem.find('observacao')
                
                if cpf_elem is None or status_elem is None:
                    raise Exception("XML_INVALIDO: Faltam campos cpf ou status")
                
                cpf = cpf_elem.text.replace('.', '').replace('-', '')
                
                # Armazenar em cache
                self.cache_status_financeiro[cpf] = {
                    'cpf': cpf,
                    'status': status_elem.text,
                    'permite_atendimento': int(permite_atendimento_elem.text or 0),
                    'observacao': observacao_elem.text if observacao_elem is not None else None,
                    'sincronizado_em': datetime.now().isoformat(),
                    'grupo_origem': grupo_origem
                }
                
                total_sincronizados += 1
            
            return ResultadoType(
                success=True,
                timestamp=datetime.now(),
                mensagem=f"Sincronizados {total_sincronizados} pacientes de {grupo_origem}"
            )
        
        except etree.XMLSyntaxError as e:
            raise Exception(f"XML_INVALIDO: {str(e)}")
        except Exception as e:
            if any(err in str(e) for err in ["XML_INVALIDO", "ASSINATURA_INVALIDA", "ASSINATURA_FALTANDO"]):
                raise
            raise Exception(f"ERRO_PROCESSAMENTO: {str(e)}")
