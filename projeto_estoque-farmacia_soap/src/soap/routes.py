"""
Rotas SOAP montáveis na aplicação FastAPI principal.
"""
import os
import traceback
from datetime import datetime

from fastapi import APIRouter, Request, Response

from src.soap.handlers.envelope import SOAPEnvelope
from src.soap.services.service_medicamentos import ServiceMedicamentos
from src.soap.services.service_estoque import ServiceEstoque
from src.soap.services.service_transacoes import ServiceTransacoes
from src.soap.services.service_integracao import ServiceIntegracao
from src.utils.hash_utils import calcular_hmac_envelope_xml, calcular_hmac_body_soap
from src.config.database import db

WSDL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'wsdl',
    'estoque_farmacia.wsdl'
)

service_medicamentos = ServiceMedicamentos()
service_estoque = ServiceEstoque()
service_transacoes = ServiceTransacoes()
service_integracao = ServiceIntegracao()

OPERACOES_MAP = {
    'listarMedicamentos': (service_medicamentos, 'listar_medicamentos', []),
    'obterMedicamento': (service_medicamentos, 'obter_medicamento', ['codigo']),
    'sincronizarMedicamentos': (service_medicamentos, 'sincronizar_medicamentos', ['arquivo_xml', 'grupo_origem']),
    'obterEstoque': (service_estoque, 'obter_estoque', ['codigo_medicamento']),
    'listarLotes': (service_estoque, 'listar_lotes', ['codigo_medicamento']),
    'consultarDisponibilidade': (service_estoque, 'consultar_disponibilidade', ['codigo_medicamento', 'quantidade', 'cpf_paciente']),
    'verificarReservas': (service_estoque, 'verificar_reservas', ['codigo_medicamento']),
    'gerarAlerta': (service_estoque, 'gerar_alerta', ['codigo_medicamento', 'quantidade_minima']),
    'criarReserva': (service_transacoes, 'criar_reserva', ['codigo_medicamento', 'quantidade', 'cpf_paciente']),
    'obterReserva': (service_transacoes, 'obter_reserva', ['id_reserva']),
    'cancelarReserva': (service_transacoes, 'cancelar_reserva', ['id_reserva']),
    'listarReservas': (service_transacoes, 'listar_reservas', []),
    'registrarBaixa': (service_transacoes, 'registrar_baixa', ['codigo_medicamento', 'quantidade', 'numero_lote', 'cpf_paciente', 'motivo']),
    'listarBaixas': (service_transacoes, 'listar_baixas', ['data_inicio', 'data_fim']),
    'gerarRelatorioConsumo': (service_integracao, 'gerar_relatorio_consumo', ['data_inicio', 'data_fim']),
    'consultarStatusPaciente': (service_integracao, 'consultar_status_paciente', ['cpf']),
    'sincronizarStatusFinanceiro': (service_integracao, 'sincronizar_status_financeiro', ['arquivo_xml', 'grupo_origem']),
}

router = APIRouter(tags=["SOAP"])


def _gerar_fault(codigo: str, mensagem: str, detalhes: str = None) -> Response:
    fault_envelope = SOAPEnvelope.criar_fault(codigo, mensagem, detalhes)
    xml_fault = SOAPEnvelope.serializar_xml(fault_envelope, pretty=False)
    return Response(
        content=xml_fault,
        media_type="application/soap+xml; charset=utf-8",
        status_code=500
    )


def _extrair_codigo_erro(erro_string: str) -> str:
    codigos = [
        "MEDICAMENTO_NAO_ENCONTRADO", "ESTOQUE_INSUFICIENTE", "LOTE_NAO_ENCONTRADO",
        "RESERVA_NAO_ENCONTRADA", "CPF_INVALIDO", "XML_INVALIDO",
        "ASSINATURA_INVALIDA", "ERRO_BANCO_DADOS", "RESERVA_JA_CANCELADA", "LOTE_VENCIDO"
    ]
    for codigo in codigos:
        if codigo in erro_string:
            return codigo
    return "OPERACAO_NAO_AUTORIZADA"


def _converter_resultado(resultado) -> dict:
    if hasattr(resultado, 'para_dict'):
        return resultado.para_dict()
    if isinstance(resultado, list):
        return {'itens': [r.para_dict() if hasattr(r, 'para_dict') else r for r in resultado]}
    if isinstance(resultado, tuple):
        return {
            'arquivo_xml': resultado[0],
            'resultado': resultado[1].para_dict()
        }
    return resultado


def _converter_parametros(parametros: dict, params_esperados: list) -> list:
    args = []
    for param_nome in params_esperados:
        valor = parametros.get(param_nome)
        if param_nome in ['codigo', 'codigo_medicamento', 'quantidade', 'quantidade_minima', 'id_prescricao']:
            valor = int(valor) if valor else None
        elif param_nome in ['data_inicio', 'data_fim']:
            if valor and valor != 'None':
                valor = datetime.fromisoformat(valor).date()
            else:
                valor = None
        args.append(valor)
    return args


@router.get("/soap")
async def wsdl(request: Request):
    """Servir WSDL (GET /soap ou GET /soap?wsdl)"""
    try:
        with open(WSDL_PATH, 'r', encoding='utf-8') as f:
            return Response(
                content=f.read(),
                media_type="application/xml; charset=utf-8"
            )
    except Exception as e:
        xml_fault = SOAPEnvelope.serializar_xml(
            SOAPEnvelope.criar_fault("WSDL_NAO_ENCONTRADO", f"Erro ao carregar WSDL: {str(e)}")
        )
        return Response(content=xml_fault, media_type="application/soap+xml; charset=utf-8", status_code=500)


@router.post("/soap")
async def soap_endpoint(request: Request):
    """Endpoint SOAP principal"""
    try:
        body_bytes = await request.body()
        body_xml = body_bytes.decode('utf-8')

        if not body_xml.strip():
            return _gerar_fault("SOAP_VAZIO", "Body SOAP vazio")

        operacao_nome, parametros, header, body_element = SOAPEnvelope.parsear_envelope(body_xml)

        if operacao_nome is None:
            return _gerar_fault("ENVELOPE_INVALIDO", "Envelope SOAP inválido ou malformado")

        if header:
            hash_recebido = header.get('hash')
            if hash_recebido:
                try:
                    hash_calculado = calcular_hmac_envelope_xml(body_xml)
                    if hash_recebido != hash_calculado:
                        return _gerar_fault(
                            "ASSINATURA_INVALIDA",
                            "Hash HMAC-SHA256 não confere",
                            f"Esperado: {hash_calculado}, Recebido: {hash_recebido}"
                        )
                except Exception as e:
                    return _gerar_fault("ERRO_VALIDACAO_ASSINATURA", str(e))

        if operacao_nome not in OPERACOES_MAP:
            return _gerar_fault(
                "OPERACAO_NAO_ENCONTRADA",
                f"Operação '{operacao_nome}' não existe em WSDL"
            )

        servico, metodo_nome, params_esperados = OPERACOES_MAP[operacao_nome]

        try:
            args = _converter_parametros(parametros, params_esperados)
            metodo = getattr(servico, metodo_nome)
            resultado = metodo(*args)
            resultado_dict = _converter_resultado(resultado)

            body_resposta = SOAPEnvelope.montar_body_resposta(operacao_nome, resultado_dict)
            hash_resposta = calcular_hmac_body_soap(body_resposta)

            envelope_resposta = SOAPEnvelope.criar_resposta(
                operacao_nome,
                resultado_dict,
                hash_resposta,
                datetime.now().isoformat(),
                grupo_origem="GRUPO_3"
            )

            xml_resposta = SOAPEnvelope.serializar_xml(envelope_resposta, pretty=False)
            return Response(
                content=xml_resposta,
                media_type="application/soap+xml; charset=utf-8"
            )
        except Exception as operacao_error:
            return _gerar_fault(
                _extrair_codigo_erro(str(operacao_error)),
                str(operacao_error),
                traceback.format_exc()
            )
    except Exception as erro_geral:
        return _gerar_fault("ERRO_INTERNO", str(erro_geral), traceback.format_exc())


@router.get("/soap/health")
async def soap_health():
    """Health check do serviço SOAP"""
    try:
        db.execute("SELECT 1", fetch_one=True)
        return {
            "status": "ok",
            "database": "conectado",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "erro",
            "database": "desconectado",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def registrar_rotas_soap(app):
    """Monta as rotas SOAP na aplicação FastAPI"""
    app.include_router(router)
