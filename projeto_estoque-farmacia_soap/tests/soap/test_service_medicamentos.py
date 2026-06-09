"""
Testes para ServiceMedicamentos
Cobertura: listarMedicamentos, obterMedicamento, sincronizarMedicamentos
"""
import pytest
from datetime import datetime
from lxml import etree

from src.soap.services.service_medicamentos import ServiceMedicamentos
from src.soap.types import MedicamentoType


@pytest.fixture
def servico():
    """Fixture para inicializar serviço"""
    return ServiceMedicamentos()


class TestListarMedicamentos:
    """Testes para listarMedicamentos"""
    
    def test_listar_retorna_lista(self, servico):
        """Verifica que listar_medicamentos retorna lista"""
        resultado = servico.listar_medicamentos()
        assert isinstance(resultado, list)
        if resultado:  # Se houver medicamentos no BD
            assert isinstance(resultado[0], MedicamentoType)
    
    def test_medicamento_tem_codigo_nome(self, servico):
        """Verifica que medicamento tem campos obrigatórios"""
        resultado = servico.listar_medicamentos()
        if resultado:
            med = resultado[0]
            assert med.codigo is not None
            assert med.nome is not None


class TestObterMedicamento:
    """Testes para obterMedicamento"""
    
    def test_obter_medicamento_inexistente_raise_exception(self, servico):
        """Verifica que medicamento inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.obter_medicamento(999999)
        assert "MEDICAMENTO_NAO_ENCONTRADO" in str(exc_info.value)
    
    def test_obter_medicamento_valido_retorna_tipo(self, servico):
        """Verifica que medicamento válido retorna MedicamentoType"""
        # Primeiro listar para pegar um válido
        lista = servico.listar_medicamentos()
        if lista:
            primeiro = lista[0]
            resultado = servico.obter_medicamento(primeiro.codigo)
            
            assert isinstance(resultado, MedicamentoType)
            assert resultado.codigo == primeiro.codigo
            assert resultado.nome == primeiro.nome


class TestSincronizarMedicamentos:
    """Testes para sincronizarMedicamentos"""
    
    def test_xml_vazio_raise_exception(self, servico):
        """Verifica que XML vazio lança exceção"""
        xml_vazio = "<medicamentos></medicamentos>"
        with pytest.raises(Exception) as exc_info:
            servico.sincronizar_medicamentos(xml_vazio, "GRUPO_1")
        assert "XML_INVALIDO" in str(exc_info.value)
    
    def test_xml_malformado_raise_exception(self, servico):
        """Verifica que XML malformado lança exceção"""
        xml_ruim = "<medicamentos><medicamento>sem fechar"
        with pytest.raises(Exception) as exc_info:
            servico.sincronizar_medicamentos(xml_ruim, "GRUPO_1")
        assert "XML_INVALIDO" in str(exc_info.value)
    
    def test_xml_falta_campos_raise_exception(self, servico):
        """Verifica que XML sem campos obrigatórios lança exceção"""
        xml_incompleto = """
        <medicamentos>
            <medicamento>
                <codigo>123</codigo>
            </medicamento>
        </medicamentos>
        """
        with pytest.raises(Exception) as exc_info:
            servico.sincronizar_medicamentos(xml_incompleto, "GRUPO_1")
        assert "XML_INVALIDO" in str(exc_info.value)
    
    def test_xml_codigo_nao_numero_raise_exception(self, servico):
        """Verifica que código não numérico lança exceção"""
        xml_bad_codigo = """
        <medicamentos>
            <medicamento>
                <codigo>ABC</codigo>
                <nome>Teste</nome>
            </medicamento>
        </medicamentos>
        """
        with pytest.raises(Exception) as exc_info:
            servico.sincronizar_medicamentos(xml_bad_codigo, "GRUPO_1")
        assert "XML_INVALIDO" in str(exc_info.value)
    
    def test_sincronizacao_valida_retorna_resultado(self, servico):
        """Verifica que XML válido sincroniza com sucesso"""
        xml_valido = f"""
        <medicamentos>
            <medicamento>
                <codigo>{9999 + int(datetime.now().timestamp())}</codigo>
                <nome>Medicamento Teste</nome>
            </medicamento>
        </medicamentos>
        """
        resultado = servico.sincronizar_medicamentos(xml_valido, "GRUPO_1")
        
        assert resultado.success is True
        assert resultado.timestamp is not None
        assert "Sincronizados" in resultado.mensagem
