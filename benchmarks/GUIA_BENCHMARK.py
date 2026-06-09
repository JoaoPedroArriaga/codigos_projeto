"""
📊 GUIA: Como Executar Benchmark REST vs SOAP
Passo a passo para comparar performance
"""

# ============================================================================
# SETUP INICIAL (Uma vez)
# ============================================================================

# 1. Instalar ferramentas de benchmark
pip install requests apache-bench locust

# 2. Ou via sistema (dependendo do SO)

# Linux/Mac
sudo apt-get install apache2-utils  # Ubuntu
brew install httpd                  # Mac

# Windows
choco install apache                # Se tem Chocolatey
# OU baixar de: https://www.apachelounge.com/download/

# ============================================================================
# PASSO 1: Rodar Servidor SOAP
# ============================================================================

# Terminal 1: Rodar servidor
cd projeto_estoque-farmacia_soap
python -m src.soap.app

# Deve aparecer:
# 🚀 Iniciando servidor SOAP na porta 8000
# 📖 WSDL: http://localhost:8000/soap?wsdl


# ============================================================================
# PASSO 2: TESTE RÁPIDO (Benchmark básico)
# ============================================================================

# Terminal 2: Ir para pasta benchmarks
cd benchmarks

# Rodar benchmark
python benchmark_comparison.py

# Resultado esperado:
# 
# ⏱️  LATÊNCIA (ms)
# SOAP - listarMedicamentos
#   Min:    2.34 ms
#   Avg:    5.67 ms
#   P95:    12.45 ms
#   P99:    18.90 ms
#   Max:    25.34 ms
#   StdDev: 3.21 ms


# ============================================================================
# PASSO 3: TESTE DE CARGA COM APACHE BENCH
# ============================================================================

# Teste 1: 1000 requisições sequenciais
ab -n 1000 -c 1 http://localhost:8000/soap?wsdl

# Teste 2: 1000 requisições com 10 concorrentes
ab -n 1000 -c 10 \
   -p payload_soap.xml \
   -T "text/xml" \
   http://localhost:8000/soap

# Teste 3: 5000 requisições com 50 concorrentes
ab -n 5000 -c 50 \
   -p payload_soap.xml \
   -T "text/xml" \
   http://localhost:8000/soap

# Interpretação de Apache Bench:
# Requests per second:   200.50 [#/sec]    ← Throughput
# Time per request:      49.87 [ms]        ← Latência média
# Failed requests:       0                 ← Erros
# Non-2xx responses:     0                 ← Não-sucesso


# ============================================================================
# PASSO 4: TESTE DE CARGA COM LOCUST
# ============================================================================

# Rodar Locust (simula 100 usuários)
locust -f locustfile.py \
  --host http://localhost:8000 \
  -u 100 \
  -r 10 \
  -t 5m

# Parâmetros:
# -u 100      = 100 usuários simultâneos
# -r 10       = spawn 10 usuários por segundo
# -t 5m       = rodar por 5 minutos
# --headless  = modo texto (sem web UI)

# Abrir em navegador (web UI):
# http://localhost:8089


# ============================================================================
# PASSO 5: TESTE CUSTOMIZADO COM CURL
# ============================================================================

# Teste 1: Medir latência simples
time curl -X POST http://localhost:8000/soap \
  -H "Content-Type: text/xml" \
  -d @exemplos_curl.sh

# Teste 2: Múltiplas requisições em loop
for i in {1..100}; do
  curl -X POST http://localhost:8000/soap \
    -H "Content-Type: text/xml" \
    -d @payload.xml > /dev/null 2>&1
done
time echo "100 requisições completas"

# Teste 3: Com statistics
ab -g results.tsv \
  -n 1000 -c 50 \
  http://localhost:8000/soap?wsdl

# Converter TSV para gráfico (opcional)
gnuplot -e "
  set terminal png;
  set output 'benchmark.png';
  plot 'results.tsv' using 5 with lines title 'Latência'
"


# ============================================================================
# PASSO 6: MONITORAMENTO DURANTE TESTE
# ============================================================================

# Terminal adicional: Monitorar recursos
# Linux
watch -n 1 "ps aux | grep python | grep app.py"
top -p PID_DO_SERVIDOR

# Mac
watch 'ps aux | grep python | grep app.py'

# Windows
Get-Process python | Select-Object ProcessName, CPU, Memory


# ============================================================================
# PASSO 7: COMPARAÇÃO REST vs SOAP (se tiver REST)
# ============================================================================

# Modificar benchmark_comparison.py para incluir:
# 1. Endpoint REST antigo
# 2. Fazer testes lado a lado
# 3. Comparar latência, tamanho, throughput

# Exemplo de comparação esperada:
#
# ╔════════════════════════════════════════════════════════════════╗
# ║ Métrica              │ REST (XML)     │ SOAP           │ Delta ║
# ╠════════════════════════════════════════════════════════════════╣
# ║ Latência Min         │ 1.5 ms         │ 2.3 ms         │ +53%  ║
# ║ Latência Avg         │ 3.2 ms         │ 5.6 ms         │ +75%  ║
# ║ Latência P99         │ 8.5 ms         │ 18.9 ms        │ +122% ║
# ║ Throughput (req/s)   │ 312            │ 178            │ -43%  ║
# ║ Payload (bytes)      │ 245            │ 512            │ +109% ║
# ║ Overhead SOAP        │ N/A            │ 267 bytes      │ -     ║
# ╚════════════════════════════════════════════════════════════════╝


# ============================================================================
# INTERPRETAÇÃO DE RESULTADOS
# ============================================================================

"""
1. Latência Esperada
   - SOAP simples (listar): 2-10 ms
   - SOAP complexo (consultar): 5-15 ms
   - Esperado 100ms+ se BD lento
   - >500ms = problema! Verificar logs

2. Throughput Esperado
   - SOAP: 150-300 req/s em um core
   - Com 4 cores: 600-1200 req/s
   - <50 req/s = servidor sobrecarregado

3. Payload Esperado
   - SOAP envelope: ~200-300 bytes
   - Resposta com dados: 500-2000 bytes
   - SOAP tem ~100% overhead vs JSON

4. Taxa de Erro Esperada
   - 0% = Perfeito
   - <0.1% = Aceitável
   - >1% = Investigar

5. P99 (99º percentil)
   - Ideal: P99 = 2x P50
   - Ruim: P99 = 10x P50 (muita variação)
   - Indica outliers/spikes
"""


# ============================================================================
# SALVAR RESULTADOS
# ============================================================================

# 1. Resultados automáticos (JSON)
cat benchmark_results.json

# 2. Exportar Apache Bench para CSV
ab -g results.tsv -n 1000 http://localhost:8000/soap?wsdl

# 3. Locust salva automaticamente em stats.csv

# 4. Criar relatório HTML
python -c "
import json
with open('benchmark_results.json') as f:
    data = json.load(f)

html = '''<html>
<body>
<h1>Benchmark Report</h1>
<pre>''' + json.dumps(data, indent=2) + '''</pre>
</body>
</html>'''

with open('benchmark_report.html', 'w') as f:
    f.write(html)
"

# Abrir em navegador
open benchmark_report.html  # Mac
xdg-open benchmark_report.html  # Linux
start benchmark_report.html  # Windows


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# ❌ "ab: command not found"
→ Instalar apache-bench (veja Setup Inicial)

# ❌ "Connection refused"
→ Servidor não está rodando em 8000
→ Verificar: curl http://localhost:8000/soap?wsdl

# ❌ "Timeout"
→ Servidor muito lento ou sobrecarregado
→ Verificar: python logs ou top/htop

# ❌ "413 Payload Too Large"
→ Payload > limite do servidor
→ Reduzir número de concorrentes

# ❌ "500 Internal Server Error"
→ Bug no código SOAP
→ Verificar logs: python -u src/soap/app.py


# ============================================================================
# DICA EXTRA: Script para Benchmark Automático
# ============================================================================

# Criar benchmark_auto.sh
cat > benchmark_auto.sh << 'EOF'
#!/bin/bash

echo "🏁 Iniciando benchmarks automáticos..."

# Teste 1: Latência
echo "\n1️⃣  Latência (100 req, sequential)"
ab -n 100 -c 1 http://localhost:8000/soap?wsdl > results_1.txt

# Teste 2: Throughput
echo "\n2️⃣  Throughput (1000 req, 10 concurrent)"
ab -n 1000 -c 10 http://localhost:8000/soap?wsdl > results_2.txt

# Teste 3: Carga
echo "\n3️⃣  Carga (5000 req, 50 concurrent)"
ab -n 5000 -c 50 http://localhost:8000/soap?wsdl > results_3.txt

# Compilar resultados
echo "\n✅ Benchmarks completos!"
echo "\nResultados:"
grep "Requests per second" results_*.txt

EOF

chmod +x benchmark_auto.sh
./benchmark_auto.sh


# ============================================================================
# PRÓXIMO PASSO: Comparar com REST
# ============================================================================

# Se tiver servidor REST rodando em :5000
# Modificar benchmark_comparison.py para:

REST_BASE = "http://localhost:5000"
SOAP_BASE = "http://localhost:8000/soap"

# E adicionar testes para ambos os endpoints
# Depois gerar tabela comparativa
