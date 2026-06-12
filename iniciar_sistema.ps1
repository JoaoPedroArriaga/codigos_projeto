# Inicia G3 SOAP (8000) e G3 REST (8001) para demonstração de interoperabilidade
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Iniciando G3 SOAP na porta 8000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$raiz\projeto_estoque-farmacia_soap'; python run_api.py"

Start-Sleep -Seconds 2

Write-Host "Iniciando G3 REST na porta 8001..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$raiz\projeto_estoque-farmacia_xml_rest'; python run_api.py"

Write-Host ""
Write-Host "Servidores iniciados em janelas separadas:"
Write-Host "  SOAP  -> http://localhost:8000/soap?wsdl"
Write-Host "  REST  -> http://localhost:8001/docs"
Write-Host "  Bench -> cd benchmarks; python benchmark_comparison.py"
