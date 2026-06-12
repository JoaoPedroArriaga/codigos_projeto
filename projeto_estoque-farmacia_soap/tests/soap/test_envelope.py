"""
Testes unitários para envelope SOAP e HMAC (sem banco de dados)
"""
from src.soap.handlers.envelope import SOAPEnvelope
from src.utils.hash_utils import calcular_hmac_body_soap


ENVELOPE_COM_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://estoque-farmacia.projeto.interop/v1">
  <soap:Header>
    <tns:autenticacao>
      <tns:hash>abc123</tns:hash>
      <tns:timestamp>2026-06-09T10:00:00Z</tns:timestamp>
      <tns:grupo_origem>GRUPO_2</tns:grupo_origem>
      <tns:algoritmo>HMAC-SHA256</tns:algoritmo>
    </tns:autenticacao>
  </soap:Header>
  <soap:Body>
    <tns:obterMedicamento>
      <tns:codigo>789123</tns:codigo>
    </tns:obterMedicamento>
  </soap:Body>
</soap:Envelope>"""


class TestParsearEnvelope:
    def test_extrai_operacao_e_parametros(self):
        operacao, params, header, body = SOAPEnvelope.parsear_envelope(ENVELOPE_COM_HEADER)

        assert operacao == 'obterMedicamento'
        assert params['codigo'] == '789123'
        assert body is not None

    def test_extrai_header_aninhado(self):
        _, _, header, _ = SOAPEnvelope.parsear_envelope(ENVELOPE_COM_HEADER)

        assert header['hash'] == 'abc123'
        assert header['timestamp'] == '2026-06-09T10:00:00Z'
        assert header['grupo_origem'] == 'GRUPO_2'
        assert header['algoritmo'] == 'HMAC-SHA256'

    def test_envelope_invalido_retorna_none(self):
        operacao, params, header, body = SOAPEnvelope.parsear_envelope('<invalid>')

        assert operacao is None
        assert params is None
        assert header is None
        assert body is None


class TestHmacBody:
    def test_hash_consistente_para_mesmo_body(self):
        body1 = SOAPEnvelope.montar_body_requisicao('listarMedicamentos', {})
        body2 = SOAPEnvelope.montar_body_requisicao('listarMedicamentos', {})

        assert calcular_hmac_body_soap(body1) == calcular_hmac_body_soap(body2)

    def test_hash_diferente_para_operacoes_diferentes(self):
        body_listar = SOAPEnvelope.montar_body_requisicao('listarMedicamentos', {})
        body_obter = SOAPEnvelope.montar_body_requisicao('obterMedicamento', {'codigo': 1})

        assert calcular_hmac_body_soap(body_listar) != calcular_hmac_body_soap(body_obter)

    def test_hash_do_envelope_parseado_confere(self):
        operacao, params, header, body = SOAPEnvelope.parsear_envelope(ENVELOPE_COM_HEADER)
        hash_calculado = calcular_hmac_body_soap(body)

        assert operacao == 'obterMedicamento'
        assert len(hash_calculado) == 64
        assert hash_calculado != header['hash']


class TestMontarEnvelope:
    def test_criar_envelope_com_resposta(self):
        resultado = {'success': True, 'mensagem': 'OK'}
        body = SOAPEnvelope.montar_body_resposta('cancelarReserva', resultado)
        hash_val = calcular_hmac_body_soap(body)
        envelope = SOAPEnvelope.criar_resposta(
            'cancelarReserva', resultado, hash_val, '2026-06-09T10:00:00Z'
        )
        xml = SOAPEnvelope.serializar_xml(envelope)

        assert 'cancelarReservaResponse' in xml
        assert hash_val in xml
