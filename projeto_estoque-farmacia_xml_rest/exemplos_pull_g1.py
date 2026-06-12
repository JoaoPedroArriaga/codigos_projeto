#!/usr/bin/env python
"""
Simula o G1 puxando o relatório de consumo via REST (começo do dia).
Uso:
    python exemplos_pull_g1.py
    python exemplos_pull_g1.py --data 2026-06-11
"""
import argparse
import sys
from datetime import date, timedelta
from urllib import request as urlrequest
from urllib.error import URLError

from src.utils.hash_utils import calcular_hmac

REST_URL = "http://localhost:8001"
GRUPO_G1 = "GRUPO_1"


def main():
    parser = argparse.ArgumentParser(description="G1 puxa relatório de consumo (REST)")
    parser.add_argument("--data", help="Data do consumo (YYYY-MM-DD). Padrão: ontem")
    parser.add_argument("--url", default=REST_URL, help="URL base do servidor G3 REST")
    args = parser.parse_args()

    if args.data:
        dia = date.fromisoformat(args.data)
    else:
        dia = date.today() - timedelta(days=1)

    query = f"data_inicio={dia.isoformat()}&data_fim={dia.isoformat()}"
    url = f"{args.url.rstrip('/')}/api/relatorios/consumo?{query}"
    hash_valor = calcular_hmac(query)

    print(f"G1 → G3 (REST): GET /api/relatorios/consumo")
    print(f"URL: {url}")
    print(f"HMAC query: {hash_valor[:16]}...")

    req = urlrequest.Request(
        url,
        headers={
            "X-Grupo-Origem": GRUPO_G1,
            "X-Hash": hash_valor,
            "Accept": "application/xml",
        },
        method="GET",
    )

    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            print(f"\nStatus: {resp.status}")
            print(f"X-Total-Itens: {resp.headers.get('X-Total-Itens')}")
            print(body[:3000])
            if len(body) > 3000:
                print("... (truncado)")
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
