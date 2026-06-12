"""
Benchmark: REST vs SOAP
Compara latência, tamanho de payload e taxa de sucesso entre os dois projetos:

  - REST: projeto_estoque-farmacia_xml_rest  (padrão http://localhost:8001)
  - SOAP: projeto_estoque-farmacia_soap      (padrão http://localhost:8000)

Uso (com os dois servidores rodando):
  cd benchmarks
  python benchmark_comparison.py              # 20 iterações (padrão)
  python benchmark_comparison.py --quick      # 10 iterações (rápido)
  python benchmark_comparison.py -n 50        # mais preciso, mais lento
"""
import argparse
import http.client
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

PROJETO_SOAP = Path(__file__).resolve().parent.parent / "projeto_estoque-farmacia_soap"
sys.path.insert(0, str(PROJETO_SOAP))

from exemplos_soap import montar_envelope  # noqa: E402

SOAP_BASE_URL = "http://localhost:8000"
REST_BASE_URL = "http://localhost:8001"

CODIGO_MEDICAMENTO = 789123
CPF_PACIENTE = "12345678901"
QUANTIDADE = 1


class HttpClient:
    """Cliente HTTP com conexão persistente (keep-alive) para medir mais rápido."""

    def __init__(self, base_url: str):
        parsed = urlparse(base_url)
        self.host = parsed.hostname
        self.port = parsed.port or 80
        self._conn: http.client.HTTPConnection | None = None

    def _get_conn(self) -> http.client.HTTPConnection:
        if self._conn is None:
            self._conn = http.client.HTTPConnection(self.host, self.port, timeout=15)
        return self._conn

    def request(
        self,
        method: str,
        path: str,
        body: bytes = None,
        headers: dict | None = None,
    ) -> tuple[int, int]:
        conn = self._get_conn()
        try:
            conn.request(method, path, body=body, headers=headers or {})
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, len(data)
        except (http.client.HTTPException, OSError):
            self.close()
            raise

    def close(self):
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
            self._conn = None


def medir_latencia(fn, iterations: int, label: str = "") -> dict | None:
    """Executa fn() N vezes e retorna estatísticas em ms."""
    latencias = []
    erros = 0
    tamanho = 0

    for i in range(iterations):
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

        if label and ((i + 1) % 5 == 0 or i + 1 == iterations):
            print(f"    {label}: {i + 1}/{iterations}", flush=True)

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


def calcular_delta(rest_val: float, soap_val: float) -> str:
    if rest_val == 0:
        return "N/A"
    diff = ((soap_val - rest_val) / rest_val) * 100
    sinal = "+" if diff > 0 else ""
    return f"{sinal}{diff:.0f}%"


def verificar_servidor(client: HttpClient, health_path: str = "/health") -> bool:
    try:
        status, _ = client.request("GET", health_path)
        return status == 200
    except (URLError, HTTPError, OSError, http.client.HTTPException):
        return False


def _criar_cenario(
    nome: str,
    rest_client: HttpClient,
    soap_client: HttpClient,
    rest_call,
    soap_call,
    soap_req_bytes: int,
    rest_endpoint: str,
    soap_endpoint: str,
    rest_req_bytes: int,
    iterations: int,
) -> dict:
    print(f"  → {nome}")
    return {
        "nome": nome,
        "rest": {
            "projeto": "projeto_estoque-farmacia_xml_rest",
            "endpoint": rest_endpoint,
            "request_bytes": rest_req_bytes,
            "stats": medir_latencia(rest_call, iterations, "REST "),
        },
        "soap": {
            "projeto": "projeto_estoque-farmacia_soap",
            "endpoint": soap_endpoint,
            "request_bytes": soap_req_bytes,
            "stats": medir_latencia(soap_call, iterations, "SOAP"),
        },
    }


def executar_benchmark(iterations: int, rest_client: HttpClient, soap_client: HttpClient) -> dict:
    cenarios = []

    soap_xml, soap_req_bytes = _soap_payload("listarMedicamentos")
    cenarios.append(_criar_cenario(
        "Listar medicamentos",
        rest_client, soap_client,
        lambda: rest_client.request("GET", "/api/medicamentos"),
        lambda: soap_client.request("POST", "/soap", soap_xml, _soap_headers("listarMedicamentos")),
        soap_req_bytes,
        "GET /api/medicamentos",
        "POST /soap → listarMedicamentos",
        2,
        iterations,
    ))

    consulta = {
        "codigo_medicamento": CODIGO_MEDICAMENTO,
        "quantidade": QUANTIDADE,
        "cpf_paciente": CPF_PACIENTE,
    }
    consulta_body = json.dumps(consulta).encode()
    soap_xml, soap_req_bytes = _soap_payload("consultarDisponibilidade", consulta)
    cenarios.append(_criar_cenario(
        "Consultar disponibilidade",
        rest_client, soap_client,
        lambda: rest_client.request(
            "POST", "/api/estoque/consultar", consulta_body,
            {"Content-Type": "application/json", "Accept": "application/json"},
        ),
        lambda: soap_client.request("POST", "/soap", soap_xml, _soap_headers("consultarDisponibilidade")),
        soap_req_bytes,
        "POST /api/estoque/consultar",
        "POST /soap → consultarDisponibilidade",
        len(consulta_body),
        iterations,
    ))

    soap_xml, soap_req_bytes = _soap_payload("obterEstoque", {"codigo_medicamento": CODIGO_MEDICAMENTO})
    cenarios.append(_criar_cenario(
        "Obter estoque",
        rest_client, soap_client,
        lambda: rest_client.request("GET", f"/api/estoque/{CODIGO_MEDICAMENTO}"),
        lambda: soap_client.request("POST", "/soap", soap_xml, _soap_headers("obterEstoque")),
        soap_req_bytes,
        f"GET /api/estoque/{CODIGO_MEDICAMENTO}",
        "POST /soap → obterEstoque",
        0,
        iterations,
    ))

    soap_xml, soap_req_bytes = _soap_payload("listarLotes", {"codigo_medicamento": CODIGO_MEDICAMENTO})
    cenarios.append(_criar_cenario(
        "Listar lotes",
        rest_client, soap_client,
        lambda: rest_client.request("GET", f"/api/estoque/lotes/{CODIGO_MEDICAMENTO}"),
        lambda: soap_client.request("POST", "/soap", soap_xml, _soap_headers("listarLotes")),
        soap_req_bytes,
        f"GET /api/estoque/lotes/{CODIGO_MEDICAMENTO}",
        "POST /soap → listarLotes",
        0,
        iterations,
    ))

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


def _soap_payload(operacao: str, parametros: dict | None = None) -> tuple[bytes, int]:
    xml = montar_envelope(operacao, parametros or {})
    data = xml.encode("utf-8")
    return data, len(data)


def _soap_headers(operacao: str) -> dict:
    return {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": operacao,
    }


def imprimir_relatorio(resultado: dict):
    print("\n" + "=" * 90)
    print("BENCHMARK: REST vs SOAP".center(90))
    print("=" * 90)
    total_req = resultado["config"]["iterations"] * 4 * 2
    print(f"Iterações por cenário: {resultado['config']['iterations']} ({total_req} requisições no total)")
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
    parser.add_argument("--iterations", "-n", type=int, default=20, help="Requisições por lado/cenário (padrão: 20)")
    parser.add_argument("--quick", "-q", action="store_true", help="Modo rápido: 10 iterações")
    parser.add_argument("--output", "-o", default="benchmark_results.json", help="Arquivo de saída JSON")
    parser.add_argument("--soap-url", default=SOAP_BASE_URL, help="URL base do projeto SOAP (padrão: 8000)")
    parser.add_argument("--rest-url", default=REST_BASE_URL, help="URL base do projeto REST (padrão: 8001)")
    args = parser.parse_args()

    iterations = 10 if args.quick else args.iterations
    SOAP_BASE_URL = args.soap_url.rstrip("/")
    REST_BASE_URL = args.rest_url.rstrip("/")

    soap_client = HttpClient(SOAP_BASE_URL)
    rest_client = HttpClient(REST_BASE_URL)

    print(f"Verificando SOAP em {SOAP_BASE_URL} ...")
    if not verificar_servidor(soap_client, "/soap/health"):
        print("ERRO: Servidor SOAP não está rodando.")
        print("Execute: cd projeto_estoque-farmacia_soap && python run_api.py")
        sys.exit(1)

    print(f"Verificando REST em {REST_BASE_URL} ...")
    if not verificar_servidor(rest_client, "/health"):
        print("ERRO: Servidor REST não está rodando.")
        print("Execute: cd projeto_estoque-farmacia_xml_rest && python run_api.py")
        sys.exit(1)

    total = iterations * 4 * 2
    print(f"\nExecutando benchmark ({iterations} iterações × 4 cenários × REST+SOAP = {total} reqs)...")
    inicio = time.perf_counter()

    try:
        resultado = executar_benchmark(iterations, rest_client, soap_client)
    finally:
        rest_client.close()
        soap_client.close()

    elapsed = time.perf_counter() - inicio
    print(f"\nConcluído em {elapsed:.1f}s")

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
            "duracao_segundos": round(elapsed, 1),
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
