"""
Utilitário para cálculo e validação de HMAC-SHA256
"""
import hashlib
import hmac
from datetime import datetime
from lxml import etree

CHAVE_SECRETA = b"chave_secreta_compartilhada_entre_grupos_2026"

def calcular_hmac(conteudo: str) -> str:
    return hmac.new(
        CHAVE_SECRETA,
        conteudo.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def serializar_xml(root: etree.Element) -> str:
    """Serializa XML de forma consistente (sem espaços extras)"""
    return etree.tostring(
        root, 
        encoding='unicode', 
        method='xml',
        pretty_print=False  # Sem formatação extra
    ).strip()

def adicionar_assinatura(root: etree.Element, grupo_origem: str) -> None:
    """Adiciona tag de assinatura ao elemento raiz"""
    # Remove assinatura anterior se existir
    for elem in root.findall('assinatura'):
        root.remove(elem)
    
    # Serializa o XML sem assinatura (sem pretty_print)
    xml_sem_assinatura = serializar_xml(root)
    hash_valor = calcular_hmac(xml_sem_assinatura)
    
    # Adiciona assinatura
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
        
        # Remove assinatura temporariamente
        root.remove(assinatura)
        
        # Serializa sem assinatura (mesmo método usado na geração)
        xml_sem_assinatura = serializar_xml(root)
        hash_calculado = calcular_hmac(xml_sem_assinatura)
        
        # Recoloca assinatura
        root.append(assinatura)
        
        if hash_calculado == hash_recebido:
            dados = {
                'hash': hash_recebido,
                'timestamp': assinatura.find('timestamp').text if assinatura.find('timestamp') is not None else None,
                'grupo_origem': assinatura.find('grupo_origem').text if assinatura.find('grupo_origem') is not None else None,
                'algoritmo': assinatura.find('algoritmo').text if assinatura.find('algoritmo') is not None else None
            }
            return True, "Assinatura valida", dados
        else:
            return False, f"Assinatura invalida - hash nao confere (calc: {hash_calculado[:16]}..., receb: {hash_recebido[:16]}...)", None
            
    except Exception as e:
        return False, f"Erro ao validar: {e}", None