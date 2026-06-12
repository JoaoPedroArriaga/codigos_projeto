#!/usr/bin/env python
"""
Cliente SOAP de exemplo para testar a API do Estoque Farmácia.
Uso:
    python exemplos_soap.py
    python exemplos_soap.py --hash-only listarMedicamentos
"""
import argparse
import sys
from datetime import datetime
from urllib import request as urlrequest
from urllib.error import URLError
from lxml import etree

from src.soap.handlers.envelope import SOAPEnvelope
from src.utils.hash_utils import calcular_hmac_envelope_xml, assinar_envelope_requisicao

SOAP_URL = "http://localhost:8000/soap"
GRUPO_ORIGEM = "GRUPO_2"


def montar_envelope(operacao: str, parametros: dict = None, grupo_origem: str = GRUPO_ORIGEM) -> str:
    """Monta envelope SOAP com HMAC válido do Body (mesma canonicalização do servidor)"""
    parametros = parametros or {}
    timestamp = datetime.now().isoformat()

    envelope = SOAPEnvelope.criar_envelope(
        operacao,
        parametros,
        "",
        timestamp,
        grupo_origem
    )
    assinar_envelope_requisicao(envelope)
    return SOAPEnvelope.serializar_xml(envelope, pretty=False)


def enviar_soap(operacao: str, parametros: dict = None, grupo_origem: str = GRUPO_ORIGEM):
    """Envia requisição SOAP para o servidor. Retorna (status_code, body_text)."""
    xml_body = montar_envelope(operacao, parametros, grupo_origem)
    req = urlrequest.Request(
        SOAP_URL,
        data=xml_body.encode('utf-8'),
        headers={
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': operacao
        },
        method='POST'
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urlrequest.HTTPError as e:
        return e.code, e.read().decode('utf-8')


def extrair_id_reserva(xml_resposta: str) -> str | None:
    """Extrai id_reserva da resposta de criarReserva"""
    try:
        root = etree.fromstring(xml_resposta.encode('utf-8'))
        ns = {'tns': SOAPEnvelope.NS_TNS}
        elem = root.find('.//tns:id_reserva', ns)
        return elem.text if elem is not None and elem.text else None
    except etree.XMLSyntaxError:
        return None


def exibir_resposta(titulo: str, status: int, body: str):
    print(f"\n{'=' * 60}")
    print(f"  {titulo}")
    print(f"{'=' * 60}")
    print(f"Status: {status}")
    print(body[:2000])
    if len(body) > 2000:
        print("... (resposta truncada)")


def main():
    parser = argparse.ArgumentParser(description="Cliente SOAP - Estoque Farmácia")
    parser.add_argument('--hash-only', action='store_true', help='Apenas exibe hash HMAC do body')
    parser.add_argument('operacao', nargs='?', default=None, help='Nome da operação SOAP')
    args = parser.parse_args()

    if args.hash_only:
        operacao = args.operacao or 'listarMedicamentos'
        print(calcular_hmac_envelope_xml(montar_envelope(operacao)))
        return

    print("Cliente SOAP - Estoque Farmácia")
    print(f"URL: {SOAP_URL}")

    params_consulta = {
        'codigo_medicamento': 789123,
        'quantidade': 1,
        'cpf_paciente': '12345678901'
    }
    params_reserva = {
        'codigo_medicamento': 789123,
        'quantidade': 1,
        'cpf_paciente': '12345678901'
    }
    params_baixa = {
        'codigo_medicamento': 789123,
        'quantidade': 1,
        'numero_lote': 'LOTE001',
        'cpf_paciente': '12345678901',
        'motivo': 'Dispensacao via SOAP'
    }

    if args.operacao:
        try:
            status, body = enviar_soap(args.operacao)
            exibir_resposta(f"Operação: {args.operacao}", status, body)
            sys.exit(0 if status == 200 else 1)
        except URLError:
            print(f"\nErro: servidor não disponível em {SOAP_URL}")
            print("Execute: python run_api.py")
            sys.exit(1)

    fluxo = [
        ("1. listarMedicamentos", "listarMedicamentos", {}),
        ("2. consultarDisponibilidade", "consultarDisponibilidade", params_consulta),
        ("3. criarReserva", "criarReserva", params_reserva),
    ]

    id_reserva_criada = None

    try:
        for titulo, operacao, params in fluxo:
            status, body = enviar_soap(operacao, params)
            exibir_resposta(titulo, status, body)
            if operacao == 'criarReserva' and status == 200:
                id_reserva_criada = extrair_id_reserva(body)

        if id_reserva_criada:
            status, body = enviar_soap('obterReserva', {'id_reserva': id_reserva_criada})
            exibir_resposta(f"4. obterReserva (id={id_reserva_criada})", status, body)
        else:
            print("\n4. obterReserva — pulado (criarReserva não retornou id)")

        status, body = enviar_soap('registrarBaixa', params_baixa)
        exibir_resposta("5. registrarBaixa", status, body)
    except URLError:
        print(f"\nErro: servidor não disponível em {SOAP_URL}")
        print("Execute: python run_api.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
