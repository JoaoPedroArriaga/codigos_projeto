"""
Envelope SOAP - Geração e parsing de envelopes SOAP
Estrutura: Header (autenticação, assinatura) + Body (operação)
"""
from datetime import datetime
from lxml import etree
from typing import Dict, Any, Optional, Tuple


class SOAPEnvelope:
    """Builder para envelopes SOAP"""
    
    # Namespaces
    NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
    NS_TIPOS = "http://estoque-farmacia.projeto.interop/v1/tipos"
    NS_TNS = "http://estoque-farmacia.projeto.interop/v1"
    
    NSMAP = {
        'soap': NS_SOAP,
        'tipos': NS_TIPOS,
        'tns': NS_TNS,
    }
    
    @staticmethod
    def criar_envelope(
        operacao: str,
        parametros: Dict[str, Any],
        hash_assinatura: str,
        timestamp: str,
        grupo_origem: str = "GRUPO_3"
    ) -> etree.Element:
        """
        Cria um envelope SOAP completo com header de autenticação/assinatura
        
        Args:
            operacao: Nome da operação (ex: listarMedicamentos)
            parametros: Dicionário de parâmetros para a operação
            hash_assinatura: HMAC-SHA256 calculado
            timestamp: ISO datetime da requisição
            grupo_origem: Identificador do grupo que originou a requisição
            
        Returns:
            Elemento XML do envelope SOAP pronto para envio
        """
        # Criar elemento raiz SOAP
        envelope = etree.Element(f"{{{SOAPEnvelope.NS_SOAP}}}Envelope", nsmap=SOAPEnvelope.NSMAP)
        
        # ===== SOAP HEADER =====
        header = etree.SubElement(envelope, f"{{{SOAPEnvelope.NS_SOAP}}}Header")
        
        # Assinatura HMAC no header
        autenticacao = etree.SubElement(header, f"{{{SOAPEnvelope.NS_TNS}}}autenticacao")
        
        etree.SubElement(autenticacao, f"{{{SOAPEnvelope.NS_TNS}}}hash").text = hash_assinatura
        etree.SubElement(autenticacao, f"{{{SOAPEnvelope.NS_TNS}}}timestamp").text = timestamp
        etree.SubElement(autenticacao, f"{{{SOAPEnvelope.NS_TNS}}}grupo_origem").text = grupo_origem
        etree.SubElement(autenticacao, f"{{{SOAPEnvelope.NS_TNS}}}algoritmo").text = "HMAC-SHA256"
        
        # ===== SOAP BODY =====
        body = etree.SubElement(envelope, f"{{{SOAPEnvelope.NS_SOAP}}}Body")
        
        # Elemento da operação
        operacao_elem = etree.SubElement(body, f"{{{SOAPEnvelope.NS_TNS}}}{operacao}")
        
        # Adicionar parâmetros
        for chave, valor in parametros.items():
            param_elem = etree.SubElement(operacao_elem, f"{{{SOAPEnvelope.NS_TNS}}}{chave}")
            param_elem.text = str(valor) if valor is not None else ""
        
        return envelope
    
    @staticmethod
    def montar_body_requisicao(operacao: str, parametros: Dict[str, Any]) -> etree.Element:
        """Monta o elemento de operação no SOAP Body (sem envelope)"""
        operacao_elem = etree.Element(f"{{{SOAPEnvelope.NS_TNS}}}{operacao}")
        for chave, valor in parametros.items():
            param_elem = etree.SubElement(operacao_elem, f"{{{SOAPEnvelope.NS_TNS}}}{chave}")
            param_elem.text = str(valor) if valor is not None else ""
        return operacao_elem

    @staticmethod
    def montar_body_resposta(operacao: str, resultado: Dict[str, Any]) -> etree.Element:
        """Monta o elemento de resposta no SOAP Body (sem envelope)"""
        response_elem = etree.Element(f"{{{SOAPEnvelope.NS_TNS}}}{operacao}Response")
        for chave, valor in resultado.items():
            SOAPEnvelope._adicionar_valor(response_elem, chave, valor)
        return response_elem

    @staticmethod
    def criar_resposta(
        operacao: str,
        resultado: Dict[str, Any],
        hash_assinatura: str,
        timestamp: str,
        grupo_origem: str = "GRUPO_3"
    ) -> etree.Element:
        """
        Cria envelope SOAP de resposta
        
        Args:
            operacao: Nome da operação (ex: listarMedicamentos)
            resultado: Dados de resultado (tipados)
            hash_assinatura: HMAC-SHA256 da resposta
            timestamp: ISO datetime da resposta
            grupo_origem: Identificador do grupo respondente
            
        Returns:
            Elemento XML do envelope SOAP de resposta
        """
        envelope = etree.Element(f"{{{SOAPEnvelope.NS_SOAP}}}Envelope", nsmap=SOAPEnvelope.NSMAP)
        
        # SOAP Header
        header = etree.SubElement(envelope, f"{{{SOAPEnvelope.NS_SOAP}}}Header")
        assinatura = etree.SubElement(header, f"{{{SOAPEnvelope.NS_TNS}}}assinatura")
        
        etree.SubElement(assinatura, f"{{{SOAPEnvelope.NS_TNS}}}hash").text = hash_assinatura
        etree.SubElement(assinatura, f"{{{SOAPEnvelope.NS_TNS}}}timestamp").text = timestamp
        etree.SubElement(assinatura, f"{{{SOAPEnvelope.NS_TNS}}}grupo_origem").text = grupo_origem
        etree.SubElement(assinatura, f"{{{SOAPEnvelope.NS_TNS}}}algoritmo").text = "HMAC-SHA256"
        
        # SOAP Body
        body = etree.SubElement(envelope, f"{{{SOAPEnvelope.NS_SOAP}}}Body")
        
        # Elemento response
        response_elem = etree.SubElement(body, f"{{{SOAPEnvelope.NS_TNS}}}{operacao}Response")
        
        # Serializar resultado (mantém estrutura de tipos complexos)
        for chave, valor in resultado.items():
            SOAPEnvelope._adicionar_valor(response_elem, chave, valor)
        
        return envelope
    
    @staticmethod
    def criar_fault(
        codigo_erro: str,
        mensagem_erro: str,
        detalhes: Optional[str] = None
    ) -> etree.Element:
        """
        Cria envelope SOAP com Fault (erro)
        
        Args:
            codigo_erro: Código único do erro
            mensagem_erro: Mensagem descritiva
            detalhes: Detalhes adicionais (stack trace, etc)
            
        Returns:
            Elemento XML do Fault SOAP
        """
        envelope = etree.Element(f"{{{SOAPEnvelope.NS_SOAP}}}Envelope", nsmap=SOAPEnvelope.NSMAP)
        
        body = etree.SubElement(envelope, f"{{{SOAPEnvelope.NS_SOAP}}}Body")
        fault = etree.SubElement(body, f"{{{SOAPEnvelope.NS_SOAP}}}Fault")
        
        # Estrutura de Fault SOAP 1.1
        etree.SubElement(fault, "faultcode").text = codigo_erro
        etree.SubElement(fault, "faultstring").text = mensagem_erro
        
        if detalhes:
            detail = etree.SubElement(fault, "detail")
            etree.SubElement(detail, "erro").text = detalhes
        
        return envelope
    
    @staticmethod
    def _adicionar_valor(parent: etree.Element, chave: str, valor: Any) -> None:
        """Helper para adicionar valores (primitivos ou complexos) ao XML"""
        if isinstance(valor, dict):
            # Tipo complexo
            elem = etree.SubElement(parent, f"{{{SOAPEnvelope.NS_TNS}}}{chave}")
            for k, v in valor.items():
                SOAPEnvelope._adicionar_valor(elem, k, v)
        elif isinstance(valor, list):
            # Array/lista
            for item in valor:
                if isinstance(item, dict):
                    SOAPEnvelope._adicionar_valor(parent, chave[:-1], item)  # Singular
                else:
                    elem = etree.SubElement(parent, f"{{{SOAPEnvelope.NS_TNS}}}{chave}")
                    elem.text = str(item)
        else:
            # Primitivo
            elem = etree.SubElement(parent, f"{{{SOAPEnvelope.NS_TNS}}}{chave}")
            elem.text = str(valor) if valor is not None else ""
    
    @staticmethod
    def _extrair_header(header_elem: etree.Element) -> Dict[str, str]:
        """Extrai campos do header SOAP (autenticacao ou assinatura aninhados)"""
        header_dict = {}
        for elem in header_elem:
            tag = elem.tag.split('}')[-1]
            if len(elem) > 0:
                for child in elem:
                    child_tag = child.tag.split('}')[-1]
                    header_dict[child_tag] = child.text
            else:
                header_dict[tag] = elem.text
        return header_dict

    @staticmethod
    def extrair_body_element(envelope_xml: str) -> Optional[etree.Element]:
        """Retorna o elemento da operação dentro do SOAP Body"""
        try:
            root = etree.fromstring(envelope_xml.encode('utf-8'))
            body = root.find(f"{{{SOAPEnvelope.NS_SOAP}}}Body")
            if body is None or len(body) == 0:
                return None
            return body[0]
        except Exception:
            return None

    @staticmethod
    def parsear_envelope(envelope_xml: str) -> Tuple[Optional[str], Optional[Dict], Optional[Dict], Optional[etree.Element]]:
        """
        Parseia um envelope SOAP recebido
        
        Args:
            envelope_xml: String XML do envelope
            
        Returns:
            Tupla: (nome_operacao, parametros_dict, header_dict, body_element)
                   ou (None, None, None, None) se erro
        """
        try:
            root = etree.fromstring(envelope_xml.encode('utf-8'))
            
            header_dict = {}
            header = root.find(f"{{{SOAPEnvelope.NS_SOAP}}}Header")
            if header is not None:
                header_dict = SOAPEnvelope._extrair_header(header)
            
            body = root.find(f"{{{SOAPEnvelope.NS_SOAP}}}Body")
            if body is None or len(body) == 0:
                return None, None, None, None
            
            operacao_elem = body[0]
            operacao_nome = operacao_elem.tag.split('}')[-1]
            
            parametros = {}
            for param in operacao_elem:
                param_nome = param.tag.split('}')[-1]
                parametros[param_nome] = param.text
            
            return operacao_nome, parametros, header_dict, operacao_elem
            
        except Exception as e:
            print(f"Erro ao parsear envelope SOAP: {e}")
            return None, None, None, None
    
    @staticmethod
    def serializar_xml(elemento: etree.Element, pretty: bool = False) -> str:
        """Serializa elemento XML para string"""
        return etree.tostring(
            elemento,
            encoding='utf-8',
            method='xml',
            pretty_print=pretty,
            xml_declaration=True
        ).decode('utf-8')
