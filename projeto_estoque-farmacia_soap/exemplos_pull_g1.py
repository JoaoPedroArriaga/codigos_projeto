#!/usr/bin/env python
"""
Simula o G1 puxando o relatório de consumo via SOAP (começo do dia).
Uso:
    python exemplos_pull_g1.py
    python exemplos_pull_g1.py --data 2026-06-11
"""
import argparse
import sys
from datetime import date, timedelta
from urllib.error import URLError

import exemplos_soap
from exemplos_soap import enviar_soap, montar_envelope
from src.utils.hash_utils import calcular_hmac_envelope_xml

GRUPO_G1 = "GRUPO_1"


def main():
    parser = argparse.ArgumentParser(description="G1 puxa relatório de consumo (SOAP)")
    parser.add_argument("--data", help="Data do consumo (YYYY-MM-DD). Padrão: ontem")
    parser.add_argument("--url", default=SOAP_URL, help="URL do servidor G3")
    args = parser.parse_args()

    if args.data:
        dia = date.fromisoformat(args.data)
    else:
        dia = date.today() - timedelta(days=1)

    params = {
        "data_inicio": dia.isoformat(),
        "data_fim": dia.isoformat(),
    }

    print(f"G1 → G3 (SOAP): gerarRelatorioConsumo")
    soap_url = args.url.rstrip("/") + "/soap"
    print(f"URL: {soap_url}")
    print(f"Período: {dia} a {dia}")
    print(f"HMAC body: {calcular_hmac_envelope_xml(montar_envelope('gerarRelatorioConsumo', params, GRUPO_G1))[:16]}...")

    try:
        exemplos_soap.SOAP_URL = soap_url
        status, body = enviar_soap("gerarRelatorioConsumo", params, GRUPO_G1)
        print(f"\nStatus: {status}")
        print(body[:3000])
        if len(body) > 3000:
            print("... (truncado)")
        sys.exit(0 if status == 200 else 1)
    except URLError:
        print(f"ERRO: servidor indisponível em {args.url}")
        print("Execute: python run_api.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
