"""
ServiceIntegracao - Operações de integração B2B com Grupos 1 e 2
3 operações: gerarRelatorioConsumo, consultarStatusPaciente, sincronizarStatusFinanceiro
"""
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, date
from lxml import etree

from src.soap.types import ResultadoType
from src.servicos.relatorio_consumo import RelatorioConsumoService
from src.servicos.status_financeiro import StatusFinanceiroService
from src.utils.hash_utils import calcular_hmac, serializar_xml


class ServiceIntegracao:
    """Serviço de integração B2B (SOAP)"""
    
    def __init__(self):
        self.relatorio_consumo = RelatorioConsumoService()
        self.status_financeiro = StatusFinanceiroService()
    
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
            xml_assinado, total, inicio, fim = self.relatorio_consumo.gerar_xml(data_inicio, data_fim)
            self.relatorio_consumo.marcar_como_enviado(inicio, fim)

            resultado = ResultadoType(
                success=True,
                timestamp=datetime.now(),
                mensagem=f"Relatório gerado: {total} itens de {inicio} a {fim}"
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
            return self.status_financeiro.consultar(cpf)
        
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
            total, mensagem = self.status_financeiro.sincronizar(arquivo_xml, grupo_origem)
            return ResultadoType(
                success=True,
                timestamp=datetime.now(),
                mensagem=mensagem
            )
        except etree.XMLSyntaxError as e:
            raise Exception(f"XML_INVALIDO: {str(e)}")
        except Exception as e:
            if any(err in str(e) for err in ["XML_INVALIDO", "ASSINATURA_INVALIDA", "ASSINATURA_FALTANDO"]):
                raise
            raise Exception(f"ERRO_PROCESSAMENTO: {str(e)}")
