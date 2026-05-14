"""
Validador de XML contra XSD
"""
import os
from pathlib import Path
from lxml import etree

class XMLValidator:
    """Validador de XML contra XSD"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.schemas = {}
            # __file__ = .../projeto/src/utils/xml_validator.py
            current_file = Path(__file__).resolve()
            # Sobe 3 níveis: src/utils/ -> src/ -> projeto/
            project_root = current_file.parent.parent.parent
            cls._instance.schema_dir = str(project_root / 'xsds')
            print(f"[DEBUG] Schema directory: {cls._instance.schema_dir}")
            print(f"[DEBUG] Existe? {os.path.exists(cls._instance.schema_dir)}")
        return cls._instance

    def carregar_schema(self, nome):
        """Carrega um schema XSD"""
        caminho = os.path.join(self.schema_dir, nome)
        print(f"[DEBUG] Carregando XSD: {caminho}")
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"XSD nao encontrado: {caminho}")

        with open(caminho, 'rb') as f:
            schema_root = etree.XML(f.read())
        self.schemas[nome] = etree.XMLSchema(schema_root)
        print(f"[OK] Schema carregado: {nome}")

    def validar(self, xml_path, schema_nome):
        """Valida um arquivo XML contra um XSD"""
        if schema_nome not in self.schemas:
            self.carregar_schema(schema_nome)

        try:
            with open(xml_path, 'rb') as f:
                xml_doc = etree.XML(f.read())

            self.schemas[schema_nome].assertValid(xml_doc)
            return True, None
        except etree.DocumentInvalid as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

# Instância global
validador = XMLValidator()