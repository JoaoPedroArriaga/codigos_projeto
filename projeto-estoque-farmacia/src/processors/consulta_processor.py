import os
from src.utils.csv_utils import ler_csv, escrever_csv, gerar_nome_arquivo, mover_para_processados
from src.models.logs import LogConsulta
from src.services.estoque_service import EstoqueService
from dotenv import load_dotenv

load_dotenv()

class ConsultaProcessor:
    
    @staticmethod
    def processar(caminho_arquivo):
        """Processa um arquivo de consulta"""
        print(f"📄 Processando consulta: {caminho_arquivo}")
        
        # 1. Ler CSV
        dados = ler_csv(caminho_arquivo)
        if not dados:
            return False
        
        print(f"   📋 [DEBUG] Dados lidos: {len(dados)} linha(s)")
        
        # Pega o ID da prescrição da primeira linha
        id_prescricao_principal = dados[0]['id_prescricao']
        
        # 2. Processar cada linha
        respostas = []
        for idx, row in enumerate(dados):
            print(f"   📋 [DEBUG] Processando linha {idx + 1}: {row}")
            
            id_prescricao = int(row['id_prescricao'])
            cpf_paciente = int(row['cpf_paciente'])
            codigo_medicamento = int(row['codigo_medicamento'])
            quantidade = float(row['quantidade'])
            
            # Verifica disponibilidade
            resultado = EstoqueService.verificar_disponibilidade(
                codigo_medicamento, quantidade
            )
            
            # Registra no log (versão simplificada)
            LogConsulta.registrar(
                os.path.basename(caminho_arquivo), 
                id_prescricao, 
                cpf_paciente, 
                codigo_medicamento,
                quantidade, 
                resultado['disponivel'], 
                'Disponível' if resultado['disponivel'] else 'Estoque insuficiente'
            )
            
            # Monta resposta (disponivel = 1 ou 0)
            respostas.append({
                'codigo_medicamento': codigo_medicamento,
                'disponivel': 1 if resultado['disponivel'] else 0,
                'observacao': '' if resultado['disponivel'] else 'Estoque insuficiente'
            })
            
            print(f"   📋 [DEBUG] Resposta gerada: disponivel={1 if resultado['disponivel'] else 0}")
        
        # 3. Gerar arquivo de resposta
        nome_resposta = gerar_nome_arquivo('RESPOSTA', id_prescricao_principal)
        
        data_dir = os.getenv('DATA_DIR', 'data')
        pasta_respostas = os.getenv('PASTA_RESPOSTAS', 'saida/respostas')
        caminho_resposta = os.path.join(data_dir, pasta_respostas, nome_resposta)
        
        campos = ['codigo_medicamento', 'disponivel', 'observacao']
        escrever_csv(caminho_resposta, campos, respostas)
        
        # 4. Mover arquivo original para processados
        mover_para_processados(caminho_arquivo, 'consultas')
        
        print(f"✅ Consulta {os.path.basename(caminho_arquivo)} processada")
        print(f"   Resposta gerada: {caminho_resposta}")
        
        return True