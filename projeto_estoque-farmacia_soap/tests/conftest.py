"""
Configuração de testes para SOAP services
Fixtures e helpers para testes
"""
import pytest
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

@pytest.fixture(scope="session")
def db_test():
    """Fixture para BD de testes (conecta ao PostgreSQL)"""
    from src.config.database import db
    db.connect()
    yield db
    db.close()


@pytest.fixture
def cleanup_after_test(db_test):
    """Fixture para limpar dados de teste após cada teste"""
    yield
    # Aqui você pode adicionar lógica de cleanup se necessário
    # Por exemplo: rollback de transações abertas


@pytest.fixture
def mock_service_medicamentos():
    """Fixture para mock de ServiceMedicamentos"""
    from src.soap.services.service_medicamentos import ServiceMedicamentos
    return ServiceMedicamentos()


@pytest.fixture
def mock_service_estoque():
    """Fixture para mock de ServiceEstoque"""
    from src.soap.services.service_estoque import ServiceEstoque
    return ServiceEstoque()


@pytest.fixture
def mock_service_transacoes():
    """Fixture para mock de ServiceTransacoes"""
    from src.soap.services.service_transacoes import ServiceTransacoes
    return ServiceTransacoes()


@pytest.fixture
def mock_service_integracao():
    """Fixture para mock de ServiceIntegracao"""
    from src.soap.services.service_integracao import ServiceIntegracao
    return ServiceIntegracao()
