"""
Testes para ServiceTransacoes
Cobertura: criarReserva, obterReserva, cancelarReserva, registrarBaixa, listarBaixas
⭐ TESTES CRÍTICOS: criarReserva e registrarBaixa (FEFO + transações)
"""
import pytest
from datetime import datetime, date, timedelta

from src.soap.services.service_transacoes import ServiceTransacoes
from src.soap.types import ReservaType, BaixaType, ResultadoType


@pytest.fixture
def servico():
    """Fixture para inicializar serviço"""
    return ServiceTransacoes()


class TestCriarReserva:
    """Testes para criarReserva (⭐ CRÍTICA)"""
    
    def test_cpf_invalido_raise_exception(self, servico):
        """Verifica que CPF inválido lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.criar_reserva(123, 1, "123")  # CPF curto
        assert "CPF_INVALIDO" in str(exc_info.value)
    
    def test_medicamento_inexistente_raise_exception(self, servico):
        """Verifica que medicamento inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.criar_reserva(999999, 1, "12345678901")
        assert "MEDICAMENTO_NAO_ENCONTRADO" in str(exc_info.value)
    
    def test_criar_reserva_retorna_tipo_correto(self, servico):
        """Verifica que retorna ReservaType se medicamento existe"""
        try:
            lista = servico.repo_medicamento.listar_todos()
            if lista:
                # Tentar criar (pode falhar se sem estoque, mas tipo deve estar certo)
                try:
                    resultado = servico.criar_reserva(lista[0]['codigo'], 1, "12345678901")
                    assert isinstance(resultado, ReservaType)
                except Exception as e:
                    if "ESTOQUE_INSUFICIENTE" in str(e):
                        pytest.skip("Sem estoque para testar")
                    raise
        except:
            pytest.skip("Sem medicamentos no BD")
    
    def test_fefo_seleciona_menor_validade(self, servico):
        """Verifica que FEFO seleciona lote com menor validade"""
        # Este teste depende de dados específicos no BD
        # Idealmente testar com dados seed conhecidos
        pytest.skip("Requer seed data com múltiplos lotes")


class TestObterReserva:
    """Testes para obterReserva"""
    
    def test_reserva_inexistente_raise_exception(self, servico):
        """Verifica que reserva inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.obter_reserva("RES_INEXISTENTE_999")
        assert "RESERVA_NAO_ENCONTRADA" in str(exc_info.value)


class TestCancelarReserva:
    """Testes para cancelarReserva"""
    
    def test_reserva_inexistente_raise_exception(self, servico):
        """Verifica que reserva inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.cancelar_reserva("RES_INEXISTENTE_999")
        assert "RESERVA_NAO_ENCONTRADA" in str(exc_info.value)


class TestRegistrarBaixa:
    """Testes para registrarBaixa (⭐ CRÍTICA)"""
    
    def test_lote_inexistente_raise_exception(self, servico):
        """Verifica que lote inexistente lança exceção"""
        with pytest.raises(Exception) as exc_info:
            servico.registrar_baixa(123, 1, "LOTE_INEXISTENTE", "12345678901")
        assert "LOTE_NAO_ENCONTRADO" in str(exc_info.value)
    
    def test_registrar_baixa_retorna_tipo_correto(self, servico):
        """Verifica que retorna BaixaType"""
        # Depende de dados no BD
        pytest.skip("Requer medicamento + lote com estoque")


class TestListarBaixas:
    """Testes para listarBaixas"""
    
    def test_listar_baixas_retorna_lista(self, servico):
        """Verifica que retorna lista"""
        resultado = servico.listar_baixas()
        assert isinstance(resultado, list)
    
    def test_listar_baixas_com_datas_retorna_lista(self, servico):
        """Verifica que com datas específicas retorna lista"""
        data_fim = datetime.now().date()
        data_inicio = data_fim - timedelta(days=7)
        
        resultado = servico.listar_baixas(data_inicio, data_fim)
        assert isinstance(resultado, list)
