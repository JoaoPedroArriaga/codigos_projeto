import os
import csv
from datetime import date
from src.utils.csv_utils import escrever_csv
from src.config.database import db
from dotenv import load_dotenv

load_dotenv()

class ConsumoGenerator:
    
    @staticmethod
    def ler_consumo_existente(caminho):
        """Lê o arquivo de consumo existente"""
        if not os.path.exists(caminho):
            return {}
        
        consumos_existentes = {}
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chave = f"{row['id_prescricao']}_{row['codigo_medicamento']}"
                    consumos_existentes[chave] = {
                        'id_prescricao': row['id_prescricao'],
                        'cpf_paciente': row['cpf_paciente'],
                        'codigo_medicamento': row['codigo_medicamento'],
                        'quantidade': float(row['quantidade']),
                        'unidade': row['unidade'],
                        'preco_total': float(row['preco_total']),
                        'data_uso': row['data_uso']
                    }
            print(f"   📖 [DEBUG] Lidos {len(consumos_existentes)} itens existentes")
        except Exception as e:
            print(f"   ⚠️ [DEBUG] Erro ao ler arquivo existente: {e}")
        
        return consumos_existentes
    
    @staticmethod
    def mesclar_consumos(consumos_existentes, novos_consumos):
        """Mescla consumos existentes com novos"""
        consumos_mesclados = consumos_existentes.copy()
        
        for novo in novos_consumos:
            chave = f"{novo['id_prescricao']}_{novo['codigo_medicamento']}"
            
            if chave in consumos_mesclados:
                consumos_mesclados[chave]['quantidade'] += novo['quantidade']
                consumos_mesclados[chave]['preco_total'] += novo['preco_total']
                print(f"   🔄 [DEBUG] Somando: {chave} | +{novo['quantidade']} | Total: {consumos_mesclados[chave]['quantidade']}")
            else:
                consumos_mesclados[chave] = novo
                print(f"   ➕ [DEBUG] Adicionando novo item: {chave}")
        
        return consumos_mesclados
    
    @staticmethod
    def gerar(p_data=None):
        """Gera o relatório de consumo do dia"""
        if p_data is None:
            p_data = date.today()
        
        print(f"📊 Gerando relatório de consumo para {p_data}")
        
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
        
        # Gerar nome do arquivo
        nome_arquivo = f"CONSUMO_{p_data.strftime('%y%m%d')}.csv"
        
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_consumos = os.getenv('PASTA_CONSUMOS', 'saida/consumos')
        caminho = os.path.join(data_dir, pasta_consumos, nome_arquivo)
        
        # Ler consumos existentes
        consumos_existentes = ConsumoGenerator.ler_consumo_existente(caminho)
        
        # Preparar novos consumos
        novos_consumos = []
        for item in novos_itens:
            novos_consumos.append({
                'id_prescricao': str(item['id_prescricao']),
                'cpf_paciente': str(item['cpf_paciente']),
                'codigo_medicamento': str(item['codigo_medicamento']),
                'quantidade': float(item['quantidade']),
                'unidade': item['unidade'],
                'preco_total': float(item['preco_total']),
                'data_uso': str(item['data_uso'])
            })
        
        # Mesclar consumos
        consumos_mesclados = ConsumoGenerator.mesclar_consumos(consumos_existentes, novos_consumos)
        
        # Converter para lista ordenada
        lista_final = list(consumos_mesclados.values())
        lista_final.sort(key=lambda x: x['data_uso'])
        
        # Campos do relatório (sem lote)
        campos = [
            'id_prescricao',
            'cpf_paciente',
            'codigo_medicamento',
            'quantidade',
            'unidade',
            'preco_total',
            'data_uso'
        ]
        
        # Escrever arquivo
        escrever_csv(caminho, campos, lista_final)
        
        # Marcar como enviados
        db.execute(
            """UPDATE itens_consumo 
               SET enviado_para_g1 = TRUE, enviado_em = CURRENT_TIMESTAMP
               WHERE consolidado_em = %s AND enviado_para_g1 = FALSE""",
            (p_data,)
        )
        
        # Registrar no log
        total_itens = len(lista_final)
        total_valor = sum(float(i['preco_total']) for i in lista_final)
        
        db.execute(
            """INSERT INTO logs_consumos 
               (arquivo_nome, data_consumo, total_itens, total_valor)
               VALUES (%s, %s, %s, %s)""",
            (nome_arquivo, p_data, total_itens, total_valor)
        )
        
        print(f"✅ Relatório gerado: {caminho}")
        print(f"   Total de itens: {total_itens}")
        print(f"   Valor total: R$ {total_valor:.2f}")
        print(f"   📌 Itens novos: {len(novos_itens)} | Itens mesclados: {len(lista_final)}")
        
        return True