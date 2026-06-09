"""
🏁 Benchmark: REST vs SOAP
Compara performance entre endpoints REST e SOAP

Requisitos:
  pip install requests apache-bench locust
  
Para executar:
  python benchmark_comparison.py
"""

import json
import time
import requests
import subprocess
from datetime import datetime
from statistics import mean, stdev
from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

# Endpoints
REST_BASE = "http://localhost:8000"  # Se existir servidor REST antigo
SOAP_BASE = "http://localhost:8000/soap"

# Payloads
REST_PAYLOAD_LISTAR = {}

SOAP_PAYLOAD_LISTAR = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Body>
    <tns:listarMedicamentos/>
  </soap:Body>
</soap:Envelope>
"""

SOAP_PAYLOAD_CONSULTAR = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>abc123def456</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:consultarDisponibilidade>
      <tns:codigo_medicamento>789123</tns:codigo_medicamento>
      <tns:quantidade>5</tns:quantidade>
      <tns:cpf_paciente>12345678901</tns:cpf_paciente>
    </tns:consultarDisponibilidade>
  </soap:Body>
</soap:Envelope>
"""

# ============================================================================
# TESTE 1: LATÊNCIA (Latency Test)
# ============================================================================

def benchmark_latency(endpoint, payload, method="POST", headers=None, name=""):
    """
    Mede latência de uma operação
    
    Retorna:
        {
            'min': tempo mínimo (ms),
            'max': tempo máximo (ms),
            'avg': tempo médio (ms),
            'stddev': desvio padrão (ms)
        }
    """
    if headers is None:
        headers = {"Content-Type": "text/xml"}
    
    latencies = []
    iterations = 100  # 100 requisições
    
    print(f"\n  🔄 {name}: {iterations} requisições...")
    
    for i in range(iterations):
        try:
            start = time.time()
            
            if method == "POST":
                response = requests.post(endpoint, data=payload, headers=headers, timeout=5)
            else:
                response = requests.get(endpoint, timeout=5)
            
            elapsed = (time.time() - start) * 1000  # Converter para ms
            
            if response.status_code in [200, 201, 500]:  # Incluir 500 para SOAP Faults
                latencies.append(elapsed)
            
            if (i + 1) % 20 == 0:
                print(f"     {i+1}/{iterations} ✓")
        
        except requests.exceptions.Timeout:
            print(f"     Timeout na requisição {i+1}")
        except Exception as e:
            print(f"     Erro na requisição {i+1}: {str(e)}")
    
    if latencies:
        return {
            'count': len(latencies),
            'min': round(min(latencies), 2),
            'max': round(max(latencies), 2),
            'avg': round(mean(latencies), 2),
            'stddev': round(stdev(latencies) if len(latencies) > 1 else 0, 2),
            'p95': round(sorted(latencies)[int(len(latencies) * 0.95)], 2),
            'p99': round(sorted(latencies)[int(len(latencies) * 0.99)], 2),
        }
    else:
        return None


# ============================================================================
# TESTE 2: TAMANHO DE PAYLOAD
# ============================================================================

def measure_payload_size(payload):
    """Mede tamanho do payload em bytes"""
    if isinstance(payload, str):
        return len(payload.encode('utf-8'))
    else:
        return len(json.dumps(payload).encode('utf-8'))


# ============================================================================
# TESTE 3: THROUGHPUT (Apache Bench)
# ============================================================================

def benchmark_throughput_ab(endpoint, payload, requests_count=1000, concurrency=10, name=""):
    """
    Usa Apache Bench para medir throughput
    
    Requer: apt-get install apache2-utils (Linux) ou 
            choco install apache (Windows)
    """
    print(f"\n  📊 {name}:")
    print(f"     Requisições: {requests_count}")
    print(f"     Concorrência: {concurrency}")
    
    try:
        # Salvar payload em arquivo temporário
        temp_file = f"/tmp/payload_{name.replace(' ', '_')}.txt"
        with open(temp_file, 'w') as f:
            f.write(payload)
        
        # Executar apache-bench
        cmd = [
            'ab',
            '-n', str(requests_count),
            '-c', str(concurrency),
            '-p', temp_file,
            '-T', 'text/xml',
            endpoint
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Parsear output
        lines = result.stdout.split('\n')
        stats = {}
        for line in lines:
            if 'Requests per second' in line:
                stats['throughput'] = float(line.split(':')[1].strip().split()[0])
            elif 'Time per request' in line and 'mean' in line:
                stats['time_per_request'] = float(line.split(':')[1].strip().split()[0])
        
        print(f"     ✅ {stats}")
        return stats
    
    except FileNotFoundError:
        print(f"     ⚠️  Apache Bench não instalado. Pulando teste.")
        return None
    except Exception as e:
        print(f"     ❌ Erro: {str(e)}")
        return None


# ============================================================================
# TESTE 4: ANÁLISE DE PAYLOAD
# ============================================================================

def analyze_payload(name, payload):
    """Analisa tamanho e estrutura do payload"""
    size = measure_payload_size(payload)
    lines = payload.count('\n')
    
    if isinstance(payload, str):
        # XML
        return {
            'type': 'XML',
            'size_bytes': size,
            'size_kb': round(size / 1024, 2),
            'lines': lines,
        }
    else:
        # JSON
        return {
            'type': 'JSON',
            'size_bytes': size,
            'size_kb': round(size / 1024, 2),
            'fields': len(payload),
        }


# ============================================================================
# TESTE 5: LOAD TEST (Locust)
# ============================================================================

def generate_locust_script(soap_endpoint):
    """Gera script Locust para load testing"""
    script = f'''
from locust import HttpUser, task, between

class SOAPUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def listar_medicamentos(self):
        payload = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Body>
    <tns:listarMedicamentos/>
  </soap:Body>
</soap:Envelope>"""
        self.client.post("/soap", data=payload, 
                        headers={{"Content-Type": "text/xml"}})
    
    @task(1)
    def consultar_disponibilidade(self):
        payload = """{SOAP_PAYLOAD_CONSULTAR}"""
        self.client.post("/soap", data=payload,
                        headers={{"Content-Type": "text/xml"}})
'''
    return script


# ============================================================================
# RELATÓRIO FINAL
# ============================================================================

def generate_report(results):
    """Gera relatório em JSON e texto"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'benchmarks': results
    }
    
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE BENCHMARK".center(80))
    print("="*80)
    
    # Latência
    if 'latency' in results:
        print("\n⏱️  LATÊNCIA (ms)")
        print("-"*80)
        for teste, dados in results['latency'].items():
            if dados:
                print(f"\n{teste}")
                print(f"  Min:    {dados['min']} ms")
                print(f"  Avg:    {dados['avg']} ms")
                print(f"  P95:    {dados['p95']} ms")
                print(f"  P99:    {dados['p99']} ms")
                print(f"  Max:    {dados['max']} ms")
                print(f"  StdDev: {dados['stddev']} ms")
    
    # Payload
    if 'payload' in results:
        print("\n\n📦 TAMANHO DE PAYLOAD")
        print("-"*80)
        for nome, dados in results['payload'].items():
            print(f"\n{nome}")
            print(f"  Tamanho: {dados['size_bytes']} bytes ({dados['size_kb']} KB)")
            if 'lines' in dados:
                print(f"  Linhas:  {dados['lines']}")
    
    # Throughput
    if 'throughput' in results:
        print("\n\n🚀 THROUGHPUT (com Apache Bench)")
        print("-"*80)
        for teste, dados in results['throughput'].items():
            if dados:
                print(f"\n{teste}")
                print(f"  Requests/sec: {dados.get('throughput', 'N/A')}")
                print(f"  Time/req:     {dados.get('time_per_request', 'N/A')} ms")
    
    print("\n" + "="*80 + "\n")
    
    # Salvar JSON
    with open('benchmark_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    print("✅ Resultados salvos em: benchmark_results.json\n")
    
    return report


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🏁 BENCHMARK: REST vs SOAP".center(80))
    print("="*80)
    
    results = {
        'latency': {},
        'payload': {},
        'throughput': {}
    }
    
    # TESTE 1: Latência SOAP
    print("\n1️⃣  LATÊNCIA - SOAP (listarMedicamentos)")
    results['latency']['SOAP - listarMedicamentos'] = benchmark_latency(
        SOAP_BASE,
        SOAP_PAYLOAD_LISTAR,
        headers={"Content-Type": "text/xml"},
        name="listarMedicamentos"
    )
    
    print("\n2️⃣  LATÊNCIA - SOAP (consultarDisponibilidade)")
    results['latency']['SOAP - consultarDisponibilidade'] = benchmark_latency(
        SOAP_BASE,
        SOAP_PAYLOAD_CONSULTAR,
        headers={"Content-Type": "text/xml"},
        name="consultarDisponibilidade"
    )
    
    # TESTE 2: Tamanho Payload
    print("\n\n3️⃣  TAMANHO DE PAYLOAD")
    print("─"*80)
    results['payload']['SOAP - listarMedicamentos'] = analyze_payload(
        'SOAP - listarMedicamentos',
        SOAP_PAYLOAD_LISTAR
    )
    results['payload']['SOAP - consultarDisponibilidade'] = analyze_payload(
        'SOAP - consultarDisponibilidade',
        SOAP_PAYLOAD_CONSULTAR
    )
    
    # TESTE 3: Throughput (opcional - requer Apache Bench)
    print("\n\n4️⃣  THROUGHPUT - Apache Bench (opcional)")
    print("─"*80)
    results['throughput']['SOAP'] = benchmark_throughput_ab(
        SOAP_BASE,
        SOAP_PAYLOAD_LISTAR,
        requests_count=100,
        concurrency=5,
        name="SOAP"
    )
    
    # TESTE 4: Gerar script Locust
    print("\n\n5️⃣  GERANDO SCRIPT LOCUST")
    print("─"*80)
    locust_script = generate_locust_script(SOAP_BASE)
    with open('locustfile.py', 'w') as f:
        f.write(locust_script)
    print("✅ Script Locust criado: locustfile.py")
    print("   Para executar: locust -f locustfile.py -u 100 -r 10 -t 5m")
    
    # Gerar Relatório
    generate_report(results)


if __name__ == "__main__":
    main()
