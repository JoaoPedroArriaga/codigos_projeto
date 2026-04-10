#!/usr/bin/env python
"""
Teste rápido para verificar se o consumo está somando corretamente
linhas com a mesma id_prescricao e codigo_medicamento
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import db
from src.processors.consumo_generator import ConsumoGenerator
from datetime import date

def limpar_tudo():
    """Limpa dados anteriores"""
    print("🧹 Limpando dados anteriores...")
    db.execute("TRUNCATE TABLE itens_consumo CASCADE")
    db.execute("TRUNCATE TABLE logs_consumos CASCADE")
    db.execute("UPDATE lotes SET quantidade_atual = quantidade_inicial")
    print("   ✅ Limpeza concluída!\n")

def inserir_itens_duplicados():
    """Insere itens de consumo duplicados manualmente"""
    print("📦 Inserindo itens de consumo duplicados...")
    
    # Inserir 2 itens iguais (mesma id_prescricao e mesmo medicamento)
    db.execute("""
        INSERT INTO itens_consumo 
        (id_prescricao, cpf_paciente, codigo_medicamento, quantidade, preco_total, data_uso, lote, unidade, id_lote, id_baixa_log)
        VALUES 
        (100001, 12345678901, 111222, 1.0, 12.00, 260327, 'LOTE004', 'CAIXA', 4, 1),
        (100001, 12345678901, 111222, 2.0, 24.00, 260327, 'LOTE004', 'CAIXA', 4, 2)
    """)
    print("   ✅ Inseridos 2 itens com id_prescricao 100001 e medicamento 111222")
    print("      - Item 1: quantidade 1.0, preço R$ 12.00")
    print("      - Item 2: quantidade 2.0, preço R$ 24.00")
    print("      - Esperado: somar para 3.0 e R$ 36.00\n")

def verificar_consumo_antes():
    """Verifica os itens antes da geração"""
    print("📋 ANTES da geração:")
    itens = db.execute("SELECT * FROM itens_consumo WHERE enviado_para_g1 = FALSE", fetch_all=True)
    for i in itens:
        print(f"   - id_prescricao={i['id_prescricao']}, medicamento={i['codigo_medicamento']}, qtd={i['quantidade']}, total={i['preco_total']}")

def verificar_consumo_depois():
    """Verifica os itens depois da geração"""
    print("\n📋 DEPOIS da geração (itens enviados):")
    itens = db.execute("SELECT * FROM itens_consumo WHERE enviado_para_g1 = TRUE", fetch_all=True)
    for i in itens:
        print(f"   - id_prescricao={i['id_prescricao']}, medicamento={i['codigo_medicamento']}, qtd={i['quantidade']}, total={i['preco_total']}")

def verificar_arquivo_consumo():
    """Verifica o conteúdo do arquivo CONSUMO gerado"""
    print("\n📄 CONTEÚDO DO ARQUIVO CONSUMO:")
    caminho = f"data/saida/consumos/CONSUMO_{date.today().strftime('%y%m%d')}.csv"
    
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("   Arquivo não encontrado")

def main():
    print("=" * 70)
    print("🧪 TESTE DE SOMA NO CONSUMO")
    print("=" * 70)
    
    db.connect()
    
    # 1. Limpar dados
    limpar_tudo()
    
    # 2. Inserir itens duplicados manualmente
    inserir_itens_duplicados()
    
    # 3. Verificar antes
    verificar_consumo_antes()
    
    # 4. Gerar consumo
    print("\n📊 Gerando relatório de consumo...")
    ConsumoGenerator.gerar(date.today())
    
    # 5. Verificar depois
    verificar_consumo_depois()
    
    # 6. Verificar arquivo
    verificar_arquivo_consumo()
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO!")
    print("   Se o arquivo CONSUMO tiver 1 linha com quantidade 3.0 e preço 36.00, a soma funcionou!")
    print("=" * 70)

if __name__ == "__main__":
    main()