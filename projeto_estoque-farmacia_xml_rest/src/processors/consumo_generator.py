# src/processors/consumo_generator.py

import os
from datetime import date
from lxml import etree
from src.config.database import db
from src.utils.xml_utils import gerar_nome_arquivo_xml, escrever_xml
from src.utils.hash_utils import adicionar_assinatura
from dotenv import load_dotenv

load_dotenv()

class ConsumoGenerator:
    
    @staticmethod
    def gerar(p_data=None):
        if p_data is None:
            p_data = date.today()
        
        print(f"📊 Gerando relatório de consumo XML para {p_data}")
        
        # Buscar itens de consumo não enviados
        novos_itens = db.execute(
            """SELECT id_prescricao, cpf_paciente, codigo_medicamento,
                      quantidade, unidade, preco_total, data_uso
               FROM itens_consumo
               WHERE consolidado_em = %s AND enviado_para_g1 = FALSE""",
            (p_data,),
            fetch_all=True
        )
        
        if not novos_itens:
            print(f"   Nenhum novo item para consolidar em {p_data}")
            return False
        
        nome_arquivo = gerar_nome_arquivo_xml('CONSUMO')
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_consumos = os.getenv('PASTA_CONSUMOS', 'saida/consumos')
        caminho = os.path.join(data_dir, pasta_consumos, nome_arquivo)
        
        # Se arquivo já existe, ler itens existentes
        itens_existentes = []
        if os.path.exists(caminho):
            try:
                root_existente = etree.parse(caminho).getroot()
                for item in root_existente.findall('item'):
                    # Pular a tag de assinatura
                    if item.tag == 'assinatura':
                        continue
                    item_dict = {}
                    for child in item:
                        item_dict[child.tag] = child.text
                    itens_existentes.append(item_dict)
                print(f"   📖 Lidos {len(itens_existentes)} itens existentes")
            except Exception as e:
                print(f"   ⚠️ Erro ao ler arquivo existente: {e}")
        
        # Preparar novos itens
        novos_itens_normalizados = []
        for item in novos_itens:
            item_dict = {
                'prescricao': str(item['id_prescricao']),
                'cpf': str(item['cpf_paciente']),
                'codigo_medicamento': str(item['codigo_medicamento']),
                'quantidade': f"{item['quantidade']:.3f}",
                'unidade': item['unidade'],
                'preco_total': f"{item['preco_total']:.2f}",
                'data_uso': str(item['data_uso'])
            }
            novos_itens_normalizados.append(item_dict)
        
        # Combinar (append - adiciona no final)
        todos_itens = itens_existentes + novos_itens_normalizados
        
        # Criar XML
        root = etree.Element('consumos')
        for item in todos_itens:
            item_elem = etree.SubElement(root, 'item')
            for campo, valor in item.items():
                etree.SubElement(item_elem, campo).text = valor
        
        # Adicionar assinatura (grupo G3)
        adicionar_assinatura(root, 'GRUPO_3')
        
        escrever_xml(caminho, root)
        
        # Marcar como enviados
        db.execute(
            """UPDATE itens_consumo 
               SET enviado_para_g1 = TRUE, enviado_em = CURRENT_TIMESTAMP
               WHERE consolidado_em = %s AND enviado_para_g1 = FALSE""",
            (p_data,)
        )
        
        total_itens = len(todos_itens)
        total_valor_novos = sum(float(i['preco_total']) for i in novos_itens)
        
        db.execute(
            """INSERT INTO logs_consumos 
               (arquivo_nome, data_consumo, total_itens, total_valor)
               VALUES (%s, %s, %s, %s)""",
            (nome_arquivo, p_data, total_itens, total_valor_novos)
        )
        
        print(f"✅ Relatório gerado com assinatura: {caminho}")
        print(f"   Total de itens no arquivo: {total_itens}")
        print(f"   Itens novos adicionados: {len(novos_itens)}")
        print(f"   Valor total dos novos: R$ {total_valor_novos:.2f}")
        
        return True