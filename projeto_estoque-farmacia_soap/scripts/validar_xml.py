#!/usr/bin/env python
"""
Script para validar arquivos XML contra seus respectivos XSDs
"""
import os
from lxml import etree

# Obtém o diretório onde o script está
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def validar_xml(xml_path, xsd_path):
    """Valida um arquivo XML contra um XSD"""
    try:
        # Construir caminhos completos
        xml_full = os.path.join(SCRIPT_DIR, xml_path)
        xsd_full = os.path.join(SCRIPT_DIR, xsd_path)
        
        # Verificar se os arquivos existem
        if not os.path.exists(xml_full):
            print(f"   ❌ Arquivo não encontrado: {xml_path}")
            return False
        
        if not os.path.exists(xsd_full):
            print(f"   ❌ XSD não encontrado: {xsd_path}")
            return False
        
        # Carregar o XSD
        with open(xsd_full, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
        
        # Carregar o XML
        with open(xml_full, 'rb') as f:
            xml_doc = etree.XML(f.read())
        
        # Validar
        schema.assertValid(xml_doc)
        print(f"✅ {os.path.basename(xml_path)} é válido!")
        return True
    except etree.DocumentInvalid as e:
        print(f"❌ {os.path.basename(xml_path)} é INVÁLIDO:")
        print(f"   Erro: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao processar {os.path.basename(xml_path)}: {e}")
        return False

def listar_arquivos():
    """Lista os arquivos XML e XSD encontrados"""
    xml_dir = os.path.join(SCRIPT_DIR, 'xmls')
    xsd_dir = os.path.join(SCRIPT_DIR, 'xsds')
    
    print("=" * 60)
    print("📁 ARQUIVOS ENCONTRADOS")
    print("=" * 60)
    
    if os.path.exists(xml_dir):
        xmls = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
        print(f"\n📄 XMLs ({len(xmls)}):")
        for xml in xmls:
            print(f"   - {xml}")
    else:
        print("❌ Pasta 'xmls' não encontrada!")
        return []
    
    if os.path.exists(xsd_dir):
        xsds = [f for f in os.listdir(xsd_dir) if f.endswith('.xsd')]
        print(f"\n📋 XSDs ({len(xsds)}):")
        for xsd in xsds:
            print(f"   - {xsd}")
    else:
        print("❌ Pasta 'xsds' não encontrada!")
        return []
    
    return xmls, xsds

def main():
    print("=" * 60)
    print("🔍 VALIDADOR DE XML COM XSD")
    print("=" * 60)
    
    # Listar arquivos
    arquivos = listar_arquivos()
    if not arquivos:
        print("\n❌ Nenhum arquivo encontrado. Verifique as pastas 'xmls' e 'xsds'.")
        return
    
    xmls, xsds = arquivos
    
    # Mapeamento dos arquivos XML para seus XSDs
    # Assumindo que os nomes correspondem (consulta.xml -> consulta.xsd)
    mapeamento = []
    for xml in xmls:
        nome_base = os.path.splitext(xml)[0]  # remove .xml
        xsd_correspondente = f"{nome_base}.xsd"
        
        if xsd_correspondente in xsds:
            mapeamento.append((f"xmls/{xml}", f"xsds/{xsd_correspondente}"))
        else:
            print(f"\n⚠️ Aviso: Não encontrado XSD para {xml}")
    
    if not mapeamento:
        print("\n❌ Nenhum par XML/XSD encontrado!")
        return
    
    print("\n" + "=" * 60)
    print("🔍 VALIDANDO XMLs")
    print("=" * 60)
    
    resultados = []
    for xml_file, xsd_file in mapeamento:
        print(f"\n📄 Validando {xml_file}...")
        valido = validar_xml(xml_file, xsd_file)
        resultados.append(valido)
    
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    total = len(resultados)
    sucessos = sum(resultados)
    print(f"   Total de arquivos: {total}")
    print(f"   Válidos: {sucessos}")
    print(f"   Inválidos: {total - sucessos}")
    
    if sucessos == total:
        print("\n✅ TODOS OS XMLs SÃO VÁLIDOS!")
    else:
        print("\n❌ ALGUNS XMLs SÃO INVÁLIDOS. Verifique os erros acima.")

if __name__ == "__main__":
    main()