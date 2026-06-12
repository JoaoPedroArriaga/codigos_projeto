"""
Utilitário para cálculo e validação de HMAC-SHA256
CORRIGIDO para seguir XSDs
"""
import hashlib
import hmac
from datetime import datetime
from lxml import etree

CHAVE_SECRETA = b"chave_secreta_compartilhada_entre_grupos_2026"


def calcular_hmac(conteudo: str) -> str:
    """Calcula HMAC-SHA256 do conteúdo"""
    return hmac.new(
        CHAVE_SECRETA,
        conteudo.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def calcular_hmac_body_soap(body_element: etree.Element) -> str:
    """Calcula HMAC-SHA256 do elemento de operação no SOAP Body"""
    return calcular_hmac(serializar_xml(body_element))


def calcular_hmac_envelope_xml(envelope_xml: str) -> str:
    """
    Calcula HMAC do body a partir do XML serializado do envelope.
    Garante que cliente e servidor usem a mesma canonicalização (parse → body[0] → hash).
    """
    from src.soap.handlers.envelope import SOAPEnvelope

    root = etree.fromstring(envelope_xml.encode('utf-8'))
    body = root.find(f"{{{SOAPEnvelope.NS_SOAP}}}Body")
    if body is None or len(body) == 0:
        raise ValueError("Envelope SOAP sem operação no Body")
    return calcular_hmac_body_soap(body[0])


def assinar_envelope_requisicao(envelope: etree.Element) -> None:
    """Calcula e injeta o hash HMAC no header de um envelope de requisição"""
    from src.soap.handlers.envelope import SOAPEnvelope

    xml_temp = SOAPEnvelope.serializar_xml(envelope, pretty=False)
    hash_valor = calcular_hmac_envelope_xml(xml_temp)

    header = envelope.find(f"{{{SOAPEnvelope.NS_SOAP}}}Header")
    autenticacao = header.find(f"{{{SOAPEnvelope.NS_TNS}}}autenticacao")
    hash_elem = autenticacao.find(f"{{{SOAPEnvelope.NS_TNS}}}hash")
    hash_elem.text = hash_valor


def serializar_xml(root: etree.Element) -> str:
    """Serializa XML de forma consistente (sem espaços extras)"""
    return etree.tostring(
        root, 
        encoding='unicode', 
        method='xml',
        pretty_print=False
    ).strip()


def adicionar_assinatura(root: etree.Element, grupo_origem: str) -> None:
    """
    Adiciona tag de assinatura ao elemento raiz
    A assinatura deve ser adicionada APÓS os elementos de dados
    """
    # Remove assinatura anterior se existir
    for elem in root.findall('assinatura'):
        root.remove(elem)
    
    # Serializa o XML sem assinatura para cálculo
    xml_sem_assinatura = serializar_xml(root)
    hash_valor = calcular_hmac(xml_sem_assinatura)
    
    # Adiciona assinatura como último elemento
    assinatura = etree.SubElement(root, 'assinatura')
    etree.SubElement(assinatura, 'hash').text = hash_valor
    etree.SubElement(assinatura, 'timestamp').text = datetime.now().isoformat()
    etree.SubElement(assinatura, 'grupo_origem').text = grupo_origem
    etree.SubElement(assinatura, 'algoritmo').text = 'HMAC-SHA256'


def validar_assinatura(xml_path: str) -> tuple:
    """Valida a assinatura de um arquivo XML"""
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        # Busca tag de assinatura
        assinatura = root.find('assinatura')
        if assinatura is None:
            return False, "Arquivo nao assinado", None
        
        hash_recebido = assinatura.find('hash').text
        timestamp = assinatura.find('timestamp')
        grupo_origem = assinatura.find('grupo_origem')
        algoritmo = assinatura.find('algoritmo')
        
        if not hash_recebido:
            return False, "Hash não encontrado na assinatura", None
        
        # Remove assinatura temporariamente
        root.remove(assinatura)
        
        # Serializa sem assinatura
        xml_sem_assinatura = serializar_xml(root)
        hash_calculado = calcular_hmac(xml_sem_assinatura)
        
        # Recoloca assinatura
        root.append(assinatura)
        
        if hash_calculado == hash_recebido:
            dados = {
                'hash': hash_recebido,
                'timestamp': timestamp.text if timestamp is not None else None,
                'grupo_origem': grupo_origem.text if grupo_origem is not None else None,
                'algoritmo': algoritmo.text if algoritmo is not None else None
            }
            return True, "Assinatura valida", dados
        else:
            return False, f"Assinatura invalida - hash nao confere", None
            
    except Exception as e:
        return False, f"Erro ao validar: {e}", None