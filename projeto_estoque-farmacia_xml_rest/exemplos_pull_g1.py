#!/usr/bin/env python
"""
Simula o G1 puxando o relatório de consumo via REST/JSON (começo do dia).
Uso:
    python exemplos_pull_g1.py
    python exemplos_pull_g1.py --data 2026-04-10
"""
import argparse
import json
import sys
from datetime import date, timedelta
from urllib import request as urlrequest
from urllib.error import URLError

REST_URL = "http://localhost:8001"


def main():
    parser = argparse.ArgumentParser(description="G1 puxa relatório de consumo (REST/JSON)")
    parser.add_argument("--data", help="Data do consumo (YYYY-MM-DD). Padrão: ontem")
    parser.add_argument("--url", default=REST_URL, help="URL base do servidor G3 REST")
    args = parser.parse_args()

    if args.data:
        dia = date.fromisoformat(args.data)
    else:
        dia = date.today() - timedelta(days=1)

    query = f"data_inicio={dia.isoformat()}&data_fim={dia.isoformat()}"
    url = f"{args.url.rstrip('/')}/api/relatorios/consumo?{query}"

    print("G1 -> G3 (REST): GET /api/relatorios/consumo")
    print(f"URL: {url}")

    req = urlrequest.Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            print(f"\nStatus: {resp.status}")
            print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
            sys.exit(0)
    except urlrequest.HTTPError as e:
        print(f"Status: {e.code}")
        print(e.read().decode("utf-8"))
        sys.exit(1)
    except URLError:
        print(f"ERRO: servidor indisponível em {args.url}")
        print("Execute: python run_api.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
