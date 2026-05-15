"""
Normalizador de XML entre grupos - CORRIGIDO para seguir XSDs
"""
from lxml import etree


class XMLNormalizer:
    """Normaliza XMLs de diferentes grupos seguindo os XSDs"""
    
    @staticmethod
    def extrair_dados_consulta(root):
        """
        Extrai dados de um XML de consulta (Grupo 2)
        Estrutura esperada: <consultas><consulta>...</consulta></consultas>
        """
        dados = []
        
        # Buscar elemento raiz correto
        consultas_elem = root if root.tag == 'consultas' else root.find('consultas')
        if consultas_elem is None:
            consultas_elem = root
        
        for consulta in consultas_elem.findall('consulta'):
            item = {}
            
            prescricao = consulta.find('prescricao')
            if prescricao is not None and prescricao.text:
                item['id_prescricao'] = int(prescricao.text)
            
            cpf = consulta.find('cpf')
            if cpf is not None and cpf.text:
                item['cpf_paciente'] = cpf.text
            
            codigo = consulta.find('codigo_medicamento')
            if codigo is not None and codigo.text:
                item['codigo_medicamento'] = int(codigo.text)
            
            quantidade = consulta.find('quantidade')
            if quantidade is not None and quantidade.text:
                item['quantidade'] = float(quantidade.text)
            
            if item:
                dados.append(item)
        
        return dados
    
    @staticmethod
    def extrair_dados_reserva(root):
        """
        Extrai dados de um XML de reserva (Grupo 2)
        Estrutura esperada: <reservas><reserva>...</reserva></reservas>
        """
        dados = []
        
        reservas_elem = root if root.tag == 'reservas' else root.find('reservas')
        if reservas_elem is None:
            reservas_elem = root
        
        for reserva in reservas_elem.findall('reserva'):
            item = {}
            
            prescricao = reserva.find('prescricao')
            if prescricao is not None and prescricao.text:
                item['id_prescricao'] = int(prescricao.text)
            
            cpf = reserva.find('cpf')
            if cpf is not None and cpf.text:
                item['cpf_paciente'] = cpf.text
            
            codigo = reserva.find('codigo_medicamento')
            if codigo is not None and codigo.text:
                item['codigo_medicamento'] = int(codigo.text)
            
            quantidade = reserva.find('quantidade')
            if quantidade is not None and quantidade.text:
                item['quantidade'] = float(quantidade.text)
            
            if item:
                dados.append(item)
        
        return dados
    
    @staticmethod
    def extrair_dados_baixa(root):
        """
        Extrai dados de um XML de baixa (Grupo 2)
        Estrutura esperada: <baixas><baixa>...</baixa></baixas>
        """
        dados = []
        
        baixas_elem = root if root.tag == 'baixas' else root.find('baixas')
        if baixas_elem is None:
            baixas_elem = root
        
        for baixa in baixas_elem.findall('baixa'):
            item = {}
            
            prescricao = baixa.find('prescricao')
            if prescricao is not None and prescricao.text:
                item['id_prescricao'] = int(prescricao.text)
            
            cpf = baixa.find('cpf')
            if cpf is not None and cpf.text:
                item['cpf_paciente'] = cpf.text
            
            codigo = baixa.find('codigo_medicamento')
            if codigo is not None and codigo.text:
                item['codigo_medicamento'] = int(codigo.text)
            
            lote = baixa.find('lote')
            if lote is not None and lote.text:
                item['lote'] = lote.text
            
            quantidade = baixa.find('quantidade')
            if quantidade is not None and quantidade.text:
                item['quantidade'] = float(quantidade.text)
            
            data_uso = baixa.find('data_uso')
            if data_uso is not None and data_uso.text:
                item['data_uso'] = int(data_uso.text)
            
            if item:
                dados.append(item)
        
        return dados
    
    @staticmethod
    def extrair_dados_finalizacao(root):
        """
        Extrai dados de um XML de finalização de atendimento
        Estrutura: <finalizacaoAtendimento>...</finalizacaoAtendimento>
        """
        item = {}
        
        id_atendimento = root.find('id_atendimento')
        if id_atendimento is not None and id_atendimento.text:
            item['id_atendimento'] = int(id_atendimento.text)
        
        cpf = root.find('cpf_paciente')
        if cpf is not None and cpf.text:
            item['cpf_paciente'] = cpf.text
        
        data_atendimento = root.find('data_atendimento')
        if data_atendimento is not None and data_atendimento.text:
            item['data_atendimento'] = data_atendimento.text
        
        tipo_atendimento = root.find('tipo_atendimento')
        if tipo_atendimento is not None and tipo_atendimento.text:
            item['tipo_atendimento'] = tipo_atendimento.text
        
        cid = root.find('cid')
        if cid is not None and cid.text:
            item['cid'] = cid.text
        
        valor_total = root.find('valor_total')
        if valor_total is not None and valor_total.text:
            item['valor_total'] = float(valor_total.text)
        
        return item
    
    @staticmethod
    def normalizar_para_consumo(dados):
        """Normaliza dados do banco para XML de consumo (Grupo 1)"""
        itens = []
        for item in dados:
            item_xml = {
                'prescricao': str(item['id_prescricao']),
                'cpf': str(item['cpf_paciente']),
                'codigo_medicamento': str(item['codigo_medicamento']),
                'quantidade': f"{item['quantidade']:.3f}",
                'unidade': item.get('unidade', 'CAIXA'),
                'preco_total': f"{item['preco_total']:.2f}",
                'data_uso': str(item['data_uso'])
            }
            itens.append(item_xml)
        return itens


class XMLBuilder:
    """Construtor de XMLs seguindo os XSDs"""
    
    @staticmethod
    def construir_consumo(itens, grupo_origem="GRUPO_3"):
        """Constrói XML de consumo no formato correto"""
        root = etree.Element('consumos')
        
        for item in itens:
            item_elem = etree.SubElement(root, 'item')
            for campo, valor in item.items():
                elem = etree.SubElement(item_elem, campo)
                elem.text = valor
        
        return root
    
    @staticmethod
    def construir_resposta(respostas, grupo_origem="GRUPO_3"):
        """Constrói XML de resposta no formato correto"""
        root = etree.Element('respostas')
        
        for resp in respostas:
            resposta_elem = etree.SubElement(root, 'resposta')
            
            codigo = etree.SubElement(resposta_elem, 'codigo_medicamento')
            codigo.text = str(resp['codigo_medicamento'])
            
            disponivel = etree.SubElement(resposta_elem, 'disponivel')
            disponivel.text = str(resp['disponivel'])
            
            if resp.get('observacao'):
                observacao = etree.SubElement(resposta_elem, 'observacao')
                observacao.text = resp['observacao']
        
        return root