"""
Normalizador de XML entre grupos
"""
from lxml import etree

class XMLNormalizer:
    """Normaliza XMLs de diferentes grupos"""
    
    # Mapeamento de campos de entrada (Grupo 2 → nosso banco)
    MAP_ENTRADA_CONSULTA = {
        'prescricao': 'id_prescricao',
        'cpf': 'cpf_paciente',
        'codigo_medicamento': 'codigo_medicamento',
        'quantidade': 'quantidade'
    }
    
    MAP_ENTRADA_RESERVA = {
        'prescricao': 'id_prescricao',
        'cpf': 'cpf_paciente',
        'codigo_medicamento': 'codigo_medicamento',
        'quantidade': 'quantidade'
    }
    
    MAP_ENTRADA_BAIXA = {
        'prescricao': 'id_prescricao',
        'cpf': 'cpf_paciente',
        'codigo_medicamento': 'codigo_medicamento',
        'lote': 'lote',
        'quantidade': 'quantidade',
        'data_uso': 'data_uso'
    }
    
    # Mapeamento de campos de saída (nosso banco → Grupo 1)
    MAP_SAIDA_CONSUMO = {
        'id_prescricao': 'prescricao',
        'cpf_paciente': 'cpf',
        'codigo_medicamento': 'codigo_medicamento',
        'quantidade': 'quantidade',
        'unidade': 'unidade',
        'preco_total': 'preco_total',
        'data_uso': 'data_uso'
    }
    
    @staticmethod
    def extrair_dados_consulta(root):
        """Extrai dados de um XML de consulta (Grupo 2)"""
        dados = []
        for consulta in root.findall('consulta'):
            item = {}
            for xml_campo, banco_campo in XMLNormalizer.MAP_ENTRADA_CONSULTA.items():
                elem = consulta.find(xml_campo)
                if elem is not None and elem.text:
                    item[banco_campo] = elem.text
            dados.append(item)
        return dados
    
    @staticmethod
    def extrair_dados_reserva(root):
        """Extrai dados de um XML de reserva (Grupo 2)"""
        dados = []
        for reserva in root.findall('reserva'):
            item = {}
            for xml_campo, banco_campo in XMLNormalizer.MAP_ENTRADA_RESERVA.items():
                elem = reserva.find(xml_campo)
                if elem is not None and elem.text:
                    item[banco_campo] = elem.text
            dados.append(item)
        return dados
    
    @staticmethod
    def extrair_dados_baixa(root):
        """Extrai dados de um XML de baixa (Grupo 2)"""
        dados = []
        for baixa in root.findall('baixa'):
            item = {}
            for xml_campo, banco_campo in XMLNormalizer.MAP_ENTRADA_BAIXA.items():
                elem = baixa.find(xml_campo)
                if elem is not None and elem.text:
                    item[banco_campo] = elem.text
            dados.append(item)
        return dados
    
    @staticmethod
    def normalizar_para_consumo(dados):
        """Normaliza dados do banco para XML de consumo (Grupo 1)"""
        itens = []
        for item in dados:
            item_xml = {}
            for banco_campo, xml_campo in XMLNormalizer.MAP_SAIDA_CONSUMO.items():
                if banco_campo in item and item[banco_campo] is not None:
                    item_xml[xml_campo] = str(item[banco_campo])
            itens.append(item_xml)
        return itens