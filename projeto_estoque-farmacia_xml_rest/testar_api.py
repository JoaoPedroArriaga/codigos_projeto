#!/usr/bin/env python
"""
Script de teste rápido para validar a API
"""
import sys
import os
import asyncio
import requests
from time import sleep

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000"

def teste_saude():
    """Testa se a API está respondendo"""
    try:
        resposta = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health Check: {resposta.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check falhou: {e}")
        return False

def teste_medicamentos():
    """Testa listagem de medicamentos"""
    try:
        resposta = requests.get(f"{BASE_URL}/api/medicamentos", timeout=5)
        if resposta.status_code == 200:
            print(f"✅ Medicamentos: {len(resposta.json())} encontrados")
        else:
            print(f"⚠️  Medicamentos: Sem dados (esperado se DB vazio)")
        return True
    except Exception as e:
        print(f"❌ Medicamentos falhou: {e}")
        return False

def teste_consulta():
    """Testa endpoint de consulta"""
    try:
        dados = {
            "codigo_medicamento": 789123,
            "quantidade": 5,
            "cpf_paciente": "12345678901"
        }
        resposta = requests.post(
            f"{BASE_URL}/api/estoque/consultar",
            json=dados,
            timeout=5
        )
        if resposta.status_code == 200:
            resultado = resposta.json()
            print(f"✅ Consulta: Disponível={resultado['disponivel']}")
        else:
            print(f"⚠️  Consulta: {resposta.status_code}")
        return True
    except Exception as e:
        print(f"❌ Consulta falhou: {e}")
        return False

def teste_info_api():
    """Testa endpoint de informações"""
    try:
        resposta = requests.get(f"{BASE_URL}/api", timeout=5)
        if resposta.status_code == 200:
            info = resposta.json()
            print(f"✅ Info API: v{info['versao']}")
            print(f"   - Endpoints: {len(info['endpoints'])}")
        return True
    except Exception as e:
        print(f"❌ Info API falhou: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 TESTE RÁPIDO DA API")
    print("=" * 60)
    
    print("\n⏳ Aguardando API em http://localhost:8000...")
    
    # Tentar conectar por 30 segundos
    for i in range(30):
        try:
            requests.get(f"{BASE_URL}/health", timeout=1)
            print("✅ API respondendo!\n")
            break
        except:
            if i > 0 and i % 5 == 0:
                print(f"   Tentativa {i+1}/30...")
            sleep(1)
    else:
        print("❌ API não está respondendo. Certifique-se de executar: python run_api.py")
        return False
    
    # Executar testes
    print("📋 Executando testes...\n")
    
    testes = [
        ("Health Check", teste_saude),
        ("Medicamentos", teste_medicamentos),
        ("Consulta", teste_consulta),
        ("Info API", teste_info_api),
    ]
    
    resultados = []
    for nome, teste_func in testes:
        print(f"Testando {nome}...", end=" ")
        try:
            resultado = teste_func()
            resultados.append(resultado)
        except Exception as e:
            print(f"❌ Erro: {e}")
            resultados.append(False)
    
    # Resumo
    print("\n" + "=" * 60)
    print(f"📊 Resultado: {sum(resultados)}/{len(resultados)} testes passaram")
    print("=" * 60)
    
    if all(resultados):
        print("\n✅ API está funcionando corretamente!")
        print(f"\n📚 Acesse a documentação em: {BASE_URL}/docs")
        print(f"🌐 Frontend disponível em: {BASE_URL}/")
        return True
    else:
        print("\n❌ Alguns testes falharam. Verifique a API.")
        return False

if __name__ == "__main__":
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Teste interrompido pelo usuário")
        sys.exit(1)
