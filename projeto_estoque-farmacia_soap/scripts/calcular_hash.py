#!/usr/bin/env python
"""
Script para calcular HMAC-SHA256 de arquivos XML
e adicionar a tag de assinatura
"""
import hashlib
import hmac
import os
import xml.etree.ElementTree as ET
from datetime import datetime

# Chave secreta (deve ser compartilhida entre os grupos)
CHAVE_SECRETA = b"chave_secreta_compartilhada_entre_grupos_2026"

def calcular_hmac(conteudo):
    """Calcula HMAC-SHA256 do conteúdo"""
    return hmac.new(
        CHAVE_SECRETA,
        conteudo.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def adicionar_assinatura(xml_path, grupo_origem):
    """Adiciona tag de assinatura ao XML"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Remover assinatura anterior se existir
    for elem in root.findall('assinatura'):
        root.remove(elem)
    
    # Serializar XML sem assinatura para calcular hash
    xml_sem_assinatura = ET.tostring(root, encoding='unicode')
    hash_valor = calcular_hmac(xml_sem_assinatura)
    
    # Criar tag de assinatura
    assinatura = ET.Element('assinatura')
    ET.SubElement(assinatura, 'hash').text = hash_valor
    ET.SubElement(assinatura, 'timestamp').text = datetime.now().isoformat()
    ET.SubElement(assinatura, 'grupo_origem').text = grupo_origem
    ET.SubElement(assinatura, 'algoritmo').text = 'HMAC-SHA256'
    
    root.append(assinatura)
    
    # Escrever XML com formatação bonita
    ET.indent(tree, space='    ')
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ Assinatura adicionada a {xml_path}")
    print(f"   Hash: {hash_valor[:32]}...")
    print(f"   Grupo: {grupo_origem}")
    return hash_valor

def verificar_assinatura(xml_path):
    """Verifica se a assinatura do XML é válida"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Encontrar tag de assinatura
    assinatura = root.find('assinatura')
    if assinatura is None:
        return False, "Arquivo não assinado"
    
    hash_recebido = assinatura.find('hash').text
    
    # Remover assinatura temporariamente para calcular hash
    root.remove(assinatura)
    xml_sem_assinatura = ET.tostring(root, encoding='unicode')
    hash_calculado = calcular_hmac(xml_sem_assinatura)
    
    # Recolocar assinatura (sem alterar o arquivo)
    root.append(assinatura)
    
    if hash_calculado == hash_recebido:
        return True, "Assinatura válida"
    else:
        return False, "Assinatura inválida"

def main():
    # Pasta onde estão os XMLs
    PASTA_XML = 'xmls'
    
    # Lista de arquivos para assinar (com caminho relativo)
    arquivos = [
        ('consulta.xml', 'GRUPO_2'),
        ('resposta.xml', 'GRUPO_3'),
        ('reserva.xml', 'GRUPO_2'),
        ('baixa.xml', 'GRUPO_2'),
        ('consumo.xml', 'GRUPO_3'),
    ]
    
    print("=" * 60)
    print("🔐 ADICIONANDO ASSINATURA HMAC AOS XMLs")
    print("=" * 60)
    print(f"📁 Pasta dos XMLs: {PASTA_XML}\n")
    
    for xml_file, grupo in arquivos:
        caminho_completo = os.path.join(PASTA_XML, xml_file)
        if os.path.exists(caminho_completo):
            print(f"📄 Processando {caminho_completo}...")
            adicionar_assinatura(caminho_completo, grupo)
        else:
            print(f"⚠️ Arquivo não encontrado: {caminho_completo}")
    
    print("\n" + "=" * 60)
    print("🔍 VERIFICANDO ASSINATURAS")
    print("=" * 60)
    
    for xml_file, _ in arquivos:
        caminho_completo = os.path.join(PASTA_XML, xml_file)
        if os.path.exists(caminho_completo):
            valido, msg = verificar_assinatura(caminho_completo)
            if valido:
                print(f"✅ {xml_file}: {msg}")
            else:
                print(f"❌ {xml_file}: {msg}")

if __name__ == "__main__":
    main()