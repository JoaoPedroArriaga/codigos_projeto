# src/processors/consumo_generator.py

import os
from datetime import date
from dotenv import load_dotenv
from src.config.database import db
from src.utils.xml_utils import gerar_nome_arquivo_xml, escrever_xml
from src.utils.hash_utils import adicionar_assinatura
from src.utils.xml_normalizer import XMLNormalizer, XMLBuilder

load_dotenv()


class ConsumoGenerator:
    
    @staticmethod
    def gerar(p_data=None):
        """
        Gera relatório de consumo XML no formato correto seguindo o XSD
        """
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
        
        # Preparar itens no formato correto
        itens_normalizados = []
        for item in novos_itens:
            item_dict = {
                'id_prescricao': item['id_prescricao'],
                'cpf_paciente': item['cpf_paciente'],
                'codigo_medicamento': item['codigo_medicamento'],
                'quantidade': float(item['quantidade']),
                'unidade': item.get('unidade', 'CAIXA'),
                'preco_total': float(item['preco_total']),
                'data_uso': item['data_uso']
            }
            itens_normalizados.append(item_dict)
        
        # Normalizar para XML (campos no formato do XSD consumo.xsd)
        itens_xml = XMLNormalizer.normalizar_para_consumo(itens_normalizados)
        
        # Construir XML usando o builder
        root = XMLBuilder.construir_consumo(itens_xml)
        
        # Adicionar assinatura como último elemento
        adicionar_assinatura(root, 'GRUPO_3')
        
        nome_arquivo = gerar_nome_arquivo_xml('CONSUMO')
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_consumos = os.getenv('PASTA_CONSUMOS', 'saida/consumos')
        caminho = os.path.join(data_dir, pasta_consumos, nome_arquivo)
        
        # Garantir diretório
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        
        # Salvar XML
        escrever_xml(caminho, root)
        
        # Marcar como enviados
        db.execute(
            """UPDATE itens_consumo 
               SET enviado_para_g1 = TRUE, enviado_em = CURRENT_TIMESTAMP
               WHERE consolidado_em = %s AND enviado_para_g1 = FALSE""",
            (p_data,)
        )
        
        # Registrar log
        total_valor = sum(float(i['preco_total']) for i in novos_itens)
        db.execute(
            """INSERT INTO logs_consumos 
               (arquivo_nome, data_consumo, total_itens, total_valor)
               VALUES (%s, %s, %s, %s)""",
            (nome_arquivo, p_data, len(novos_itens), total_valor)
        )
        
        print(f"✅ Relatório gerado: {caminho}")
        print(f"   Itens: {len(novos_itens)}, Valor Total: R$ {total_valor:.2f}")
        return True