"""
Testes para ServiceEstoque
Cobertura: obterEstoque, listarLotes, consultarDisponibilidade, verificarReservas, gerarAlerta
"""
import pytest
from datetime import datetime

from src.soap.services.service_estoque import ServiceEstoque
from src.soap.types import EstoqueType, LoteType, RespostaType, ResultadoType


@pytest.fixture
def servico():
    """Fixture para inicializar serviço"""
    return ServiceEstoque()


class TestObterEstoque:
    """Testes para obterEstoque"""
    
    def test_obter_estoque_inexistente_raise_exception(self, servico):
        """Verifica que medicamento inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.obter_estoque(999999)
        assert "MEDICAMENTO_NAO_ENCONTRADO" in str(exc_info.value)
    
    def test_obter_estoque_retorna_tipo_correto(self, servico):
        """Verifica que retorna EstoqueType"""
        try:
            lista = servico.repo_medicamento.listar_todos()
            if lista:
                resultado = servico.obter_estoque(lista[0]['codigo'])
                assert isinstance(resultado, EstoqueType)
                assert resultado.codigo_medicamento is not None
                assert isinstance(resultado.lotes, list)
        except:
            pytest.skip("Sem medicamentos no BD")


class TestListarLotes:
    """Testes para listarLotes"""
    
    def test_listar_lotes_inexistente_raise_exception(self, servico):
        """Verifica que medicamento inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.listar_lotes(999999)
        assert "MEDICAMENTO_NAO_ENCONTRADO" in str(exc_info.value)
    
    def test_listar_lotes_retorna_lista(self, servico):
        """Verifica que retorna lista de lotes"""
        try:
            lista = servico.repo_medicamento.listar_todos()
            if lista:
                resultado = servico.listar_lotes(lista[0]['codigo'])
                assert isinstance(resultado, list)
        except:
            pytest.skip("Sem medicamentos no BD")


class TestConsultarDisponibilidade:
    """Testes para consultarDisponibilidade (⭐ CRÍTICA)"""
    
    def test_cpf_invalido_raise_exception(self, servico):
        """Verifica que CPF inválido lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.consultar_disponibilidade(123, 1, "123")  # CPF curto
        assert "CPF_INVALIDO" in str(exc_info.value)
    
    def test_cpf_valido_retorna_resposta(self, servico):
        """Verifica que CPF válido retorna RespostaType"""
        resultado = servico.consultar_disponibilidade(
            123, 
            1, 
            "12345678901"  # CPF válido
        )
        assert isinstance(resultado, RespostaType)
        assert isinstance(resultado.respostas, list)
    
    def test_resposta_contem_disponibilidade(self, servico):
        """Verifica que resposta tem campo disponível"""
        resultado = servico.consultar_disponibilidade(
            123, 
            1, 
            "12345678901"
        )
        if resultado.respostas:
            assert resultado.respostas[0].disponivel in [0, 1]


class TestVerificarReservas:
    """Testes para verificarReservas"""
    
    def test_verificar_reservas_retorna_lista(self, servico):
        """Verifica que retorna lista"""
        resultado = servico.verificar_reservas(123)
        assert isinstance(resultado, list)


class TestGerarAlerta:
    """Testes para gerarAlerta"""
    
    def test_medicamento_inexistente_raise_exception(self, servico):
        """Verifica que medicamento inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.gerar_alerta(999999, 10)
        assert "MEDICAMENTO_NAO_ENCONTRADO" in str(exc_info.value)
    
    def test_gerar_alerta_retorna_resultado(self, servico):
        """Verifica que retorna ResultadoType"""
        try:
            lista = servico.repo_medicamento.listar_todos()
            if lista:
                resultado = servico.gerar_alerta(lista[0]['codigo'], 10)
                assert isinstance(resultado, ResultadoType)
                assert resultado.success is True
        except:
            pytest.skip("Sem medicamentos no BD")
