#!/usr/bin/env python
"""
Simula o G1 enviando status financeiro via REST/JSON.
Uso:
    python exemplos_push_g1_status.py
"""
import argparse
import json
import sys
from urllib import request as urlrequest
from urllib.error import URLError

REST_URL = "http://localhost:8001"

PAYLOAD_EXEMPLO = {
    "pacientes": [
        {
            "cpf": "11122233344",
            "status": "ADIMPLENTE",
            "permite_atendimento": 1,
            "observacao": "Sincronizado via REST",
        },
        {
            "cpf": "12345678901",
            "status": "INADIMPLENTE",
            "permite_atendimento": 0,
            "observacao": "Pendência financeira",
        },
    ]
}


def main():
    parser = argparse.ArgumentParser(description="G1 envia status financeiro (REST/JSON)")
    parser.add_argument("--url", default=REST_URL, help="URL base do servidor G3 REST")
    args = parser.parse_args()

    url = f"{args.url.rstrip('/')}/api/integracao/status-financeiro"
    body = json.dumps(PAYLOAD_EXEMPLO).encode("utf-8")

    print("G1 -> G3 (REST): POST /api/integracao/status-financeiro")
    print(f"URL: {url}")

    req = urlrequest.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            resposta = resp.read().decode("utf-8")
            print(f"\nStatus: {resp.status}")
            print(json.dumps(json.loads(resposta), indent=2, ensure_ascii=False))
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
