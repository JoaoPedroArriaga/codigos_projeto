"""
Tipos SOAP - Mapeamento entre tipos Python e estruturas XML SOAP
Alinhados com XSDs: resposta.xsd, reserva.xsd, baixa.xsd
"""
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import List, Optional, Dict, Any


@dataclass
class MedicamentoType:
    """Tipo: Medicamento"""
    codigo: int
    nome: str
    id: Optional[int] = None
    
    def para_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LoteType:
    """Tipo: Lote (alinhado com resposta.xsd)"""
    numero_lote: str
    codigo_medicamento: int
    quantidade_atual: int
    data_validade: date
    preco_venda: float
    id_lote: Optional[int] = None
    quantidade_inicial: Optional[int] = None
    
    def para_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Converter date para string ISO
        if isinstance(data.get('data_validade'), date):
            data['data_validade'] = data['data_validade'].isoformat()
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class RespostaItemType:
    """Tipo: Item de Resposta (baseado em resposta.xsd)"""
    codigo_medicamento: int
    disponivel: int  # 0 ou 1
    observacao: Optional[str] = None
    
    def para_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RespostaType:
    """Tipo: Resposta (baseado em resposta.xsd)"""
    respostas: List[RespostaItemType]
    
    def para_dict(self) -> Dict[str, Any]:
        return {
            'respostas': [r.para_dict() for r in self.respostas]
        }


@dataclass
class ReservaType:
    """Tipo: Reserva (baseado em reserva.xsd)"""
    id_prescricao: int
    cpf_paciente: str
    codigo_medicamento: int
    quantidade: int
    numero_lote: str
    id_reserva: Optional[str] = None
    data_validade: Optional[date] = None
    preco: Optional[float] = None
    status: Optional[str] = None
    data_criacao: Optional[datetime] = None
    
    def para_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if isinstance(data.get('data_validade'), date):
            data['data_validade'] = data['data_validade'].isoformat()
        if isinstance(data.get('data_criacao'), datetime):
            data['data_criacao'] = data['data_criacao'].isoformat()
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class BaixaType:
    """Tipo: Baixa (baseado em baixa.xsd)"""
    id_prescricao: int
    cpf_paciente: str
    codigo_medicamento: int
    quantidade: int
    numero_lote: str
    id_baixa: Optional[str] = None
    motivo: Optional[str] = None
    data_uso: Optional[int] = None
    quantidade_restante: Optional[int] = None
    timestamp: Optional[datetime] = None
    
    def para_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class EstoqueType:
    """Tipo: Estoque (resposta de estoque)"""
    codigo_medicamento: int
    quantidade_total: int
    lotes: List[LoteType]
    nome_medicamento: Optional[str] = None
    
    def para_dict(self) -> Dict[str, Any]:
        return {
            'codigo_medicamento': self.codigo_medicamento,
            'quantidade_total': self.quantidade_total,
            'nome_medicamento': self.nome_medicamento,
            'lotes': [l.para_dict() for l in self.lotes]
        }


@dataclass
class AssinaturaType:
    """Tipo: Assinatura SOAP (HMAC-SHA256)"""
    hash: str
    timestamp: datetime
    grupo_origem: str
    algoritmo: str = "HMAC-SHA256"
    
    def para_dict(self) -> Dict[str, Any]:
        return {
            'hash': self.hash,
            'timestamp': self.timestamp.isoformat(),
            'grupo_origem': self.grupo_origem,
            'algoritmo': self.algoritmo
        }


@dataclass
class ErroType:
    """Tipo: Erro (Fault)"""
    codigo: str
    mensagem: str
    detalhes: Optional[str] = None
    
    def para_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ResultadoType:
    """Tipo: Status Resultado"""
    success: bool
    timestamp: datetime
    mensagem: Optional[str] = None
    
    def para_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'mensagem': self.mensagem,
            'timestamp': self.timestamp.isoformat()
        }
