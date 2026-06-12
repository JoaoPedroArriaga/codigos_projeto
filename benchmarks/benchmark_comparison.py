"""
Benchmark: REST vs SOAP
Compara latência, tamanho de payload e taxa de sucesso entre os dois projetos:

  - REST: projeto_estoque-farmacia_xml_rest  (padrão http://localhost:8001)
  - SOAP: projeto_estoque-farmacia_soap      (padrão http://localhost:8000)

Uso (com os dois servidores rodando):
  cd benchmarks
  python benchmark_comparison.py
  python benchmark_comparison.py --iterations 50

Subir os servidores:
  Terminal 1: cd projeto_estoque-farmacia_soap && python run_api.py
  Terminal 2: cd projeto_estoque-farmacia_xml_rest && python run_api.py
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

PROJETO_SOAP = Path(__file__).resolve().parent.parent / "projeto_estoque-farmacia_soap"
sys.path.insert(0, str(PROJETO_SOAP))

from exemplos_soap import montar_envelope  # noqa: E402

SOAP_BASE_URL = "http://localhost:8000"
REST_BASE_URL = "http://localhost:8001"

CODIGO_MEDICAMENTO = 789123
CPF_PACIENTE = "12345678901"
QUANTIDADE = 1


def medir_latencia(fn, iterations: int) -> dict | None:
    """Executa fn() N vezes e retorna estatísticas em ms."""
    latencias = []
    erros = 0

    for _ in range(iterations):
        try:
            inicio = time.perf_counter()
            status, tamanho = fn()
            elapsed_ms = (time.perf_counter() - inicio) * 1000

            if status in (200, 201):
                latencias.append(elapsed_ms)
            else:
                erros += 1
        except Exception:
            erros += 1

    if not latencias:
        return None

    ordenado = sorted(latencias)
    return {
        "count": len(latencias),
        "errors": erros,
        "success_rate": round(len(latencias) / iterations * 100, 1),
        "min_ms": round(min(latencias), 2),
        "avg_ms": round(mean(latencias), 2),
        "max_ms": round(max(latencias), 2),
        "stddev_ms": round(stdev(latencias) if len(latencias) > 1 else 0, 2),
        "p95_ms": round(ordenado[int(len(ordenado) * 0.95)], 2),
        "p99_ms": round(ordenado[min(int(len(ordenado) * 0.99), len(ordenado) - 1)], 2),
        "last_response_bytes": tamanho,
    }


def _http_request(url: str, method: str = "GET", data: bytes = None, headers: dict = None):
    """Retorna (status_code, response_bytes)."""
    req = urlrequest.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urlrequest.urlopen(req, timeout=10) as resp:
            body = resp.read()
            return resp.status, len(body)
    except HTTPError as e:
        body = e.read()
        return e.code, len(body)


def req_rest_get(path: str):
    def _call():
        return _http_request(f"{REST_BASE_URL}{path}")
    return _call


def req_rest_post(path: str, payload: dict):
    body = json.dumps(payload).encode("utf-8")

    def _call():
        return _http_request(
            f"{REST_BASE_URL}{path}",
            method="POST",
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
    return _call


def req_soap(operacao: str, parametros: dict | None = None):
    xml = montar_envelope(operacao, parametros or {})
    data = xml.encode("utf-8")

    def _call():
        return _http_request(
            f"{SOAP_BASE_URL}/soap",
            method="POST",
            data=data,
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": operacao,
            },
        )

    return _call, len(data)


def calcular_delta(rest_val: float, soap_val: float) -> str:
    if rest_val == 0:
        return "N/A"
    diff = ((soap_val - rest_val) / rest_val) * 100
    sinal = "+" if diff > 0 else ""
    return f"{sinal}{diff:.0f}%"


def verificar_servidor(base_url: str, health_path: str = "/health") -> bool:
    try:
        status, _ = _http_request(f"{base_url}{health_path}")
        return status == 200
    except (URLError, HTTPError, TimeoutError):
        return False


def executar_benchmark(iterations: int) -> dict:
    cenarios = []

    # 1. Listar medicamentos
    soap_fn, soap_req_bytes = req_soap("listarMedicamentos")
    rest_payload = {}
    cenarios.append({
        "nome": "Listar medicamentos",
        "rest": {
            "projeto": "projeto_estoque-farmacia_xml_rest",
            "endpoint": "GET /api/medicamentos",
            "request_bytes": len(json.dumps(rest_payload).encode()),
            "stats": medir_latencia(req_rest_get("/api/medicamentos"), iterations),
        },
        "soap": {
            "projeto": "projeto_estoque-farmacia_soap",
            "endpoint": "POST /soap → listarMedicamentos",
            "request_bytes": soap_req_bytes,
            "stats": medir_latencia(soap_fn, iterations),
        },
    })

    # 2. Consultar disponibilidade
    consulta_rest = {
        "codigo_medicamento": CODIGO_MEDICAMENTO,
        "quantidade": QUANTIDADE,
        "cpf_paciente": CPF_PACIENTE,
    }
    consulta_soap = dict(consulta_rest)
    soap_fn, soap_req_bytes = req_soap("consultarDisponibilidade", consulta_soap)
    cenarios.append({
        "nome": "Consultar disponibilidade",
        "rest": {
            "projeto": "projeto_estoque-farmacia_xml_rest",
            "endpoint": "POST /api/estoque/consultar",
            "request_bytes": len(json.dumps(consulta_rest).encode()),
            "stats": medir_latencia(req_rest_post("/api/estoque/consultar", consulta_rest), iterations),
        },
        "soap": {
            "projeto": "projeto_estoque-farmacia_soap",
            "endpoint": "POST /soap → consultarDisponibilidade",
            "request_bytes": soap_req_bytes,
            "stats": medir_latencia(soap_fn, iterations),
        },
    })

    # 3. Obter estoque
    soap_fn, soap_req_bytes = req_soap("obterEstoque", {"codigo_medicamento": CODIGO_MEDICAMENTO})
    cenarios.append({
        "nome": "Obter estoque",
        "rest": {
            "projeto": "projeto_estoque-farmacia_xml_rest",
            "endpoint": f"GET /api/estoque/{CODIGO_MEDICAMENTO}",
            "request_bytes": 0,
            "stats": medir_latencia(req_rest_get(f"/api/estoque/{CODIGO_MEDICAMENTO}"), iterations),
        },
        "soap": {
            "projeto": "projeto_estoque-farmacia_soap",
            "endpoint": "POST /soap → obterEstoque",
            "request_bytes": soap_req_bytes,
            "stats": medir_latencia(soap_fn, iterations),
        },
    })

    # 4. Listar lotes
    soap_fn, soap_req_bytes = req_soap("listarLotes", {"codigo_medicamento": CODIGO_MEDICAMENTO})
    cenarios.append({
        "nome": "Listar lotes",
        "rest": {
            "projeto": "projeto_estoque-farmacia_xml_rest",
            "endpoint": f"GET /api/estoque/lotes/{CODIGO_MEDICAMENTO}",
            "request_bytes": 0,
            "stats": medir_latencia(req_rest_get(f"/api/estoque/lotes/{CODIGO_MEDICAMENTO}"), iterations),
        },
        "soap": {
            "projeto": "projeto_estoque-farmacia_soap",
            "endpoint": "POST /soap → listarLotes",
            "request_bytes": soap_req_bytes,
            "stats": medir_latencia(soap_fn, iterations),
        },
    })

    return {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "soap_url": SOAP_BASE_URL,
            "rest_url": REST_BASE_URL,
            "iterations": iterations,
            "codigo_medicamento": CODIGO_MEDICAMENTO,
        },
        "cenarios": cenarios,
    }


def imprimir_relatorio(resultado: dict):
    print("\n" + "=" * 90)
    print("BENCHMARK: REST vs SOAP".center(90))
    print("=" * 90)
    print(f"Iterações por cenário: {resultado['config']['iterations']}")
    print(f"REST (xml_rest): {resultado['config']['rest_url']}")
    print(f"SOAP (soap):     {resultado['config']['soap_url']}\n")

    for cenario in resultado["cenarios"]:
        rest = cenario["rest"]
        soap = cenario["soap"]
        rs = rest["stats"]
        ss = soap["stats"]

        print(f"--- {cenario['nome']} ---")
        print(f"  REST  {rest['endpoint']}  [{rest['projeto']}]")
        print(f"  SOAP  {soap['endpoint']}  [{soap['projeto']}]")

        if not rs or not ss:
            print("  ERRO: um dos lados não retornou sucesso\n")
            continue

        print(f"\n  {'Métrica':<22} {'REST':>12} {'SOAP':>12} {'Delta':>10}")
        print(f"  {'-'*22} {'-'*12} {'-'*12} {'-'*10}")
        for metric, key in [
            ("Latência média (ms)", "avg_ms"),
            ("Latência P95 (ms)", "p95_ms"),
            ("Latência P99 (ms)", "p99_ms"),
            ("Latência máx (ms)", "max_ms"),
        ]:
            print(f"  {metric:<22} {rs[key]:>12} {ss[key]:>12} {calcular_delta(rs[key], ss[key]):>10}")

        print(f"  {'Payload request (B)':<22} {rest['request_bytes']:>12} {soap['request_bytes']:>12} {calcular_delta(rest['request_bytes'] or 1, soap['request_bytes']):>10}")
        print(f"  {'Payload response (B)':<22} {rs['last_response_bytes']:>12} {ss['last_response_bytes']:>12} {calcular_delta(rs['last_response_bytes'], ss['last_response_bytes']):>10}")
        print(f"  {'Taxa sucesso (%)':<22} {rs['success_rate']:>12} {ss['success_rate']:>12}")
        print()

    medias_rest = [c["rest"]["stats"]["avg_ms"] for c in resultado["cenarios"] if c["rest"]["stats"]]
    medias_soap = [c["soap"]["stats"]["avg_ms"] for c in resultado["cenarios"] if c["soap"]["stats"]]
    if medias_rest and medias_soap:
        avg_rest = mean(medias_rest)
        avg_soap = mean(medias_soap)
        print("=" * 90)
        print("RESUMO")
        print(f"  Latência média geral REST: {avg_rest:.2f} ms")
        print(f"  Latência média geral SOAP: {avg_soap:.2f} ms")
        print(f"  SOAP vs REST: {calcular_delta(avg_rest, avg_soap)} na latência média")
        print("=" * 90)


def main():
    global SOAP_BASE_URL, REST_BASE_URL

    parser = argparse.ArgumentParser(description="Benchmark REST (xml_rest) vs SOAP (soap)")
    parser.add_argument("--iterations", "-n", type=int, default=50, help="Requisições por cenário (padrão: 50)")
    parser.add_argument("--output", "-o", default="benchmark_results.json", help="Arquivo de saída JSON")
    parser.add_argument("--soap-url", default=SOAP_BASE_URL, help="URL base do projeto SOAP (padrão: 8000)")
    parser.add_argument("--rest-url", default=REST_BASE_URL, help="URL base do projeto REST (padrão: 8001)")
    args = parser.parse_args()

    SOAP_BASE_URL = args.soap_url.rstrip("/")
    REST_BASE_URL = args.rest_url.rstrip("/")

    print(f"Verificando SOAP em {SOAP_BASE_URL} ...")
    if not verificar_servidor(SOAP_BASE_URL, "/soap/health"):
        print("ERRO: Servidor SOAP não está rodando.")
        print("Execute: cd projeto_estoque-farmacia_soap && python run_api.py")
        sys.exit(1)

    print(f"Verificando REST em {REST_BASE_URL} ...")
    if not verificar_servidor(REST_BASE_URL, "/health"):
        print("ERRO: Servidor REST não está rodando.")
        print("Execute: cd projeto_estoque-farmacia_xml_rest && python run_api.py")
        sys.exit(1)

    print(f"Executando benchmark ({args.iterations} iterações/cenário)...")
    resultado = executar_benchmark(args.iterations)

    output_path = Path(__file__).parent / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    imprimir_relatorio(resultado)
    print(f"\nResultados salvos em: {output_path}")

    conclusao_path = Path(__file__).parent / "benchmark_conclusion.json"
    medias_rest = [c["rest"]["stats"]["avg_ms"] for c in resultado["cenarios"] if c["rest"]["stats"]]
    medias_soap = [c["soap"]["stats"]["avg_ms"] for c in resultado["cenarios"] if c["soap"]["stats"]]
    if medias_rest and medias_soap:
        avg_rest = mean(medias_rest)
        avg_soap = mean(medias_soap)
        diff = ((avg_soap - avg_rest) / avg_rest) * 100 if avg_rest else 0
        conclusao = {
            "titulo": "Benchmark: REST vs SOAP",
            "data": resultado["timestamp"],
            "servidores": {
                "rest": REST_BASE_URL,
                "soap": SOAP_BASE_URL,
            },
            "metricas": {
                "latencia_media_rest_ms": round(avg_rest, 2),
                "latencia_media_soap_ms": round(avg_soap, 2),
                "delta_percentual": round(diff, 1),
            },
            "conclusao": {
                "melhor_para_performance": "REST" if avg_rest < avg_soap else "SOAP",
                "melhor_para_interoperabilidade": "SOAP (WSDL, contrato formal, integração G1/G2)",
                "projeto_rest": "projeto_estoque-farmacia_xml_rest",
                "projeto_soap": "projeto_estoque-farmacia_soap",
                "recomendacao": "Comparar os dois projetos em portas distintas para benchmark justo",
            },
            "arquivo_resultados": str(output_path.name),
        }
        with open(conclusao_path, "w", encoding="utf-8") as f:
            json.dump(conclusao, f, indent=2, ensure_ascii=False)
        print(f"Conclusão atualizada: {conclusao_path}")


if __name__ == "__main__":
    main()
