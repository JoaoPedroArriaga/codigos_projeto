"""
Schemas Pydantic para validação de requisições e respostas.
Seguindo DRY e Single Responsibility.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


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
    cpf_paciente: str = Field(..., pattern=r"^\d{11}$", description="CPF com 11 dígitos")


class ConsultaResponseSchema(BaseModel):
    """Schema de resposta de consulta"""
    success: bool
    disponivel: bool
    lote: Optional[str] = None
    validade: Optional[date] = None
    preco: Optional[float] = None
    mensagem: str


class ReservaRequestSchema(BaseModel):
    """Schema para requisição de reserva"""
    codigo_medicamento: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)
    lote: str = Field(..., min_length=1)
    cpf_paciente: str = Field(..., pattern=r"^\d{11}$")


class ReservaResponseSchema(BaseModel):
    """Schema de resposta de reserva"""
    success: bool
    id_reserva: Optional[str] = None
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
