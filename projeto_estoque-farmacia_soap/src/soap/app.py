"""
Servidor SOAP - FastAPI endpoint para /soap
Responsável por:
1. Receber SOAP requests (XML POST)
2. Validar HMAC-SHA256 no header
3. Rotear para serviço correto
4. Executar operação
5. Retornar SOAP response (XML)
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import XMLResponse
from datetime import datetime
import json
import traceback

from src.soap.handlers.envelope import SOAPEnvelope
from src.soap.types import ResultadoType
from src.soap.services.service_medicamentos import ServiceMedicamentos
from src.soap.services.service_estoque import ServiceEstoque
from src.soap.services.service_transacoes import ServiceTransacoes
from src.soap.services.service_integracao import ServiceIntegracao
from src.utils.hash_utils import calcular_hmac, validar_assinatura
from src.config.database import db


# ===== Inicializar serviços =====
service_medicamentos = ServiceMedicamentos()
service_estoque = ServiceEstoque()
service_transacoes = ServiceTransacoes()
service_integracao = ServiceIntegracao()


# ===== Mapeamento de operações → serviços =====
OPERACOES_MAP = {
    # ServiceMedicamentos
    'listarMedicamentos': (service_medicamentos, 'listar_medicamentos', []),
    'obterMedicamento': (service_medicamentos, 'obter_medicamento', ['codigo']),
    'sincronizarMedicamentos': (service_medicamentos, 'sincronizar_medicamentos', ['arquivo_xml', 'grupo_origem']),
    
    # ServiceEstoque
    'obterEstoque': (service_estoque, 'obter_estoque', ['codigo_medicamento']),
    'listarLotes': (service_estoque, 'listar_lotes', ['codigo_medicamento']),
    'consultarDisponibilidade': (service_estoque, 'consultar_disponibilidade', ['codigo_medicamento', 'quantidade', 'cpf_paciente']),
    'verificarReservas': (service_estoque, 'verificar_reservas', ['codigo_medicamento']),
    'gerarAlerta': (service_estoque, 'gerar_alerta', ['codigo_medicamento', 'quantidade_minima']),
    
    # ServiceTransacoes
    'criarReserva': (service_transacoes, 'criar_reserva', ['codigo_medicamento', 'quantidade', 'cpf_paciente']),
    'obterReserva': (service_transacoes, 'obter_reserva', ['id_reserva']),
    'cancelarReserva': (service_transacoes, 'cancelar_reserva', ['id_reserva']),
    'registrarBaixa': (service_transacoes, 'registrar_baixa', ['codigo_medicamento', 'quantidade', 'numero_lote', 'cpf_paciente', 'motivo']),
    'listarBaixas': (service_transacoes, 'listar_baixas', ['data_inicio', 'data_fim']),
    
    # ServiceIntegracao
    'gerarRelatorioConsumo': (service_integracao, 'gerar_relatorio_consumo', ['data_inicio', 'data_fim']),
    'consultarStatusPaciente': (service_integracao, 'consultar_status_paciente', ['cpf']),
    'sincronizarStatusFinanceiro': (service_integracao, 'sincronizar_status_financeiro', ['arquivo_xml', 'grupo_origem']),
}


def criar_app():
    """Factory para criar aplicação FastAPI com rotas SOAP"""
    app = FastAPI(
        title="Estoque Farmácia - SOAP API v1",
        description="API SOAP para gerenciamento de estoque farmacêutico",
        version="1.0"
    )
    
    @app.get("/soap", response_class=XMLResponse)
    async def wsdl():
        """Servir WSDL (GET /soap?wsdl)"""
        try:
            with open('src/wsdl/estoque_farmacia.wsdl', 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return SOAPEnvelope.criar_fault(
                "WSDL_NAO_ENCONTRADO",
                f"Erro ao carregar WSDL: {str(e)}"
            )
    
    @app.post("/soap", response_class=XMLResponse)
    async def soap_endpoint(request: Request):
        """
        Endpoint SOAP principal
        
        Fluxo:
        1. Receber XML do body
        2. Parsear envelope SOAP
        3. Validar HMAC-SHA256 do header
        4. Extrair operação + parâmetros
        5. Chamar serviço correto
        6. Gerar SOAP response
        7. Retornar como XML
        """
        try:
            # 1. Receber XML
            body_bytes = await request.body()
            body_xml = body_bytes.decode('utf-8')
            
            if not body_xml.strip():
                return _gerar_fault("SOAP_VAZIO", "Body SOAP vazio")
            
            # 2. Parsear envelope
            operacao_nome, parametros, header = SOAPEnvelope.parsear_envelope(body_xml)
            
            if operacao_nome is None:
                return _gerar_fault("ENVELOPE_INVALIDO", "Envelope SOAP inválido ou malformado")
            
            # 3. Validar HMAC-SHA256 do header
            if header:
                hash_recebido = header.get('autenticacao/hash') or header.get('hash')
                if hash_recebido:
                    try:
                        # Extrair body sem header para validação
                        # Calcular novo hash
                        hash_calculado = calcular_hmac(str(parametros))
                        
                        if hash_recebido != hash_calculado:
                            return _gerar_fault(
                                "ASSINATURA_INVALIDA",
                                "Hash HMAC-SHA256 não confere",
                                f"Esperado: {hash_calculado}, Recebido: {hash_recebido}"
                            )
                    except Exception as e:
                        return _gerar_fault("ERRO_VALIDACAO_ASSINATURA", str(e))
            
            # 4. Extrair grupo origem do header (para auditoria)
            grupo_origem = header.get('grupo_origem', 'DESCONHECIDO') if header else 'DESCONHECIDO'
            timestamp_entrada = header.get('timestamp', datetime.now().isoformat()) if header else datetime.now().isoformat()
            
            # 5. Validar operação existe
            if operacao_nome not in OPERACOES_MAP:
                return _gerar_fault(
                    "OPERACAO_NAO_ENCONTRADA",
                    f"Operação '{operacao_nome}' não existe em WSDL"
                )
            
            # 6. Chamar serviço
            servico, metodo_nome, params_esperados = OPERACOES_MAP[operacao_nome]
            
            try:
                # Extrair parâmetros esperados do dicionário recebido
                args = []
                for param_nome in params_esperados:
                    valor = parametros.get(param_nome)
                    
                    # Conversão de tipos se necessário
                    if param_nome in ['codigo', 'codigo_medicamento', 'quantidade', 'quantidade_minima', 'id_prescricao']:
                        valor = int(valor) if valor else None
                    elif param_nome in ['data_inicio', 'data_fim']:
                        from datetime import datetime as dt
                        if valor and valor != 'None':
                            valor = dt.fromisoformat(valor).date()
                        else:
                            valor = None
                    
                    args.append(valor)
                
                # Chamar método do serviço
                metodo = getattr(servico, metodo_nome)
                resultado = metodo(*args)
                
                # 7. Gerar SOAP response
                # Converter resultado para dict se for tipo SOAP
                if hasattr(resultado, 'para_dict'):
                    resultado_dict = resultado.para_dict()
                elif isinstance(resultado, list):
                    # Lista de tipos
                    resultado_dict = {
                        'itens': [r.para_dict() if hasattr(r, 'para_dict') else r for r in resultado]
                    }
                elif isinstance(resultado, tuple):
                    # Tuple (xml_string, resultado_type) - para gerarRelatorioConsumo
                    resultado_dict = {
                        'arquivo_xml': resultado[0],
                        'resultado': resultado[1].para_dict()
                    }
                else:
                    resultado_dict = resultado
                
                # Calcular novo hash para resposta
                hash_resposta = calcular_hmac(str(resultado_dict))
                
                # Criar envelope de resposta
                envelope_resposta = SOAPEnvelope.criar_resposta(
                    operacao_nome,
                    resultado_dict,
                    hash_resposta,
                    datetime.now().isoformat(),
                    grupo_origem="GRUPO_3"
                )
                
                # 8. Serializar e retornar
                xml_resposta = SOAPEnvelope.serializar_xml(envelope_resposta, pretty=False)
                return Response(
                    content=xml_resposta,
                    media_type="application/soap+xml; charset=utf-8"
                )
            
            except Exception as operacao_error:
                # Erro na execução da operação
                return _gerar_fault(
                    _extrair_codigo_erro(str(operacao_error)),
                    str(operacao_error),
                    traceback.format_exc()
                )
        
        except Exception as erro_geral:
            # Erro geral (parsing, header, etc)
            return _gerar_fault(
                "ERRO_INTERNO",
                str(erro_geral),
                traceback.format_exc()
            )
    
    @app.get("/soap/health")
    async def health():
        """Health check"""
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
    
    return app


def _gerar_fault(codigo: str, mensagem: str, detalhes: str = None) -> Response:
    """Helper para gerar SOAP Fault"""
    fault_envelope = SOAPEnvelope.criar_fault(codigo, mensagem, detalhes)
    xml_fault = SOAPEnvelope.serializar_xml(fault_envelope, pretty=False)
    return Response(
        content=xml_fault,
        media_type="application/soap+xml; charset=utf-8",
        status_code=500
    )


def _extrair_codigo_erro(erro_string: str) -> str:
    """Extrai código de erro da exception string"""
    if "MEDICAMENTO_NAO_ENCONTRADO" in erro_string:
        return "MEDICAMENTO_NAO_ENCONTRADO"
    elif "ESTOQUE_INSUFICIENTE" in erro_string:
        return "ESTOQUE_INSUFICIENTE"
    elif "LOTE_NAO_ENCONTRADO" in erro_string:
        return "LOTE_NAO_ENCONTRADO"
    elif "RESERVA_NAO_ENCONTRADA" in erro_string:
        return "RESERVA_NAO_ENCONTRADA"
    elif "CPF_INVALIDO" in erro_string:
        return "CPF_INVALIDO"
    elif "XML_INVALIDO" in erro_string:
        return "XML_INVALIDO"
    elif "ASSINATURA_INVALIDA" in erro_string:
        return "ASSINATURA_INVALIDA"
    elif "ERRO_BANCO_DADOS" in erro_string:
        return "ERRO_BANCO_DADOS"
    else:
        return "OPERACAO_NAO_AUTORIZADA"


# Criar app
app = criar_app()


if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor SOAP na porta 8000")
    print("📖 WSDL disponível em: http://localhost:8000/soap?wsdl")
    print("📝 Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
