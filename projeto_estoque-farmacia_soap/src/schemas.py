"""
Schemas Pydantic para validação de requisições e respostas.
Seguindo DRY e Single Responsibility.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
import re


class MedicamentoSchema(BaseModel):
    """Schema para dados de medicamento"""
    codigo: int = Field(..., gt=0, description="Código único do medicamento")
    nome: str = Field(..., min_length=1, max_length=255, description="Nome do medicamento")
    
    class Config:
        from_attributes = True


class MedicamentoResponseSchema(MedicamentoSchema):
    """Schema de resposta com dados adicionais"""
    id: Optional[int] = None


class LoteSchema(BaseModel):
    """Schema para dados de lote"""
    numero_lote: str = Field(..., min_length=1, description="Número do lote")
    codigo_medicamento: int = Field(..., gt=0, description="Código do medicamento")
    quantidade_inicial: int = Field(..., gt=0, description="Quantidade inicial")
    quantidade_atual: int = Field(..., ge=0, description="Quantidade atual")
    data_validade: date = Field(..., description="Data de validade")
    preco_venda: float = Field(..., gt=0, description="Preço de venda")
    
    class Config:
        from_attributes = True


class LoteResponseSchema(LoteSchema):
    """Schema de resposta com IDs"""
    id_lote: Optional[int] = None


class ConsultaRequestSchema(BaseModel):
    """Schema para requisição de consulta"""
    codigo_medicamento: int = Field(..., gt=0, description="Código do medicamento")
    quantidade: int = Field(..., gt=0, description="Quantidade desejada")
    cpf_paciente: str = Field(..., description="CPF com 11 dígitos")
    
    @field_validator('cpf_paciente')
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        cpf_limpo = re.sub(r'[^0-9]', '', v)
        if len(cpf_limpo) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf_limpo


class ResposaItemSchema(BaseModel):
    """Schema para um item de resposta de consulta (baseado em resposta.xsd)"""
    codigo_medicamento: int
    disponivel: int = Field(..., description="0 ou 1 (0=indisponível, 1=disponível)")
    observacao: Optional[str] = None


class ConsultaResponseSchema(BaseModel):
    """Schema de resposta de consulta (baseado em resposta.xsd, sem assinatura)"""
    respostas: List[ResposaItemSchema]


class ReservaRequestSchema(BaseModel):
    """
    Schema para requisição de reserva - FEFO: lote é definido pelo sistema
    O campo lote NÃO é necessário - o sistema seleciona automaticamente
    """
    codigo_medicamento: int = Field(..., gt=0, description="Código do medicamento")
    quantidade: int = Field(..., gt=0, description="Quantidade desejada")
    cpf_paciente: str = Field(..., description="CPF com 11 dígitos")
    
    @field_validator('cpf_paciente')
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        cpf_limpo = re.sub(r'[^0-9]', '', v)
        if len(cpf_limpo) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf_limpo


class ReservaResponseSchema(BaseModel):
    """Schema de resposta de reserva com informações do lote selecionado via FEFO"""
    success: bool
    id_reserva: Optional[str] = None
    lote_selecionado: Optional[str] = Field(None, description="Lote selecionado automaticamente pelo FEFO")
    data_validade: Optional[date] = Field(None, description="Data de validade do lote selecionado")
    preco: Optional[float] = Field(None, description="Preço do medicamento")
    mensagem: str
    timestamp: datetime


class BaixaRequestSchema(BaseModel):
    """Schema para requisição de baixa"""
    codigo_medicamento: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)
    lote: str = Field(..., min_length=1)
    motivo: Optional[str] = None


class BaixaResponseSchema(BaseModel):
    """Schema de resposta de baixa"""
    success: bool
    id_baixa: Optional[str] = None
    quantidade_restante: Optional[int] = None
    mensagem: str
    timestamp: datetime


class EstoqueResponseSchema(BaseModel):
    """Schema de resposta de estoque"""
    codigo_medicamento: int
    nome_medicamento: str
    quantidade_total: int
    lotes: List[LoteResponseSchema]


class ErroResponseSchema(BaseModel):
    """Schema para respostas de erro"""
    success: bool = False
    erro: str
    detalhes: Optional[dict] = None
    timestamp: datetime